from web3 import Web3
acct = Web3().eth.account.create()
print("Address:", acct.address)
print("Private Key:", acct.key.hex())