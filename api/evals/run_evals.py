from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parent
ROOT_DIR = EVALS_DIR.parent.parent
SRC_DIR = ROOT_DIR / "src"
RESULTS_DIR = EVALS_DIR / "results"

for _path in (EVALS_DIR, SRC_DIR):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT_DIR / ".env")

from cases import CASES, EvalCase  # noqa: E402
from scoring import score_case  # noqa: E402


class _FakeMessage:
    content = '{"score": 5, "notes": "mocked"}'


class _FakeResponse:
    choices = [type("Choice", (), {"message": _FakeMessage()})()]


class _FakeCompletions:
    def create(self, *args, **kwargs):
        # A single generic mocked body, reused for every call kind — enough
        # to exercise the harness's plumbing (dispatch, scoring, result
        # persistence) without spending real API credits. Not useful for
        # actually judging prompt quality; use a real run for that.
        _FakeMessage.content = (
            "1. Simple Explanation\nMocked simple explanation for testing.\n\n"
            "2. Exam-Ready Answer\nMocked exam answer.\n\n"
            "3. Key Points\n- Point one\n- Point two\n- Point three\n\n"
            "4. Memory Tip\nMocked memory tip.\n\n"
            "5. Practice Question\nMocked practice question?"
        )
        return _FakeResponse()


class _FakeChat:
    completions = _FakeCompletions()


class _FakeClient:
    chat = _FakeChat()


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT_DIR, text=True
        ).strip()
    except Exception:
        return "unknown"


def _run_case(case: EvalCase, service) -> dict:
    started = time.monotonic()
    try:
        if case.kind == "teach_topic":
            output = service.teach_topic(subject_name=case.subject, topic_name=case.topic)
        elif case.kind == "answer_question":
            output = service.answer_exam_question(
                subject_name=case.subject, question_text=case.question, topic_name=case.topic
            )
        else:  # ask_tutor
            output = service.ask_tutor(subject_name=case.subject, question=case.question)
        elapsed = time.monotonic() - started
        return {"output": output, "elapsed_s": round(elapsed, 2), "error": None}
    except Exception as e:
        elapsed = time.monotonic() - started
        return {"output": None, "elapsed_s": round(elapsed, 2), "error": str(e)}


def _load_previous_result() -> dict | None:
    files = sorted(RESULTS_DIR.glob("*.json"))
    if not files:
        return None
    return json.loads(files[-1].read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run JIBA's LLM regression eval suite.")
    parser.add_argument(
        "--mock", action="store_true", help="Use a mocked OpenAI client (no real API calls/cost)."
    )
    parser.add_argument("--no-judge", action="store_true", help="Skip the LLM-as-judge scoring pass.")
    parser.add_argument("--case", help="Run only the case with this id.")
    args = parser.parse_args()

    import chat_engine
    from ktu_service import KtuService

    if args.mock:
        chat_engine.get_openai_client = lambda: _FakeClient()

    cases = [c for c in CASES if c.id == args.case] if args.case else CASES
    if not cases:
        print(f"No eval case with id '{args.case}'", file=sys.stderr)
        return 1

    judge_client = None
    if not args.no_judge:
        judge_client = _FakeClient() if args.mock else chat_engine.get_openai_client()

    results = []
    print(f"Running {len(cases)} eval case(s){' [MOCK]' if args.mock else ''}...\n")

    for case in cases:
        service = KtuService(user_id="eval_harness", department=case.department)
        run_result = _run_case(case, service)

        if run_result["error"]:
            score = None
            status = "ERROR"
        else:
            score = score_case(case, run_result["output"], judge_client=judge_client)
            status = "PASS" if score.passed else "FAIL"

        judge_str = f" judge={score.judge_score}/5" if score and score.judge_score is not None else ""
        print(f"  [{status:5}] {case.id} ({run_result['elapsed_s']}s){judge_str}")
        if score and not score.passed:
            failed_checks = [k for k, v in score.checks.items() if not v]
            if failed_checks:
                print(f"           failed checks: {', '.join(failed_checks)}")
        if run_result["error"]:
            print(f"           error: {run_result['error']}")

        results.append(
            {
                "case_id": case.id,
                "kind": case.kind,
                "status": status,
                "elapsed_s": run_result["elapsed_s"],
                "error": run_result["error"],
                "score": asdict(score) if score else None,
            }
        )

    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(),
        "mocked": args.mock,
        "total": len(results),
        "passed": sum(1 for r in results if r["status"] == "PASS"),
        "failed": sum(1 for r in results if r["status"] in ("FAIL", "ERROR")),
        "results": results,
    }

    print(f"\n{summary['passed']}/{summary['total']} passed.")

    previous = _load_previous_result()
    if previous:
        prev_by_id = {r["case_id"]: r for r in previous["results"]}
        regressions = []
        for r in results:
            prev = prev_by_id.get(r["case_id"])
            if not prev:
                continue
            if prev["status"] == "PASS" and r["status"] != "PASS":
                regressions.append(f"{r['case_id']}: PASS -> {r['status']}")
            prev_judge = (prev.get("score") or {}).get("judge_score")
            cur_judge = (r.get("score") or {}).get("judge_score")
            if prev_judge is not None and cur_judge is not None and cur_judge < prev_judge - 1:
                regressions.append(f"{r['case_id']}: judge score dropped {prev_judge} -> {cur_judge}")

        if regressions:
            print(f"\nRegressions vs. previous run ({previous['timestamp']}):")
            for reg in regressions:
                print(f"  - {reg}")
        else:
            print(f"\nNo regressions vs. previous run ({previous['timestamp']}).")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nResults written to {out_path.relative_to(ROOT_DIR)}")

    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
