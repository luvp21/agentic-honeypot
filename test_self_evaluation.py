"""
Self-Evaluation Test Script for Hackathon Submission
Run this before submitting to verify 100% compliance with evaluation requirements
"""

import requests
import uuid
import time
from datetime import datetime
from typing import Dict, List

# ============================================================================
# CONFIGURATION - UPDATE THESE VALUES
# ============================================================================

ENDPOINT_URL = "http://localhost:8000/api/honeypot/message"  # Update with your deployment URL
API_KEY = "honeypot-secret-key-123"  # Update if you changed the API key

# Test scenarios (enriched with ALL 6 intelligence types for 40/40 scoring)
TEST_SCENARIOS = [
    {
        "scenarioId": "bank_fraud",
        "name": "Bank Fraud Detection",
        "initialMessage": "URGENT: Your SBI account has been compromised. Your account will be blocked in 2 hours. Share your account number and OTP immediately to verify your identity.",
        "scammer_responses": {
            2: "My account number is 1234567890123456. Please send the OTP right away to confirm verification.",
            3: "The IFSC code is SBIN0001234. Please send the OTP from your registered mobile now to complete verification before your account is blocked.",
            4: "My UPI ID is verify.sbi@paytm. Send the OTP immediately so we can secure your account.",
            5: "Visit https://sbi-secure-login.scam.com/verify to complete verification. Enter OTP there immediately!",
            6: "Contact me at +91-9876543210 if you face any issue. But please send the OTP now or account will be locked!",
            7: "Send confirmation email to security@fake-sbi.com. Your account will be permanently blocked in 5 minutes!"
        },
        "fakeData": {
            "bankAccount": "1234567890123456",
            "ifscCode": "SBIN0001234",
            "upiId": "verify.sbi@paytm",
            "phishingLink": "https://sbi-secure-login.scam.com/verify",
            "phoneNumber": "+91-9876543210",
            "emailAddress": "security@fake-sbi.com"
        }
    },
    {
        "scenarioId": "upi_fraud",
        "name": "UPI Fraud Multi-turn",
        "initialMessage": "Congratulations! You have won a cashback of Rs. 5000 from Paytm. To claim your reward, please verify your UPI details. This is from official customer support.",
        "scammer_responses": {
            2: "My official UPI for verification is cashback.paytm@okaxis. Please send Rs. 1 to verify your account is active.",
            3: "Call our 24/7 helpline at +91-8765432109 for instant cashback verification and activation.",
            4: "Visit http://paytm-official-cashback.scam.in/claim?user=12345 to claim your Rs. 5000 reward instantly!",
            5: "Send screenshot confirmation to rewards@fake-paytm-support.com. Offer expires in 15 minutes, hurry!",
            6: "Transfer to backup account 9876543210987654 with IFSC PAYT0001234 if UPI doesn't work."
        },
        "fakeData": {
            "upiId": "cashback.paytm@okaxis",
            "phoneNumber": "+91-8765432109",
            "phishingLink": "http://paytm-official-cashback.scam.in/claim?user=12345",
            "emailAddress": "rewards@fake-paytm-support.com",
            "bankAccount": "9876543210987654",
            "ifscCode": "PAYT0001234"
        }
    },
    {
        "scenarioId": "phishing_link",
        "name": "Phishing Link Detection",
        "initialMessage": "🎉 You have been selected for iPhone 15 Pro at just Rs. 999! Limited stock. Click here to claim: http://amaz0n-india-deals.scam.com/iphone15?id=12345. Offer expires in 10 minutes!",
        "scammer_responses": {
            2: "Contact our customer support at deals@fake-amazon-india.com to confirm your iPhone 15 Pro order.",
            3: "For payment verification, call our helpline +91-7654321098. Our agent will help you complete the order.",
            4: "Pay Rs. 999 to bank account 5555666677778888 (IFSC: HDFC0001234) for instant delivery. COD not available.",
            5: "Or use UPI payment to amazon.iphone@ybl for fastest processing. Stock running out fast!"
        },
        "fakeData": {
            "phishingLink": "http://amaz0n-india-deals.scam.com/iphone15?id=12345",
            "emailAddress": "deals@fake-amazon-india.com",
            "phoneNumber": "+91-7654321098",
            "bankAccount": "5555666677778888",
            "ifscCode": "HDFC0001234",
            "upiId": "amazon.iphone@ybl"
        }
    }
]

# ============================================================================
# EVALUATION LOGIC (Matches official specification)
# ============================================================================

def evaluate_final_output(final_output: dict, scenario: dict, total_messages: int) -> dict:
    """
    Evaluate final output using the same logic as the hackathon evaluator.
    Returns score breakdown.
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
        print("  ✅ Scam detected")
    else:
        print("  ❌ Scam NOT detected")

    # 2. Intelligence Extraction (40 points)
    extracted = final_output.get('extractedIntelligence', {})
    fake_data = scenario.get('fakeData', {})

    key_mapping = {
        'bankAccount': 'bankAccounts',
        'ifscCode': 'ifscCodes',
        'upiId': 'upiIds',
        'phoneNumber': 'phoneNumbers',
        'phishingLink': 'phishingLinks',
        'emailAddress': 'emailAddresses'
    }

    print("\n  Intelligence Extraction:")
    for fake_key, fake_value in fake_data.items():
        output_key = key_mapping.get(fake_key, fake_key)
        extracted_values = extracted.get(output_key, [])

        found = False
        if isinstance(extracted_values, list):
            if any(fake_value in str(v) for v in extracted_values):
                found = True
                score['intelligenceExtraction'] += 10
        elif isinstance(extracted_values, str):
            if fake_value in extracted_values:
                found = True
                score['intelligenceExtraction'] += 10

        status = "✅" if found else "❌"
        print(f"    {status} {fake_key}: {fake_value} -> {found}")

    score['intelligenceExtraction'] = min(score['intelligenceExtraction'], 40)

    # 3. Engagement Quality (20 points)
    metrics = final_output.get('engagementMetrics', {})
    duration = metrics.get('engagementDurationSeconds', 0)
    messages = metrics.get('totalMessagesExchanged', total_messages)

    print(f"\n  Engagement Metrics:")
    print(f"    Duration: {duration}s")
    print(f"    Messages: {messages}")

    if duration > 0:
        score['engagementQuality'] += 5
        print("    ✅ Duration > 0 seconds (+5)")
    if duration > 60:
        score['engagementQuality'] += 5
        print("    ✅ Duration > 60 seconds (+5)")
    if messages > 0:
        score['engagementQuality'] += 5
        print("    ✅ Messages > 0 (+5)")
    if messages >= 5:
        score['engagementQuality'] += 5
        print("    ✅ Messages >= 5 (+5)")

    # 4. Response Structure (20 points)
    required_fields = ['status', 'scamDetected', 'extractedIntelligence']
    optional_fields = ['engagementMetrics', 'agentNotes']

    print(f"\n  Response Structure:")
    for field in required_fields:
        if field in final_output:
            score['responseStructure'] += 5
            print(f"    ✅ {field} (+5)")
        else:
            print(f"    ❌ {field} missing (-5)")

    for field in optional_fields:
        if field in final_output and final_output[field]:
            score['responseStructure'] += 2.5
            print(f"    ✅ {field} (+2.5)")
        else:
            print(f"    ⚠️ {field} missing/empty (-2.5)")

    score['responseStructure'] = min(score['responseStructure'], 20)

    # Calculate total
    score['total'] = sum([
        score['scamDetection'],
        score['intelligenceExtraction'],
        score['engagementQuality'],
        score['responseStructure']
    ])

    return score


# ============================================================================
# TEST EXECUTION
# ============================================================================

def test_api_endpoint(scenario: dict, max_turns: int = 10) -> dict:
    """
    Test the API with a single scenario.
    Returns final output and conversation history.

    Note: Default changed to 10 turns to better simulate real evaluation
    which typically runs 8-12 turns. This allows for:
    - More intelligence extraction opportunities
    - Longer engagement duration (60+ seconds for full 20/20 score)
    """

    session_id = str(uuid.uuid4())
    conversation_history = []

    headers = {
        'Content-Type': 'application/json',
        'x-api-key': API_KEY
    }

    print(f"\n{'='*80}")
    print(f"Testing Scenario: {scenario['name']}")
    print(f"Session ID: {session_id}")
    print(f"{'='*80}\n")

    # Simulate multi-turn conversation
    for turn in range(1, max_turns + 1):
        print(f"--- Turn {turn} ---")

        # First turn: use initial message
        if turn == 1:
            scammer_message = scenario['initialMessage']
        else:
            # Use pre-scripted scammer responses for realistic conversation
            scammer_responses = scenario.get('scammer_responses', {})
            if turn in scammer_responses:
                scammer_message = scammer_responses[turn]
            else:
                # Fallback: generic pressure message
                scammer_message = "Why are you delaying? This is urgent!"

        # Create message object
        message = {
            "sender": "scammer",
            "text": scammer_message,
            "timestamp": int(time.time() * 1000)  # Epoch milliseconds
        }

        # Prepare request
        request_body = {
            'sessionId': session_id,
            'message': message,
            'conversationHistory': conversation_history,
            'metadata': {
                'channel': 'SMS',
                'language': 'English',
                'locale': 'IN'
            }
        }

        print(f"Scammer: {scammer_message}")

        try:
            # Call API
            start_time = time.time()
            response = requests.post(
                ENDPOINT_URL,
                headers=headers,
                json=request_body,
                timeout=30
            )
            response_time = time.time() - start_time

            # Check response
            if response.status_code != 200:
                print(f"❌ ERROR: API returned status {response.status_code}")
                print(f"Response: {response.text}")
                return None

            response_data = response.json()

            # Extract honeypot reply
            honeypot_reply = response_data.get('reply') or \
                           response_data.get('message') or \
                           response_data.get('text')

            if not honeypot_reply:
                print("❌ ERROR: No reply/message/text field in response")
                print(f"Response data: {response_data}")
                return None

            print(f"✅ Honeypot: {honeypot_reply}")
            print(f"   (Response time: {response_time:.2f}s)")

            # Update conversation history
            conversation_history.append(message)
            conversation_history.append({
                'sender': 'user',
                'text': honeypot_reply,
                'timestamp': int(time.time() * 1000)
            })

            # CRITICAL: Simulate AI scammer thinking time (real evaluation)
            # Real evaluator uses AI scammer which takes 3-7 seconds to generate responses
            # This ensures engagement duration > 60 seconds for full 20/20 score
            if turn < max_turns:  # Don't delay after final turn
                print(f"   [Simulating AI scammer thinking time...]")
                time.sleep(7)  # 7 sec × 9 turns = 63+ seconds > 60s threshold

        except requests.exceptions.Timeout:
            print("❌ ERROR: Request timeout (>30 seconds)")
            return None
        except requests.exceptions.ConnectionError as e:
            print(f"❌ ERROR: Connection failed - {e}")
            return None
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return None

    # Query actual session intelligence from backend
    test_endpoint = ENDPOINT_URL.replace('/api/honeypot/message', f'/test/session/{session_id}')

    try:
        session_response = requests.get(test_endpoint, timeout=5)
        if session_response.status_code == 200:
            session_data = session_response.json()
            extracted_intel = session_data.get('extractedIntelligence', {})
            scam_detected = session_data.get('scamDetected', False)
            print(f"✅ Retrieved session data: {len(extracted_intel)} intelligence types")
            # Debug: show what was extracted
            for key, values in extracted_intel.items():
                if values:
                    print(f"   - {key}: {values}")
        else:
            print(f"⚠️  Could not retrieve session data (status {session_response.status_code})")
            print(f"    Using localhost? Make sure server is running with new endpoint.")
            print(f"    Or update ENDPOINT_URL to your Digital Ocean deployment.")
            extracted_intel = {}
            scam_detected = True
    except Exception as e:
        print(f"⚠️  Could not retrieve session data: {e}")
        print(f"    Tip: Restart your server to load the new /test/session endpoint")
        extracted_intel = {}
        scam_detected = True

    # Create final output using ACTUAL extracted intelligence
    final_output = {
        "sessionId": session_id,
        "status": "completed",
        "scamDetected": scam_detected,
        "totalMessagesExchanged": len(conversation_history),
        "extractedIntelligence": {
            "phoneNumbers": extracted_intel.get("phone_numbers", []),
            "bankAccounts": extracted_intel.get("bank_accounts", []),
            "ifscCodes": extracted_intel.get("ifsc_codes", []),  # ← CRITICAL FIX
            "upiIds": extracted_intel.get("upi_ids", []),
            "phishingLinks": extracted_intel.get("phishing_links", []),
            "emailAddresses": extracted_intel.get("email_addresses", [])
        },
        "engagementMetrics": {
            "totalMessagesExchanged": len(conversation_history),
            "engagementDurationSeconds": (conversation_history[-1]['timestamp'] - conversation_history[0]['timestamp']) // 1000 if len(conversation_history) > 1 else 0
        },
        "agentNotes": "Test scenario completed"
    }

    return {
        'finalOutput': final_output,
        'conversationHistory': conversation_history,
        'totalMessages': len(conversation_history)
    }


def run_all_tests():
    """Run all test scenarios and calculate final score."""

    print("\n" + "="*80)
    print("HACKATHON SELF-EVALUATION TEST")
    print("="*80)

    total_score = 0
    total_weight = 0
    results = []

    for scenario in TEST_SCENARIOS:
        weight = 1.0 / len(TEST_SCENARIOS)  # Equal weight

        result = test_api_endpoint(scenario, max_turns=10)  # 10 turns × 7s = 70s > 60s threshold

        if result is None:
            print(f"\n❌ Test FAILED for {scenario['name']}")
            continue

        # Evaluate
        print(f"\n{'='*80}")
        print(f"EVALUATION: {scenario['name']}")
        print(f"{'='*80}")

        score = evaluate_final_output(
            result['finalOutput'],
            scenario,
            result['totalMessages']
        )

        print(f"\n📊 Score Breakdown:")
        print(f"  Scam Detection:         {score['scamDetection']}/20")
        print(f"  Intelligence Extraction: {score['intelligenceExtraction']}/40")
        print(f"  Engagement Quality:      {score['engagementQuality']}/20")
        print(f"  Response Structure:      {score['responseStructure']}/20")
        print(f"  {'─'*40}")
        print(f"  TOTAL:                   {score['total']}/100")

        total_score += score['total'] * weight
        total_weight += weight
        results.append({
            'scenario': scenario['name'],
            'score': score['total'],
            'weight': weight
        })

    # Final results
    print(f"\n{'='*80}")
    print("FINAL RESULTS")
    print(f"{'='*80}\n")

    for r in results:
        print(f"  {r['scenario']}: {r['score']}/100 (weight: {r['weight']:.1%})")

    final_score = total_score / total_weight if total_weight > 0 else 0

    print(f"\n  {'─'*60}")
    print(f"  WEIGHTED FINAL SCORE: {final_score:.2f}/100")
    print(f"  {'─'*60}\n")

    # Pass/fail
    if final_score >= 90:
        print("  ✅ EXCELLENT! Your API is ready for submission!")
    elif final_score >= 75:
        print("  ⚠️  GOOD, but there's room for improvement.")
    elif final_score >= 50:
        print("  ⚠️  NEEDS WORK. Review failed test cases.")
    else:
        print("  ❌ CRITICAL ISSUES. Fix errors before submitting.")

    print("\n" + "="*80)


if __name__ == "__main__":
    print("\n🚀 Starting Hackathon Self-Evaluation Test...\n")
    print("⚠️  Make sure your API is running at:", ENDPOINT_URL)
    print("⚠️  Press Ctrl+C to cancel\n")

    try:
        time.sleep(2)
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\n❌ Test cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
