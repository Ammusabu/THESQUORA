"""Authentication endpoints."""
from fastapi import APIRouter, Depends, status

from app.middleware.auth_middleware import get_current_user
from app.schemas.auth import (
    LoginRequest, RegisterRequest, TokenResponse, UserOut,
)
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
)
def register(payload: RegisterRequest):
    return auth_service.register(
        name=payload.name,
        email=payload.email,
        password=payload.password,
        department=payload.department,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    return auth_service.login(email=payload.email, password=payload.password)


@router.get("/me", response_model=UserOut)
def me(current_user: dict = Depends(get_current_user)):
    return current_user
