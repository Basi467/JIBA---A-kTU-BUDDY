from __future__ import annotations

import re
from typing import List, Optional, Dict

# Matches a leading list marker only — "1. ", "- ", "• ", or a single "* "
# bullet (but never the opening "**" of a markdown bold span, since the
# lookahead rejects a "*" immediately followed by another "*").
_LIST_MARKER_RE = re.compile(r"^\s*(?:\d+[.)]\s*|[-•]\s*|\*(?!\*)\s*)")

from study_plan_engine import generate_study_plan
from exam_mode_engine import (
    build_exam_mode,
    fetch_topic_pyqs,
    build_high_priority_teach_queue,
    build_repeated_question_queue,
)
from chat_engine import safe_ask_chatgpt
from context_manager import (
    get_or_create_session,
    add_message,
    get_chat_history,
)
from progress_engine import (
    get_weak_topics,
    auto_update_progress,
)


class KtuService:
    def __init__(self, user_id: str, department: Optional[str] = None):
        self.user_id = user_id
        self.department = department

    # -----------------------------
    # STUDY PLAN
    # -----------------------------
    def generate_study_plan(
        self,
        subject_name: str,
        exam_date: str,
        hours_per_day: float,
        manual_weak_topics: Optional[List[str]] = None,
    ):
        manual_weak_topics = manual_weak_topics or []

        stored_weak = get_weak_topics(self.user_id, subject_name, department=self.department)
        all_weak = list(set(manual_weak_topics + stored_weak))

        return generate_study_plan(
            subject_name=subject_name,
            exam_date_str=exam_date,
            hours_per_day=hours_per_day,
            weak_topics=all_weak,
            department=self.department,
        )

    # -----------------------------
    # EXAM MODE
    # -----------------------------
    def get_exam_mode(self, subject_name: str):
        return build_exam_mode(subject_name, department=self.department)

    def get_high_priority_teach_queue(self, subject_name: str):
        return build_high_priority_teach_queue(subject_name, department=self.department)

    def get_repeated_question_queue(self, subject_name: str, limit_per_module: int = 5):
        return build_repeated_question_queue(
            subject_name, limit_per_module=limit_per_module, department=self.department
        )

    def get_related_pyqs(self, subject_name: str, topic_name: str, limit: int = 4):
        return fetch_topic_pyqs(subject_name, topic_name, limit=limit, department=self.department)

    def teach_topic(self, subject_name: str, topic_name: str) -> Dict:
        """
        Generate a structured exam-focused lesson for a topic.
        Used by Exam Mode -> Teach High Priority.
        """
        related_pyqs = self.get_related_pyqs(subject_name, topic_name, limit=4)

        pyq_lines = []
        for q in related_pyqs:
            pyq_lines.append(
                f"- [{q.year}] ({q.marks} marks) {q.question_text}"
            )

        pyq_block = "\n".join(pyq_lines) if pyq_lines else "No linked PYQs found."

        prompt = f"""
You are a KTU exam-focused tutor.

Subject: {subject_name}
Topic: {topic_name}

Related previous year questions:
{pyq_block}

Teach this topic in the following exact structure:

1. Simple Explanation
Explain the topic in very simple student-friendly language.

2. Exam-Ready Answer
Write a concise university exam answer.

3. Key Points
Give 4 to 6 short bullet points.

4. Memory Tip
Give one quick memory trick / mnemonic / short recall tip.

5. Practice Question
Give one likely exam-style question.

Keep the answer concise, clear, and useful for KTU exam preparation.
Do not add extra sections outside this structure.
"""

        try:
            raw_text = self.ask_tutor(
                subject_name=subject_name,
                question=prompt,
                topic_name=topic_name,
            )
            return self._parse_teaching_response(raw_text, topic_name, related_pyqs)
        except Exception:
            return {
                "simple_explanation": f"{topic_name} is an important topic in {subject_name}.",
                "exam_answer": (
                    f"{topic_name} should be explained with definition, main concept, "
                    f"key points, and significance."
                ),
                "key_points": [
                    f"Definition of {topic_name}",
                    f"Core concept of {topic_name}",
                    f"Importance of {topic_name}",
                ],
                "memory_tip": f"Remember {topic_name} using 3 to 4 keywords.",
                "practice_question": f"Explain {topic_name} with suitable example.",
                "related_pyqs": related_pyqs,
            }

    def answer_exam_question(
        self,
        subject_name: str,
        question_text: str,
        topic_name: Optional[str] = None,
    ) -> str:
        """
        Generate an exam-style answer for one repeated/PYQ question.
        Used by Exam Mode -> Solve Repeated PYQs.
        """
        topic_context = f"Topic: {topic_name}" if topic_name else "Topic: Not explicitly mapped"

        prompt = f"""
You are a KTU exam-focused tutor.

Subject: {subject_name}
{topic_context}

Question:
{question_text}

Write a strong university exam answer with:
- short introduction / definition
- main explanation in clear points
- important keywords
- short conclusion

Keep it concise, exam-oriented, and easy to reproduce in an answer sheet.
Avoid casual conversational tone.
"""

        try:
            return self.ask_tutor(
                subject_name=subject_name,
                question=prompt,
                topic_name=topic_name,
            )
        except Exception:
            return (
                f"Answer for: {question_text}\n\n"
                "Start with a definition, explain the main points clearly, "
                "and end with a short conclusion."
            )

    def _parse_teaching_response(self, raw_text: str, topic_name: str, related_pyqs) -> Dict:
        """
        Parse a structured teaching response into UI-friendly fields.
        """
        sections = {
            "simple_explanation": "",
            "exam_answer": "",
            "key_points": [],
            "memory_tip": "",
            "practice_question": "",
        }

        current_section = None

        for line in raw_text.splitlines():
            stripped = line.strip()
            lower = stripped.lower()

            if not stripped:
                continue

            if "simple explanation" in lower:
                current_section = "simple_explanation"
                continue
            if "exam-ready answer" in lower or "exam ready answer" in lower:
                current_section = "exam_answer"
                continue
            if "key points" in lower:
                current_section = "key_points"
                continue
            if "memory tip" in lower:
                current_section = "memory_tip"
                continue
            if "practice question" in lower:
                current_section = "practice_question"
                continue

            if current_section == "key_points":
                cleaned = _LIST_MARKER_RE.sub("", stripped).strip()
                if cleaned:
                    sections["key_points"].append(cleaned)
            elif current_section in ("simple_explanation", "exam_answer", "memory_tip", "practice_question"):
                if sections[current_section]:
                    sections[current_section] += "\n" + stripped
                else:
                    sections[current_section] = stripped

        # Safe fallbacks
        if not sections["simple_explanation"]:
            sections["simple_explanation"] = raw_text[:500]

        if not sections["exam_answer"]:
            sections["exam_answer"] = raw_text[:900]

        if not sections["key_points"]:
            sections["key_points"] = [
                f"Definition of {topic_name}",
                f"Main concept of {topic_name}",
                f"Exam relevance of {topic_name}",
            ]

        if not sections["memory_tip"]:
            sections["memory_tip"] = f"Remember {topic_name} with 3 to 4 keywords."

        if not sections["practice_question"]:
            sections["practice_question"] = f"Explain {topic_name} with suitable example."

        sections["related_pyqs"] = related_pyqs
        return sections

    # -----------------------------
    # TUTOR
    # -----------------------------
    def ask_tutor(
        self,
        subject_name: str,
        question: str,
        topic_name: Optional[str] = None,
    ) -> str:
        session_id = get_or_create_session(self.user_id, subject_name, department=self.department)

        add_message(session_id, "user", question)

        if topic_name:
            # Best-effort activity tracking, not the point of this call — a
            # topic_name that doesn't exactly match a row in `topics` (e.g.
            # a PYQ's free-text topic label that was fuzzy-linked to a
            # differently-worded canonical topic) must not take down the
            # actual tutor response. Found via api/evals: this raised
            # uncaught here, which answer_exam_question's outer try/except
            # then silently swallowed into generic filler text.
            try:
                auto_update_progress(
                    user_id=self.user_id,
                    subject_name=subject_name,
                    topic_name=topic_name,
                    interaction_type="asked_question",
                    department=self.department,
                )
            except ValueError:
                pass

        history = get_chat_history(session_id)

        reply = safe_ask_chatgpt(
            subject_name=subject_name,
            user_question=question,
            chat_history=history,
            department=self.department,
        )

        add_message(session_id, "assistant", reply)

        return reply

    # -----------------------------
    # TOPIC INTERACTIONS
    # -----------------------------
    def topic_viewed(self, subject_name: str, topic_name: str):
        return auto_update_progress(
            self.user_id, subject_name, topic_name, "viewed", department=self.department
        )

    def topic_studied(self, subject_name: str, topic_name: str):
        return auto_update_progress(
            self.user_id, subject_name, topic_name, "studied", department=self.department
        )

    def topic_completed(self, subject_name: str, topic_name: str):
        return auto_update_progress(
            self.user_id, subject_name, topic_name, "marked_completed", department=self.department
        )

    def topic_weak(self, subject_name: str, topic_name: str):
        return auto_update_progress(
            self.user_id, subject_name, topic_name, "marked_weak", department=self.department
        )

    def pyq_solved(self, subject_name: str, topic_name: str):
        return auto_update_progress(
            self.user_id, subject_name, topic_name, "solved_pyq", department=self.department
        )