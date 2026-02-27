import os
from dotenv import load_dotenv

# Load the environment variables strictly server-side
load_dotenv()

class Config:
    WEB3_PROVIDER_URI = os.getenv("WEB3_PROVIDER_URI", "http://127.0.0.1:8545")
    IPFS_HTTP_API = os.getenv("IPFS_HTTP_API", "http://127.0.0.1:5001")
    
    SYSTEM_SALT = os.getenv("SYSTEM_SALT")
    GOVT_PRIVATE_KEY = os.getenv("GOVT_PRIVATE_KEY")
    
    # Path to where ABI and Addresses are stored (shared with hardhat/scripts)
    BLOCKCHAIN_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "blockchain")
    DEPLOYED_ADDRESSES_PATH = os.path.join(BLOCKCHAIN_ROOT, "scripts", "DeployedAddresses.json")
    
    ROLE_MANAGER_ABI_PATH = os.path.join(BLOCKCHAIN_ROOT, "artifacts", "contracts", "RoleManager.sol", "RoleManager.json")
    CERT_REGISTRY_ABI_PATH = os.path.join(BLOCKCHAIN_ROOT, "artifacts", "contracts", "CertificateRegistry.sol", "CertificateRegistry.json")
    
    @staticmethod
    def validate():
        if not Config.SYSTEM_SALT:
            raise ValueError("CRITICAL: SYSTEM_SALT is not configured in .env")
        if not Config.GOVT_PRIVATE_KEY or Config.GOVT_PRIVATE_KEY == "your_private_key_here":
            raise ValueError("CRITICAL: GOVT_PRIVATE_KEY is not configured in .env")
