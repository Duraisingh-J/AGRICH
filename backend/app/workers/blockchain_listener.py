"""Background blockchain event listener with resilient polling."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping
from typing import Any

from app.services.blockchain_service import BlockchainService
from app.workers.event_processor import process_event

LOGGER = logging.getLogger(__name__)


class BlockchainListener:
    """Polls blockchain contract events and forwards to processor."""

    def __init__(self, poll_interval_seconds: float = 3.0, max_backoff_seconds: float = 30.0) -> None:
        self.poll_interval_seconds = poll_interval_seconds
        self.max_backoff_seconds = max_backoff_seconds
        self.blockchain_service = BlockchainService()
        self._stop_event = asyncio.Event()
        self._from_block = 0
        self._running = False

    async def start(self) -> None:
        """Start listener polling loop."""

        if self._running:
            return

        self._running = True
        retry_delay = self.poll_interval_seconds
        LOGGER.info("Blockchain listener started")

        while not self._stop_event.is_set():
            try:
                events, next_from_block = await self.blockchain_service.fetch_events(self._from_block)
                self._from_block = next_from_block

                for event in events:
                    await self._handle_event(event)

                retry_delay = self.poll_interval_seconds
                await asyncio.sleep(self.poll_interval_seconds)
            except asyncio.CancelledError:
                LOGGER.info("Blockchain listener cancelled")
                break
            except Exception:
                LOGGER.exception("Listener polling failed; retrying")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, self.max_backoff_seconds)

        self._running = False
        LOGGER.info("Blockchain listener stopped")

    async def _handle_event(self, event: Mapping[str, Any]) -> None:
        """Process one event with safety logging."""

        ok = await process_event(event)
        if not ok:
            LOGGER.warning("Event processing returned false", extra={"event": dict(event)})

    async def stop(self) -> None:
        """Request graceful listener shutdown."""

        self._stop_event.set()


async def _main() -> None:
    """Run a short listener dry-run for local verification."""

    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    listener = BlockchainListener()
    healthy = await listener.blockchain_service.is_blockchain_healthy()
    if not healthy:
        LOGGER.info("web3 unavailable — running in passive mode")

    task = asyncio.create_task(listener.start())
    try:
        await asyncio.sleep(5)
    finally:
        await listener.stop()
        await task


if __name__ == "__main__":
    asyncio.run(_main())
