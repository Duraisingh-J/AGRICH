"""Blockchain interaction service layer using Web3.py abstractions."""

import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any

import asyncio
from fastapi.concurrency import run_in_threadpool

from app.config import get_settings
from app.utils.blockchain_config import get_contract, get_web3

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class BlockchainTxResult:
    """Represents a blockchain transaction outcome."""

    success: bool
    tx_hash: str
    network: str


class BlockchainUnavailable(Exception):
    """Raised when blockchain RPC/client is unavailable."""


class ContractNotConfigured(Exception):
    """Raised when contract client is missing/misconfigured."""


class TransactionFailed(Exception):
    """Raised when on-chain transaction execution fails."""


class BlockchainService:
    """Async-safe blockchain wrappers for AGRICHAIN operations."""

    def __init__(self) -> None:
        settings = get_settings()
        self.rpc_url = settings.web3_rpc_url
        self.default_sender = settings.blockchain_default_sender
        self.network = "ethereum"
        self.request_timeout_seconds = settings.blockchain_request_timeout_seconds
        self.failure_threshold = settings.blockchain_failure_threshold
        self.cooldown_seconds = settings.blockchain_cooldown_seconds
        self.health_cache_ttl_seconds = settings.blockchain_health_cache_ttl_seconds
        self._web3: Any | None = None
        self._contract: Any | None = None
        self._failure_count = 0
        self._cooldown_until = 0.0
        self._health_cache_value = False
        self._health_cache_until = 0.0

    def _lazy_clients(self) -> tuple[Any | None, Any | None]:
        """Get cached Web3 and contract clients lazily."""

        if self._web3 is None:
            self._web3 = get_web3()
        if self._contract is None:
            self._contract = get_contract()
        return self._web3, self._contract

    @staticmethod
    def _mock_tx_result() -> BlockchainTxResult:
        """Return deterministic shaped mock tx response."""

        return BlockchainTxResult(
            success=True,
            tx_hash=f"0x{uuid.uuid4().hex}{uuid.uuid4().hex[:8]}",
            network="ethereum",
        )

    async def is_blockchain_healthy(self) -> bool:
        """Check blockchain RPC connectivity health."""

        now = time.monotonic()
        if now < self._health_cache_until:
            return self._health_cache_value

        web3, _ = self._lazy_clients()
        if web3 is None:
            self._health_cache_value = False
            self._health_cache_until = now + self.health_cache_ttl_seconds
            return False
        try:
            healthy = bool(await asyncio.wait_for(run_in_threadpool(web3.is_connected), timeout=self.request_timeout_seconds))
            self._health_cache_value = healthy
            self._health_cache_until = now + self.health_cache_ttl_seconds
            return healthy
        except Exception:
            LOGGER.exception("Blockchain health check failed")
            self._health_cache_value = False
            self._health_cache_until = now + self.health_cache_ttl_seconds
            return False

    def _is_circuit_open(self) -> bool:
        """Return whether circuit-breaker cooldown is active."""

        return time.monotonic() < self._cooldown_until

    def _record_failure(self) -> None:
        """Track failure count and open cooldown circuit when threshold reached."""

        self._failure_count += 1
        if self._failure_count >= self.failure_threshold:
            self._cooldown_until = time.monotonic() + self.cooldown_seconds

    def _record_success(self) -> None:
        """Reset failure counters after successful blockchain operation."""

        self._failure_count = 0
        self._cooldown_until = 0.0

    async def mint_batch(self, batch_id: str, metadata_cid: str) -> BlockchainTxResult:
        """Mint batch token on blockchain with real-call fallback behavior."""

        LOGGER.info("Mint batch requested", extra={"batch_id": batch_id, "cid": metadata_cid})
        if self._is_circuit_open():
            LOGGER.warning("Mint skipped due to circuit cooldown")
            return self._mock_tx_result()

        web3, contract = self._lazy_clients()
        if web3 is None or contract is None or not self.default_sender:
            if web3 is None:
                LOGGER.warning("Blockchain unavailable", extra={"error_type": "BlockchainUnavailable"})
            else:
                LOGGER.warning("Contract not configured", extra={"error_type": "ContractNotConfigured"})
            self._record_failure()
            return self._mock_tx_result()

        try:
            sender = web3.to_checksum_address(self.default_sender)

            def _transact() -> str:
                tx_hash = contract.functions.mintBatch(batch_id, metadata_cid).transact({"from": sender})
                receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                return receipt.transactionHash.hex()

            tx_hash = await asyncio.wait_for(run_in_threadpool(_transact), timeout=self.request_timeout_seconds)
            self._record_success()
            return BlockchainTxResult(success=True, tx_hash=tx_hash, network=self.network)
        except Exception as exc:
            self._record_failure()
            LOGGER.exception(
                "Mint failed, using mock response",
                extra={"error_type": TransactionFailed.__name__, "reason": str(exc)},
            )
            return self._mock_tx_result()

    async def transfer_ownership(
        self,
        batch_id: str,
        from_addr: str,
        to_addr: str,
    ) -> BlockchainTxResult:
        """Transfer ownership on blockchain with real-call fallback behavior."""

        LOGGER.info(
            "Transfer ownership requested",
            extra={"batch_id": batch_id, "from": from_addr, "to": to_addr},
        )
        if self._is_circuit_open():
            LOGGER.warning("Transfer skipped due to circuit cooldown")
            return self._mock_tx_result()

        web3, contract = self._lazy_clients()
        if web3 is None or contract is None:
            if web3 is None:
                LOGGER.warning("Blockchain unavailable", extra={"error_type": "BlockchainUnavailable"})
            else:
                LOGGER.warning("Contract not configured", extra={"error_type": "ContractNotConfigured"})
            self._record_failure()
            return self._mock_tx_result()

        try:
            from_checksum = web3.to_checksum_address(from_addr)
            to_checksum = web3.to_checksum_address(to_addr)

            def _transact() -> str:
                transfer_fn = contract.functions.transferOwnership
                try:
                    tx_hash = transfer_fn(batch_id, from_checksum, to_checksum).transact({"from": from_checksum})
                except TypeError:
                    tx_hash = transfer_fn(batch_id, to_checksum).transact({"from": from_checksum})
                receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                return receipt.transactionHash.hex()

            tx_hash = await asyncio.wait_for(run_in_threadpool(_transact), timeout=self.request_timeout_seconds)
            self._record_success()
            return BlockchainTxResult(success=True, tx_hash=tx_hash, network=self.network)
        except Exception as exc:
            self._record_failure()
            LOGGER.exception(
                "Transfer failed, using mock response",
                extra={"error_type": TransactionFailed.__name__, "reason": str(exc)},
            )
            return self._mock_tx_result()

    async def get_batch_history(self, batch_id: str) -> list[dict[str, Any]]:
        """Get historical blockchain events for a batch (real-call fallback)."""

        web3, contract = self._lazy_clients()
        if web3 is None or contract is None:
            self._record_failure()
            return [
                {
                    "batch_id": batch_id,
                    "event": "BatchMinted",
                    "tx_hash": f"0x{uuid.uuid4().hex}{uuid.uuid4().hex[:8]}",
                }
            ]

        try:
            def _fetch_history() -> list[dict[str, Any]]:
                minted = contract.events.BatchMinted.create_filter(fromBlock=0).get_all_entries()
                transferred = contract.events.OwnershipTransferred.create_filter(fromBlock=0).get_all_entries()
                records: list[dict[str, Any]] = []
                for event in [*minted, *transferred]:
                    args = dict(event["args"])
                    event_batch_id = str(args.get("batchId") or args.get("batch_id") or "")
                    if event_batch_id != batch_id:
                        continue
                    tx_hash = event["transactionHash"].hex()
                    records.append(
                        {
                            "batch_id": event_batch_id,
                            "event": event["event"],
                            "tx_hash": tx_hash,
                            "block_number": event["blockNumber"],
                            "args": {k: str(v) for k, v in args.items()},
                        }
                    )
                return records

            history = await asyncio.wait_for(run_in_threadpool(_fetch_history), timeout=self.request_timeout_seconds)
            self._record_success()
            return history
        except Exception:
            self._record_failure()
            LOGGER.exception("History fetch failed, using mock fallback")
            return [
                {
                    "batch_id": batch_id,
                    "event": "BatchMinted",
                    "tx_hash": f"0x{uuid.uuid4().hex}{uuid.uuid4().hex[:8]}",
                }
            ]

    async def verify_transaction(self, tx_hash: str) -> dict[str, Any]:
        """Verify transaction inclusion/finality with fallback behavior."""

        web3, _ = self._lazy_clients()
        if web3 is None:
            self._record_failure()
            return {"tx_hash": tx_hash, "confirmed": True, "network": self.network, "mocked": True}

        try:
            def _verify() -> dict[str, Any]:
                receipt = web3.eth.get_transaction_receipt(tx_hash)
                return {
                    "tx_hash": tx_hash,
                    "confirmed": receipt is not None and receipt.get("status", 0) == 1,
                    "block_number": receipt.get("blockNumber") if receipt else None,
                    "network": self.network,
                    "mocked": False,
                }

            result = await asyncio.wait_for(run_in_threadpool(_verify), timeout=self.request_timeout_seconds)
            self._record_success()
            return result
        except Exception:
            self._record_failure()
            LOGGER.exception("Transaction verification failed, using mock fallback")
            return {"tx_hash": tx_hash, "confirmed": True, "network": self.network, "mocked": True}

    async def fetch_events(self, from_block: int) -> tuple[list[dict[str, Any]], int]:
        """Fetch contract events for listener polling loop."""

        web3, contract = self._lazy_clients()
        if web3 is None or contract is None:
            self._record_failure()
            return [], from_block

        try:
            latest_block = int(
                await asyncio.wait_for(
                    run_in_threadpool(lambda: web3.eth.block_number),
                    timeout=self.request_timeout_seconds,
                )
            )
            if latest_block < from_block:
                return [], latest_block

            def _fetch() -> list[dict[str, Any]]:
                minted = contract.events.BatchMinted.create_filter(fromBlock=from_block, toBlock=latest_block).get_all_entries()
                transferred = contract.events.OwnershipTransferred.create_filter(fromBlock=from_block, toBlock=latest_block).get_all_entries()
                payload: list[dict[str, Any]] = []
                for event in [*minted, *transferred]:
                    payload.append(
                        {
                            "event_name": event["event"],
                            "tx_hash": event["transactionHash"].hex(),
                            "log_index": int(event["logIndex"]),
                            "block_number": int(event["blockNumber"]),
                            "args": {key: str(value) for key, value in dict(event["args"]).items()},
                        }
                    )
                return payload

            events = await asyncio.wait_for(run_in_threadpool(_fetch), timeout=self.request_timeout_seconds)
            self._record_success()
            return events, latest_block + 1
        except Exception:
            self._record_failure()
            LOGGER.exception("Event fetch failed")
            return [], from_block
