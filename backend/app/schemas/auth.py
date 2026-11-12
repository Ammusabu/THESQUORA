"""Pydantic schemas for authentication.

Note on email validation:
- Pydantic's `EmailStr` (via email-validator) rejects RFC-reserved TLDs like
  `.local`, `.test`, `.invalid`, `.example`. That's fine for production but
  painful for local dev.
- We define `DevEmail` which still validates a normal email format but allows
  those dev-only TLDs. Swap to `EmailStr` before shipping to prod.
"""
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator

EMAIL_REGEX = (
    r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$"
)


class DevEmail(str):
    """A str that validates with a permissive regex, not email-validator."""

    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler):  # noqa: D401
        from pydantic_core import core_schema
        return core_schema.no_info_after_validator_function(
            cls._validate,
            core_schema.str_schema(),
        )

    @classmethod
    def _validate(cls, value: str) -> "DevEmail":
        import re
        if not re.match(EMAIL_REGEX, value or ""):
            raise ValueError("invalid email format")
        return cls(value)


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: DevEmail
    password: str = Field(..., min_length=8, max_length=72)
    department: str | None = Field(default=None, max_length=120)


class LoginRequest(BaseModel):
    email: DevEmail
    password: str


class UserOut(BaseModel):
    id: str
    name: str
    email: str  # keep as str so DevEmail output serializes cleanly
    role: str
    department: str | None
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
