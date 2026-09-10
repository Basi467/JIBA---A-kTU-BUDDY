from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env
load_dotenv()

# Project paths
ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "database" / "ktu.db"


@dataclass
class TopicContext:
    module_no: int
    topic_name: str
    priority_label: str
    question_count: int


@dataclass
class PyqContext:
    year: Optional[int]
    marks: Optional[int]
    topic_name: Optional[str]
    question_text: str


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found. Create a .env file in project root and add:\n"
            "OPENAI_API_KEY=your_api_key_here"
        )
    return OpenAI(api_key=api_key)


def fetch_subject_context(subject_name: str, department: Optional[str] = None) -> List[sqlite3.Row]:
    conn = get_connection()
    try:
        query = """
            SELECT
                s.subject_name,
                m.module_no,
                m.module_title,
                t.topic_name
            FROM subjects s
            JOIN modules m ON s.id = m.subject_id
            JOIN topics t ON m.id = t.module_id
            WHERE LOWER(TRIM(s.subject_name)) = LOWER(TRIM(?))
        """
        params: list = [subject_name]
        if department:
            query += " AND LOWER(TRIM(s.department)) = LOWER(TRIM(?))"
            params.append(department)
        query += " ORDER BY m.module_no, t.topic_name"

        rows = conn.execute(query, params).fetchall()
        return rows
    finally:
        conn.close()


def fetch_priority_topics(subject_name: str, limit: int = 12, department: Optional[str] = None) -> List[TopicContext]:
    conn = get_connection()
    try:
        query = """
            SELECT
                mtp.module_no,
                t.topic_name,
                mtp.priority_label,
                mtp.question_count
            FROM module_topic_priority mtp
            JOIN subjects s ON mtp.subject_id = s.id
            JOIN topics t ON mtp.topic_id = t.id
            WHERE LOWER(TRIM(s.subject_name)) = LOWER(TRIM(?))
        """
        params: list = [subject_name]
        if department:
            query += " AND LOWER(TRIM(s.department)) = LOWER(TRIM(?))"
            params.append(department)
        query += """
            ORDER BY
                mtp.module_no,
                CASE mtp.priority_label
                    WHEN 'High' THEN 1
                    WHEN 'Medium' THEN 2
                    ELSE 3
                END,
                mtp.weighted_score DESC,
                mtp.question_count DESC,
                t.topic_name
            LIMIT ?
        """
        params.append(limit)

        rows = conn.execute(query, params).fetchall()

        return [
            TopicContext(
                module_no=int(r["module_no"]),
                topic_name=r["topic_name"],
                priority_label=r["priority_label"],
                question_count=int(r["question_count"]),
            )
            for r in rows
        ]
    finally:
        conn.close()


def fetch_related_pyq(subject_name: str, limit: int = 10, department: Optional[str] = None) -> List[PyqContext]:
    conn = get_connection()
    try:
        query = """
            SELECT
                q.year,
                q.marks,
                t.topic_name,
                q.question_text
            FROM pyq_questions q
            JOIN subjects s ON q.subject_id = s.id
            LEFT JOIN topics t ON q.topic_id = t.id
            WHERE LOWER(TRIM(s.subject_name)) = LOWER(TRIM(?))
        """
        params: list = [subject_name]
        if department:
            query += " AND LOWER(TRIM(s.department)) = LOWER(TRIM(?))"
            params.append(department)
        query += """
            ORDER BY
                COALESCE(q.marks, 0) DESC,
                COALESCE(q.year, 0) DESC
            LIMIT ?
        """
        params.append(limit)

        rows = conn.execute(query, params).fetchall()

        return [
            PyqContext(
                year=r["year"],
                marks=r["marks"],
                topic_name=r["topic_name"],
                question_text=r["question_text"],
            )
            for r in rows
        ]
    finally:
        conn.close()


def build_subject_summary(
    subject_name: str,
    max_modules: int = 5,
    max_topics_per_module: int = 6,
    department: Optional[str] = None,
) -> str:
    rows = fetch_subject_context(subject_name, department=department)
    if not rows:
        return f"No syllabus context found for subject: {subject_name}"

    modules: dict[int, dict[str, List[str]]] = {}
    for row in rows:
        module_no = int(row["module_no"])
        module_title = row["module_title"]
        topic_name = row["topic_name"]

        if module_no not in modules:
            modules[module_no] = {"title": module_title, "topics": []}

        if topic_name not in modules[module_no]["topics"]:
            if len(modules[module_no]["topics"]) < max_topics_per_module:
                modules[module_no]["topics"].append(topic_name)

    lines = [f"Subject: {subject_name}", "Syllabus context:"]
    count = 0
    for module_no in sorted(modules.keys()):
        if count >= max_modules:
            break
        lines.append(f"Module {module_no}: {modules[module_no]['title']}")
        for topic in modules[module_no]["topics"]:
            lines.append(f"  - {topic}")
        count += 1

    return "\n".join(lines)


def build_priority_summary(subject_name: str, department: Optional[str] = None) -> str:
    topics = fetch_priority_topics(subject_name, department=department)
    if not topics:
        return "No priority-topic data found."

    lines = ["Important topics from PYQ trend inside modules:"]
    for t in topics:
        lines.append(
            f"- Module {t.module_no}: {t.topic_name} "
            f"(Priority: {t.priority_label}, Repeated: {t.question_count})"
        )
    return "\n".join(lines)


def build_pyq_summary(subject_name: str, department: Optional[str] = None) -> str:
    pyqs = fetch_related_pyq(subject_name, department=department)
    if not pyqs:
        return "No PYQ context found."

    lines = ["Relevant previous-year question patterns:"]
    for q in pyqs:
        year = q.year if q.year is not None else "N/A"
        marks = q.marks if q.marks is not None else "N/A"
        topic = q.topic_name if q.topic_name else "Unknown topic"
        lines.append(f"- [{year}] ({marks} marks) [{topic}] {q.question_text}")
    return "\n".join(lines)


def build_prompt(
    subject_name: str,
    user_question: str,
    chat_history: Optional[List[dict]] = None,
    department: Optional[str] = None,
) -> List[dict]:
    syllabus_summary = build_subject_summary(subject_name, department=department)
    priority_summary = build_priority_summary(subject_name, department=department)
    pyq_summary = build_pyq_summary(subject_name, department=department)

    system_message = f"""
You are KTU Buddy, an exam-focused tutor for KTU students.

Your job:
- answer according to the selected subject syllabus
- explain in a way suitable for university exam preparation
- keep answers clear, structured, and easy to write in exams
- when useful, mention which module the answer belongs to
- when useful, connect the answer to repeated PYQ trends
- if the user asks for a short answer, keep it concise
- if the user asks for a long answer, provide exam-ready structured content
- do not invent syllabus topics outside the given context
- if unsure, stay close to the available syllabus and PYQ context

Context:
{syllabus_summary}

{priority_summary}

{pyq_summary}
""".strip()

    messages = [{"role": "system", "content": system_message}]

    if chat_history:
        # keep only recent turns
        messages.extend(chat_history[-8:])

    messages.append({"role": "user", "content": user_question})
    return messages


def ask_chatgpt(
    subject_name: str,
    user_question: str,
    chat_history: Optional[List[dict]] = None,
    model: str = "gpt-4o-mini",
    department: Optional[str] = None,
) -> str:
    client = get_openai_client()
    messages = build_prompt(
        subject_name=subject_name,
        user_question=user_question,
        chat_history=chat_history,
        department=department,
    )

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.3,
    )

    return response.choices[0].message.content.strip()


def safe_ask_chatgpt(
    subject_name: str,
    user_question: str,
    chat_history: Optional[List[dict]] = None,
    model: str = "gpt-4o-mini",
    department: Optional[str] = None,
) -> str:
    try:
        return ask_chatgpt(
            subject_name=subject_name,
            user_question=user_question,
            chat_history=chat_history,
            model=model,
            department=department,
        )
    except Exception as e:
        return f"Error while generating response: {e}"


if __name__ == "__main__":
    subject_name = "Operating Systems"
    user_question = "Explain deadlock prevention in a way I can write for the exam."

    chat_history = [
        {"role": "user", "content": "I am studying Operating Systems."},
        {"role": "assistant", "content": "Okay, ask me anything from Operating Systems."},
    ]

    reply = safe_ask_chatgpt(
        subject_name=subject_name,
        user_question=user_question,
        chat_history=chat_history,
    )

    print("\nKTU Buddy Reply:\n")
    print(reply)