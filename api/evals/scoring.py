from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from cases import EvalCase

JUDGE_MODEL = "gpt-4o-mini"


@dataclass
class ScoreResult:
    passed: bool
    checks: Dict[str, bool] = field(default_factory=dict)
    judge_score: Optional[int] = None
    judge_notes: Optional[str] = None
    error: Optional[str] = None
    # Truncated raw response text, kept alongside the pass/fail verdict so a
    # failure is debuggable from the results file alone — without this, a
    # "FAIL: keyword_grounding" tells you nothing about what the model
    # actually said.
    response_preview: Optional[str] = None


def _response_text(output: Union[str, Dict[str, Any]]) -> str:
    """teach_topic returns a dict of fields; answer_question/ask_tutor return
    a plain string. Flatten either into one blob for the keyword check."""
    if isinstance(output, str):
        return output
    parts = [
        str(output.get("simple_explanation", "")),
        str(output.get("exam_answer", "")),
        " ".join(output.get("key_points", []) or []),
        str(output.get("memory_tip", "")),
        str(output.get("practice_question", "")),
    ]
    return "\n".join(parts)


def _structural_checks(case: EvalCase, output: Union[str, Dict[str, Any]]) -> Dict[str, bool]:
    checks: Dict[str, bool] = {}

    if case.kind == "teach_topic":
        assert isinstance(output, dict)
        for field_name in ("simple_explanation", "exam_answer", "memory_tip", "practice_question"):
            checks[f"has_{field_name}"] = bool(str(output.get(field_name, "")).strip())
        key_points = output.get("key_points") or []
        checks["key_points_count_in_range"] = 3 <= len(key_points) <= 7
    else:
        assert isinstance(output, str)
        checks["min_length"] = len(output.strip()) >= case.min_length

    return checks


def _keyword_check(case: EvalCase, output: Union[str, Dict[str, Any]]) -> Optional[bool]:
    if not case.must_include_any:
        return None
    text = _response_text(output).lower()
    return any(keyword.lower() in text for keyword in case.must_include_any)


def _judge(case: EvalCase, output: Union[str, Dict[str, Any]], client) -> tuple:
    """LLM-as-judge: a second, cheap model call scoring the response for
    topical relevance and factual plausibility on a 1-5 scale. Separate from
    the keyword check — it catches cases where the response is grounded and
    well-formed but subtly wrong or off-target in a way substring matching
    can't detect."""
    text = _response_text(output)
    prompt = f"""You are grading an AI tutor's response for a KTU (APJ Abdul Kalam \
Technological University) exam-prep app. Be strict but fair.

Subject: {case.subject}
Topic/Question asked: {case.topic or case.question}

The tutor's response:
\"\"\"
{text[:3000]}
\"\"\"

Grading rubric for this case: {case.judge_rubric}

Respond with ONLY a JSON object, no other text: {{"score": <1-5 int>, "notes": "<one sentence>"}}"""

    response = client.chat.completions.create(
        model=JUDGE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    raw = response.choices[0].message.content.strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    parsed = json.loads(raw)
    return int(parsed["score"]), str(parsed.get("notes", ""))


def score_case(
    case: EvalCase,
    output: Union[str, Dict[str, Any]],
    *,
    judge_client=None,
) -> ScoreResult:
    checks = _structural_checks(case, output)

    keyword_result = _keyword_check(case, output)
    if keyword_result is not None:
        checks["keyword_grounding"] = keyword_result

    judge_score: Optional[int] = None
    judge_notes: Optional[str] = None
    if judge_client is not None:
        try:
            judge_score, judge_notes = _judge(case, output, judge_client)
        except Exception as e:  # judge failures shouldn't crash the whole run
            judge_notes = f"judge error: {e}"

    structural_pass = all(checks.values())
    judge_pass = judge_score is None or judge_score >= 3
    passed = structural_pass and judge_pass

    return ScoreResult(
        passed=passed,
        checks=checks,
        judge_score=judge_score,
        judge_notes=judge_notes,
        response_preview=_response_text(output)[:500],
    )
