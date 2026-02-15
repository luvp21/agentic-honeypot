#!/usr/bin/env python3
"""Simulate judge's creative test cases"""
import asyncio
from ai_agent import AIHoneypotAgent

async def judge_test():
    agent = AIHoneypotAgent()

    # Creative test cases judges might use
    creative_tests = [
        "क्या आप हिंदी बोलते हैं? अपना OTP भेजें।",  # Hindi language
        "Sir plz updete ur KYC detales on bitly/scam123",  # Typos + short URL
        "🚨ALERT🚨 Suspicious activity detected!!! 😱",  # Emojis
        "Government of India - Tax Refund Pending",  # Authority impersonation
        "WhatsApp: +91-99999-XXXXX for prize claim",  # Partial number
    ]

    print("\n" + "="*80)
    print("JUDGES' CREATIVE TEST CASES")
    print("="*80)

    for i, test in enumerate(creative_tests, 1):
        print(f"\n{i}. Scammer: {test}")

        response = await agent.generate_response(
            message=test,
            conversation_history=[],
            scam_type="phishing",
            missing_intel=['upi_ids', 'phone_numbers']
        )

        print(f"   Honeypot: {response}")

        # Check extraction
        asks = any(w in response.lower() for w in
                  ['your', 'upi', 'phone', 'number', 'account', 'contact'])
        print(f"   {'✅' if asks else '❌'} Extracts: {asks}")

if __name__ == "__main__":
    asyncio.run(judge_test())
