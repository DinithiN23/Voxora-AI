"""
Voxora Backend — Auth schemas.

Request/response schemas for authentication endpoints.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ── Request Schemas ──────────────────────────────────────────

class RegisterRequest(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    tenant_name: str = Field(min_length=2, max_length=255)


class LoginRequest(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh."""
    refresh_token: str


# ── Response Schemas ─────────────────────────────────────────

class TokenResponse(BaseModel):
    """JWT token pair returned on login/register."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserResponse(BaseModel):
    """User profile data."""
    id: UUID
    email: str
    name: str
    avatar_url: str | None = None
    tenant_id: UUID
    tenant_name: str
    role: str | None = None
    is_active: bool
    last_login: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    """Combined auth response with tokens + user data."""
    tokens: TokenResponse
    user: UserResponse
