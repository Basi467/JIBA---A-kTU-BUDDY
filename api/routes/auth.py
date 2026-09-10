from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, Request, status

from auth_engine import get_user_by_email, login_user, register_user, set_password

from ..auth_tokens import issue_token
from ..deps import get_current_user
from ..email_client import send_password_reset_email
from ..limiter import limiter
from ..password_reset_tokens import issue_reset_token, mark_used, resolve_reset_token
from ..schemas import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _to_user_out(row) -> UserOut:
    return UserOut(
        id=row["id"],
        name=row["name"],
        email=row["email"],
        scheme=row["scheme"],
        department=row["department"],
        semester=row["semester"],
    )


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(request: Request, payload: RegisterRequest):
    try:
        user_id = register_user(
            name=payload.name,
            email=payload.email,
            password=payload.password,
            scheme=payload.scheme,
            department=payload.department,
            semester=payload.semester,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return RegisterResponse(user_id=user_id)


@router.post("/login", response_model=LoginResponse)
@limiter.limit("8/minute")
def login(request: Request, payload: LoginRequest):
    user = login_user(email=payload.email, password=payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = issue_token(user["id"])
    return LoginResponse(token=token, user=_to_user_out(user))


@router.get("/me", response_model=UserOut)
def me(current_user: dict = Depends(get_current_user)):
    return _to_user_out(current_user)


_GENERIC_RESET_MESSAGE = "If that email is registered, a password reset link has been sent."


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
@limiter.limit("5/minute")
def forgot_password(request: Request, payload: ForgotPasswordRequest):
    # Always returns the same message regardless of whether the email
    # exists — leaking that would let an attacker enumerate registered
    # accounts. The real work only happens when a user is actually found.
    user = get_user_by_email(payload.email)
    if user is not None:
        token = issue_reset_token(user["id"])
        frontend_base = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173")
        reset_link = f"{frontend_base}/reset-password?token={token}"
        send_password_reset_email(user["email"], reset_link)

    return ForgotPasswordResponse(message=_GENERIC_RESET_MESSAGE)


@router.post("/reset-password", response_model=ResetPasswordResponse)
@limiter.limit("5/minute")
def reset_password(request: Request, payload: ResetPasswordRequest):
    user_id = resolve_reset_token(payload.token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset link is invalid or has expired. Request a new one.",
        )

    set_password(user_id, payload.new_password)
    mark_used(payload.token)

    return ResetPasswordResponse(message="Password updated. You can now log in.")
