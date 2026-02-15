#!/usr/bin/env python3
"""Test that system progressively extracts all intel types in priority order"""
import asyncio
import sys
sys.path.insert(0, '/home/luv/Desktop/files')

from ai_agent import AIHoneypotAgent

async def test_progression():
    agent = AIHoneypotAgent()

    print("\n" + "="*80)
    print("PROGRESSIVE EXTRACTION TEST")
    print("="*80)

    # Simulate conversation where we gradually get intel
    conversation = []

    intel_states = [
        # Turn 1: Nothing extracted yet
        {
            'bankAccounts': [],
            'ifscCodes': [],
            'upiIds': [],
            'phoneNumbers': [],
            'links': [],
            'description': 'No intel yet'
        },

        # Turn 2: Got bank account
        {
            'bankAccounts': ['1234567890'],
            'ifscCodes': [],
            'upiIds': [],
            'phoneNumbers': [],
            'links': [],
            'description': 'Got Bank Account'
        },

        # Turn 3: Got IFSC too
        {
            'bankAccounts': ['1234567890'],
            'ifscCodes': ['SBIN0001234'],
            'upiIds': [],
            'phoneNumbers': [],
            'links': [],
            'description': 'Got Bank + IFSC'
        },

        # Turn 4: Got UPI
        {
            'bankAccounts': ['1234567890'],
            'ifscCodes': ['SBIN0001234'],
            'upiIds': ['scammer@paytm'],
            'phoneNumbers': [],
            'links': [],
            'description': 'Got Bank + IFSC + UPI'
        },

        # Turn 5: Got link
        {
            'bankAccounts': ['1234567890'],
            'ifscCodes': ['SBIN0001234'],
            'upiIds': ['scammer@paytm'],
            'phoneNumbers': [],
            'links': ['http://scam.com'],
            'description': 'Got Bank + IFSC + UPI + Link'
        },

        # Turn 6: Got phone - all intel collected!
        {
            'bankAccounts': ['1234567890'],
            'ifscCodes': ['SBIN0001234'],
            'upiIds': ['scammer@paytm'],
            'phoneNumbers': ['+91-9876543210'],
            'links': ['http://scam.com'],
            'description': 'ALL INTEL COLLECTED'
        },
    ]

    expected_targets = [
        'ACCOUNT',   # Turn 1: Should ask for bank account
        'IFSC',      # Turn 2: Should ask for IFSC
        'UPI',       # Turn 3: Should ask for UPI
        'LINK',      # Turn 4: Should ask for phishing link
        'PHONE',     # Turn 5: Should ask for phone
        'BACKUP',    # Turn 6: Should ask for backups/alternatives
    ]

    all_passed = True

    for turn, intel_dict in enumerate(intel_states, 1):
        print(f"\n{'─'*80}")
        print(f"TURN {turn}: {intel_dict['description']}")
        print(f"{'─'*80}")

        # Show what we have so far
        has_bank = len(intel_dict['bankAccounts']) > 0
        has_ifsc = len(intel_dict['ifscCodes']) > 0
        has_upi = len(intel_dict['upiIds']) > 0
        has_phone = len(intel_dict['phoneNumbers']) > 0
        has_link = len(intel_dict['links']) > 0

        print(f"📊 Current intel: Bank={has_bank}, IFSC={has_ifsc}, UPI={has_upi}, Link={has_link}, Phone={has_phone}")

        # Generate response
        template = agent._select_extraction_template(
            missing_intel_dict=intel_dict,
            scam_type='phishing',
            message='Send your details now!',
            conversation_history=conversation
        )

        print(f"🤖 Response: {template}")

        # Check what it's asking for
        asks_for = []
        template_lower = template.lower()

        if 'account' in template_lower and 'ifsc' not in template_lower:
            asks_for.append('ACCOUNT')
        if 'ifsc' in template_lower:
            asks_for.append('IFSC')
        if 'upi' in template_lower:
            asks_for.append('UPI')
        if ('phone' in template_lower or 'number' in template_lower or 'contact' in template_lower) and 'account' not in template_lower:
            asks_for.append('PHONE')
        if 'link' in template_lower or 'website' in template_lower:
            asks_for.append('LINK')
        if 'backup' in template_lower or 'another' in template_lower or 'alternate' in template_lower or 'other' in template_lower:
            asks_for.append('BACKUP')

        actual_target = ', '.join(asks_for) if asks_for else 'UNKNOWN'
        expected_target = expected_targets[turn - 1]

        print(f"🎯 Asking for: {actual_target}")
        print(f"✅ Expected: {expected_target}")

        # Check if it matches expected
        if expected_target in actual_target:
            print(f"✅ PASS - Correct target!")
        else:
            print(f"❌ FAIL - Expected {expected_target}, got {actual_target}")
            all_passed = False

        # Add to conversation history
        conversation.append({
            'sender': 'assistant',
            'message': template
        })

        # Add dummy scammer response
        conversation.append({
            'sender': 'user',
            'message': 'Yes, send it!'
        })

    print("\n" + "="*80)
    if all_passed:
        print("✅ ✅ ✅ ALL TESTS PASSED! ✅ ✅ ✅")
        print("Progressive extraction working correctly!")
    else:
        print("❌ SOME TESTS FAILED")
        print("Review the output above to see which turns failed")
    print("="*80)
    print("\nExpected progression: Bank → IFSC → UPI → Link → Phone → Backup")
    print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(test_progression())
