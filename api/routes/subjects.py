from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends

from auth_engine import get_subjects_for_user

from ..deps import get_current_user
from ..schemas import SubjectOut

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.get("", response_model=List[SubjectOut])
def list_subjects(current_user: dict = Depends(get_current_user)):
    rows = get_subjects_for_user(current_user["id"])
    return [SubjectOut(subject_code=r["subject_code"], subject_name=r["subject_name"]) for r in rows]
