"""Event processing pipeline for blockchain events."""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import UTC, datetime, timedelta
from collections.abc import Mapping
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.database import SessionLocal
from app.models.batch import Batch, BatchStatus
from app.models.blockchain_event import BlockchainEvent, BlockchainEventStatus
from app.models.user import User
from app.services.trust_service import TrustService

LOGGER = logging.getLogger(__name__)


class EventProcessor:
    """Applies blockchain events to database state with idempotency guards."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] = SessionLocal,
        max_retries: int = 5,
    ) -> None:
        self.session_factory = session_factory
        self.trust_service = TrustService()
        self._processed_event_keys: set[str] = set()
        self._lock = asyncio.Lock()
        self.max_retries = max_retries

    @staticmethod
    def _event_key(event: Mapping[str, Any]) -> str:
        """Build deterministic key for duplicate event detection."""

        return f"{event.get('tx_hash')}:{event.get('event_name')}:{event.get('log_index')}"

    async def process_event(self, event: Mapping[str, Any]) -> bool:
        """Process a blockchain event transaction-safely and idempotently."""

        event_key = self._event_key(event)
        async with self._lock:
            if event_key in self._processed_event_keys:
                LOGGER.info("Skipping duplicate event", extra={"event_key": event_key})
                return True

        event_name = str(event.get("event_name", ""))
        tx_hash = str(event.get("tx_hash", ""))
        args = event.get("args", {})
        if not isinstance(args, Mapping):
            LOGGER.warning("Invalid event args payload", extra={"event": event})
            return False

        event_record_id = await self._upsert_event_record(event_name, tx_hash, event, args)
        if event_record_id is None:
            return False

        try:
            async with self.session_factory() as session:
                async with session.begin():
                    event_record = await session.get(BlockchainEvent, event_record_id, with_for_update=True)
                    if event_record is None:
                        return False

                    if event_record.status == BlockchainEventStatus.COMPLETED:
                        return True

                    if (
                        event_record.status == BlockchainEventStatus.FAILED
                        and event_record.next_retry_at is not None
                        and event_record.next_retry_at > datetime.now(UTC)
                    ):
                        return False

                    event_record.status = BlockchainEventStatus.PROCESSING
                    handled = await self._apply_event(session, event_name, tx_hash, args)
                    if not handled:
                        await self.mark_event_failed(event_record.id, "Domain apply returned false", session=session)
                        return False

                    event_record.status = BlockchainEventStatus.COMPLETED
                    event_record.processed_at = datetime.now(UTC)
                    event_record.last_error = None
                    event_record.next_retry_at = None

            await self.trust_service.update_trust_on_event(event_name)
            async with self._lock:
                self._processed_event_keys.add(event_key)
            return True
        except Exception as exc:
            await self.mark_event_failed(event_record_id, str(exc))
            LOGGER.exception("Failed processing blockchain event", extra={"event": event})
            return False

    async def _upsert_event_record(
        self,
        event_name: str,
        tx_hash: str,
        event: Mapping[str, Any],
        args: Mapping[str, Any],
    ) -> uuid.UUID | None:
        """Create or fetch durable event row using unique tx/log identity."""

        raw_log_index = event.get("log_index")
        try:
            log_index = int(raw_log_index)
        except (TypeError, ValueError):
            LOGGER.warning("Invalid log_index in event", extra={"event": event})
            return None

        raw_block_number = event.get("block_number")
        try:
            block_number = int(raw_block_number)
        except (TypeError, ValueError):
            block_number = 0

        payload = {
            "event_name": event_name,
            "tx_hash": tx_hash,
            "args": dict(args),
            "block_number": block_number,
            "log_index": log_index,
        }

        async with self.session_factory() as session:
            stmt = (
                insert(BlockchainEvent)
                .values(
                    id=uuid.uuid4(),
                    event_name=event_name,
                    tx_hash=tx_hash,
                    log_index=log_index,
                    block_number=block_number,
                    payload=payload,
                    status=BlockchainEventStatus.PENDING,
                    retry_count=0,
                )
                .on_conflict_do_nothing(index_elements=["tx_hash", "log_index"])
            )
            await session.execute(stmt)
            await session.commit()

            row = (
                await session.execute(
                    select(BlockchainEvent.id).where(
                        BlockchainEvent.tx_hash == tx_hash,
                        BlockchainEvent.log_index == log_index,
                    )
                )
            ).scalar_one_or_none()
            return row

    async def mark_event_failed(
        self,
        event_id: uuid.UUID,
        reason: str,
        session: AsyncSession | None = None,
    ) -> None:
        """Mark event as failed with exponential retry metadata."""

        now = datetime.now(UTC)

        async def _apply(target_session: AsyncSession) -> None:
            event_row = await target_session.get(BlockchainEvent, event_id, with_for_update=True)
            if event_row is None:
                return

            event_row.retry_count = int(event_row.retry_count) + 1
            capped_attempt = min(event_row.retry_count, 8)
            backoff_seconds = 2**capped_attempt
            event_row.last_error = reason[:2000]
            event_row.next_retry_at = now + timedelta(seconds=backoff_seconds)
            event_row.status = (
                BlockchainEventStatus.FAILED
                if event_row.retry_count < self.max_retries
                else BlockchainEventStatus.FAILED
            )
            LOGGER.warning(
                "Event marked failed",
                extra={
                    "event_id": str(event_id),
                    "retry_count": event_row.retry_count,
                    "next_retry_at": event_row.next_retry_at,
                },
            )

        if session is not None:
            await _apply(session)
            return

        async with self.session_factory() as managed_session:
            async with managed_session.begin():
                await _apply(managed_session)

    async def get_event_backlog_size(self) -> int:
        """Return count of events pending or eligible for retry."""

        now = datetime.now(UTC)
        async with self.session_factory() as session:
            query = select(func.count()).where(
                (BlockchainEvent.status.in_([BlockchainEventStatus.PENDING, BlockchainEventStatus.PROCESSING]))
                | (
                    (BlockchainEvent.status == BlockchainEventStatus.FAILED)
                    & ((BlockchainEvent.next_retry_at.is_(None)) | (BlockchainEvent.next_retry_at <= now))
                )
            )
            count = (await session.execute(query)).scalar_one()
            return int(count)

    async def get_last_processed_block(self) -> int | None:
        """Return latest block number for completed events."""

        async with self.session_factory() as session:
            block = (
                await session.execute(
                    select(func.max(BlockchainEvent.block_number)).where(
                        BlockchainEvent.status == BlockchainEventStatus.COMPLETED
                    )
                )
            ).scalar_one_or_none()
            return int(block) if block is not None else None

    async def process_retriable_events(self, limit: int = 25) -> int:
        """Process failed events that are eligible for retry."""

        now = datetime.now(UTC)
        processed = 0
        async with self.session_factory() as session:
            rows = (
                await session.execute(
                    select(BlockchainEvent)
                    .where(
                        BlockchainEvent.status == BlockchainEventStatus.FAILED,
                        BlockchainEvent.retry_count < self.max_retries,
                        (BlockchainEvent.next_retry_at.is_(None) | (BlockchainEvent.next_retry_at <= now)),
                    )
                    .order_by(BlockchainEvent.block_number.asc(), BlockchainEvent.log_index.asc())
                    .limit(limit)
                )
            ).scalars().all()

        for row in rows:
            payload = row.payload if isinstance(row.payload, dict) else {}
            event = {
                "event_name": payload.get("event_name", row.event_name),
                "tx_hash": payload.get("tx_hash", row.tx_hash),
                "log_index": payload.get("log_index", row.log_index),
                "block_number": payload.get("block_number", row.block_number),
                "args": payload.get("args", {}),
            }
            if await self.process_event(event):
                processed += 1
        return processed

    async def _apply_event(
        self,
        session: AsyncSession,
        event_name: str,
        tx_hash: str,
        args: Mapping[str, Any],
    ) -> bool:
        """Apply concrete event mutation in a DB transaction."""

        batch_id_raw = str(args.get("batchId") or args.get("batch_id") or "")
        if not batch_id_raw:
            LOGGER.warning("Batch id missing in event")
            return False

        try:
            batch_id = uuid.UUID(batch_id_raw)
        except ValueError:
            LOGGER.warning("Malformed batch id in event", extra={"batch_id": batch_id_raw})
            return False

        batch = (await session.execute(select(Batch).where(Batch.id == batch_id))).scalar_one_or_none()
        if not batch:
            LOGGER.warning("Batch not found for event", extra={"batch_id": str(batch_id)})
            return False

        if batch.blockchain_tx_hash == tx_hash:
            LOGGER.info("Duplicate tx hash already applied", extra={"tx_hash": tx_hash})
            return True

        if event_name == "BatchMinted":
            batch.blockchain_tx_hash = tx_hash
            batch.status = BatchStatus.CREATED
            return True

        if event_name == "OwnershipTransferred":
            to_address_raw = str(args.get("to") or args.get("newOwner") or args.get("to_addr") or "")
            if not to_address_raw:
                LOGGER.warning("OwnershipTransferred missing to-address")
                return False

            target_user = (
                await session.execute(
                    select(User).where(func.lower(User.wallet_address) == to_address_raw.lower())
                )
            ).scalar_one_or_none()
            if not target_user:
                LOGGER.warning("Target user not found for transfer", extra={"to": to_address_raw})
                return False

            batch.current_owner_id = target_user.id
            batch.status = BatchStatus.IN_TRANSIT
            batch.blockchain_tx_hash = tx_hash
            return True

        LOGGER.info("Ignoring unhandled event type", extra={"event_name": event_name})
        return True


event_processor = EventProcessor()


async def process_event(event: Mapping[str, Any]) -> bool:
    """Process blockchain event using shared processor instance."""

    return await event_processor.process_event(event)


async def mark_event_failed(event_id: uuid.UUID, reason: str) -> None:
    """Mark persisted event failed with retry metadata."""

    await event_processor.mark_event_failed(event_id=event_id, reason=reason)
