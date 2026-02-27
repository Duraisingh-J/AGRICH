"""Authentication router with role-based registration and JWT tokens."""

import hashlib
import logging
import re
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.database import get_db
from app.models.user import User, UserRole

LOGGER = logging.getLogger(__name__)
WALLET_PATTERN = re.compile(r"^0x[a-fA-F0-9]{40}$")

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


class RegisterRequest(BaseModel):
    """Request payload for user registration."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str = Field(min_length=8, max_length=20)
    role: UserRole
    aadhaar: str = Field(min_length=12, max_length=12)
    wallet_address: str
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    """Request payload for login."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RefreshTokenRequest(BaseModel):
    """Request payload for access token refresh."""

    refresh_token: str


class TokenResponse(BaseModel):
    """JWT access and refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


def _hash_aadhaar(aadhaar: str) -> str:
    """Hash Aadhaar number and never persist raw value."""

    return hashlib.sha256(aadhaar.encode("utf-8")).hexdigest()


async def _hash_password(password: str) -> str:
    """Hash password with bcrypt without blocking event loop."""

    import bcrypt

    def _sync_hash() -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    return await run_in_threadpool(_sync_hash)


async def _verify_password(password: str, password_hash: str) -> bool:
    """Verify bcrypt hash without blocking event loop."""

    import bcrypt

    def _sync_verify() -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))

    return await run_in_threadpool(_sync_verify)


def _create_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    """Create signed JWT token."""

    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _decode_token(token: str) -> dict[str, Any]:
    """Decode and validate JWT token."""

    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc
    return payload


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Register a new user and issue JWT tokens."""

    if not payload.aadhaar.isdigit():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid Aadhaar")
    if not WALLET_PATTERN.fullmatch(payload.wallet_address):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid wallet address",
        )

    user = User(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        role=payload.role,
        aadhaar_hash=_hash_aadhaar(payload.aadhaar),
        wallet_address=payload.wallet_address,
        password_hash=await _hash_password(payload.password),
        is_verified=False,
    )
    db.add(user)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        LOGGER.info("Registration conflict for email=%s", payload.email)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with provided email, phone, or wallet address already exists",
        ) from exc
    await db.refresh(user)

    subject = str(user.id)
    return TokenResponse(
        access_token=_create_token(
            subject,
            token_type="access",
            expires_delta=timedelta(minutes=settings.jwt_access_token_expire_minutes),
        ),
        refresh_token=_create_token(
            subject,
            token_type="refresh",
            expires_delta=timedelta(minutes=settings.jwt_refresh_token_expire_minutes),
        ),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Authenticate user by email and password."""

    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user or not await _verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    subject = str(user.id)
    return TokenResponse(
        access_token=_create_token(
            subject,
            token_type="access",
            expires_delta=timedelta(minutes=settings.jwt_access_token_expire_minutes),
        ),
        refresh_token=_create_token(
            subject,
            token_type="refresh",
            expires_delta=timedelta(minutes=settings.jwt_refresh_token_expire_minutes),
        ),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshTokenRequest) -> TokenResponse:
    """Refresh token endpoint to rotate access token."""

    claims = _decode_token(payload.refresh_token)
    if claims.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    subject = claims["sub"]
    return TokenResponse(
        access_token=_create_token(
            subject,
            token_type="access",
            expires_delta=timedelta(minutes=settings.jwt_access_token_expire_minutes),
        ),
        refresh_token=_create_token(
            subject,
            token_type="refresh",
            expires_delta=timedelta(minutes=settings.jwt_refresh_token_expire_minutes),
        ),
    )
