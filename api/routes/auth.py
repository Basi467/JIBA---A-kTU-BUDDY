from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from auth_engine import login_user, register_user

from ..auth_tokens import issue_token
from ..deps import get_current_user
from ..limiter import limiter
from ..schemas import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse, UserOut

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
