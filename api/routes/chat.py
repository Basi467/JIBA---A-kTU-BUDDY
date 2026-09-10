from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query, Request

from context_manager import get_chat_history, get_or_create_session
from ktu_service import KtuService

from ..deps import get_current_user
from ..limiter import limiter
from ..schemas import ChatAskRequest, ChatAskResponse, ChatMessageOut

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/history", response_model=List[ChatMessageOut])
def history(subject: str = Query(...), current_user: dict = Depends(get_current_user)):
    session_id = get_or_create_session(
        str(current_user["id"]), subject, department=current_user["department"]
    )
    messages = get_chat_history(session_id)
    return [ChatMessageOut(role=m["role"], content=m["content"]) for m in messages]


@router.post("/ask", response_model=ChatAskResponse)
@limiter.limit("15/minute")
def ask(request: Request, payload: ChatAskRequest, current_user: dict = Depends(get_current_user)):
    service = KtuService(user_id=str(current_user["id"]), department=current_user["department"])
    reply = service.ask_tutor(
        subject_name=payload.subject, question=payload.question, topic_name=payload.topic
    )
    return ChatAskResponse(reply=reply)
