"""Quick test to verify UPI extraction fix"""
import asyncio
import sys
sys.path.insert(0, '/home/luv/Desktop/files')

from intelligence_extractor import IntelligenceExtractor

async def test_upi_extraction():
    extractor = IntelligenceExtractor()

    test_cases = [
        "Transfer money to this UPI ID to verify: scammer.fraud@fakebank",
        "My UPI is test@fakeupi",
        "Send payment to scam@testbank",
        "Pay to legitimate@paytm"
    ]

    print("=" * 60)
    print("UPI EXTRACTION TEST")
    print("=" * 60)

    for i, text in enumerate(test_cases, 1):
        print(f"\nTest {i}: {text}")
        result = await extractor.extract(text, message_index=i, context_window="")

        upi_found = [r for r in result if r.type == "upi_ids"]
        if upi_found:
            print(f"✅ EXTRACTED: {[r.value for r in upi_found]}")
        else:
            print(f"❌ NOT EXTRACTED")

    print("\n" + "=" * 60)
    print("CRITICAL TEST: scammer.fraud@fakebank")
    print("=" * 60)

    critical_text = "Transfer money to this UPI ID to verify: scammer.fraud@fakebank"
    result = await extractor.extract(critical_text, message_index=0, context_window="")
    upi_found = [r for r in result if r.type == "upi_ids"]

    if upi_found and 'scammer.fraud@fakebank' in [r.value for r in upi_found]:
        print("✅ SUCCESS! UPI extraction bug is FIXED!")
        print(f"   Extracted: {[r.value for r in upi_found]}")
        return True
    else:
        print("❌ FAILED! UPI still not extracted")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_upi_extraction())
    sys.exit(0 if success else 1)
