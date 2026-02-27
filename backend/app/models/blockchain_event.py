"""Blockchain event persistence model for durable, idempotent processing."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class BlockchainEventStatus(str, enum.Enum):
    """Status lifecycle for persisted blockchain events."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class BlockchainEvent(Base):
    """Durable blockchain event log with retry metadata."""

    __tablename__ = "blockchain_events"
    __table_args__ = (
        UniqueConstraint("tx_hash", "log_index", name="uq_blockchain_events_tx_log"),
        Index("ix_blockchain_events_status", "status"),
        Index("ix_blockchain_events_block_number", "block_number"),
        Index("ix_blockchain_events_next_retry_at", "next_retry_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_name: Mapped[str] = mapped_column(String(80), nullable=False)
    tx_hash: Mapped[str] = mapped_column(String(100), nullable=False)
    log_index: Mapped[int] = mapped_column(Integer, nullable=False)
    block_number: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[BlockchainEventStatus] = mapped_column(
        Enum(BlockchainEventStatus, name="blockchain_event_status"),
        nullable=False,
        default=BlockchainEventStatus.PENDING,
    )
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
