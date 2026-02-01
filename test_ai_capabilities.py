
import urllib.request
import json
import ssl
import time

API_URL = "https://agentic-honeypot-laju.onrender.com/api/conversation/message"
API_KEY = "honeypot-secret-key-123"

def send_message(message, conversation_id=None):
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    data = {
        "message": message,
        "conversation_id": conversation_id
    }
    json_data = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(API_URL, data=json_data, headers=headers, method='POST')
    ctx = ssl.create_default_context()

    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error: {e}")
        return None

def run_tests():
    print("🚀 Starting AI Capabilities Trace...\n")

    # Test 1: Legitimate Message
    print("1️⃣  Testing Legitimate Message Processing...")
    legit_response = send_message("Hi, just checking in on the project status.")
    if legit_response:
        print(f"   Is Scam: {legit_response['is_scam']} (Expected: False)")
        print(f"   Confidence: {legit_response['confidence_score']}")
        if not legit_response['is_scam']:
            print("   ✅ PASS: Correctly identified as legitimate.")
        else:
            print("   ❌ FAIL: False positive.")
    else:
        print("   ❌ FAIL: API Error.")
    print("-" * 50)

    # Test 2: Scam Detection (Phishing)
    print("2️⃣  Testing Scam Detection (Phishing)...")
    scam_msg = "URGENT! Your account is suspended. Click here to verify: http://bit.ly/fake123"
    scam_response = send_message(scam_msg)
    if scam_response:
        print(f"   Is Scam: {scam_response['is_scam']} (Expected: True)")
        print(f"   Confidence: {scam_response['confidence_score']}")
        print(f"   AI Response: \"{scam_response['ai_response']}\"")
        if scam_response['is_scam']:
            print("   ✅ PASS: Correctly flagged as scam.")
        else:
            print("   ❌ FAIL: False negative.")
    else:
        print("   ❌ FAIL: API Error.")
    print("-" * 50)

    # Test 3: Intelligence Extraction
    print("3️⃣  Testing Intelligence Extraction...")
    intel_msg = "Please send payment to account 1234567890123456 or UPI scammer@paytm immediately!"
    intel_response = send_message(intel_msg)
    if intel_response:
        extracted = intel_response.get('extracted_intelligence', {})
        print(f"   Extracted Data: {json.dumps(extracted, indent=2)}")

        has_bank = 'bank_accounts' in extracted and '1234567890123456' in extracted['bank_accounts']
        has_upi = 'upi_ids' in extracted and 'scammer@paytm' in extracted['upi_ids']

        if has_bank and has_upi:
            print("   ✅ PASS: Successfully extracted Bank Account and UPI ID.")
        else:
            print("   ❌ FAIL: Failed to extract all intelligence.")
    else:
        print("   ❌ FAIL: API Error.")
    print("-" * 50)

    # Test 4: Conversation Context/Persona
    print("4️⃣  Testing Agent Persona Consistency...")
    # Use the conversation ID from Test 2 to continue that thread
    if scam_response:
        conv_id = scam_response['conversation_id']
        follow_up_msg = "Why haven't you clicked the link yet? It is urgent!"
        follow_up_response = send_message(follow_up_msg, conversation_id=conv_id)

        if follow_up_response:
            print(f"   AI Response to Follow-up: \"{follow_up_response['ai_response']}\"")
            print("   (Verify this response matches a cautious/confused victim persona)")
            print("   ✅ PASS: Conversation flow maintained.")
        else:
            print("   ❌ FAIL: API Error on follow-up.")

    print("\n🏁 Use Case Verification Complete.")

if __name__ == "__main__":
    run_tests()
