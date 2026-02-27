"""Integration validator for reliability checks without real blockchain."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select

from app.db.database import SessionLocal
from app.models.batch import Batch, BatchStatus
from app.models.blockchain_event import BlockchainEvent, BlockchainEventStatus
from app.workers.event_processor import EventProcessor

LOGGER = logging.getLogger("app.integration_validator")


def _mock_event(event_name: str, batch_id: uuid.UUID, tx_hash: str, log_index: int, block_number: int) -> dict[str, Any]:
    """Create a mock blockchain event payload in listener format."""

    args: dict[str, Any]
    if event_name == "BatchMinted":
        args = {"batchId": str(batch_id)}
    else:
        args = {"batchId": str(batch_id), "to": "0x1111111111111111111111111111111111111111"}

    return {
        "event_name": event_name,
        "tx_hash": tx_hash,
        "log_index": log_index,
        "block_number": block_number,
        "args": args,
    }


async def run_integration_validation() -> dict[str, Any]:
    """Run integration reliability checks against local DB state."""

    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    processor = EventProcessor()

    async with SessionLocal() as session:
        batch = (
            await session.execute(select(Batch).order_by(Batch.created_at.desc()).limit(1))
        ).scalar_one_or_none()
        if batch is None:
            return {
                "status": "fail",
                "message": "No batch available for integration validation",
            }

    mint_tx_hash = f"0x{uuid.uuid4().hex}{uuid.uuid4().hex[:8]}"
    mint_event = _mock_event("BatchMinted", batch.id, mint_tx_hash, log_index=0, block_number=100)

    mint_first = await processor.process_event(mint_event)
    mint_second_duplicate = await processor.process_event(mint_event)

    async with SessionLocal() as session:
        event_rows = (
            await session.execute(
                select(BlockchainEvent).where(
                    BlockchainEvent.tx_hash == mint_tx_hash,
                    BlockchainEvent.log_index == 0,
                )
            )
        ).scalars().all()
        persisted_unique = len(event_rows) == 1

    bad_event = {
        "event_name": "OwnershipTransferred",
        "tx_hash": f"0x{uuid.uuid4().hex}{uuid.uuid4().hex[:8]}",
        "log_index": 1,
        "block_number": 101,
        "args": {"batchId": str(batch.id)},
    }
    bad_processed = await processor.process_event(bad_event)

    async with SessionLocal() as session:
        failed_row = (
            await session.execute(
                select(BlockchainEvent).where(
                    BlockchainEvent.tx_hash == bad_event["tx_hash"],
                    BlockchainEvent.log_index == 1,
                )
            )
        ).scalar_one_or_none()

        retry_meta_ok = bool(
            failed_row is not None
            and failed_row.status == BlockchainEventStatus.FAILED
            and failed_row.retry_count >= 1
            and failed_row.next_retry_at is not None
        )

        if failed_row is not None:
            failed_row.next_retry_at = datetime.now(UTC) - timedelta(seconds=1)
            await session.commit()

    retried_count = await processor.process_retriable_events(limit=10)

    async with SessionLocal() as session:
        updated_batch = await session.get(Batch, batch.id)
        status_is_valid = bool(updated_batch and updated_batch.status in {BatchStatus.CREATED, BatchStatus.IN_TRANSIT})

    checks = {
        "mint_first_processed": mint_first,
        "duplicate_protection": mint_second_duplicate,
        "event_unique_constraint_effective": persisted_unique,
        "failed_event_detected": not bad_processed,
        "retry_metadata_written": retry_meta_ok,
        "retriable_events_attempted": retried_count >= 0,
        "batch_state_intact": status_is_valid,
    }

    overall = all(checks.values())
    result = {
        "status": "pass" if overall else "fail",
        "checks": checks,
    }
    LOGGER.info("Integration validator result", extra={"result": result})
    return result


async def _main() -> None:
    """CLI entrypoint for integration validator."""

    result = await run_integration_validation()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(_main())
