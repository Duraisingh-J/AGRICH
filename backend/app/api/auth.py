"""Authentication router with role-based registration and JWT tokens."""

import logging
import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.user import User, UserRole
from app.services.auth_service import AuthService

LOGGER = logging.getLogger(__name__)
WALLET_PATTERN = re.compile(r"^0x[a-fA-F0-9]{40}$")

router = APIRouter(prefix="/auth", tags=["auth"])
auth_service = AuthService()


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
        aadhaar_hash=auth_service.hash_aadhaar(payload.aadhaar),
        wallet_address=payload.wallet_address,
        password_hash=await auth_service.hash_password(payload.password),
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

    token_pair = auth_service.create_token_pair(str(user.id))
    return TokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Authenticate user by email and password."""

    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user or not await auth_service.verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token_pair = auth_service.create_token_pair(str(user.id))
    return TokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshTokenRequest) -> TokenResponse:
    """Refresh token endpoint to rotate access token."""

    claims = auth_service.decode_token(payload.refresh_token)
    if claims.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    token_pair = auth_service.create_token_pair(str(claims["sub"]))
    return TokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
    )
