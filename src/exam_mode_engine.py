from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import List, Dict, Optional

DB_PATH = "database/ktu.db"


@dataclass
class ExamQuestion:
    year: int | None
    marks: int | None
    topic_name: str | None
    question_text: str


@dataclass
class ModuleExamFocus:
    module_no: int
    high_priority_topics: List[str]
    medium_priority_topics: List[str]
    low_priority_topics: List[str]
    repeated_questions: List[ExamQuestion]


@dataclass
class TeachTopicItem:
    module_no: int
    topic_name: str
    priority_label: str
    question_count: int | None
    weighted_score: float | None


@dataclass
class TeachQuestionItem:
    module_no: int
    year: int | None
    marks: int | None
    topic_name: str | None
    question_text: str


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_subject_id(subject_name: str, department: Optional[str] = None) -> int | None:
    conn = get_connection()
    try:
        query = """
            SELECT id
            FROM subjects
            WHERE LOWER(TRIM(subject_name)) = LOWER(TRIM(?))
        """
        params: list = [subject_name]
        if department:
            query += " AND LOWER(TRIM(department)) = LOWER(TRIM(?))"
            params.append(department)
        query += " LIMIT 1"

        row = conn.execute(query, params).fetchone()
        return row["id"] if row else None
    finally:
        conn.close()


def fetch_module_topic_priority(subject_name: str, department: Optional[str] = None) -> List[sqlite3.Row]:
    conn = get_connection()
    try:
        query = """
            SELECT
                mtp.module_no,
                t.topic_name,
                mtp.priority_label,
                mtp.question_count,
                mtp.weighted_score
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
        """

        rows = conn.execute(query, params).fetchall()
        return rows
    finally:
        conn.close()


def fetch_repeated_questions(
    subject_name: str, module_no: int, limit: int = 8, department: Optional[str] = None
) -> List[sqlite3.Row]:
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
              AND q.module_no = ?
        """
        params: list = [subject_name, module_no]
        if department:
            query += " AND LOWER(TRIM(s.department)) = LOWER(TRIM(?))"
            params.append(department)
        query += """
            ORDER BY
                COALESCE(q.marks, 0) DESC,
                COALESCE(q.year, 0) DESC,
                q.question_text
            LIMIT ?
        """
        params.append(limit)

        rows = conn.execute(query, params).fetchall()
        return rows
    finally:
        conn.close()


def fetch_topic_pyqs(
    subject_name: str, topic_name: str, limit: int = 5, department: Optional[str] = None
) -> List[ExamQuestion]:
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
              AND LOWER(TRIM(t.topic_name)) = LOWER(TRIM(?))
        """
        params: list = [subject_name, topic_name]
        if department:
            query += " AND LOWER(TRIM(s.department)) = LOWER(TRIM(?))"
            params.append(department)
        query += """
            ORDER BY
                COALESCE(q.marks, 0) DESC,
                COALESCE(q.year, 0) DESC,
                q.question_text
            LIMIT ?
        """
        params.append(limit)

        rows = conn.execute(query, params).fetchall()

        return [
            ExamQuestion(
                year=row["year"],
                marks=row["marks"],
                topic_name=row["topic_name"],
                question_text=row["question_text"],
            )
            for row in rows
        ]
    finally:
        conn.close()


def build_exam_mode(subject_name: str, department: Optional[str] = None) -> List[ModuleExamFocus]:
    priority_rows = fetch_module_topic_priority(subject_name, department=department)
    if not priority_rows:
        return []

    grouped: Dict[int, Dict[str, List[str]]] = {}

    for row in priority_rows:
        module_no = int(row["module_no"])
        grouped.setdefault(
            module_no,
            {"High": [], "Medium": [], "Low": []},
        )

        label = row["priority_label"]
        topic_name = row["topic_name"]

        if topic_name not in grouped[module_no][label]:
            grouped[module_no][label].append(topic_name)

    result: List[ModuleExamFocus] = []

    for module_no in sorted(grouped.keys()):
        questions = fetch_repeated_questions(subject_name, module_no, department=department)

        result.append(
            ModuleExamFocus(
                module_no=module_no,
                high_priority_topics=grouped[module_no]["High"],
                medium_priority_topics=grouped[module_no]["Medium"],
                low_priority_topics=grouped[module_no]["Low"],
                repeated_questions=[
                    ExamQuestion(
                        year=row["year"],
                        marks=row["marks"],
                        topic_name=row["topic_name"],
                        question_text=row["question_text"],
                    )
                    for row in questions
                ],
            )
        )

    return result


def build_high_priority_teach_queue(subject_name: str, department: Optional[str] = None) -> List[TeachTopicItem]:
    rows = fetch_module_topic_priority(subject_name, department=department)
    if not rows:
        return []

    queue: List[TeachTopicItem] = []
    seen = set()

    for row in rows:
        if row["priority_label"] != "High":
            continue

        key = (int(row["module_no"]), row["topic_name"])
        if key in seen:
            continue
        seen.add(key)

        queue.append(
            TeachTopicItem(
                module_no=int(row["module_no"]),
                topic_name=row["topic_name"],
                priority_label=row["priority_label"],
                question_count=row["question_count"],
                weighted_score=row["weighted_score"],
            )
        )

    return queue


def build_repeated_question_queue(
    subject_name: str, limit_per_module: int = 5, department: Optional[str] = None
) -> List[TeachQuestionItem]:
    exam_data = build_exam_mode(subject_name, department=department)
    if not exam_data:
        return []

    queue: List[TeachQuestionItem] = []
    seen_questions = set()

    for module in exam_data:

        for q in module.repeated_questions[:limit_per_module]:

            normalized_question = (
                q.question_text.strip().lower()
            )

            if normalized_question in seen_questions:
                continue

            seen_questions.add(normalized_question)

            queue.append(
                TeachQuestionItem(
                    module_no=module.module_no,
                    year=q.year,
                    marks=q.marks,
                    topic_name=q.topic_name,
                    question_text=q.question_text,
                )
            )
    return queue

if __name__ == "__main__":
    subject_name = "Operating Systems"
    exam_data = build_exam_mode(subject_name)

    print(f"\nExam Mode Preview: {subject_name}\n")

    for module in exam_data:
        print(f"Module {module.module_no}")
        print("  High Priority Topics:")
        for topic in module.high_priority_topics[:5]:
            print(f"   - {topic}")

        print("  Repeated Questions:")
        for q in module.repeated_questions[:5]:
            print(f"   - [{q.year}] ({q.marks} marks) {q.question_text}")
        print()