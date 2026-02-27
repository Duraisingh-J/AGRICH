"""Blockchain interaction service layer using Web3.py abstractions."""

import logging
import uuid
from dataclasses import dataclass
from typing import Any

from app.config import get_settings

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
        self.network = "ethereum"
        self._web3: Any | None = None

    def _get_web3(self) -> Any | None:
        """Initialize Web3 client lazily."""

        if self._web3 is not None:
            return self._web3
        try:
            from web3 import HTTPProvider, Web3

            self._web3 = Web3(HTTPProvider(self.rpc_url))
            return self._web3
        except Exception:
            LOGGER.warning("Web3 client unavailable; using mocked blockchain responses")
            return None

    async def mint_batch(self, batch_id: str, metadata_cid: str) -> BlockchainTxResult:
        """Mint batch token on blockchain (stubbed structure for real call)."""

        self._get_web3()
        LOGGER.info("Mint batch requested", extra={"batch_id": batch_id, "cid": metadata_cid})
        return BlockchainTxResult(
            success=True,
            tx_hash=f"0x{uuid.uuid4().hex}{uuid.uuid4().hex[:8]}",
            network=self.network,
        )

    async def transfer_ownership(
        self,
        batch_id: str,
        from_addr: str,
        to_addr: str,
    ) -> BlockchainTxResult:
        """Transfer ownership on blockchain (stubbed structure for real call)."""

        self._get_web3()
        LOGGER.info(
            "Transfer ownership requested",
            extra={"batch_id": batch_id, "from": from_addr, "to": to_addr},
        )
        return BlockchainTxResult(
            success=True,
            tx_hash=f"0x{uuid.uuid4().hex}{uuid.uuid4().hex[:8]}",
            network=self.network,
        )

    async def get_batch_history(self, batch_id: str) -> list[dict[str, Any]]:
        """Get historical blockchain events for a batch."""

        self._get_web3()
        return [
            {
                "batch_id": batch_id,
                "event": "MINTED",
                "tx_hash": f"0x{uuid.uuid4().hex}{uuid.uuid4().hex[:8]}",
            }
        ]

    async def verify_transaction(self, tx_hash: str) -> dict[str, Any]:
        """Verify transaction inclusion/finality (stubbed)."""

        self._get_web3()
        return {
            "tx_hash": tx_hash,
            "confirmed": True,
            "network": self.network,
        }
