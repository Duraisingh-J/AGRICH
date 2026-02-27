"""Event processing pipeline for blockchain events."""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import Mapping
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.database import SessionLocal
from app.models.batch import Batch, BatchStatus
from app.models.user import User
from app.services.trust_service import TrustService

LOGGER = logging.getLogger(__name__)


class EventProcessor:
    """Applies blockchain events to database state with idempotency guards."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession] = SessionLocal) -> None:
        self.session_factory = session_factory
        self.trust_service = TrustService()
        self._processed_event_keys: set[str] = set()
        self._lock = asyncio.Lock()

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

        try:
            async with self.session_factory() as session:
                async with session.begin():
                    handled = await self._apply_event(session, event_name, tx_hash, args)
                    if not handled:
                        return False

            await self.trust_service.update_trust_on_event(event_name)
            async with self._lock:
                self._processed_event_keys.add(event_key)
            return True
        except Exception:
            LOGGER.exception("Failed processing blockchain event", extra={"event": event})
            return False

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
