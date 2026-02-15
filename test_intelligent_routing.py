#!/usr/bin/env python3
"""Test intelligent LLM vs Heuristic routing based on situation"""
import asyncio
import sys
sys.path.insert(0, '/home/luv/Desktop/files')

from ai_agent import AIHoneypotAgent

async def test_intelligent_routing():
    agent = AIHoneypotAgent()

    print("\n" + "="*80)
    print("INTELLIGENT HYBRID ROUTING TEST")
    print("="*80)
    print("\nTesting situational awareness for LLM vs Heuristic selection\n")

    # Test scenarios with expected routing
    scenarios = [
        # HEURISTIC CASES (Direct scam patterns)
        {
            'name': 'Direct Scam Keywords',
            'message': 'URGENT! Your SBI account is blocked. Send OTP and CVV immediately to verify.',
            'turn': 5,
            'intel': {'bankAccounts': [], 'ifscCodes': [], 'upiIds': [], 'phoneNumbers': [], 'links': []},
            'expected': 'HEURISTIC',
            'reason': 'High density scam keywords (urgent, blocked, otp, cvv, verify)'
        },
        {
            'name': 'Extraction Phase',
            'message': 'Please confirm your payment details now.',
            'turn': 5,
            'intel': {'bankAccounts': [], 'ifscCodes': [], 'upiIds': [], 'phoneNumbers': [], 'links': []},
            'expected': 'HEURISTIC',
            'reason': 'Turn > 3 with missing critical intel (extraction phase)'
        },
        {
            'name': 'Simple Urgent Message',
            'message': 'Send it now urgently!',
            'turn': 4,
            'intel': {'bankAccounts': ['123'], 'ifscCodes': [], 'upiIds': [], 'phoneNumbers': [], 'links': []},
            'expected': 'HEURISTIC',
            'reason': 'Short message (<15 words) + urgent keyword'
        },
        {
            'name': 'Credential Flip',
            'message': 'Send me your OTP code immediately.',
            'turn': 6,
            'intel': {'bankAccounts': [], 'ifscCodes': [], 'upiIds': ['scammer@upi'], 'phoneNumbers': [], 'links': []},
            'expected': 'HEURISTIC',
            'reason': 'Direct credential request (send me + otp)'
        },

        # LLM CASES (Complex, novel, early turns)
        {
            'name': 'Early Turn (Rapport)',
            'message': 'Hello, this is from SBI security department. We noticed suspicious activity.',
            'turn': 1,
            'intel': {'bankAccounts': [], 'ifscCodes': [], 'upiIds': [], 'phoneNumbers': [], 'links': []},
            'expected': 'LLM',
            'reason': 'Turn <= 3 (building rapport phase)'
        },
        {
            'name': 'Complex Novel Message',
            'message': 'I am calling from the Reserve Bank of India cybersecurity division. We have detected unauthorized transactions from your account totaling Rs. 50,000. To prevent further loss, we need to verify your identity through a secure process.',
            'turn': 2,
            'intel': {'bankAccounts': [], 'ifscCodes': [], 'upiIds': [], 'phoneNumbers': [], 'links': []},
            'expected': 'LLM',
            'reason': 'Low keyword density + long message (>20 words) - novel pattern'
        },
        {
            'name': 'Authority Challenge',
            'message': 'Why should I trust you? How do I know you are really from the bank?',
            'turn': 4,
            'intel': {'bankAccounts': [], 'ifscCodes': [], 'upiIds': [], 'phoneNumbers': [], 'links': []},
            'expected': 'LLM',
            'reason': 'Authority challenge detected (why, trust, prove)'
        },
    ]

    print("─" * 80)

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{'='*80}")
        print(f"SCENARIO {i}: {scenario['name']}")
        print(f"{'='*80}")

        print(f"\n📨 Scammer (Turn {scenario['turn']}): \"{scenario['message']}\"")
        print(f"\n📊 Intel Status: {len([k for k,v in scenario['intel'].items() if v])} types collected")

        # Build conversation history
        conversation = [{'sender': 'user', 'message': scenario['message']}] * scenario['turn']

        # Get routing decision
        should_use_llm = agent._should_use_llm_for_extraction(
            message=scenario['message'],
            turn_number=scenario['turn'],
            missing_intel_dict=scenario['intel'],
            conversation_history=conversation
        )

        actual = 'LLM' if should_use_llm else 'HEURISTIC'
        expected = scenario['expected']

        print(f"\n🎯 Expected: {expected}")
        print(f"   Reason: {scenario['reason']}")
        print(f"\n{'✅' if actual == expected else '❌'} Actual: {actual}")

        if actual != expected:
            print(f"   ⚠️  MISMATCH!")

    print("\n" + "="*80)
    print("ROUTING LOGIC SUMMARY")
    print("="*80)

    print("\n⚡ HEURISTIC (50% - Direct/Known Patterns):")
    print("   1. High scam keyword density (≥3 keywords)")
    print("   2. Extraction phase (turn > 3 + missing intel)")
    print("   3. Simple urgent messages (short + urgent)")
    print("   4. Direct credential requests (send me OTP)")

    print("\n🤖 LLM (50% - Complex/Novel/Early):")
    print("   1. Early turns (1-3) for building rapport")
    print("   2. Novel/complex messages (low keywords, long)")
    print("   3. Authority challenges (why, prove, trust)")
    print("   4. Multi-turn negotiations (varied conversation)")

    print("\n🎯 RESULT: Intelligent routing maximizes:")
    print("   • Speed & cost efficiency (heuristic for obvious patterns)")
    print("   • Creativity & adaptability (LLM for complex situations)")
    print("   • Extraction success (every message extracts intel)")

    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(test_intelligent_routing())
