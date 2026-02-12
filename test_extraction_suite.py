
import sys
import os
import re

# Add current directory to path
sys.path.append('/home/luv/Desktop/files')

from intelligence_extractor import IntelligenceExtractor

def test_extraction():
    extractor = IntelligenceExtractor()

    test_cases = [
        {
            "name": "Original User Failure Case",
            "text": "Our UPI ID is scammer.fraud@fakebank, phone number +91-9876543210, account number 1234567890123456",
            "expected_phone": "+91-9876543210"
        },
        {
            "name": "Phone with 'whatsapp' context",
            "text": "Contact me on whatsapp 9876543210 for more info. IFSC: SBIN0001234",
            "expected_phone": "9876543210"
        },
        {
            "name": "Phone with '+91' but nearby account",
            "text": "Send OTP to +919876543210. My account is 1234567890.",
            "expected_phone": "+919876543210"
        },
        {
            "name": "Negative Case: Account number that looks like phone (should NOT be extracted as phone)",
            "text": "My account number is 9876543210",
            "expected_phone": None
        },
        {
            "name": "Negative Case: UPI with number (should NOT be extracted as phone)",
            "text": "Pay to 9876543210@upi",
            "expected_phone": None
        }
    ]

    overall_success = True
    for case in test_cases:
        print(f"\n--- Testing: {case['name']} ---")
        extracted = extractor.extract(case['text'], message_index=0)

        found_phones = [item.value for item in extracted if item.type == "phone_numbers"]
        print(f"Text: {case['text']}")
        print(f"Extracted Phones: {found_phones}")

        expected = case['expected_phone']
        if expected is None:
            if not found_phones:
                print("✅ Correct: No phone number extracted.")
            else:
                print(f"❌ Failure: Extracted unexpected phone(s): {found_phones}")
                overall_success = False
        else:
            if expected in [found for found in found_phones]:
                 print(f"✅ Correct: Phone number {expected} extracted.")
            else:
                print(f"❌ Failure: Expected phone {expected} NOT found in {found_phones}")
                overall_success = False

    if overall_success:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED.")
        return 1

if __name__ == "__main__":
    sys.exit(test_extraction())
