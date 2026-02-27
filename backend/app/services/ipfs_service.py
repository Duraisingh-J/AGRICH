"""IPFS service wrappers for metadata and file uploads."""

import hashlib
import json

from app.config import get_settings


class IPFSService:
    """Service for IPFS upload operations."""

    def __init__(self) -> None:
        self.api_url = get_settings().ipfs_api_url

    async def upload_json(self, data: dict) -> str:
        """Upload JSON payload to IPFS and return CID (mocked)."""

        digest = hashlib.sha256(json.dumps(data, sort_keys=True).encode("utf-8")).hexdigest()
        return f"bafy{digest[:40]}"

    async def upload_file(self, file_bytes: bytes) -> str:
        """Upload file bytes to IPFS and return CID (mocked)."""

        digest = hashlib.sha256(file_bytes).hexdigest()
        return f"bafy{digest[:40]}"
