import os
import json
import google.generativeai as genai
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Configure Web3 connection
RPC_URL = os.getenv("RPC_URL", "http://127.0.0.1:7545")

# Load blockchain contract data
with open('contract_data.json', 'r') as f:
    contract_data = json.load(f)

CONTRACT_ADDRESS = contract_data['contract_address']
ABI = contract_data['abi']

# Initialize Web3
web3 = Web3(Web3.HTTPProvider(RPC_URL))
contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)

# Sample pollen database (in a real system, this would be more comprehensive)
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



safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
)

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

def chatbot_interface():
    """Simple command-line interface for the chatbot"""
    print("🐝 Welcome to HoneyGuard AI - Your honey authenticity assistant 🐝")
    print("Type 'exit' to quit")
    
    while True:
        query = input("\nYou: ")
        if query.lower() == 'exit':
            break
        
        # Check if query contains a batch number
        batch_id = None
        if "batch" in query.lower() and any(char.isdigit() for char in query):
            # Extract potential batch number
            import re
            matches = re.findall(r'\d+', query)
            if matches:
                batch_id = int(matches[0])
        
        response = process_user_query(query, batch_id)
        print(f"\nHoneyGuard AI: {response}")

if __name__ == "__main__":
    chatbot_interface()