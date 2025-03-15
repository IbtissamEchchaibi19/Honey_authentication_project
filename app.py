from flask import Flask, render_template, request, jsonify
from web3 import Web3
import json
import os
import google.generativeai as genai
from dotenv import load_dotenv
from llm import verify_honey_authenticity, process_user_query, pollen_database  # Import functions from llm.py

# Load environment variables
load_dotenv()

# Configure Web3 connection
RPC_URL = os.getenv("RPC_URL", "http://127.0.0.1:7545")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

# Load blockchain contract data
with open('contract_data.json', 'r') as f:
    contract_data = json.load(f)

CONTRACT_ADDRESS = contract_data['contract_address']
ABI = contract_data['abi']

# Initialize Web3
web3 = Web3(Web3.HTTPProvider(RPC_URL))
account = web3.eth.account.from_key(PRIVATE_KEY)
contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)

# Initialize Gemini AI
if "GEMINI_API_KEY" in os.environ:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-1.5-flash")
else:
    model = None

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register_honey():
    if request.method == 'POST':
        data = request.json
        batch_id = int(data['batch_id'])
        origin = data['origin']
        
        tx = contract.functions.registerHoney(batch_id, origin).build_transaction({
            'from': account.address,
            'nonce': web3.eth.get_transaction_count(account.address),
            'gas': 300000,
            'gasPrice': web3.to_wei('20', 'gwei')
        })
        signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        web3.eth.wait_for_transaction_receipt(tx_hash)
        
        return jsonify({"message": "Batch registered successfully!", "batch_id": batch_id})
    return render_template('register.html')

@app.route('/get_token', methods=['GET'])
def get_token():
    batch_id = int(request.args.get('batch_id'))
    token = contract.functions.getVerificationToken(batch_id).call()
    return jsonify({"batch_id": batch_id, "verification_token": token})

@app.route('/verify', methods=['GET', 'POST'])
def verify_honey():
    if request.method == 'POST':
        data = request.json
        batch_id = int(data['batch_id'])
        user_token = data.get('token', None)
        
        batch = contract.functions.honeyBatches(batch_id).call()
        if not batch[1]:
            return jsonify({"verified": False, "reason": "Batch not found"})
        
        if user_token and user_token != batch[2]:
            return jsonify({"verified": False, "reason": "Token mismatch"})
        
        return jsonify({"verified": True, "batch_info": {
            "origin": batch[0],
            "timestamp": batch[1],
            "verification_token": batch[2]
        }})
    return render_template('verify.html')

pollen_database = {
    "Atlas Mountains, Morocco": {
        "common_pollens": ["Thyme", "Rosemary", "Lavender", "Eucalyptus"],
        "seasonal_variations": "Higher thyme pollen concentration in spring, lavender in summer",
        "unique_markers": "High concentration of native Atlas cedar pollen"
    },
    "Yucatan Peninsula, Mexico": {
        "common_pollens": ["Tajonal", "Dzidzilche", "Citrus", "Mangrove"],
        "seasonal_variations": "Tajonal blooms October to December, Dzidzilche January to May",
        "unique_markers": "Presence of endemic Melipona beecheii bee pollen"
    }
}

def get_batch_info(batch_id):
    """Retrieve batch information from blockchain"""
    try:
        batch = contract.functions.honeyBatches(batch_id).call()
        return {
            "origin": batch[0],
            "timestamp": batch[1],
            "verification_token": batch[2]
        }
    except Exception as e:
        print(f"Error retrieving batch info: {e}")
        return None

def get_pollen_data(origin):
    """Get pollen data for a specific origin"""
    return pollen_database.get(origin, {
        "common_pollens": ["Unknown"],
        "seasonal_variations": "Data not available for this region",
        "unique_markers": "No unique markers identified"
    })

def verify_honey_authenticity(batch_id, user_token=None):
    """Verify honey authenticity based on blockchain data"""
    batch_info = get_batch_info(batch_id)
    
    if not batch_info:
        return {"verified": False, "reason": "Batch not found in registry"}
    
    # If user provided a token, verify it matches
    if user_token and user_token != batch_info["verification_token"]:
        return {"verified": False, "reason": "Verification token mismatch"}
    
    # Get associated pollen data
    pollen_data = get_pollen_data(batch_info["origin"])
    
    return {
        "verified": True,
        "batch_info": batch_info,
        "pollen_data": pollen_data
    }

def process_user_query(query, batch_id=None):
    """Process user query with Gemini AI"""
    
    # Prepare context for the AI
    context = "You are HoneyGuard AI, a specialist in honey authenticity and traceability. "
    
    if batch_id:
        # Get blockchain verification data
        verification_result = verify_honey_authenticity(batch_id)
        if verification_result["verified"]:
            context += f"""
            Batch Information:
            - Origin: {verification_result['batch_info']['origin']}
            - Timestamp: {verification_result['batch_info']['timestamp']}
            - Verification Token: {verification_result['batch_info']['verification_token']}
            
            Pollen Profile:
            - Common pollens: {', '.join(verification_result['pollen_data']['common_pollens'])}
            - Seasonal variations: {verification_result['pollen_data']['seasonal_variations']}
            - Unique markers: {verification_result['pollen_data']['unique_markers']}
            """
        else:
            context += f"Batch {batch_id} verification failed: {verification_result['reason']}."
    
    # Add general honey knowledge
    context += """
    Please provide helpful information about honey authenticity, traceability, or explain the verification process.
    If asked about a specific honey batch, provide details about its origin, pollen profile, and authenticity.
    Be conversational but informative, and focus on building consumer trust through transparency.
    """
    
    # Generate response with Gemini
    prompt = f"{context}\n\nUser query: {query}"
    response = model.generate_content(prompt)
    
    return response.text
 
@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    """Handle both serving the chatbot interface and processing user queries"""
    if request.method == 'GET':
        # Serve the chatbot HTML page when accessed via GET
        return render_template('chatbot.html')
    
    elif request.method == 'POST':
        user_input = request.json.get("query", "")
        
        if not user_input:
            return jsonify({"error": "No query provided"}), 400

        batch_id = None
        if "batch" in user_input.lower() and any(char.isdigit() for char in user_input):
            # Extract potential batch number
            import re
            matches = re.findall(r'\d+', user_input)
            if matches:
                batch_id = int(matches[0])
        
        response_text = process_user_query(user_input, batch_id)
        
        return jsonify({"response": response_text})


if __name__ == '__main__':
    app.run(debug=True)
