from web3 import Web3
import json

RPC_URL = "http://127.0.0.1:7545"
with open('contract_data.json', 'r') as f:
    contract_data = json.load(f)

CONTRACT_ADDRESS = contract_data['contract_address']
ABI = contract_data['abi']

web3 = Web3(Web3.HTTPProvider(RPC_URL))
contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)

batch_id = 1
token = contract.functions.getVerificationToken(batch_id).call()
print(f"Verification Token for Batch {batch_id}: {token}")
