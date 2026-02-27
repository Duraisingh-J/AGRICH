"""Utilities for blockchain Web3 and contract configuration."""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import get_settings

LOGGER = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_web3() -> Any | None:
    """Return cached Web3 client instance initialized from environment."""

    settings = get_settings()
    try:
        from web3 import HTTPProvider, Web3

        web3 = Web3(HTTPProvider(settings.web3_rpc_url))
        return web3
    except Exception:
        LOGGER.warning("Unable to initialize Web3 client")
        return None


@lru_cache(maxsize=1)
def load_contract_abi() -> list[dict[str, Any]] | None:
    """Load contract ABI JSON from configured path."""

    settings = get_settings()
    if not settings.batch_contract_abi_path:
        LOGGER.info("BATCH_CONTRACT_ABI_PATH not configured")
        return None

    abi_path = Path(settings.batch_contract_abi_path)
    if not abi_path.exists():
        LOGGER.warning("Contract ABI path not found", extra={"abi_path": str(abi_path)})
        return None

    try:
        payload = json.loads(abi_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and "abi" in payload:
            abi = payload["abi"]
        else:
            abi = payload
        if not isinstance(abi, list):
            LOGGER.warning("Contract ABI payload is not a list")
            return None
        return abi
    except Exception:
        LOGGER.exception("Failed to load contract ABI")
        return None


def is_contract_address_valid(address: str | None) -> bool:
    """Validate EVM contract address format."""

    if not address:
        return False

    web3 = get_web3()
    if web3 is None:
        return False

    try:
        return bool(web3.is_address(address))
    except Exception:
        return False


@lru_cache(maxsize=1)
def get_contract() -> Any | None:
    """Return configured contract instance if available and valid."""

    settings = get_settings()
    web3 = get_web3()
    abi = load_contract_abi()

    if web3 is None or abi is None:
        return None
    if not is_contract_address_valid(settings.batch_contract_address):
        LOGGER.info("BATCH_CONTRACT_ADDRESS missing/invalid")
        return None

    try:
        checksum_address = web3.to_checksum_address(str(settings.batch_contract_address))
        return web3.eth.contract(address=checksum_address, abi=abi)
    except Exception:
        LOGGER.exception("Failed to initialize contract instance")
        return None
