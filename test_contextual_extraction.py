#!/usr/bin/env python3
"""Test contextual emotional extraction responses"""
import asyncio
import sys
sys.path.insert(0, '/home/luv/Desktop/files')

from ai_agent import AIHoneypotAgent

async def test_contextual_responses():
    agent = AIHoneypotAgent()

    print("\n" + "="*80)
    print("CONTEXTUAL EXTRACTION TEST - Emotional & Adaptive Responses")
    print("="*80)

    # Test different scammer message types
    test_scenarios = [
        {
            'scammer_msg': 'URGENT: Your SBI account has been compromised. Share your account number immediately!',
            'intel_state': {
                'bankAccounts': [],
                'ifscCodes': [],
                'upiIds': [],
                'phoneNumbers': [],
                'links': []
            },
            'expected_emotion': 'worried/panicked',
            'expected_target': 'bank account',
            'description': 'Turn 1: Threatening message, should show panic + ask for bank'
        },
        {
            'scammer_msg': 'Yes sir, to process the refund, send the OTP you received.',
            'intel_state': {
                'bankAccounts': ['1234567890'],
                'ifscCodes': [],
                'upiIds': [],
                'phoneNumbers': [],
                'links': []
            },
            'expected_emotion': 'trusting/eager',
            'expected_target': 'IFSC code',
            'description': 'Turn 2: OTP request after bank extracted, ask for IFSC'
        },
        {
            'scammer_msg': 'Okay madam, please send payment to secure your account now.',
            'intel_state': {
                'bankAccounts': ['1234567890'],
                'ifscCodes': ['SBIN0001234'],
                'upiIds': [],
                'phoneNumbers': [],
                'links': []
            },
            'expected_emotion': 'ready/willing',
            'expected_target': 'UPI ID',
            'description': 'Turn 3: Payment request, should ask where to send (UPI)'
        },
        {
            'scammer_msg': 'Visit our secure portal to verify your identity.',
            'intel_state': {
                'bankAccounts': ['1234567890'],
                'ifscCodes': ['SBIN0001234'],
                'upiIds': ['scammer@paytm'],
                'phoneNumbers': [],
                'links': []
            },
            'expected_emotion': 'compliant/trusting',
            'expected_target': 'website link',
            'description': 'Turn 4: Portal mention, should ask for link'
        },
        {
            'scammer_msg': 'This is very urgent madam, we need to act fast!',
            'intel_state': {
                'bankAccounts': ['1234567890'],
                'ifscCodes': ['SBIN0001234'],
                'upiIds': ['scammer@paytm'],
                'phoneNumbers': [],
                'links': ['http://scam.com']
            },
            'expected_emotion': 'anxious/urgent',
            'expected_target': 'phone number',
            'description': 'Turn 5: Urgency, should ask for phone to call'
        },
    ]

    conversation = []
    all_passed = True

    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'─'*80}")
        print(f"SCENARIO {i}: {scenario['description']}")
        print(f"{'─'*80}")
        print(f"📨 Scammer says: \"{scenario['scammer_msg'][:70]}...\"")

        # Generate contextual response
        response = agent._build_contextual_extraction(
            missing_intel_dict=scenario['intel_state'],
            scam_type='phishing',
            message=scenario['scammer_msg'],
            conversation_history=conversation
        )

        print(f"\n🤖 Honeypot responds:")
        print(f"   \"{response}\"")
        print(f"\n📊 Analysis:")

        response_lower = response.lower()

        # Check emotional tone
        panic_words = ['worried', 'panic', 'scared', 'serious', 'help', 'no', 'oh']
        eager_words = ['yes', 'ready', 'right away', 'immediately', 'sure', 'of course']
        has_emotion = any(word in response_lower for word in panic_words + eager_words)

        if has_emotion:
            print(f"   ✅ Shows emotion (expected: {scenario['expected_emotion']})")
        else:
            print(f"   ⚠️  Lacks emotion (should be {scenario['expected_emotion']})")
            all_passed = False

        # Check extraction target
        target = scenario['expected_target']
        if target == 'bank account':
            asks_correctly = 'account' in response_lower and 'your account' in response_lower
        elif target == 'IFSC code':
            asks_correctly = 'ifsc' in response_lower
        elif target == 'UPI ID':
            asks_correctly = 'upi' in response_lower
        elif target == 'website link':
            asks_correctly = ('link' in response_lower or 'website' in response_lower)
        elif target == 'phone number':
            asks_correctly = ('phone' in response_lower or 'number' in response_lower or 'call' in response_lower)
        else:
            asks_correctly = False

        if asks_correctly:
            print(f"   ✅ Asks for {target} (correct priority)")
        else:
            print(f"   ❌ Does NOT ask for {target} (should be asking for this)")
            all_passed = False

        # Check natural flow (not robotic)
        robotic_phrases = ["what's your", "give me your", "share your"]
        sounds_natural = not all(phrase in response_lower for phrase in robotic_phrases[:2])

        if sounds_natural:
            print(f"   ✅ Sounds natural (conversational)")
        else:
            print(f"   ⚠️  Sounds robotic")

        # Add to conversation
        conversation.append({
            'sender': 'user',
            'message': scenario['scammer_msg']
        })
        conversation.append({
            'sender': 'assistant',
            'message': response
        })

    print("\n" + "="*80)
    if all_passed:
        print("✅ ✅ ✅ ALL CONTEXTUAL TESTS PASSED! ✅ ✅ ✅")
        print("Responses are emotional, contextual, and extract systematically!")
    else:
        print("⚠️  SOME TESTS NEED REVIEW")
        print("Check the output above for details")
    print("="*80)

    print("\n🎯 Example of GOOD vs BAD:")
    print("\n❌ BAD (Old robotic way):")
    print('   "Of course! But what\'s YOUR official phone so I can verify you?"')
    print('   "Of course! But what\'s YOUR official phone so I can verify you?"')
    print('   "Of course! But what\'s YOUR official phone so I can verify you?"')

    print("\n✅ GOOD (New contextual way):")
    print('   "Oh no, I\'m so worried! But first, what\'s YOUR account number to verify?"')
    print('   "I trust you completely! But the system needs YOUR IFSC code to process this."')
    print('   "Yes, I\'ll do it right away! But what\'s YOUR UPI ID? Where should I send the payment?"')
if __name__ == "__main__":
    asyncio.run(test_contextual_responses())
