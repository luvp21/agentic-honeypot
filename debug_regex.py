
import re
import asyncio

# Mock RawIntel check
class RawIntel:
    def __init__(self, type, value, source="debug", confidence_delta=0.0, message_index=0):
        self.type = type
        self.value = value
    def __repr__(self):
        return f"{self.type}: {self.value}"

# UPDATED Regex Logic from intelligence_extractor.py
def extract_debug(text):
    extracted = []

    # 1. Bank Accounts (New Regex)
    bank_context_pattern = r'(?i)(?:account\s*(?:number|no\.?|#)|a\/c|acc\.?)(?:\s+(?:is|of|for|:|-))?\s*[:\-]?\s*([0-9]{9,18})'
    for match in re.finditer(bank_context_pattern, text):
        extracted.append(RawIntel("bank_accounts", match.group(1)))

    # 2. UPI IDs
    upi_handles = ["oksbi", "okaxis", "okicici", "paytm", "upi", "ybl", "ibl", "axl", "hdfcbank"]
    handles_regex = "|".join(upi_handles)

    # Strict
    upi_pattern = fr'\b([a-zA-Z0-9.\-_]{{2,}}@(?:{handles_regex}))\b'
    for match in re.finditer(upi_pattern, text):
        extracted.append(RawIntel("upi_ids", match.group(1)))

    # Generic (Updated condition)
    if "upi" in text.lower() or "pay" in text.lower():
        generic_pattern = r'\b([a-zA-Z0-9.\-_]{2,}@[a-zA-Z0-9.\-_]{2,})\b'
        for match in re.finditer(generic_pattern, text):
            extracted.append(RawIntel("upi_ids", match.group(1), source="generic"))

    return extracted

# Test Cases from User Logs
test_cases = [
    "My account number is 1234567890123456.",
    "My account number is 1234567890123456; please send the OTP",
    "My account number is 1234567890123456 and my UPI ID is scammer.fraud@fakebank",
    "The account is registered under the name 'Scammer Fraud' with account number 1234567890123456",
    # Test valid phone number exclusion
    "Call me at 9876543210 (my account number is not this)"
]

print("--- FINAL VERIFICATION ---")
for i, msg in enumerate(test_cases):
    print(f"\nMessage {i+1}: '{msg}'")
    results = extract_debug(msg)
    if results:
        print(f"✅ FOUND: {results}")
    else:
        print("❌ FAILED TO EXTRACT")
