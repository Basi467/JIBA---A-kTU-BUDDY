from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal, Optional

Kind = Literal["teach_topic", "answer_question", "ask_tutor"]


@dataclass
class EvalCase:
    id: str
    kind: Kind
    subject: str
    department: str
    # teach_topic / answer_question use `topic` to look up related PYQs; ask_tutor
    # leaves it unset since it's a free-form question.
    topic: Optional[str] = None
    question: Optional[str] = None
    # At least one of these (case-insensitive substring) must appear in the
    # response for the case to pass the grounding check. Empty means "skip
    # this check, rely on the LLM judge only" — used for cases where no
    # single keyword can capture correctness (e.g. an off-topic redirect).
    must_include_any: List[str] = field(default_factory=list)
    min_length: int = 60
    # What "5/5" means for this specific case, handed to the LLM judge
    # verbatim. Kept per-case rather than one conditional prompt — an
    # earlier version tried a single branching rubric ("if the question was
    # off-topic, score 5 for X, else 5 for Y") and the judge model didn't
    # reliably follow the branch, scoring a correct off-topic redirect as a
    # failure. A rubric with no in-prompt branching is what actually fixed it.
    judge_rubric: str = (
        "Score 5 if the response correctly and clearly addresses the subject/topic "
        "for a KTU exam-prep context with no apparent factual errors. Score 1 if it "
        "is empty, off-topic, or clearly wrong."
    )


# A fixed bank of real syllabus content pulled from the live database, not
# synthetic examples — each case exercises one of the three AI-backed
# features against a topic/question that actually exists in the app.
CASES: List[EvalCase] = [
    EvalCase(
        id="teach-modes-of-communication",
        kind="teach_topic",
        subject="Computer Networks",
        department="CSE",
        topic="Modes of communication",
        must_include_any=["simplex", "duplex"],
    ),
    EvalCase(
        id="teach-signal-encoding",
        kind="teach_topic",
        subject="Computer Networks",
        department="CSE",
        topic="Signal encoding",
        must_include_any=["manchester", "encoding"],
    ),
    EvalCase(
        id="teach-bandwidth",
        kind="teach_topic",
        subject="Computer Networks",
        department="CSE",
        topic="Bandwidth",
        must_include_any=["bandwidth", "bit"],
    ),
    EvalCase(
        id="answer-transmission-time",
        kind="answer_question",
        subject="Computer Networks",
        department="CSE",
        topic="Bandwidth",
        question=(
            "What is the transmission time of a packet sent by a station if the length "
            "of the packet is 1 million bytes and the bandwidth of the channel is 200 Kbps?"
        ),
        must_include_any=["second", "kbps", "bandwidth"],
    ),
    EvalCase(
        id="answer-bit-stuffing",
        kind="answer_question",
        subject="Computer Networks",
        department="CSE",
        topic="Data link layer",
        question=(
            "A bit string 01111011111011111110 needs to be transmitted at the data link "
            "layer. If the flag used is 01111110, what is the string actually transmitted "
            "after bit stuffing?"
        ),
        must_include_any=["stuff", "flag", "bit"],
    ),
    EvalCase(
        id="tutor-osi-vs-tcpip",
        kind="ask_tutor",
        subject="Computer Networks",
        department="CSE",
        question="What's the difference between the OSI model and TCP/IP model?",
        must_include_any=["osi", "tcp/ip", "layer"],
    ),
    EvalCase(
        id="tutor-off-topic-redirect",
        kind="ask_tutor",
        subject="Computer Networks",
        department="CSE",
        question="Can you help me plan a birthday party?",
        # No keyword captures "handled this gracefully" — the system prompt
        # asks the model to stay close to the syllabus, but there's no hard
        # refusal rule, so this case exists to catch scope drift over time
        # via the LLM judge rather than assert one exact behavior.
        must_include_any=[],
        min_length=10,
        judge_rubric=(
            "This question ('Can you help me plan a birthday party?') is deliberately "
            "unrelated to the Computer Networks syllabus. Score 5 if the tutor declined "
            "or redirected back to the subject instead of engaging with the request. "
            "Score 1 if it answered the birthday-party request as a general-purpose "
            "assistant would, ignoring its tutoring scope."
        ),
    ),
]
