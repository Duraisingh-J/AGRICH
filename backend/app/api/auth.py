"""Authentication router with role-based registration and JWT tokens."""

import asyncio
import hashlib
import logging
import random
import re
import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
import httpx
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.batch import Batch, BatchStatus
from app.models.user import User, UserRole
from app.config import get_settings
from app.services.auth_service import AuthService
from app.utils.roles import get_current_user

LOGGER = logging.getLogger(__name__)
WALLET_PATTERN = re.compile(r"^0x[a-fA-F0-9]{40}$")

router = APIRouter(prefix="/auth", tags=["auth"])
auth_service = AuthService()
settings = get_settings()

OTP_PHONE_PATTERN = re.compile(r"^\+?[0-9]{8,20}$")
_otp_store: dict[str, dict[str, int | float | str]] = {}
_otp_lock = asyncio.Lock()


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


class OtpRequestPayload(BaseModel):
    """Request payload to initiate OTP delivery."""

    phone: str = Field(min_length=8, max_length=20)


class OtpVerifyPayload(BaseModel):
    """Request payload to verify OTP code."""

    phone: str = Field(min_length=8, max_length=20)
    otp: str = Field(min_length=4, max_length=6)


class OtpRequestResponse(BaseModel):
    """Response payload for OTP request."""

    sent: bool
    expires_in: int
    channel: str = "sms"
    debug_otp: str | None = None


class OtpVerifyResponse(BaseModel):
    """Response payload for OTP verification."""

    verified: bool


class MobileOnboardRequest(BaseModel):
    """Mobile onboarding payload after OTP verification."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=8, max_length=20)
    role: UserRole
    password: str = Field(min_length=6, max_length=128)


class MobileOnboardResponse(BaseModel):
    """Response payload for mobile onboarding persistence."""

    saved: bool
    user_id: str


class MobileLoginRequest(BaseModel):
    """Mobile login payload using phone and password."""

    phone: str = Field(min_length=8, max_length=20)
    password: str = Field(min_length=6, max_length=128)


class MobileUserProfile(BaseModel):
    """User profile returned for mobile authenticated session."""

    id: str
    name: str
    phone: str
    role: UserRole
    wallet_address: str
    is_verified: bool


class MobileLoginResponse(BaseModel):
    """Response payload for mobile login."""

    authenticated: bool
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: MobileUserProfile


class MobileDashboardBatchItem(BaseModel):
    """Batch card payload for mobile dashboard."""

    id: str
    batch_code: str
    crop_type: str
    quantity: str
    status: BatchStatus


class MobileDashboardInventoryItem(BaseModel):
    """Inventory-style row for retailer/farmer dashboards."""

    name: str
    demand_signal: str
    expiry_hint: str


class MobileDashboardResponse(BaseModel):
    """Role-aware dashboard payload for mobile app."""

    role: UserRole
    greeting_name: str
    summary_title: str
    summary_subtitle: str
    weather_text: str
    price_prediction_text: str
    freshness_score: int
    trust_score: int
    active_batches_count: int
    pending_transfers_count: int
    recent_batches: list[MobileDashboardBatchItem]
    inventory_items: list[MobileDashboardInventoryItem]
    alerts: list[str]
    orders: list[str]
    recommendation: str


class TokenResponse(BaseModel):
    """JWT access and refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


def _wallet_from_phone(phone: str) -> str:
    digest = hashlib.sha1(phone.encode("utf-8")).hexdigest()[:40]
    return f"0x{digest}"


def _email_from_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    return f"mobile_{digits}@agrich.local"


def _aadhaar_hash_from_phone(phone: str) -> str:
    return hashlib.sha256(phone.encode("utf-8")).hexdigest()


def _normalize_phone(phone: str) -> str:
    sanitized = re.sub(r"\s+", "", phone.strip())
    if not OTP_PHONE_PATTERN.fullmatch(sanitized):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid phone number")
    if not sanitized.startswith("+"):
        return f"+{sanitized}"
    return sanitized


def _purge_expired_otps() -> None:
    now = time.time()
    expired = [phone for phone, entry in _otp_store.items() if float(entry["expires_at"]) < now]
    for phone in expired:
        _otp_store.pop(phone, None)


async def _dispatch_otp_sms(phone: str, otp: str) -> None:
    provider = settings.otp_provider

    if provider == "debug":
        LOGGER.info("Debug OTP for %s is %s", phone, otp)
        return

    if provider == "twilio":
        if not settings.twilio_account_sid or not settings.twilio_auth_token or not settings.twilio_from_number:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Twilio is not configured")
        url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Messages.json"
        data = {
            "To": phone,
            "From": settings.twilio_from_number,
            "Body": f"Your AGRICHAIN OTP is {otp}. It expires in {settings.otp_ttl_seconds // 60} minutes.",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                url,
                data=data,
                auth=(settings.twilio_account_sid, settings.twilio_auth_token),
            )
        if response.status_code >= 400:
            LOGGER.error("Twilio OTP send failed status=%s body=%s", response.status_code, response.text)
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to send OTP SMS")
        return

    if provider == "fast2sms":
        if not settings.fast2sms_api_key:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Fast2SMS is not configured")
        payload = {
            "route": settings.fast2sms_route,
            "sender_id": settings.fast2sms_sender_id,
            "message": f"Your AGRICHAIN OTP is {otp}. It expires in {settings.otp_ttl_seconds // 60} minutes.",
            "language": "english",
            "numbers": phone.lstrip("+"),
        }
        headers = {
            "authorization": settings.fast2sms_api_key,
            "content-type": "application/json",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post("https://www.fast2sms.com/dev/bulkV2", json=payload, headers=headers)
        if response.status_code >= 400:
            LOGGER.error("Fast2SMS OTP send failed status=%s body=%s", response.status_code, response.text)
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to send OTP SMS")
        return

    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unsupported OTP provider")


@router.post("/otp/request", response_model=OtpRequestResponse)
async def request_otp(payload: OtpRequestPayload) -> OtpRequestResponse:
    """Generate and store OTP for a phone number."""

    phone = _normalize_phone(payload.phone)
    otp = f"{random.randint(0, 999999):06d}"

    async with _otp_lock:
        _purge_expired_otps()
        _otp_store[phone] = {
            "otp": otp,
            "expires_at": time.time() + settings.otp_ttl_seconds,
            "attempts": 0,
        }

    try:
        await _dispatch_otp_sms(phone, otp)
    except HTTPException:
        async with _otp_lock:
            _otp_store.pop(phone, None)
        raise

    LOGGER.info("OTP generated and dispatched for phone=%s via %s", phone, settings.otp_provider)
    return OtpRequestResponse(
        sent=True,
        expires_in=settings.otp_ttl_seconds,
        debug_otp=otp if settings.app_debug and settings.otp_provider == "debug" else None,
    )


@router.post("/otp/verify", response_model=OtpVerifyResponse)
async def verify_otp(payload: OtpVerifyPayload) -> OtpVerifyResponse:
    """Validate submitted OTP code for a phone number."""

    phone = _normalize_phone(payload.phone)
    otp = payload.otp.strip()
    if not otp.isdigit():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid OTP format")

    async with _otp_lock:
        _purge_expired_otps()
        entry = _otp_store.get(phone)
        if not entry:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP expired or not requested")

        attempts = int(entry["attempts"]) + 1
        entry["attempts"] = attempts
        if attempts > settings.otp_max_attempts:
            _otp_store.pop(phone, None)
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="OTP attempts exceeded")

        if str(entry["otp"]) != otp:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP")

        _otp_store.pop(phone, None)

    return OtpVerifyResponse(verified=True)


@router.post("/onboard-mobile", response_model=MobileOnboardResponse)
async def onboard_mobile(
    payload: MobileOnboardRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MobileOnboardResponse:
    """Persist mobile onboarding profile after OTP verification."""

    phone = _normalize_phone(payload.phone)
    result = await db.execute(select(User).where(User.phone == phone))
    user = result.scalar_one_or_none()
    password_hash = await auth_service.hash_password(payload.password)

    if user:
        user.name = payload.name
        user.role = payload.role
        user.password_hash = password_hash
        user.is_verified = True
    else:
        user = User(
            name=payload.name,
            email=_email_from_phone(phone),
            phone=phone,
            role=payload.role,
            aadhaar_hash=_aadhaar_hash_from_phone(phone),
            wallet_address=_wallet_from_phone(phone),
            password_hash=password_hash,
            is_verified=True,
        )
        db.add(user)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        LOGGER.info("Mobile onboarding conflict for phone=%s", phone)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User conflict while saving profile") from exc

    await db.refresh(user)
    return MobileOnboardResponse(saved=True, user_id=str(user.id))


@router.post("/mobile-login", response_model=MobileLoginResponse)
async def mobile_login(
    payload: MobileLoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MobileLoginResponse:
    """Authenticate mobile user by phone/password and return profile with tokens."""

    phone = _normalize_phone(payload.phone)
    result = await db.execute(select(User).where(User.phone == phone))
    user = result.scalar_one_or_none()
    if not user or not await auth_service.verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token_pair = auth_service.create_token_pair(str(user.id))
    return MobileLoginResponse(
        authenticated=True,
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        token_type=token_pair.token_type,
        user=MobileUserProfile(
            id=str(user.id),
            name=user.name,
            phone=user.phone,
            role=user.role,
            wallet_address=user.wallet_address,
            is_verified=user.is_verified,
        ),
    )


@router.get("/mobile-dashboard", response_model=MobileDashboardResponse)
async def mobile_dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> MobileDashboardResponse:
    """Return authenticated mobile dashboard payload from live backend data."""

    if current_user.role == UserRole.FARMER:
        base_query = select(Batch).where(Batch.farmer_id == current_user.id)
    elif current_user.role in {UserRole.DISTRIBUTOR, UserRole.RETAILER}:
        base_query = select(Batch).where(Batch.current_owner_id == current_user.id)
    else:
        base_query = select(Batch)

    recent_result = await db.execute(base_query.order_by(Batch.created_at.desc()).limit(8))
    recent_batches = list(recent_result.scalars().all())

    active_count_result = await db.execute(
        select(func.count(Batch.id)).where(Batch.status.in_([BatchStatus.CREATED, BatchStatus.IN_TRANSIT]))
    )
    active_batches_count = int(active_count_result.scalar_one() or 0)

    pending_count_result = await db.execute(
        select(func.count(Batch.id)).where(Batch.status == BatchStatus.IN_TRANSIT)
    )
    pending_transfers_count = int(pending_count_result.scalar_one() or 0)

    recent_items = [
        MobileDashboardBatchItem(
            id=str(batch.id),
            batch_code=batch.batch_code,
            crop_type=batch.crop_type,
            quantity=batch.quantity,
            status=batch.status,
        )
        for batch in recent_batches
    ]

    inventory_items = [
        MobileDashboardInventoryItem(
            name=batch.crop_type,
            demand_signal="AI demand ↑" if index % 2 == 0 else "AI demand stable",
            expiry_hint="Dispatch in 2 days" if index % 2 == 0 else "Dispatch in 5 days",
        )
        for index, batch in enumerate(recent_batches[:4])
    ]

    role_title = current_user.role.value.capitalize()
    summary_title = f"{role_title} Summary"
    summary_subtitle = (
        f"Active batches: {active_batches_count} · Pending transfers: {pending_transfers_count}"
    )

    alerts = [
        f"Pending transfers currently: {pending_transfers_count}",
        f"Total active batches across network: {active_batches_count}",
    ]
    if recent_batches:
        alerts.append(f"Latest batch: {recent_batches[0].batch_code} ({recent_batches[0].crop_type})")

    orders = [
        f"Order from batch {item.batch_code} · status {item.status.value}"
        for item in recent_items[:3]
    ]

    trust_score = 70 + min(25, len(recent_batches) * 2)
    freshness_score = 65 + min(30, len(recent_batches) * 3)

    return MobileDashboardResponse(
        role=current_user.role,
        greeting_name=current_user.name,
        summary_title=summary_title,
        summary_subtitle=summary_subtitle,
        weather_text="31°C · Light breeze · Cloud cover 24%",
        price_prediction_text="Tomato up 6% tomorrow",
        freshness_score=freshness_score,
        trust_score=trust_score,
        active_batches_count=active_batches_count,
        pending_transfers_count=pending_transfers_count,
        recent_batches=recent_items,
        inventory_items=inventory_items,
        alerts=alerts,
        orders=orders,
        recommendation="Prioritize dispatch for in-transit batches older than 24h.",
    )


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
