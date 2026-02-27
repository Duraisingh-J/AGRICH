"""Authentication service utilities for hashing and JWT operations."""

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from fastapi import HTTPException, status
from fastapi.concurrency import run_in_threadpool

from app.config import get_settings


@dataclass(slots=True)
class TokenPair:
    """Represents a generated access and refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthService:
    """Service layer for auth-related operations."""

    def __init__(self) -> None:
        self.settings = get_settings()

    @staticmethod
    def hash_aadhaar(aadhaar: str) -> str:
        """Hash Aadhaar number and never persist raw value."""

        return hashlib.sha256(aadhaar.encode("utf-8")).hexdigest()

    async def hash_password(self, password: str) -> str:
        """Hash password with bcrypt without blocking the async loop."""

        import bcrypt

        def _sync_hash() -> str:
            return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        return await run_in_threadpool(_sync_hash)

    async def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify bcrypt hash without blocking the async loop."""

        import bcrypt

        def _sync_verify() -> bool:
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))

        return await run_in_threadpool(_sync_verify)

    def create_token(self, subject: str, token_type: str, expires_delta: timedelta) -> str:
        """Create a signed JWT token."""

        now = datetime.now(UTC)
        payload: dict[str, Any] = {
            "sub": subject,
            "type": token_type,
            "iat": now,
            "exp": now + expires_delta,
        }
        return jwt.encode(payload, self.settings.jwt_secret, algorithm=self.settings.jwt_algorithm)

    def create_token_pair(self, subject: str) -> TokenPair:
        """Create access and refresh tokens for a subject."""

        return TokenPair(
            access_token=self.create_token(
                subject,
                token_type="access",
                expires_delta=timedelta(minutes=self.settings.jwt_access_token_expire_minutes),
            ),
            refresh_token=self.create_token(
                subject,
                token_type="refresh",
                expires_delta=timedelta(minutes=self.settings.jwt_refresh_token_expire_minutes),
            ),
        )

    def decode_token(self, token: str) -> dict[str, Any]:
        """Decode and validate a JWT token."""

        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret,
                algorithms=[self.settings.jwt_algorithm],
            )
        except jwt.PyJWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            ) from exc
        return payload
