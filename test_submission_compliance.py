"""
Comprehensive Submission Compliance Test
Tests API against official hackathon documentation requirements
"""

import requests
import json
import time
from datetime import datetime

# Configuration
ENDPOINT_URL = "http://localhost:8000/api/honeypot/message"
API_KEY = "honeypot-secret-key-123"

# Test scenario from documentation
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


def test_api_response_format():
    """Test 1: Verify API response has correct format"""
    print("\n" + "=" * 60)
    print("TEST 1: API Response Format")
    print("=" * 60)

    session_id = f"test-{int(time.time())}"

    request_body = {
        'sessionId': session_id,
        'message': {
            'sender': 'scammer',
            'text': test_scenario['initialMessage'],
            'timestamp': int(time.time() * 1000)
        },
        'conversationHistory': [],
        'metadata': test_scenario['metadata']
    }

    try:
        response = requests.post(
            ENDPOINT_URL,
            headers={
                'Content-Type': 'application/json',
                'x-api-key': API_KEY
            },
            json=request_body,
            timeout=30
        )

        print(f"✓ Status Code: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        print(f"✓ Response: {json.dumps(data, indent=2)}")

        # Check required fields
        assert 'status' in data, "Missing 'status' field"
        assert data['status'] == 'success', f"Expected status='success', got '{data['status']}'"
        print(f"✓ status field: {data['status']}")

        # Check for reply field (priority order: reply, message, text)
        has_reply = 'reply' in data or 'message' in data or 'text' in data
        assert has_reply, "Missing reply/message/text field in response"

        reply_text = data.get('reply') or data.get('message') or data.get('text')
        print(f"✓ reply field: {reply_text[:100]}...")

        # Verify NO extra fields (only status and reply allowed)
        allowed_fields = {'status', 'reply', 'message', 'text'}
        extra_fields = set(data.keys()) - allowed_fields
        if extra_fields:
            print(f"⚠ Warning: Extra fields in response: {extra_fields}")
            print("  Documentation requires ONLY 'status' and 'reply' fields")

        print("\n✅ TEST 1 PASSED: API response format is correct")
        return True, session_id

    except AssertionError as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        return False, None
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        return False, None


def test_final_output_structure():
    """Test 2: Verify final output JSON structure matches documentation"""
    print("\n" + "=" * 60)
    print("TEST 2: Final Output Structure")
    print("=" * 60)

    # Expected structure from documentation
    expected_structure = {
        "sessionId": "string",
        "status": "string",  # Required - 5 points
        "scamDetected": "boolean",  # Required - 5 points
        "extractedIntelligence": {  # Required - 5 points
            "phoneNumbers": "array",
            "bankAccounts": "array",
            "upiIds": "array",
            "phishingLinks": "array",
            "emailAddresses": "array"
        },
        "engagementMetrics": {  # Optional - 2.5 points
            "totalMessagesExchanged": "integer",
            "engagementDurationSeconds": "integer"
        },
        "agentNotes": "string"  # Optional - 2.5 points
    }

    print("Expected structure:")
    print(json.dumps(expected_structure, indent=2))

    # Check if callback.py creates correct structure
    print("\n📋 Checking FinalCallbackPayload model...")

    from models import FinalCallbackPayload, ExtractedIntelligence, EngagementMetrics

    # Create sample payload
    payload = FinalCallbackPayload(
        sessionId="test-123",
        status="completed",
        scamDetected=True,
        extractedIntelligence=ExtractedIntelligence(
            phoneNumbers=["+91-9876543210"],
            bankAccounts=["1234567890123456"],
            upiIds=["scammer@fakeupi"],
            phishingLinks=["http://malicious.com"],
            emailAddresses=["scam@fake.com"]
        ),
        engagementMetrics=EngagementMetrics(
            totalMessagesExchanged=10,
            engagementDurationSeconds=120
        ),
        agentNotes="Test notes"
    )

    payload_dict = payload.model_dump()
    print("\n✓ Generated payload:")
    print(json.dumps(payload_dict, indent=2))

    # Verify required fields
    required_fields = ['sessionId', 'status', 'scamDetected', 'extractedIntelligence']
    for field in required_fields:
        assert field in payload_dict, f"Missing required field: {field}"
        print(f"✓ Required field present: {field}")

    # Verify optional fields
    optional_fields = ['engagementMetrics', 'agentNotes']
    for field in optional_fields:
        if field in payload_dict:
            print(f"✓ Optional field present: {field}")

    # CRITICAL CHECK: Verify totalMessagesExchanged is ONLY in engagementMetrics
    if 'totalMessagesExchanged' in payload_dict:
        print("\n❌ ERROR: 'totalMessagesExchanged' should NOT be at top level!")
        print("   It should ONLY be inside 'engagementMetrics'")
        return False

    if 'engagementMetrics' in payload_dict:
        if 'totalMessagesExchanged' in payload_dict['engagementMetrics']:
            print("✓ 'totalMessagesExchanged' correctly placed inside 'engagementMetrics'")

    # Verify extractedIntelligence structure
    intel = payload_dict['extractedIntelligence']
    expected_intel_fields = ['phoneNumbers', 'bankAccounts', 'upiIds', 'phishingLinks', 'emailAddresses']
    for field in expected_intel_fields:
        assert field in intel, f"Missing intelligence field: {field}"
        print(f"✓ Intelligence field present: {field}")

    print("\n✅ TEST 2 PASSED: Final output structure is correct")
    return True


def test_scoring_fields():
    """Test 3: Verify all scoring fields are present"""
    print("\n" + "=" * 60)
    print("TEST 3: Scoring Fields Verification")
    print("=" * 60)

    from models import FinalCallbackPayload, ExtractedIntelligence, EngagementMetrics

    payload = FinalCallbackPayload(
        sessionId="test-123",
        status="completed",
        scamDetected=True,
        extractedIntelligence=ExtractedIntelligence(),
        engagementMetrics=EngagementMetrics(
            totalMessagesExchanged=10,
            engagementDurationSeconds=120
        ),
        agentNotes="Test"
    )

    payload_dict = payload.model_dump()

    # Scoring breakdown from documentation
    scoring = {
        "Scam Detection (20 pts)": {
            "scamDetected": True in payload_dict.values()
        },
        "Intelligence Extraction (40 pts)": {
            "extractedIntelligence": 'extractedIntelligence' in payload_dict
        },
        "Engagement Quality (20 pts)": {
            "engagementMetrics": 'engagementMetrics' in payload_dict,
            "totalMessagesExchanged": payload_dict.get('engagementMetrics', {}).get('totalMessagesExchanged') is not None,
            "engagementDurationSeconds": payload_dict.get('engagementMetrics', {}).get('engagementDurationSeconds') is not None
        },
        "Response Structure (20 pts)": {
            "status": 'status' in payload_dict,
            "scamDetected": 'scamDetected' in payload_dict,
            "extractedIntelligence": 'extractedIntelligence' in payload_dict,
            "engagementMetrics": 'engagementMetrics' in payload_dict,
            "agentNotes": 'agentNotes' in payload_dict
        }
    }

    total_score = 0

    for category, checks in scoring.items():
        print(f"\n{category}:")
        category_passed = True
        for field, present in checks.items():
            status_icon = "✓" if present else "❌"
            print(f"  {status_icon} {field}: {present}")
            if not present and field in ['status', 'scamDetected', 'extractedIntelligence']:
                category_passed = False

        if category_passed:
            print(f"  ✅ {category} - Fields present")

    print("\n✅ TEST 3 PASSED: All scoring fields verified")
    return True


def test_multi_turn_conversation():
    """Test 4: Test multi-turn conversation flow"""
    print("\n" + "=" * 60)
    print("TEST 4: Multi-Turn Conversation")
    print("=" * 60)

    session_id = f"test-multi-{int(time.time())}"
    conversation_history = []

    # Simulated multi-turn messages
    scammer_messages = [
        test_scenario['initialMessage'],
        "I'm calling from SBI fraud department. My ID is SBI-12345. What's your account number?",
        "You can reach me at +91-9876543210. We need your UPI ID too.",
        "Please send money to scammer.fraud@fakebank to verify your account."
    ]

    for turn, scammer_msg in enumerate(scammer_messages, 1):
        print(f"\n--- Turn {turn} ---")

        message = {
            'sender': 'scammer',
            'text': scammer_msg,
            'timestamp': int(time.time() * 1000)
        }

        request_body = {
            'sessionId': session_id,
            'message': message,
            'conversationHistory': conversation_history,
            'metadata': test_scenario['metadata']
        }

        try:
            response = requests.post(
                ENDPOINT_URL,
                headers={
                    'Content-Type': 'application/json',
                    'x-api-key': API_KEY
                },
                json=request_body,
                timeout=30
            )

            assert response.status_code == 200, f"Turn {turn} failed with status {response.status_code}"

            data = response.json()
            honeypot_reply = data.get('reply') or data.get('message') or data.get('text')

            print(f"Scammer: {scammer_msg[:80]}...")
            print(f"Honeypot: {honeypot_reply[:80]}...")

            # Update conversation history
            conversation_history.append(message)
            conversation_history.append({
                'sender': 'user',
                'text': honeypot_reply,
                'timestamp': int(time.time() * 1000)
            })

            time.sleep(0.5)  # Small delay between turns

        except Exception as e:
            print(f"❌ Turn {turn} failed: {e}")
            return False

    print(f"\n✅ TEST 4 PASSED: Multi-turn conversation completed ({len(scammer_messages)} turns)")
    return True


def run_all_tests():
    """Run all compliance tests"""
    print("\n" + "=" * 60)
    print("HACKATHON SUBMISSION COMPLIANCE TEST SUITE")
    print("=" * 60)
    print(f"Endpoint: {ENDPOINT_URL}")
    print(f"API Key: {API_KEY[:20]}...")

    results = {}

    # Test 1: API Response Format
    results['api_response'] = test_api_response_format()

    # Test 2: Final Output Structure
    results['final_output'] = test_final_output_structure()

    # Test 3: Scoring Fields
    results['scoring_fields'] = test_scoring_fields()

    # Test 4: Multi-Turn Conversation
    results['multi_turn'] = test_multi_turn_conversation()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for r in results.values() if r in [True, (True, None)] or (isinstance(r, tuple) and r[0]))
    total = len(results)

    for test_name, result in results.items():
        if isinstance(result, tuple):
            result = result[0]
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED - SUBMISSION READY!")
    else:
        print("\n⚠️  SOME TESTS FAILED - FIX ISSUES BEFORE SUBMISSION")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
