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
ARTIFACTS_DIR = os.path.join(BASE_DIR, "..", "artifacts", "contracts")
OUTPUT_FILE = os.path.join(BASE_DIR, "DeployedAddresses.json")


def load_contract_artifact(contract_name):
    path = os.path.join(
        ARTIFACTS_DIR,
        f"{contract_name}.sol",
        f"{contract_name}.json"
    )
    with open(path) as f:
        return json.load(f)


def deploy_contract(contract_name, constructor_args=[]):
    artifact = load_contract_artifact(contract_name)

    contract = w3.eth.contract(
        abi=artifact["abi"],
        bytecode=artifact["bytecode"]
    )

    chain_id = w3.eth.chain_id
    nonce = w3.eth.get_transaction_count(DEPLOYER_ADDRESS, "pending")

    tx = contract.constructor(*constructor_args).build_transaction({
        "from": DEPLOYER_ADDRESS,
        "nonce": nonce,
        "gas": 5_000_000,
        "maxFeePerGas": w3.to_wei("2", "gwei"),
        "maxPriorityFeePerGas": w3.to_wei("1", "gwei"),
        "chainId": chain_id,
        "type": 2  # EIP-1559
    })

    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    print(f"{contract_name} deployed at:", receipt.contractAddress)
    return receipt.contractAddress

if __name__ == "__main__":

    print("Deploying RoleManager...")
    role_manager_address = deploy_contract(
        "RoleManager",
        [DEPLOYER_ADDRESS]
    )

    print("Deploying CertificateRegistry...")
    certificate_registry_address = deploy_contract(
        "CertificateRegistry",
        [role_manager_address]
    )

    deployed_data = {
        "RoleManager": role_manager_address,
        "CertificateRegistry": certificate_registry_address,
        "ChainId": w3.eth.chain_id
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(deployed_data, f, indent=4)

    print("\n============================")
    print("Saved to:", OUTPUT_FILE)
    print("============================")