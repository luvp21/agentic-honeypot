#!/usr/bin/env python3
"""
Quick automated test - simulates 5 turns with UPI data
"""
import requests
import uuid
from datetime import datetime

ENDPOINT = "http://localhost:8000/api/honeypot/message"
API_KEY = "honeypot-secret-key-123"

def test_quick():
    session_id = str(uuid.uuid4())
    headers = {'Content-Type': 'application/json', 'x-api-key': API_KEY}
    history = []

    scammer_messages = [
        "URGENT: Your SBI account has been compromised. Share your account number immediately!",
        "Your account 1234567890123456 will be blocked. Verify now!",
        "Transfer money to my UPI: scammer.fraud@fakebank",
        "Call me at +91-9876543210 right now!",
        "Click here to verify: http://malicious-sbi-verify.com"
    ]

    print("🍯 Running Quick 5-Turn Test...")
    print("=" * 60)

    for i, msg in enumerate(scammer_messages, 1):
        message = {
            "sender": "scammer",
            "text": msg,
            "timestamp": int(datetime.utcnow().timestamp() * 1000)
        }

        req = {
            'sessionId': session_id,
            'message': message,
            'conversationHistory': history,
            'metadata': {'channel': 'SMS', 'language': 'English', 'locale': 'IN'}
        }

        print(f"\nTurn {i}: {msg[:50]}...")

        try:
            resp = requests.post(ENDPOINT, headers=headers, json=req, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                reply = data.get('reply', 'No reply')
                print(f"✅ Agent: {reply[:50]}...")

                history.append(message)
                history.append({
                    'sender': 'user',
                    'text': reply,
                    'timestamp': int(datetime.utcnow().timestamp() * 1000)
                })
            else:
                print(f"❌ Error: {resp.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

    # Check extracted intelligence
    print("\n" + "=" * 60)
    print("📊 CHECKING EXTRACTION RESULTS...")
    print("=" * 60)

    try:
        test_url = f"http://localhost:8000/test/session/{session_id}"
        resp = requests.get(test_url, headers=headers, timeout=5)

        if resp.status_code == 200:
            data = resp.json()
            intel = data.get('extractedIntelligence', {})

            print("\n✅ Extracted Intelligence:")
            for key, values in intel.items():
                if values:
                    print(f"  • {key}: {values}")

            # Check critical items
            upi_extracted = 'scammer.fraud@fakebank' in str(intel.get('upi_ids', []))
            bank_extracted = '1234567890123456' in str(intel.get('bank_accounts', []))
            phone_extracted = '+91-9876543210' in str(intel.get('phone_numbers', [])) or '9876543210' in str(intel.get('phone_numbers', []))
            link_extracted = 'malicious-sbi-verify.com' in str(intel.get('phishing_links', []))

            print(f"\n📈 Extraction Status:")
            print(f"  {'✅' if bank_extracted else '❌'} Bank Account: 1234567890123456")
            print(f"  {'✅' if upi_extracted else '❌'} UPI ID: scammer.fraud@fakebank")
            print(f"  {'✅' if phone_extracted else '❌'} Phone: +91-9876543210")
            print(f"  {'✅' if link_extracted else '❌'} Link: http://malicious-sbi-verify.com")

            # Calculate score
            score = 20  # Scam detection
            score += 10 if bank_extracted else 0
            score += 10 if upi_extracted else 0
            score += 10 if phone_extracted else 0
            score += 10 if link_extracted else 0
            score += 15  # Engagement (5 messages, <60s)
            score += 20  # Response structure

            print(f"\n🎯 ESTIMATED SCORE: {score}/100")

            if upi_extracted:
                print("\n✅ UPI BUG FIX VERIFIED! +10 points recovered")
            else:
                print("\n❌ UPI still not extracted - bug not fixed")

            return score
        else:
            print(f"❌ Could not fetch test data: {resp.status_code}")
            return None

    except Exception as e:
        print(f"❌ Error checking results: {e}")
        return None

if __name__ == "__main__":
    score = test_quick()
    exit(0 if score and score >= 75 else 1)
