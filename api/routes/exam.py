from __future__ import annotations

from dataclasses import asdict
from typing import List

from fastapi import APIRouter, Depends, Query, Request

from ktu_service import KtuService

from ..deps import get_current_user
from ..limiter import limiter
from ..schemas import (
    AnswerQuestionRequest,
    AnswerQuestionResponse,
    ModuleExamFocusOut,
    TeachLessonOut,
    TeachQuestionItemOut,
    TeachTopicItemOut,
    TeachTopicRequest,
)

router = APIRouter(prefix="/exam", tags=["exam"])


def _service(current_user: dict) -> KtuService:
    return KtuService(user_id=str(current_user["id"]), department=current_user["department"])


@router.get("/overview", response_model=List[ModuleExamFocusOut])
def overview(subject: str = Query(...), current_user: dict = Depends(get_current_user)):
    modules = _service(current_user).get_exam_mode(subject)
    return [asdict(m) for m in modules]


@router.get("/teach-queue", response_model=List[TeachTopicItemOut])
def teach_queue(subject: str = Query(...), current_user: dict = Depends(get_current_user)):
    items = _service(current_user).get_high_priority_teach_queue(subject)
    return [asdict(i) for i in items]


@router.post("/teach-topic", response_model=TeachLessonOut)
@limiter.limit("15/minute")
def teach_topic(request: Request, payload: TeachTopicRequest, current_user: dict = Depends(get_current_user)):
    lesson = _service(current_user).teach_topic(subject_name=payload.subject, topic_name=payload.topic)
    lesson["related_pyqs"] = [asdict(q) for q in lesson.get("related_pyqs", [])]
    return lesson


@router.get("/pyq-queue", response_model=List[TeachQuestionItemOut])
def pyq_queue(
    subject: str = Query(...),
    limit_per_module: int = Query(4),
    current_user: dict = Depends(get_current_user),
):
    items = _service(current_user).get_repeated_question_queue(subject, limit_per_module=limit_per_module)
    return [asdict(i) for i in items]


@router.post("/answer-question", response_model=AnswerQuestionResponse)
@limiter.limit("15/minute")
def answer_question(
    request: Request, payload: AnswerQuestionRequest, current_user: dict = Depends(get_current_user)
):
    answer = _service(current_user).answer_exam_question(
        subject_name=payload.subject, question_text=payload.question_text, topic_name=payload.topic
    )
    return AnswerQuestionResponse(answer=answer)
