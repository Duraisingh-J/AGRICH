import json
import logging
from web3 import Web3
from utils.config import Config

logger = logging.getLogger(__name__)

class BlockchainService:
    def __init__(self):
        # Establish Web3 connection
        self.w3 = Web3(Web3.HTTPProvider(Config.WEB3_PROVIDER_URI))
        if not self.w3.is_connected():
            raise ConnectionError(f"Failed to connect to the blockchain node at {Config.WEB3_PROVIDER_URI}")
            
        # Load Contract Addresses
        try:
            with open(Config.DEPLOYED_ADDRESSES_PATH, 'r') as f:
                addresses = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Deployed addresses not found at {Config.DEPLOYED_ADDRESSES_PATH}")
            
        role_manager_addr = addresses.get("RoleManager")
        cert_registry_addr = addresses.get("CertificateRegistry")
        chain_id = addresses.get("ChainId", 1337)
        self.chain_id = chain_id
        
        if not role_manager_addr or not cert_registry_addr:
            raise ValueError("Contract addresses not found in DeployedAddresses.json")
            
        # Load ABIs
        try:
            with open(Config.ROLE_MANAGER_ABI_PATH, 'r') as f:
                role_manager_artifact = json.load(f)
            with open(Config.CERT_REGISTRY_ABI_PATH, 'r') as f:
                cert_registry_artifact = json.load(f)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Contract ABI file missing: {e}")
            
        role_abi = role_manager_artifact.get("abi", [])
        cert_abi = cert_registry_artifact.get("abi", [])
        
        # Initialize Contract objects
        self.role_manager = self.w3.eth.contract(
            address=Web3.to_checksum_address(role_manager_addr), 
            abi=role_abi
        )
        self.cert_registry = self.w3.eth.contract(
            address=Web3.to_checksum_address(cert_registry_addr), 
            abi=cert_abi
        )
        
        # Load wallet
        if Config.GOVT_PRIVATE_KEY and Config.GOVT_PRIVATE_KEY != "your_private_key_here":
            self.account = self.w3.eth.account.from_key(Config.GOVT_PRIVATE_KEY)
        else:
            self.account = None

    def verify_admin_role(self) -> bool:
        """
        Verify that the configured account actually holds the GOVERNMENT role.
        """
        if not self.account:
            return False
            
        try:
            is_govt = self.role_manager.functions.isGovernment(self.account.address).call()
            return is_govt
        except Exception as e:
            logger.error(f"Role verification failed for address {self.account.address}: {e}")
            return False
            
    def get_account_address(self):
        return self.account.address if self.account else None

    def _build_and_send_tx(self, func_call):
        """
        Internal wrapper to safely build, sign, and broadcast transactions.
        """
        if not self.account:
            raise ValueError("Private key not configured. Cannot perform state-changing transactions.")
            
        nonce = self.w3.eth.get_transaction_count(self.account.address, "pending")
        
        try:
            tx = func_call.build_transaction({
                'chainId': self.chain_id,
                'gas': 2000000,
                'maxFeePerGas': self.w3.to_wei('2', 'gwei'),
                'maxPriorityFeePerGas': self.w3.to_wei('1', 'gwei'),
                'type': 2,
                'nonce': nonce,
            })
        except Exception as e:
            logger.warning(f"Gas estimation failed: {e}. Falling back to manual gas limits.")
            tx = func_call.build_transaction({
                'chainId': self.chain_id,
                'gas': 3000000,
                'maxFeePerGas': self.w3.to_wei('2', 'gwei'),
                'maxPriorityFeePerGas': self.w3.to_wei('1', 'gwei'),
                'type': 2,
                'nonce': nonce,
            })
            
        signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.account.key)
        
        # In web3 v6 it is signed_tx.rawTransaction 
        # and send_raw_transaction 
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status != 1:
            raise Exception(f"Transaction failed on the blockchain. TX Hash: {tx_hash.hex()}")
            
        return tx_hash.hex()

    def approve_certificate(self, aadhaar_hash_hex: str, document_hash_hex: str, ipfs_cid: str) -> str:
        """
        Verify role and issue approveCertificate transaction.
        """
        if not self.verify_admin_role():
            raise PermissionError("The configured account does not have Government role.")
            
        aadhaar_hash_bytes = Web3.to_bytes(hexstr=aadhaar_hash_hex)
        document_hash_bytes = Web3.to_bytes(hexstr=document_hash_hex)
        
        func = self.cert_registry.functions.approveCertificate(aadhaar_hash_bytes, document_hash_bytes, ipfs_cid)
        return self._build_and_send_tx(func)

    def revoke_certificate(self, aadhaar_hash_hex: str) -> str:
        """
        Verify role and issue revokeCertificate transaction.
        """
        if not self.verify_admin_role():
            raise PermissionError("The configured account does not have Government role.")
            
        aadhaar_hash_bytes = Web3.to_bytes(hexstr=aadhaar_hash_hex)
        
        func = self.cert_registry.functions.revokeCertificate(aadhaar_hash_bytes)
        return self._build_and_send_tx(func)

    def is_approved(self, aadhaar_hash_hex: str) -> bool:
        aadhaar_hash_bytes = Web3.to_bytes(hexstr=aadhaar_hash_hex)
        return self.cert_registry.functions.isApproved(aadhaar_hash_bytes).call()

    def get_document_hash(self, aadhaar_hash_hex: str) -> str:
        aadhaar_hash_bytes = Web3.to_bytes(hexstr=aadhaar_hash_hex)
        result = self.cert_registry.functions.getDocumentHash(aadhaar_hash_bytes).call()
        return Web3.to_hex(result)

    def get_ipfs_cid(self, aadhaar_hash_hex: str) -> str:
        """Fetch the IPFS CID linked to the given Aadhaar hash"""
        aadhaar_hash_bytes = Web3.to_bytes(hexstr=aadhaar_hash_hex)
        return self.cert_registry.functions.getIpfsCID(aadhaar_hash_bytes).call()

    def get_bound_wallet(self, aadhaar_hash_hex: str) -> str:
        aadhaar_hash_bytes = Web3.to_bytes(hexstr=aadhaar_hash_hex)
        return self.cert_registry.functions.getBoundWallet(aadhaar_hash_bytes).call()
        
    def get_approval_events(self, from_block=0):
        try:
            events = self.cert_registry.events.CertificateApproved.get_logs(fromBlock=from_block)
            return events
        except Exception as e:
            logger.error(f"Failed to fetch events: {e}")
            return []
