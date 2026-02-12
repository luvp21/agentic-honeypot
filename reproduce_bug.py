
import sys
import os

# Add current directory to path
sys.path.append('/home/luv/Desktop/files')

from intelligence_extractor import IntelligenceExtractor

def test_repro():
    extractor = IntelligenceExtractor()
    messages = [
        "Our UPI ID is scammer.fraud@fakebank, phone number +91-9876543210, account number 1234567890123456"
    ]

    for i, msg in enumerate(messages):
        print(f"\nTesting message: {msg}")
        extracted = extractor.extract(msg, message_index=i)

        print("Extracted Intelligence:")
        found_phone = False
        for item in extracted:
            print(f" - {item.type}: {item.value} (source: {item.source})")
            if item.type == "phone_numbers":
                found_phone = True

        if not found_phone:
            print("❌ FAILURE: Phone number not extracted!")
        else:
            print("✅ SUCCESS: Phone number extracted.")

if __name__ == "__main__":
    test_repro()
