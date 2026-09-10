from __future__ import annotations

from dataclasses import asdict
from typing import List

from fastapi import APIRouter, Depends, Query

from module_topic_priority_engine import preview_subject

from ..deps import get_current_user
from ..schemas import ModuleTopicPriorityOut

router = APIRouter(prefix="/priority", tags=["priority"])


@router.get("/predicted", response_model=List[ModuleTopicPriorityOut])
def predicted(subject: str = Query(...), current_user: dict = Depends(get_current_user)):
    rows = preview_subject(subject, department=current_user["department"])
    return [asdict(r) for r in rows]
