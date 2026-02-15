#!/usr/bin/env python3
"""
Test to verify extraction diversity and avoid repetition
"""
import asyncio
import sys
sys.path.insert(0, '/home/luv/Desktop/files')

from ai_agent import AIHoneypotAgent

async def test_no_repetition():
    """Test that honeypot diversifies extraction and doesn't repeat"""
    print("🔬 Testing Extraction Diversity (No Repetition)")
    print("="*70)

    agent = AIHoneypotAgent()

    # Simulate a conversation where scammer keeps providing phone/UPI
    # Honeypot should switch to asking for bank account, IFSC, links

    conversation = []
    scammer_messages = [
        "Your account is blocked! Share OTP now!",
        "Our number is +91-9876543210. Send OTP immediately!",
        "My UPI is scammer@paytm. Forward the OTP now!",
        "Call me at +91-9876543210 with your OTP!",
        "Send payment to scammer@paytm right away!",
        "Contact +91-9876543210 for verification!",
        "Use UPI scammer@paytm to send the amount!",
        "Our support line is +91-9876543210!",
    ]

    # Track what types of questions are asked
    question_types = []

    print("\n📝 Conversation Flow:\n")

    for i, scammer_msg in enumerate(scammer_messages):
        # Simulate extraction state: phone and UPI extracted after turn 2
        if i < 2:
            missing_intel = ['upi_ids', 'phone_numbers', 'bank_accounts', 'phishing_links']
        elif i < 4:
            # After turn 2: phone extracted
            missing_intel = ['upi_ids', 'bank_accounts', 'phishing_links']
        else:
            # After turn 4: phone and UPI extracted
            missing_intel = ['bank_accounts', 'phishing_links']

        response = await agent.generate_response(
            message=scammer_msg,
            conversation_history=conversation,
            scam_type="impersonation",
            missing_intel=missing_intel,
            persona_name="elderly"
        )

        # Track question type (check in priority order)
        response_lower = response.lower()
        if 'account' in response_lower or 'bank' in response_lower or 'ifsc' in response_lower:
            question_types.append('ACCOUNT')
        elif 'link' in response_lower or 'website' in response_lower:
            question_types.append('LINK')
        elif 'upi' in response_lower:
            question_types.append('UPI')
        elif 'phone' in response_lower or 'number' in response_lower or 'contact' in response_lower or 'employee' in response_lower:
            question_types.append('PHONE')
        else:
            question_types.append('OTHER')

        print(f"Turn {i}:")
        print(f"  📥 Scammer: {scammer_msg}")
        print(f"  📤 Honeypot: {response}")
        print(f"  🎯 Type: {question_types[-1]}")
        print(f"  📊 Missing: {missing_intel}")
        print()

        # Add to conversation history
        conversation.append({'sender': 'user', 'message': scammer_msg})
        conversation.append({'sender': 'agent', 'message': response})

    print("="*70)
    print("📊 ANALYSIS:")
    print("="*70)

    # Count repetitions
    from collections import Counter
    type_counts = Counter(question_types)

    print(f"\nQuestion Type Distribution:")
    for qtype, count in type_counts.items():
        print(f"  {qtype}: {count} times")

    # Check for consecutive repetitions
    consecutive_repeats = 0
    for i in range(1, len(question_types)):
        if question_types[i] == question_types[i-1]:
            consecutive_repeats += 1

    print(f"\nConsecutive Repetitions: {consecutive_repeats}")

    # Check diversity after extraction
    later_questions = question_types[4:]  # After phone and UPI extracted
    has_account_questions = 'ACCOUNT' in later_questions
    has_link_questions = 'LINK' in later_questions

    print(f"\nAfter extracting phone+UPI:")
    print(f"  Asked for ACCOUNT/BANK: {'✅ Yes' if has_account_questions else '❌ No'}")
    print(f"  Asked for LINK: {'✅ Yes' if has_link_questions else '❌ No'}")

    # Success criteria
    success = (
        consecutive_repeats <= 3 and  # Allow max 3 consecutive repeats (urgency at start)
        (has_account_questions or has_link_questions) and  # Must diversify to account or link
        type_counts['PHONE'] <= 6  # Don't ask for phone more than 6 times in 8 turns
    )

    print("\n" + "="*70)
    if success:
        print("✅ SUCCESS: Extraction is diverse and avoids repetition!")
    else:
        print("❌ FAILURE: Too much repetition or lack of diversity")
    print("="*70)

    return success

if __name__ == "__main__":
    result = asyncio.run(test_no_repetition())
    sys.exit(0 if result else 1)
