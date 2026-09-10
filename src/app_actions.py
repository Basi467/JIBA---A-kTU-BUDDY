from __future__ import annotations

from typing import Optional

from progress_engine import auto_update_progress


def mark_topic_viewed(user_id: str, subject_name: str, topic_name: str, department: Optional[str] = None) -> str:
    return auto_update_progress(
        user_id=user_id,
        subject_name=subject_name,
        topic_name=topic_name,
        interaction_type="viewed",
        department=department,
    )


def mark_topic_studied(user_id: str, subject_name: str, topic_name: str, department: Optional[str] = None) -> str:
    return auto_update_progress(
        user_id=user_id,
        subject_name=subject_name,
        topic_name=topic_name,
        interaction_type="studied",
        department=department,
    )


def mark_topic_weak(user_id: str, subject_name: str, topic_name: str, department: Optional[str] = None) -> str:
    return auto_update_progress(
        user_id=user_id,
        subject_name=subject_name,
        topic_name=topic_name,
        interaction_type="marked_weak",
        department=department,
    )


def mark_topic_completed(user_id: str, subject_name: str, topic_name: str, department: Optional[str] = None) -> str:
    return auto_update_progress(
        user_id=user_id,
        subject_name=subject_name,
        topic_name=topic_name,
        interaction_type="marked_completed",
        department=department,
    )


def mark_tutor_question(user_id: str, subject_name: str, topic_name: str, department: Optional[str] = None) -> str:
    return auto_update_progress(
        user_id=user_id,
        subject_name=subject_name,
        topic_name=topic_name,
        interaction_type="asked_question",
        department=department,
    )


def mark_pyq_solved(user_id: str, subject_name: str, topic_name: str, department: Optional[str] = None) -> str:
    return auto_update_progress(
        user_id=user_id,
        subject_name=subject_name,
        topic_name=topic_name,
        interaction_type="solved_pyq",
        department=department,
    )
