from web3 import Web3
from utils.config import Config

class HashService:
    @staticmethod
    def get_aadhaar_hash(aadhaar_number: str) -> str:
        """
        Compute keccak256 hash of Aadhaar + system salt
        """
        salt_bytes = Web3.to_bytes(hexstr=Config.SYSTEM_SALT)
        
        # We hash the aadhaar string and the salt bytes together
        return Web3.solidity_keccak(['string', 'bytes32'], [aadhaar_number, salt_bytes]).hex()

    @staticmethod
    def get_document_hash(file_bytes: bytes) -> str:
        """
        Compute keccak256 hash of file bytes
        """
        return Web3.keccak(file_bytes).hex()
