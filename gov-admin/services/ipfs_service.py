import requests
from utils.config import Config

class IPFSService:
    @staticmethod
    def upload_file(file_bytes: bytes) -> str:
        """Uploads a file to local IPFS node and returns the CID."""
        url = f"{Config.IPFS_HTTP_API}/api/v0/add"
        
        files = {
            'file': file_bytes
        }
        
        response = requests.post(url, files=files)
        response.raise_for_status()
        
        data = response.json()
        return data.get("Hash")
