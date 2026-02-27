"""Batch lifecycle APIs with role-based access and service orchestration."""

import uuid
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.qr import generate_batch_qr
from app.db.database import get_db
from app.models.batch import Batch, BatchStatus
from app.models.user import User, UserRole
from app.services.blockchain_service import BlockchainService
from app.services.ipfs_service import IPFSService
from app.utils.roles import get_current_user, require_role

router = APIRouter(prefix="/batches", tags=["batches"])

blockchain_service = BlockchainService()
ipfs_service = IPFSService()


class CreateBatchRequest(BaseModel):
    """Request payload for farmer batch creation."""

    model_config = ConfigDict(str_strip_whitespace=True)

    crop_type: str = Field(min_length=2, max_length=120)
    quantity: str = Field(min_length=1, max_length=50)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TransferBatchRequest(BaseModel):
    """Request payload for ownership transfer."""

    new_owner_id: uuid.UUID
    status: BatchStatus = BatchStatus.IN_TRANSIT


class BatchResponse(BaseModel):
    """API response model for batch details."""

    id: uuid.UUID
    batch_code: str
    farmer_id: uuid.UUID
    current_owner_id: uuid.UUID
    crop_type: str
    quantity: str
    ipfs_metadata_cid: str
    blockchain_tx_hash: str | None
    status: BatchStatus
    qr_data: str
    created_at: datetime
    updated_at: datetime


def _batch_code() -> str:
    """Generate a readable, unique batch code."""

    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    suffix = uuid.uuid4().hex[:6].upper()
    return f"BATCH-{timestamp}-{suffix}"


def _to_response(batch: Batch) -> BatchResponse:
    """Map ORM Batch model to API response schema."""

    return BatchResponse(
        id=batch.id,
        batch_code=batch.batch_code,
        farmer_id=batch.farmer_id,
        current_owner_id=batch.current_owner_id,
        crop_type=batch.crop_type,
        quantity=batch.quantity,
        ipfs_metadata_cid=batch.ipfs_metadata_cid,
        blockchain_tx_hash=batch.blockchain_tx_hash,
        status=batch.status,
        qr_data=generate_batch_qr(batch.id),
        created_at=batch.created_at,
        updated_at=batch.updated_at,
    )


@router.post("/create", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
async def create_batch(
    payload: CreateBatchRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role([UserRole.FARMER.value]))],
) -> BatchResponse:
    """Create a new product batch and mint blockchain asset."""

    metadata_payload = {
        "crop_type": payload.crop_type,
        "quantity": payload.quantity,
        "farmer_id": str(current_user.id),
        **payload.metadata,
    }
    cid = await ipfs_service.upload_json(metadata_payload)
    batch_id = uuid.uuid4()
    minted = await blockchain_service.mint_batch(str(batch_id), cid)

    batch = Batch(
        id=batch_id,
        batch_code=_batch_code(),
        farmer_id=current_user.id,
        current_owner_id=current_user.id,
        crop_type=payload.crop_type,
        quantity=payload.quantity,
        ipfs_metadata_cid=cid,
        blockchain_tx_hash=minted.tx_hash,
        status=BatchStatus.CREATED,
    )
    db.add(batch)
    await db.commit()
    await db.refresh(batch)

    return _to_response(batch)


@router.post("/{batch_id}/transfer", response_model=BatchResponse)
async def transfer_batch(
    batch_id: uuid.UUID,
    payload: TransferBatchRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_role([UserRole.DISTRIBUTOR.value, UserRole.RETAILER.value])),
    ],
) -> BatchResponse:
    """Transfer current batch ownership and update blockchain state."""

    batch_result = await db.execute(select(Batch).where(Batch.id == batch_id))
    batch = batch_result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    if batch.current_owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only current owner can transfer")

    owner_result = await db.execute(select(User).where(User.id == payload.new_owner_id))
    new_owner = owner_result.scalar_one_or_none()
    if not new_owner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New owner not found")

    transfer_result = await blockchain_service.transfer_ownership(
        str(batch.id),
        from_addr=current_user.wallet_address,
        to_addr=new_owner.wallet_address,
    )

    batch.current_owner_id = new_owner.id
    batch.status = payload.status
    batch.blockchain_tx_hash = transfer_result.tx_hash

    await db.commit()
    await db.refresh(batch)

    return _to_response(batch)


@router.get("/{batch_id}", response_model=BatchResponse)
async def get_batch(
    batch_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> BatchResponse:
    """Return full batch detail payload."""

    result = await db.execute(select(Batch).where(Batch.id == batch_id))
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    return _to_response(batch)
