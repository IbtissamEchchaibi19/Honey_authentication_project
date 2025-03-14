from web3 import Web3
import json

RPC_URL = "http://127.0.0.1:7545"
PRIVATE_KEY = "0xce2f29a37daaa2950c5dfd18b09dc950bd48f9f7f7c3ba019e1fad96a0cf276f"

# Load ABI and contract address from the JSON file
with open('contract_data.json', 'r') as f:
    contract_data = json.load(f)

CONTRACT_ADDRESS = contract_data['contract_address']
ABI = contract_data['abi']

web3 = Web3(Web3.HTTPProvider(RPC_URL))
account = web3.eth.account.from_key(PRIVATE_KEY)
contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)

# Register Honey batch
batch_id = 1
origin = "Atlas Mountains, Morocco"

tx = contract.functions.registerHoney(batch_id, origin).build_transaction({
    'from': account.address,
    'nonce': web3.eth.get_transaction_count(account.address),
    'gas': 300000,
    'gasPrice': web3.to_wei('20', 'gwei')
})

signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
web3.eth.wait_for_transaction_receipt(tx_hash)

print(f"Honey batch {batch_id} registered successfully!")
