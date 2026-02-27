"""Background blockchain event listener with resilient polling."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Mapping
from typing import Any

from app.config import get_settings
from app.services.blockchain_service import BlockchainService
from app.workers.event_processor import event_processor, process_event

LOGGER = logging.getLogger(__name__)


class BlockchainListener:
    """Polls blockchain contract events and forwards to processor."""

    def __init__(self, poll_interval_seconds: float = 3.0, max_backoff_seconds: float = 30.0) -> None:
        settings = get_settings()
        self.poll_interval_seconds = poll_interval_seconds
        self.max_backoff_seconds = max_backoff_seconds
        self.heartbeat_cycles = settings.listener_heartbeat_cycles
        self.blockchain_service = BlockchainService()
        self._stop_event = asyncio.Event()
        self._from_block = 0
        self._running = False
        self._started_at: float | None = None
        self._cycle_count = 0

    async def start(self) -> None:
        """Start listener polling loop."""

        if self._running:
            return

        self._running = True
        self._started_at = time.monotonic()
        retry_delay = self.poll_interval_seconds
        LOGGER.info("Blockchain listener started")

        while not self._stop_event.is_set():
            try:
                retried = await event_processor.process_retriable_events()
                if retried:
                    LOGGER.info("Retried failed events", extra={"count": retried})

                events, next_from_block = await self.blockchain_service.fetch_events(self._from_block)
                self._from_block = next_from_block
                self._cycle_count += 1

                if self._cycle_count % max(self.heartbeat_cycles, 1) == 0:
                    LOGGER.info(
                        "Listener heartbeat",
                        extra={
                            "cycle": self._cycle_count,
                            "from_block": self._from_block,
                            "running": self._running,
                        },
                    )

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

    @property
    def is_running(self) -> bool:
        """Return whether listener loop is active."""

        return self._running

    @property
    def current_block(self) -> int:
        """Return current polling block pointer."""

        return self._from_block

    def uptime_seconds(self) -> int:
        """Return listener uptime in seconds."""

        if self._started_at is None:
            return 0
        return int(max(0.0, time.monotonic() - self._started_at))


_listener_instance: BlockchainListener | None = None


def get_listener(poll_interval: float | None = None) -> BlockchainListener:
    """Return a shared listener instance to prevent duplicates."""

    global _listener_instance
    if _listener_instance is None:
        settings = get_settings()
        _listener_instance = BlockchainListener(poll_interval_seconds=poll_interval or settings.blockchain_poll_interval)
    return _listener_instance


async def get_event_backlog_size() -> int:
    """Get event backlog size from durable event store."""

    return await event_processor.get_event_backlog_size()


async def get_last_processed_block() -> int | None:
    """Get latest processed block number from durable event store."""

    return await event_processor.get_last_processed_block()


def get_listener_uptime() -> int:
    """Return uptime of shared listener instance."""

    listener = get_listener()
    return listener.uptime_seconds()


async def _main() -> None:
    """Run a short listener dry-run for local verification."""

    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    listener = get_listener()
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
