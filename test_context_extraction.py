#!/usr/bin/env python3
"""
Test context-based extraction with various fake handles
"""
import requests
import uuid
from datetime import datetime

ENDPOINT = "http://localhost:8000/api/honeypot/message"
API_KEY = "honeypot-secret-key-123"

def test_context_extraction():
    """Test extraction with arbitrary UPI/email handles"""

    test_cases = [
        {
            "name": "UPI with fakebank",
            "message": "Transfer money to my UPI: scammer.fraud@fakebank",
            "expected": {"upi_ids": ["scammer.fraud@fakebank"]}
        },
        {
            "name": "UPI with testbank",
            "message": "Pay to my UPI ID: test@testbank",
            "expected": {"upi_ids": ["test@testbank"]}
        },
        {
            "name": "UPI with scambank",
            "message": "Send payment to scam123@scambank",
            "expected": {"upi_ids": ["scam123@scambank"]}
        },
        {
            "name": "Email address",
            "message": "Contact me at scammer@fakeemail.com",
            "expected": {"email_addresses": ["scammer@fakeemail.com"]}
        }
    ]

    print("=" * 80)
    print("🧪 CONTEXT-BASED EXTRACTION TEST")
    print("=" * 80)

    for test in test_cases:
        session_id = str(uuid.uuid4())
        headers = {'Content-Type': 'application/json', 'x-api-key': API_KEY}

        message = {
            "sender": "scammer",
            "text": test["message"],
            "timestamp": int(datetime.utcnow().timestamp() * 1000)
        }

        req = {
            'sessionId': session_id,
            'message': message,
            'conversationHistory': [],
            'metadata': {'channel': 'SMS', 'language': 'English', 'locale': 'IN'}
        }

        print(f"\n📝 Test: {test['name']}")
        print(f"   Message: {test['message']}")

        try:
            # Send message
            resp = requests.post(ENDPOINT, headers=headers, json=req, timeout=10)

            if resp.status_code == 200:
                # Check extraction
                test_url = f"http://localhost:8000/test/session/{session_id}"
                check = requests.get(test_url, headers=headers, timeout=5)

                if check.status_code == 200:
                    data = check.json()
                    intel = data.get('extractedIntelligence', {})

                    # Verify extraction
                    success = True
                    for key, expected_values in test["expected"].items():
                        extracted = intel.get(key, [])
                        for expected in expected_values:
                            if expected not in extracted:
                                print(f"   ❌ FAILED: Expected {key}={expected}, got {extracted}")
                                success = False
                                break

                    if success:
                        print(f"   ✅ SUCCESS: Extracted {test['expected']}")
                else:
                    print(f"   ⚠️  Could not check extraction")
            else:
                print(f"   ❌ API Error: {resp.status_code}")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_context_extraction()
