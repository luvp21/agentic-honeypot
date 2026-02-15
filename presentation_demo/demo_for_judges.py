#!/usr/bin/env python3
"""Quick demo showing system handling various scam types"""
import asyncio
from ai_agent import AIHoneypotAgent

async def demo():
    agent = AIHoneypotAgent()

    print("\n" + "="*80)
    print("SCAM HONEYPOT DEMO - Hybrid Extraction System")
    print("="*80)

    test_cases = [
        {
            "name": "Phishing - Bank Account",
            "message": "URGENT: Your SBI account will be blocked in 1 hour. Verify now!",
            "scam_type": "phishing"
        },
        {
            "name": "Lottery Scam",
            "message": "Congratulations! You won ₹50 lakhs. Pay ₹500 processing fee.",
            "scam_type": "lottery"
        },
        {
            "name": "Tech Support",
            "message": "Your device is infected! Call this number immediately: 9876543210",
            "scam_type": "tech_support"
        },
        {
            "name": "OTP Theft",
            "message": "Send your OTP and PIN to verify your identity.",
            "scam_type": "phishing"
        },
        {
            "name": "UPI Payment Scam",
            "message": "Send ₹1000 to scammer@paytm to activate your account.",
            "scam_type": "payment"
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'─'*80}")
        print(f"TEST {i}: {test['name']}")
        print(f"{'─'*80}")
        print(f"Scammer: {test['message']}")

        response = await agent.generate_response(
            message=test['message'],
            conversation_history=[],
            scam_type=test['scam_type'],
            missing_intel=['upi_ids', 'phone_numbers', 'bank_accounts']
        )

        print(f"Honeypot: {response}")

        # Analyze response
        extracts = []
        if 'upi' in response.lower():
            extracts.append('UPI ID')
        if 'phone' in response.lower() or 'number' in response.lower():
            extracts.append('Phone')
        if 'account' in response.lower():
            extracts.append('Account')
        if 'link' in response.lower():
            extracts.append('Link')

        if extracts:
            print(f"✅ Attempts to extract: {', '.join(extracts)}")
        else:
            print(f"⚠️  No clear extraction attempt")

    print("\n" + "="*80)
    print("DEMO COMPLETE")
    print("="*80)
    print("\nKey Features Demonstrated:")
    print("✓ Adapts to different scam types")
    print("✓ Always asks for scammer's information")
    print("✓ Natural victim behavior")
    print("✓ Multiple extraction strategies")

if __name__ == "__main__":
    asyncio.run(demo())
