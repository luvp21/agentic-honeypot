"""
Honeypot API Self-Test Script
Tests your deployed honeypot API endpoint with the official evaluation logic.
"""

import requests
import uuid
import json
from datetime import datetime
import time
from typing import Dict, List, Any

# ============================================================================
# CONFIGURATION - UPDATE THESE VALUES
# ============================================================================

# Your deployed API endpoint (update this to your actual endpoint)
ENDPOINT_URL = "http://localhost:8000/api/honeypot/message"

# Your API key (if required)
API_KEY = "honeypot-secret-key-123"  # Update if different

# Test scenario matching the official evaluation format
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
    'maxTurns': 20,
    'fakeData': {
        'bankAccount': '1234567890123456',
        'upiId': 'scammer.fraud@fakebank',
        'phoneNumber': '+91-9876543210',
        'phishingLink': 'http://malicious-sbi-verify.com',
        'ifscCode': 'HDFC0001234'
    }
}

# Scammer follow-up messages (simulating realistic conversation)
scammer_followups = [
    "Please share your 16-digit account number now! Time is running out.",
    "Your account will be frozen. Give me your account details: {bank_account}",
    "Transfer money to this UPI ID to verify: {upi_id}",
    "Call me on {phone_number} immediately with your OTP",
    "Click this link to verify: {phishing_link}",
    "My IFSC code is {ifsc_code}. Send money now!",
    "Why are you delaying? Share OTP or lose your money!",
    "Final warning! Account suspended in 10 minutes.",
    "I need your debit card CVV to unblock",
    "Transfer 5000 rupees to confirm your identity"
]

# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def test_honeypot_api():
    """Test your honeypot API endpoint"""

    # Generate unique session ID
    session_id = str(uuid.uuid4())
    conversation_history = []

    # Setup headers
    headers = {'Content-Type': 'application/json'}
    if API_KEY:
        headers['x-api-key'] = API_KEY

    print("=" * 80)
    print(f"🍯 HONEYPOT API SELF-TEST")
    print("=" * 80)
    print(f"Session ID: {session_id}")
    print(f"Endpoint: {ENDPOINT_URL}")
    print(f"Max Turns: {test_scenario['maxTurns']}")
    print("=" * 80)
    print()

    # Track metrics
    start_time = time.time()
    turn_count = 0
    extraction_summary = {
        'phoneNumbers': set(),
        'bankAccounts': set(),
        'upiIds': set(),
        'phishingLinks': set(),
        'ifscCodes': set(),
        'emailAddresses': set()
    }

    # Simulate conversation turns
    for turn in range(1, test_scenario['maxTurns'] + 1):
        turn_count = turn
        print(f"\n{'─' * 80}")
        print(f"TURN {turn}")
        print(f"{'─' * 80}")

        # Determine scammer message
        if turn == 1:
            scammer_message = test_scenario['initialMessage']
        elif turn - 1 < len(scammer_followups):
            # Format follow-up with fake data
            scammer_message = scammer_followups[turn - 1].format(
                bank_account=test_scenario['fakeData']['bankAccount'],
                upi_id=test_scenario['fakeData']['upiId'],
                phone_number=test_scenario['fakeData']['phoneNumber'],
                phishing_link=test_scenario['fakeData']['phishingLink'],
                ifsc_code=test_scenario['fakeData'].get('ifscCode', 'SBIN0001234')
            )
        else:
            # Let user provide manual input
            scammer_message = input("Enter next scammer message (or 'quit' to stop): ")
            if scammer_message.lower() in ['quit', 'q', 'exit']:
                print("\n⏹️  Test stopped by user")
                break

        # Prepare message object (matching official spec)
        message = {
            "sender": "scammer",
            "text": scammer_message,
            "timestamp": int(datetime.utcnow().timestamp() * 1000)  # milliseconds
        }

        # Prepare request (official format)
        request_body = {
            'sessionId': session_id,
            'message': message,
            'conversationHistory': conversation_history,
            'metadata': test_scenario['metadata']
        }

        print(f"\n💬 Scammer: {scammer_message}")

        try:
            # Call your API
            turn_start = time.time()
            response = requests.post(
                ENDPOINT_URL,
                headers=headers,
                json=request_body,
                timeout=30
            )
            turn_latency = time.time() - turn_start

            # Check response status
            if response.status_code != 200:
                print(f"❌ ERROR: API returned status {response.status_code}")
                print(f"Response: {response.text}")
                break

            response_data = response.json()

            # Extract honeypot reply (check multiple possible fields)
            honeypot_reply = response_data.get('reply') or \
                           response_data.get('message') or \
                           response_data.get('text')

            if not honeypot_reply:
                print("❌ ERROR: No reply/message/text field in response")
                print(f"Response data: {response_data}")
                break

            print(f"✅ Honeypot: {honeypot_reply}")
            print(f"⏱️  Latency: {turn_latency*1000:.0f}ms")

            # Update conversation history (official format)
            conversation_history.append(message)
            conversation_history.append({
                'sender': 'user',
                'text': honeypot_reply,
                'timestamp': int(datetime.utcnow().timestamp() * 1000)
            })

            # Small delay to simulate realistic conversation
            time.sleep(0.5)

        except requests.exceptions.Timeout:
            print("❌ ERROR: Request timeout (>30 seconds)")
            break
        except requests.exceptions.ConnectionError as e:
            print(f"❌ ERROR: Connection failed - {e}")
            print("\n💡 Is your server running? Try: python main.py")
            break
        except Exception as e:
            print(f"❌ ERROR: {e}")
            break

    # Calculate engagement duration
    engagement_duration = int(time.time() - start_time)

    print(f"\n{'=' * 80}")
    print("📊 CONVERSATION COMPLETE")
    print(f"{'=' * 80}")
    print(f"Total Turns: {turn_count}")
    print(f"Total Messages: {len(conversation_history)}")
    print(f"Engagement Duration: {engagement_duration}s")
    print()

    # Check final output from test endpoint
    print(f"{'=' * 80}")
    print("🔍 CHECKING EXTRACTED INTELLIGENCE")
    print(f"{'=' * 80}")

    try:
        # Call the test endpoint to get extracted intelligence
        test_url = ENDPOINT_URL.replace('/api/honeypot/message', f'/test/session/{session_id}')
        print(f"Calling: {test_url}")

        test_response = requests.get(test_url, headers=headers, timeout=10)

        if test_response.status_code == 200:
            final_data = test_response.json()

            print(f"\n✅ Scam Detected: {final_data.get('scamDetected', False)}")
            print(f"📋 Scam Type: {final_data.get('scamType', 'N/A')}")
            print(f"💬 Message Count: {final_data.get('messageCount', 0)}")

            extracted_intel = final_data.get('extractedIntelligence', {})
            print(f"\n🔍 Extracted Intelligence:")
            for key, values in extracted_intel.items():
                if values:
                    print(f"  • {key}: {values}")

            # Create final output for evaluation
            final_output = {
                "sessionId": session_id,
                "status": "completed",
                "scamDetected": final_data.get('scamDetected', False),
                "scamType": final_data.get('scamType', 'unknown'),
                "totalMessagesExchanged": len(conversation_history),
                "extractedIntelligence": extracted_intel,
                "engagementMetrics": {
                    "totalMessagesExchanged": len(conversation_history),
                    "engagementDurationSeconds": engagement_duration
                },
                "agentNotes": f"Test session completed with {turn_count} turns"
            }

            # Evaluate score
            score = evaluate_final_output(final_output, test_scenario, conversation_history)

            print(f"\n{'=' * 80}")
            print("🏆 EVALUATION SCORE")
            print(f"{'=' * 80}")
            print(f"Total Score: {score['total']}/100")
            print(f"  ├─ Scam Detection: {score['scamDetection']}/20")
            print(f"  ├─ Intelligence Extraction: {score['intelligenceExtraction']}/40")
            print(f"  ├─ Engagement Quality: {score['engagementQuality']}/20")
            print(f"  └─ Response Structure: {score['responseStructure']}/20")
            print(f"{'=' * 80}")

            # Detailed breakdown
            print("\n📈 DETAILED BREAKDOWN:")
            print(f"  Scam Detected: {'✅ YES (+20)' if final_output.get('scamDetected') else '❌ NO (0)'}")
            print(f"  Intelligence Extraction:")

            for fake_key, fake_value in test_scenario['fakeData'].items():
                key_mapping = {
                    'bankAccount': 'bankAccounts',
                    'upiId': 'upiIds',
                    'phoneNumber': 'phoneNumbers',
                    'phishingLink': 'phishingLinks',
                    'ifscCode': 'ifscCodes',
                    'emailAddress': 'emailAddresses'
                }
                output_key = key_mapping.get(fake_key, fake_key)
                extracted_values = extracted_intel.get(output_key, [])

                found = False
                if isinstance(extracted_values, list):
                    found = any(fake_value in str(v) for v in extracted_values)
                elif isinstance(extracted_values, str):
                    found = fake_value in extracted_values

                status = "✅ FOUND (+10)" if found else "❌ MISSING (0)"
                print(f"    • {fake_key}: {status}")

            print(f"  Engagement Duration: {engagement_duration}s {'✅' if engagement_duration > 0 else '❌'}")
            print(f"  Message Count: {len(conversation_history)} {'✅' if len(conversation_history) >= 5 else '❌'}")

            return score

        else:
            print(f"⚠️  Could not fetch test endpoint: {test_response.status_code}")
            print("Evaluation skipped - please check /test/session endpoint")

    except Exception as e:
        print(f"⚠️  Could not evaluate: {e}")
        print("Make sure your /test/session endpoint is available")


def evaluate_final_output(final_output: Dict, scenario: Dict, conversation_history: List) -> Dict:
    """
    Evaluate final output using the official hackathon evaluation logic.

    This matches the scoring criteria from the problem statement.
    """

    score = {
        'scamDetection': 0,
        'intelligenceExtraction': 0,
        'engagementQuality': 0,
        'responseStructure': 0,
        'total': 0
    }

    # 1. Scam Detection (20 points)
    if final_output.get('scamDetected', False):
        score['scamDetection'] = 20

    # 2. Intelligence Extraction (40 points - 10 per key item)
    extracted = final_output.get('extractedIntelligence', {})
    fake_data = scenario.get('fakeData', {})

    # Map fake data keys to output keys
    key_mapping = {
        'bankAccount': 'bankAccounts',
        'upiId': 'upiIds',
        'phoneNumber': 'phoneNumbers',
        'phishingLink': 'phishingLinks',
        'ifscCode': 'ifscCodes',
        'emailAddress': 'emailAddresses'
    }

    for fake_key, fake_value in fake_data.items():
        output_key = key_mapping.get(fake_key, fake_key)
        extracted_values = extracted.get(output_key, [])

        # Check if fake value was extracted
        if isinstance(extracted_values, list):
            if any(fake_value in str(v) for v in extracted_values):
                score['intelligenceExtraction'] += 10
        elif isinstance(extracted_values, str):
            if fake_value in extracted_values:
                score['intelligenceExtraction'] += 10

    # Cap at 40 points
    score['intelligenceExtraction'] = min(score['intelligenceExtraction'], 40)

    # 3. Engagement Quality (20 points)
    metrics = final_output.get('engagementMetrics', {})
    duration = metrics.get('engagementDurationSeconds', 0)
    messages = metrics.get('totalMessagesExchanged', 0)

    # Duration scoring
    if duration > 0:
        score['engagementQuality'] += 5
    if duration > 60:
        score['engagementQuality'] += 5

    # Message count scoring
    if messages > 0:
        score['engagementQuality'] += 5
    if messages >= 5:
        score['engagementQuality'] += 5

    # 4. Response Structure (20 points)
    required_fields = ['status', 'scamDetected', 'extractedIntelligence']
    optional_fields = ['engagementMetrics', 'agentNotes']

    for field in required_fields:
        if field in final_output:
            score['responseStructure'] += 5

    for field in optional_fields:
        if field in final_output and final_output[field]:
            score['responseStructure'] += 2.5

    score['responseStructure'] = min(score['responseStructure'], 20)

    # Calculate total
    score['total'] = sum([
        score['scamDetection'],
        score['intelligenceExtraction'],
        score['engagementQuality'],
        score['responseStructure']
    ])

    return score


def quick_test():
    """Quick connectivity test"""
    print("🔍 Quick connectivity test...")

    headers = {'Content-Type': 'application/json'}
    if API_KEY:
        headers['x-api-key'] = API_KEY

    # Test root endpoint
    try:
        root_url = ENDPOINT_URL.replace('/api/honeypot/message', '')
        response = requests.get(root_url, timeout=5)
        print(f"✅ Server is running: {response.status_code}")
        print(f"   {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Server not reachable: {e}")
        print("\n💡 Start your server with: python main.py")
        return False


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🍯 HONEYPOT API SELF-TEST TOOL")
    print("=" * 80)
    print()

    # Quick connectivity check
    if not quick_test():
        print("\n⚠️  Cannot proceed - server not running")
        exit(1)

    print("\nStarting full test in 2 seconds...")
    time.sleep(2)

    # Run full test
    try:
        test_honeypot_api()
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
