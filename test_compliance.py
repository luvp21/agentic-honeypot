"""
Test Script - Validates Spec Compliance
Tests the compliant API with official request formats
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "honeypot-secret-key-123"

HEADERS = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}


def test_first_message():
    """
    Test Case 1: First Message (Empty conversationHistory)
    This simulates the platform sending the very first message.
    """
    print("\n" + "="*80)
    print("TEST 1: FIRST MESSAGE (Official Format)")
    print("="*80)

    request_payload = {
        "sessionId": "test-session-001",
        "message": {
            "sender": "scammer",
            "text": "URGENT! Your bank account will be blocked today. Click here to verify immediately: http://bit.ly/fake123",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        },
        "conversationHistory": [],  # EMPTY for first message
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    }

    print("\n📤 REQUEST:")
    print(json.dumps(request_payload, indent=2))

    response = requests.post(
        f"{BASE_URL}/api/honeypot/message",
        json=request_payload,
        headers=HEADERS
    )

    print(f"\n📥 RESPONSE ({response.status_code}):")
    print(json.dumps(response.json(), indent=2))

    # Validation
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "status" in data, "Missing 'status' field"
    assert "reply" in data, "Missing 'reply' field"
    assert data["status"] == "success", f"Expected status='success', got {data['status']}"
    assert len(data.keys()) == 2, f"Response has extra fields: {data.keys()}"

    print("\n✅ TEST 1 PASSED")
    return request_payload


def test_follow_up_message(first_request):
    """
    Test Case 2: Follow-up Message (Non-empty conversationHistory)
    This simulates the platform sending a second message with conversation history.
    """
    print("\n" + "="*80)
    print("TEST 2: FOLLOW-UP MESSAGE (Official Format)")
    print("="*80)

    request_payload = {
        "sessionId": "test-session-001",  # Same session
        "message": {
            "sender": "scammer",
            "text": "Share your account number and UPI ID to avoid suspension. Use UPI: scammer@paytm",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        },
        "conversationHistory": [
            # Include previous messages
            first_request["message"],
            {
                "sender": "user",
                "text": "Why will my account be blocked? I'm confused.",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        ],
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    }

    print("\n📤 REQUEST:")
    print(json.dumps(request_payload, indent=2))

    response = requests.post(
        f"{BASE_URL}/api/honeypot/message",
        json=request_payload,
        headers=HEADERS
    )

    print(f"\n📥 RESPONSE ({response.status_code}):")
    print(json.dumps(response.json(), indent=2))

    # Validation
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data.keys()) == 2

    print("\n✅ TEST 2 PASSED")
    return request_payload


def test_multi_turn_conversation():
    """
    Test Case 3: Multi-turn Conversation (5+ messages)
    This tests the callback trigger condition.
    """
    print("\n" + "="*80)
    print("TEST 3: MULTI-TURN CONVERSATION (Callback Trigger)")
    print("="*80)

    session_id = "test-session-002"
    conversation_history = []

    messages = [
        "Your account will be suspended! Click: http://scam.link",
        "I need your help urgently. Send money to 9876543210",
        "Call this number: +91-1234567890",
        "Transfer to account: 1234567890123456",
        "Use UPI: scammer@paytm immediately!"
    ]

    for i, msg in enumerate(messages):
        print(f"\n--- Message {i+1}/5 ---")

        request_payload = {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",
                "text": msg,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            },
            "conversationHistory": conversation_history.copy(),
            "metadata": {"channel": "SMS"}
        }

        response = requests.post(
            f"{BASE_URL}/api/honeypot/message",
            json=request_payload,
            headers=HEADERS
        )

        print(f"Response: {response.json()['reply'][:80]}...")

        # Add to history for next message
        conversation_history.append(request_payload["message"])
        conversation_history.append({
            "sender": "user",
            "text": response.json()["reply"],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

        assert response.status_code == 200

    print("\n✅ TEST 3 PASSED")
    print("⚠️  Check server logs for callback status")


def test_error_cases():
    """
    Test Case 4: Error Handling
    """
    print("\n" + "="*80)
    print("TEST 4: ERROR HANDLING")
    print("="*80)

    # Test 4a: Missing API key
    print("\n--- Test 4a: Missing API Key ---")
    response = requests.post(
        f"{BASE_URL}/api/honeypot/message",
        json={"sessionId": "test", "message": {}, "conversationHistory": []}
    )
    print(f"Status: {response.status_code} (Expected: 403)")
    assert response.status_code == 403

    # Test 4b: Invalid schema
    print("\n--- Test 4b: Invalid Schema ---")
    response = requests.post(
        f"{BASE_URL}/api/honeypot/message",
        json={"wrong": "schema"},
        headers=HEADERS
    )
    print(f"Status: {response.status_code} (Expected: 422)")
    assert response.status_code == 422

    print("\n✅ TEST 4 PASSED")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("OFFICIAL SPEC COMPLIANCE TESTS")
    print("="*80)
    print("\nTesting against: " + BASE_URL)
    print("Make sure the server is running: python main.py\n")

    try:
        # Test server is running
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Server is running: {response.json()}")
    except:
        print("❌ Server is not running! Start with: python main.py")
        return

    try:
        # Run tests
        first_req = test_first_message()
        test_follow_up_message(first_req)
        test_multi_turn_conversation()
        test_error_cases()

        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED!")
        print("="*80)
        print("\nThe API is SPEC COMPLIANT and ready for submission.")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")


if __name__ == "__main__":
    main()
