"""Quick test to send UPI message to API"""
import requests

url = "http://localhost:8000/api/honeypot/message"
headers = {"Content-Type": "application/json", "x-api-key": "honeypot-secret-key-123"}

payload = {
    "sessionId": "test-upi-debug-001",
    "message": {
        "sender": "scammer",
        "text": "My UPI ID is scammer.fraud@fakebank. Send money now!",
        "timestamp": 1000000
    },
    "conversationHistory": [],
    "metadata": {"channel": "SMS"}
}

print("Sending UPI test message...")
response = requests.post(url, json=payload, headers=headers)
print(f"Response: {response.status_code}")
print(f"Reply: {response.json().get('reply')}")

# Check extraction
check_url = f"http://localhost:8000/test/session/test-upi-debug-001"
check = requests.get(check_url, headers=headers)
if check.status_code == 200:
    data = check.json()
    upis = data.get('extractedIntelligence', {}).get('upi_ids', [])
    print(f"\nExtracted UPIs: {upis}")
    if upis:
        for upi in upis:
            print(f"  - '{upi}' (length: {len(upi)})")
