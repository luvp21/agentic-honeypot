#!/usr/bin/env python3
"""
Comprehensive test of hybrid extraction across multiple turns
"""
import asyncio
from ai_agent import AIHoneypotAgent

async def test_multiple_turns():
    """Test hybrid extraction across turns 0, 1, 2"""
    agent = AIHoneypotAgent()

    test_scenarios = [
        {
            "turn": 0,
            "message": "Hello sir, I'm from bank. Your account needs verification.",
            "history": [],
            "missing": ['upi_ids', 'phone_numbers', 'bank_accounts']
        },
        {
            "turn": 1,
            "message": "Please download this app and login with your details.",
            "history": [{"role": "scammer", "content": "Hello sir"}],
            "missing": ['phishing_links', 'phone_numbers']
        },
        {
            "turn": 2,
            "message": "Send me your OTP to verify your identity.",
            "history": [
                {"role": "scammer", "content": "Hello"},
                {"role": "agent", "content": "What's your number?"}
            ],
            "missing": ['phone_numbers', 'upi_ids']
        }
    ]

    print("🔬 Testing hybrid extraction across multiple turns...\n")

    all_passed = True
    for scenario in test_scenarios:
        print(f"{'='*60}")
        print(f"TURN {scenario['turn']}")
        print(f"{'='*60}")
        print(f"📥 Scammer: {scenario['message']}")
        print(f"📊 Missing: {scenario['missing']}")

        response = await agent.generate_response(
            message=scenario['message'],
            conversation_history=scenario['history'],
            scam_type="impersonation",
            missing_intel=scenario['missing'],
            persona_name="elderly"
        )

        print(f"📤 Agent: {response}")

        # Check if it asks for info
        extraction_keywords = [
            'your', 'contact', 'number', 'phone', 'upi', 'account',
            'details', 'link', 'whatsapp', 'telegram', 'alternate', 'backup'
        ]

        asks_for_info = any(keyword in response.lower() for keyword in extraction_keywords)
        is_long_enough = len(response) > 15
        not_generic = 'sure' not in response.lower() or 'your' in response.lower()

        passed = asks_for_info and is_long_enough and not_generic

        print(f"{'✅' if asks_for_info else '❌'} Asks for info: {asks_for_info}")
        print(f"{'✅' if is_long_enough else '❌'} Length OK: {len(response)} chars")
        print(f"{'✅' if not_generic else '❌'} Not generic")
        print(f"{'✅ PASS' if passed else '❌ FAIL'}\n")

        if not passed:
            all_passed = False

    print(f"{'='*60}")
    if all_passed:
        print("✅ ALL TESTS PASSED - Hybrid extraction working on all turns!")
    else:
        print("❌ SOME TESTS FAILED")
    print(f"{'='*60}")

    return all_passed

if __name__ == "__main__":
    result = asyncio.run(test_multiple_turns())
    import sys
    sys.exit(0 if result else 1)
