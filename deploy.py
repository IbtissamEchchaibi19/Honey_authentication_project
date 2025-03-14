from web3 import Web3
from solcx import compile_source, install_solc, set_solc_version
import json

# Install and set the Solidity compiler version
install_solc('0.8.0')
set_solc_version('0.8.0')

# Connect to Ganache
RPC_URL = "http://127.0.0.1:7545"
PRIVATE_KEY = "0xce2f29a37daaa2950c5dfd18b09dc950bd48f9f7f7c3ba019e1fad96a0cf276f"
web3 = Web3(Web3.HTTPProvider(RPC_URL))
account = web3.eth.account.from_key(PRIVATE_KEY)

# Load and compile Solidity contract
contract_source = open("HoneyRegistry.sol").read()
compiled_sol = compile_source(contract_source)
contract_interface = compiled_sol['<stdin>:HoneyRegistry']

# Deploy contract
HoneyRegistry = web3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])
tx = HoneyRegistry.constructor().build_transaction({
    'from': account.address,
    'nonce': web3.eth.get_transaction_count(account.address),
    'gas': 3000000,
    'gasPrice': web3.to_wei('20', 'gwei')
})
signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

# Save ABI and contract address
contract_data = {
    'contract_address': tx_receipt.contractAddress,
    'abi': contract_interface['abi']
}

with open('contract_data.json', 'w') as f:
    json.dump(contract_data, f)

print(f"Contract deployed at: {tx_receipt.contractAddress}")
