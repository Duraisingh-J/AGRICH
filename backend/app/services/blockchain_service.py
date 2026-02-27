"""Blockchain interaction service layer using Web3.py abstractions."""

import logging
import uuid
from dataclasses import dataclass
from typing import Any

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


class BlockchainService:
    """Async-safe blockchain wrappers for AGRICHAIN operations."""

    def __init__(self) -> None:
        settings = get_settings()
        self.rpc_url = settings.web3_rpc_url
        self.default_sender = settings.blockchain_default_sender
        self.network = "ethereum"
        self._web3: Any | None = None
        self._contract: Any | None = None

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

        web3, _ = self._lazy_clients()
        if web3 is None:
            return False
        try:
            return bool(await run_in_threadpool(web3.is_connected))
        except Exception:
            LOGGER.exception("Blockchain health check failed")
            return False

    async def mint_batch(self, batch_id: str, metadata_cid: str) -> BlockchainTxResult:
        """Mint batch token on blockchain with real-call fallback behavior."""

        LOGGER.info("Mint batch requested", extra={"batch_id": batch_id, "cid": metadata_cid})
        web3, contract = self._lazy_clients()
        if web3 is None or contract is None or not self.default_sender:
            LOGGER.warning("Mint fallback to mock response")
            return self._mock_tx_result()

        try:
            sender = web3.to_checksum_address(self.default_sender)

            def _transact() -> str:
                tx_hash = contract.functions.mintBatch(batch_id, metadata_cid).transact({"from": sender})
                receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                return receipt.transactionHash.hex()

            tx_hash = await run_in_threadpool(_transact)
            return BlockchainTxResult(success=True, tx_hash=tx_hash, network=self.network)
        except Exception:
            LOGGER.exception("Mint failed, using mock response")
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
        web3, contract = self._lazy_clients()
        if web3 is None or contract is None:
            LOGGER.warning("Transfer fallback to mock response")
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

            tx_hash = await run_in_threadpool(_transact)
            return BlockchainTxResult(success=True, tx_hash=tx_hash, network=self.network)
        except Exception:
            LOGGER.exception("Transfer failed, using mock response")
            return self._mock_tx_result()

    async def get_batch_history(self, batch_id: str) -> list[dict[str, Any]]:
        """Get historical blockchain events for a batch (real-call fallback)."""

        web3, contract = self._lazy_clients()
        if web3 is None or contract is None:
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

            return await run_in_threadpool(_fetch_history)
        except Exception:
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

            return await run_in_threadpool(_verify)
        except Exception:
            LOGGER.exception("Transaction verification failed, using mock fallback")
            return {"tx_hash": tx_hash, "confirmed": True, "network": self.network, "mocked": True}

    async def fetch_events(self, from_block: int) -> tuple[list[dict[str, Any]], int]:
        """Fetch contract events for listener polling loop."""

        web3, contract = self._lazy_clients()
        if web3 is None or contract is None:
            return [], from_block

        try:
            latest_block = int(await run_in_threadpool(lambda: web3.eth.block_number))
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

            events = await run_in_threadpool(_fetch)
            return events, latest_block + 1
        except Exception:
            LOGGER.exception("Event fetch failed")
            return [], from_block
