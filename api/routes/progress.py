from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ktu_service import KtuService
from progress_engine import get_completed_topics, get_in_progress_topics, get_weak_topics

from ..deps import get_current_user
from ..schemas import ProgressMarkRequest, ProgressMarkResponse, ProgressOut

router = APIRouter(prefix="/progress", tags=["progress"])

_ACTION_METHODS = {
    "viewed": "topic_viewed",
    "studied": "topic_studied",
    "weak": "topic_weak",
    "completed": "topic_completed",
    "solved_pyq": "pyq_solved",
}


@router.get("", response_model=ProgressOut)
def get_progress(subject: str = Query(...), current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["id"])
    department = current_user["department"]

    weak = get_weak_topics(user_id, subject, department=department)
    completed = get_completed_topics(user_id, subject, department=department)
    in_progress = get_in_progress_topics(user_id, subject, department=department)

    unique_topics = set(weak + completed + in_progress)
    total_tracked = len(unique_topics)
    progress_ratio = (len(completed) / total_tracked) if total_tracked > 0 else 0.0

    return ProgressOut(weak=weak, completed=completed, in_progress=in_progress, progress_ratio=progress_ratio)


@router.post("/mark", response_model=ProgressMarkResponse)
def mark_progress(payload: ProgressMarkRequest, current_user: dict = Depends(get_current_user)):
    service = KtuService(user_id=str(current_user["id"]), department=current_user["department"])
    method = getattr(service, _ACTION_METHODS[payload.action])

    try:
        status_value = method(payload.subject, payload.topic)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return ProgressMarkResponse(status=status_value)
