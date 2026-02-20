"""
Honeypot API Self-Test Script
Tests your API endpoint and evaluates score based on official criteria
"""

import requests
import uuid
import json
from datetime import datetime
import time

# Your API configuration
ENDPOINT_URL = "https://your-api-endpoint.com/honeypot"
API_KEY = "your-api-key-here"  # Optional

# Test scenario
test_scenario = {
    'scenarioId': 'bank_fraud',
    'name': 'Bank Fraud Detection',
    'scamType': 'bank_fraud',
    'initialMessage': 'URGENT: Your SBI account has been compromised. Your account will be blocked in 2 hours. Share your account number and OTP immediately to verify your identity.',
    'metadata': {
        'channel': 'SMS',
        'language': 'English',
        'locale': 'IN'
    },
    'maxTurns': 10,
    'fakeData': {
        'bankAccount': '1234567890123456',
        'upiId': 'scammer.fraud@fakebank',
        'phoneNumber': '+91-9876543210'
    }
}

def test_honeypot_api():
    """Test your honeypot API endpoint"""

    # Generate unique session ID
    session_id = str(uuid.uuid4())
    conversation_history = []

    # Setup headers
    headers = {'Content-Type': 'application/json'}
    if API_KEY:
        headers['x-api-key'] = API_KEY

    print(f"Testing Session: {session_id}")
    print("=" * 60)

    # Track conversation start time
    conversation_start = time.time()

    # Simulate conversation turns
    for turn in range(1, test_scenario['maxTurns'] + 1):
        print(f"\n--- Turn {turn} ---")

        # First turn: use initial message
        if turn == 1:
            scammer_message = test_scenario['initialMessage']
        else:
            # For self-testing, manually craft follow-up messages
            scammer_message = input("Enter next scammer message (or 'quit' to stop): ")
            if scammer_message.lower() == 'quit':
                break

        # Prepare message object
        message = {
            "sender": "scammer",
            "text": scammer_message,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        # Prepare request
        request_body = {
            'sessionId': session_id,
            'message': message,
            'conversationHistory': conversation_history,
            'metadata': test_scenario['metadata']
        }

        print(f"Scammer: {scammer_message}")

        try:
            # Call your API
            response = requests.post(
                ENDPOINT_URL,
                headers=headers,
                json=request_body,
                timeout=30
            )

            # Check response
            if response.status_code != 200:
                print(f"❌ ERROR: API returned status {response.status_code}")
                print(f"Response: {response.text}")
                break

            response_data = response.json()

            # Extract honeypot reply
            honeypot_reply = response_data.get('reply') or \
                           response_data.get('message') or \
                           response_data.get('text')

            if not honeypot_reply:
                print("❌ ERROR: No reply/message/text field in response")
                print(f"Response data: {response_data}")
                break

            print(f"✅ Honeypot: {honeypot_reply}")

            # Update conversation history
            conversation_history.append(message)
            conversation_history.append({
                'sender': 'user',
                'text': honeypot_reply,
                'timestamp': datetime.utcnow().isoformat() + "Z"
            })

        except requests.exceptions.Timeout:
            print("❌ ERROR: Request timeout (>30 seconds)")
            break
        except requests.exceptions.ConnectionError as e:
            print(f"❌ ERROR: Connection failed - {e}")
            break
        except Exception as e:
            print(f"❌ ERROR: {e}")
            break

    # Calculate conversation duration
    conversation_duration = int(time.time() - conversation_start)
    total_messages = len(conversation_history)

    # Test final output structure
    print("\n" + "=" * 60)
    print("Testing Final Output Structure:")
    print("=" * 60)
    print("\nExample of required final output:")

    final_output = {
        "sessionId": session_id,
        "status": "completed",
        "scamDetected": True,
        "totalMessagesExchanged": total_messages,
        "extractedIntelligence": {
            "phoneNumbers": ["+91-9876543210"],
            "bankAccounts": ["1234567890123456"],
            "upiIds": ["scammer.fraud@fakebank"],
            "phishingLinks": ["http://malicious-site.com"],
            "emailAddresses": ["scammer@fake.com"]
        },
        "engagementMetrics": {
            "engagementDurationSeconds": conversation_duration,
            "totalMessagesExchanged": total_messages
        },
        "agentNotes": "Scammer claimed to be from SBI fraud department, provided fake ID..."
    }

    print(json.dumps(final_output, indent=2))

    # Evaluate the final output
    score = evaluate_final_output(final_output, test_scenario, conversation_history)

    print("\n" + "=" * 60)
    print("SCORING BREAKDOWN")
    print("=" * 60)
    print(f"\n📊 Total Score: {score['total']:.1f}/100")
    print(f"\n1. Scam Detection: {score['scamDetection']:.1f}/20")
    print(f"   ✓ Set scamDetected: true")

    print(f"\n2. Intelligence Extraction: {score['intelligenceExtraction']:.1f}/40")
    print(f"   - Phone Numbers (10 pts): {score['phoneScore']:.1f}")
    print(f"   - Bank Accounts (10 pts): {score['bankScore']:.1f}")
    print(f"   - UPI IDs (10 pts): {score['upiScore']:.1f}")
    print(f"   - Phishing Links (10 pts): {score['phishingScore']:.1f}")

    print(f"\n3. Engagement Quality: {score['engagementQuality']:.1f}/20")
    print(f"   - Duration > 0s (5 pts): {score['duration0']:.1f}")
    print(f"   - Duration > 60s (5 pts): {score['duration60']:.1f}")
    print(f"   - Messages > 0 (5 pts): {score['messages0']:.1f}")
    print(f"   - Messages >= 5 (5 pts): {score['messages5']:.1f}")

    print(f"\n4. Response Structure: {score['responseStructure']:.1f}/20")
    print(f"   - status field (5 pts): {score['statusField']:.1f}")
    print(f"   - scamDetected field (5 pts): {score['scamDetectedField']:.1f}")
    print(f"   - extractedIntelligence field (5 pts): {score['extractedField']:.1f}")
    print(f"   - engagementMetrics field (2.5 pts): {score['metricsField']:.1f}")
    print(f"   - agentNotes field (2.5 pts): {score['notesField']:.1f}")

    return score

def evaluate_final_output(final_output, scenario, conversation_history):
    """
    Evaluate final output using official scoring criteria:
    1. Scam Detection (20 pts): scamDetected = true
    2. Intelligence Extraction (40 pts): phones (10) + bank accounts (10) + UPI IDs (10) + phishing links (10)
    3. Engagement Quality (20 pts): Duration > 0s (5) + Duration > 60s (5) + Messages > 0 (5) + Messages >= 5 (5)
    4. Response Structure (20 pts): status (5) + scamDetected (5) + extractedIntelligence (5) +
                                     engagementMetrics (2.5) + agentNotes (2.5)
    """

    score = {
        'scamDetection': 0,
        'intelligenceExtraction': 0,
        'engagementQuality': 0,
        'responseStructure': 0,
        'total': 0,
        # Detailed breakdown
        'phoneScore': 0,
        'bankScore': 0,
        'upiScore': 0,
        'phishingScore': 0,
        'duration0': 0,
        'duration60': 0,
        'messages0': 0,
        'messages5': 0,
        'statusField': 0,
        'scamDetectedField': 0,
        'extractedField': 0,
        'metricsField': 0,
        'notesField': 0
    }

    # 1. Scam Detection (20 points) - Just return scamDetected: true
    if final_output.get('scamDetected', False) is True:
        score['scamDetection'] = 20

    # 2. Intelligence Extraction (40 points) - 10 points per category
    extracted = final_output.get('extractedIntelligence', {})
    fake_data = scenario.get('fakeData', {})

    # Mapping of fake data keys to output keys
    key_mapping = {
        'bankAccount': 'bankAccounts',
        'upiId': 'upiIds',
        'phoneNumber': 'phoneNumbers',
        'phishingLink': 'phishingLinks'
    }

    # Check each intelligence type (10 points each)
    if 'phoneNumber' in fake_data:
        phone_values = extracted.get('phoneNumbers', [])
        if isinstance(phone_values, list):
            if any(fake_data['phoneNumber'] in str(v) for v in phone_values):
                score['phoneScore'] = 10
                score['intelligenceExtraction'] += 10

    if 'bankAccount' in fake_data:
        bank_values = extracted.get('bankAccounts', [])
        if isinstance(bank_values, list):
            if any(fake_data['bankAccount'] in str(v) for v in bank_values):
                score['bankScore'] = 10
                score['intelligenceExtraction'] += 10

    if 'upiId' in fake_data:
        upi_values = extracted.get('upiIds', [])
        if isinstance(upi_values, list):
            if any(fake_data['upiId'] in str(v) for v in upi_values):
                score['upiScore'] = 10
                score['intelligenceExtraction'] += 10

    if 'phishingLink' in fake_data:
        phishing_values = extracted.get('phishingLinks', [])
        if isinstance(phishing_values, list):
            if any(fake_data['phishingLink'] in str(v) for v in phishing_values):
                score['phishingScore'] = 10
                score['intelligenceExtraction'] += 10

    score['intelligenceExtraction'] = min(score['intelligenceExtraction'], 40)

    # 3. Engagement Quality (20 points)
    metrics = final_output.get('engagementMetrics', {})
    duration = metrics.get('engagementDurationSeconds', 0)
    messages = final_output.get('totalMessagesExchanged', 0)

    # Duration > 0s (5 points)
    if duration > 0:
        score['duration0'] = 5
        score['engagementQuality'] += 5

    # Duration > 60s (5 points)
    if duration > 60:
        score['duration60'] = 5
        score['engagementQuality'] += 5

    # Messages > 0 (5 points)
    if messages > 0:
        score['messages0'] = 5
        score['engagementQuality'] += 5

    # Messages >= 5 (5 points)
    if messages >= 5:
        score['messages5'] = 5
        score['engagementQuality'] += 5

    # 4. Response Structure (20 points)
    # Required fields: status (5), scamDetected (5), extractedIntelligence (5)
    if 'status' in final_output:
        score['statusField'] = 5
        score['responseStructure'] += 5

    if 'scamDetected' in final_output:
        score['scamDetectedField'] = 5
        score['responseStructure'] += 5

    if 'extractedIntelligence' in final_output:
        score['extractedField'] = 5
        score['responseStructure'] += 5

    # Optional fields: engagementMetrics (2.5), agentNotes (2.5)
    if 'engagementMetrics' in final_output and final_output['engagementMetrics']:
        score['metricsField'] = 2.5
        score['responseStructure'] += 2.5

    if 'agentNotes' in final_output and final_output['agentNotes']:
        score['notesField'] = 2.5
        score['responseStructure'] += 2.5

    score['responseStructure'] = min(score['responseStructure'], 20)

    # Calculate total score
    score['total'] = (
        score['scamDetection'] +
        score['intelligenceExtraction'] +
        score['engagementQuality'] +
        score['responseStructure']
    )

    return score

# Run the test
if __name__ == "__main__":
    print("=" * 60)
    print("HONEYPOT API SELF-TEST")
    print("=" * 60)
    print("\nThis script will test your honeypot API and score it")
    print("using the official evaluation criteria.")
    print("\nScoring Breakdown:")
    print("  1. Scam Detection (20 pts)")
    print("  2. Intelligence Extraction (40 pts)")
    print("  3. Engagement Quality (20 pts)")
    print("  4. Response Structure (20 pts)")
    print("  TOTAL: 100 pts")
    print("\n" + "=" * 60 + "\n")

    test_honeypot_api()
