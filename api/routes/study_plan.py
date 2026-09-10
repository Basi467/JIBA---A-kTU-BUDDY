from __future__ import annotations

from dataclasses import asdict
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from ktu_service import KtuService

from ..deps import get_current_user
from ..schemas import StudyPlanItemOut, StudyPlanRequest

router = APIRouter(prefix="/study-plan", tags=["study-plan"])


@router.post("/generate", response_model=List[StudyPlanItemOut])
def generate(payload: StudyPlanRequest, current_user: dict = Depends(get_current_user)):
    service = KtuService(user_id=str(current_user["id"]), department=current_user["department"])

    try:
        plan = service.generate_study_plan(
            subject_name=payload.subject,
            exam_date=payload.exam_date,
            hours_per_day=payload.hours_per_day,
            manual_weak_topics=payload.manual_weak_topics,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return [asdict(item) for item in plan]
