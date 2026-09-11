# JIBA eval suite

Regression tests for the three AI-backed features (`teach_topic`,
`answer_exam_question`, `ask_tutor`) — separate from `api/tests/`, which
mocks the OpenAI client and only verifies the code paths work. This suite
calls the real OpenAI API and grades what actually comes back, so it costs
real (small) API usage per run.

## Running it

```bash
# Real run against the live OpenAI API — costs a handful of API calls
python api/evals/run_evals.py

# Dry-run with a mocked client — verifies the harness itself, not prompt quality, free
python api/evals/run_evals.py --mock

# Skip the LLM-as-judge pass (keyword/structural checks only, cheaper)
python api/evals/run_evals.py --no-judge

# Run a single case
python api/evals/run_evals.py --case teach-signal-encoding
```

Run it manually whenever you change a prompt in `src/chat_engine.py` or
`src/ktu_service.py` — it's deliberately not wired into CI/pre-commit, since
that would spend API credits on every push.

## How a case is scored

Each case in `cases.py` is checked three ways:

1. **Structural** — required fields are non-empty; `teach_topic`'s
   `key_points` list has 3-7 items (matches the prompt's own "4 to 6 short
   bullet points" instruction).
2. **Keyword grounding** — the response contains at least one of a fixed
   set of topic-specific keywords (free, no extra API call).
3. **LLM-as-judge** — a second `gpt-4o-mini` call rates the response 1-5
   against a per-case rubric (`EvalCase.judge_rubric`) and must score >= 3
   to pass. A per-case rubric, not one shared conditional prompt — an
   earlier version tried a single prompt with an if/else rubric embedded in
   it, and the judge model didn't reliably follow the branch.

A case passes only if every structural/keyword check passes AND the judge
score clears the bar.

## Tracking over time

Every run writes a timestamped JSON file to `results/` (git commit hash,
per-case pass/fail, judge score, and a truncated response preview for
debugging failures without re-running). The next run automatically diffs
against the most recent prior result and flags:

- any case that went from PASS to FAIL/ERROR
- any case whose judge score dropped by more than 1 point

`results/` is committed to the repo, so `git log -- api/evals/results/` is a
literal history of prompt-quality over time.
