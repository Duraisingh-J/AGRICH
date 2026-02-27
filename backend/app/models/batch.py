"""Product batch ORM model for traceability lifecycle."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class BatchStatus(str, enum.Enum):
    """Lifecycle status for product batches."""

    CREATED = "created"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    RECEIVED = "received"
    REJECTED = "rejected"


class Batch(Base):
    """Product batch metadata and ownership tracking."""

    __tablename__ = "batches"
    __table_args__ = (
        Index("ix_batches_batch_code", "batch_code"),
        Index("ix_batches_farmer_id", "farmer_id"),
        Index("ix_batches_current_owner_id", "current_owner_id"),
        Index("ix_batches_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    current_owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    crop_type: Mapped[str] = mapped_column(String(120), nullable=False)
    quantity: Mapped[str] = mapped_column(String(50), nullable=False)
    ipfs_metadata_cid: Mapped[str] = mapped_column(String(120), nullable=False)
    blockchain_tx_hash: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[BatchStatus] = mapped_column(
        Enum(BatchStatus, name="batch_status"),
        nullable=False,
        default=BatchStatus.CREATED,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
