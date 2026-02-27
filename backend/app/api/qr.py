"""QR APIs for AGRICHAIN batch URIs."""

import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/qr", tags=["qr"])


def generate_batch_qr(batch_id: uuid.UUID) -> str:
    """Generate QR payload for a batch URI."""

    return f"agrichain://batch/{batch_id}"


def decode_qr(data: str) -> uuid.UUID:
    """Decode AGRICHAIN batch URI payload into UUID."""

    prefix = "agrichain://batch/"
    if not data.startswith(prefix):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid QR payload")
    raw_batch_id = data.replace(prefix, "", 1)
    try:
        return uuid.UUID(raw_batch_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid batch UUID") from exc


class DecodeQRRequest(BaseModel):
    """Request schema for QR payload decoding."""

    data: str


@router.get("/generate/{batch_id}")
async def generate_qr_endpoint(batch_id: uuid.UUID) -> dict[str, str]:
    """Return QR payload string for the given batch UUID."""

    return {"qr_data": generate_batch_qr(batch_id)}


@router.post("/decode")
async def decode_qr_endpoint(payload: DecodeQRRequest) -> dict[str, str]:
    """Decode QR payload into batch UUID."""

    return {"batch_id": str(decode_qr(payload.data))}
