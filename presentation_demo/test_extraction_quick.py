#!/usr/bin/env python3
"""Quick test that extraction is working"""
import asyncio
from ai_agent import AIHoneypotAgent

async def test():
    agent = AIHoneypotAgent()

    print("\n" + "="*80)
    print("EXTRACTION TEST")
    print("="*80)

    response = await agent.generate_response(
        message="URGENT: Send your OTP now!",
        conversation_history=[],
        scam_type="phishing",
        missing_intel=['upi_ids', 'phone_numbers', 'bank_accounts']
    )

    print(f"\nScammer: URGENT: Send your OTP now!")
    print(f"Honeypot: {response}")

    # Check if it asks for scammer's info
    asks = any(word in response.lower() for word in
              ['your upi', 'your phone', 'your number', 'your account', 'your contact'])

    print(f"\n{'✅' if asks else '❌'} Asks for scammer's info: {asks}")

    if asks:
        print("\n🎉 HYBRID EXTRACTION IS WORKING!")
    else:
        print("\n❌ Still using old responses")
        print("   Response should ask for 'YOUR phone' or 'YOUR UPI'")

if __name__ == "__main__":
    asyncio.run(test())
