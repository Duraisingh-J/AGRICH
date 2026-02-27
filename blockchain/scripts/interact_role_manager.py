from web3 import Web3
import json
import os
from dotenv import load_dotenv

load_dotenv()

RPC_URL = "http://127.0.0.1:8545"
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
DEPLOYER_ADDRESS = Web3.to_checksum_address(os.getenv("DEPLOYER_ADDRESS"))

w3 = Web3(Web3.HTTPProvider(RPC_URL))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEPLOYED_FILE = os.path.join(BASE_DIR, "DeployedAddresses.json")

with open(DEPLOYED_FILE) as f:
    deployed = json.load(f)

ROLE_MANAGER_ADDRESS = Web3.to_checksum_address(deployed["RoleManager"])

artifact_path = os.path.join(
    os.path.dirname(BASE_DIR), 
    "artifacts",
    "contracts",
    "RoleManager.sol",
    "RoleManager.json"
)

with open(artifact_path) as f:
    artifact = json.load(f)

contract = w3.eth.contract(
    address=ROLE_MANAGER_ADDRESS,
    abi=artifact["abi"]
)

def send_tx(tx):
    signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt

# Create new farmer wallet
farmer_account = w3.eth.account.create()
farmer_address = farmer_account.address

print("New Farmer:", farmer_address)

nonce = w3.eth.get_transaction_count(DEPLOYER_ADDRESS, "pending")

tx = contract.functions.assignRole(
    farmer_address,
    1  # FARMER enum
).build_transaction({
    "from": DEPLOYER_ADDRESS,
    "nonce": nonce,
    "gas": 500000,
    "maxFeePerGas": w3.to_wei("2", "gwei"),
    "maxPriorityFeePerGas": w3.to_wei("1", "gwei"),
    "chainId": w3.eth.chain_id,
    "type": 2
})

receipt = send_tx(tx)
print("Role assigned. Tx:", receipt.transactionHash.hex())

role = contract.functions.getRole(farmer_address).call()
print("Role stored:", role)