"""
Voxora Backend — Auth API endpoints.

Handles registration, login, token refresh, and user profile.
"""

try:
    from datetime import UTC, datetime
except ImportError:
    from datetime import datetime, timezone
    UTC = timezone.utc

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.core.security import (
    TokenPayload,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.role import Role
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _build_token_payload(user: User, tenant: Tenant, role: Role | None) -> dict:
    """Build JWT payload from user data."""
    return {
        "sub": str(user.id),
        "email": user.email,
        "tenant_id": str(user.tenant_id),
        "role": role.name if role else "member",
    }


def _build_token_response(payload: dict, settings: Settings) -> TokenResponse:
    """Create access + refresh token pair."""
    return TokenResponse(
        access_token=create_access_token(payload, settings),
        refresh_token=create_refresh_token(payload, settings),
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


def _build_user_response(user: User, tenant: Tenant, role: Role | None) -> UserResponse:
    """Build user profile response."""
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        tenant_id=user.tenant_id,
        tenant_name=tenant.name,
        role=role.name if role else None,
        is_active=user.is_active,
        last_login=user.last_login,
        created_at=user.created_at,
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Register a new user and tenant."""

    # Check if email already exists
    existing = await db.execute(select(User).where(User.email == request.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    # Create tenant
    slug = request.tenant_name.lower().replace(" ", "-")
    # Ensure unique slug
    slug_check = await db.execute(select(Tenant).where(Tenant.slug == slug))
    if slug_check.scalar_one_or_none():
        slug = f"{slug}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"

    tenant = Tenant(name=request.tenant_name, slug=slug)
    db.add(tenant)
    await db.flush()

    # Create default admin role
    admin_role = Role(
        tenant_id=tenant.id,
        name="admin",
        description="Full access to all business areas",
        permissions_matrix={"level": "admin", "areas": ["*"]},
    )
    db.add(admin_role)
    await db.flush()

    # Create user
    user = User(
        tenant_id=tenant.id,
        email=request.email,
        name=request.name,
        hashed_password=hash_password(request.password),
        role_id=admin_role.id,
        last_login=datetime.now(UTC),
    )
    db.add(user)
    await db.flush()

    # Build response
    token_payload = _build_token_payload(user, tenant, admin_role)
    tokens = _build_token_response(token_payload, settings)
    user_data = _build_user_response(user, tenant, admin_role)

    return AuthResponse(tokens=tokens, user=user_data)


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Authenticate a user and return tokens."""

    # Find user
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    # Load tenant and role
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = tenant_result.scalar_one()

    role = None
    if user.role_id:
        role_result = await db.execute(select(Role).where(Role.id == user.role_id))
        role = role_result.scalar_one_or_none()

    # Update last login
    user.last_login = datetime.now(UTC)
    await db.flush()

    # Build response
    token_payload = _build_token_payload(user, tenant, role)
    tokens = _build_token_response(token_payload, settings)
    user_data = _build_user_response(user, tenant, role)

    return AuthResponse(tokens=tokens, user=user_data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    settings: Settings = Depends(get_settings),
):
    """Refresh an access token using a refresh token."""

    payload = decode_token(request.refresh_token, settings)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Issue new token pair
    new_payload = {
        "sub": payload["sub"],
        "email": payload["email"],
        "tenant_id": payload["tenant_id"],
        "role": payload["role"],
    }

    return _build_token_response(new_payload, settings)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's profile."""

    result = await db.execute(select(User).where(User.id == current_user.user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    tenant_result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = tenant_result.scalar_one()

    role = None
    if user.role_id:
        role_result = await db.execute(select(Role).where(Role.id == user.role_id))
        role = role_result.scalar_one_or_none()

    return _build_user_response(user, tenant, role)
