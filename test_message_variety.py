#!/usr/bin/env python3
"""
Test to demonstrate message variety for different test cases
Shows that extraction messages vary across different scenarios
"""
import sys
sys.path.insert(0, '/home/luv/Desktop/files')

from ai_agent import AIHoneypotAgent

def test_phone_extraction_variety():
    agent = AIHoneypotAgent()

    print("\n" + "="*80)
    print("MESSAGE VARIETY TEST - Phone Number Extraction")
    print("="*80)
    print("\nTesting if honeypot uses different messages to extract phone numbers\n")

    # Simulate missing only phone number (all other intel collected)
    missing_intel_dict = {
        'bankAccounts': ['123456789'],  # Already have bank
        'ifscCodes': ['SBIN0001234'],   # Already have IFSC
        'upiIds': ['scammer@upi'],      # Already have UPI
        'phoneNumbers': [],              # MISSING - need to extract
        'links': ['http://fake.com']    # Already have link
    }

    # Different scammer messages
    test_scenarios = [
        {
            'scammer_msg': "Send me the OTP code immediately!",
            'context': "Direct credential request"
        },
        {
            'scammer_msg': "Your account will be blocked in 30 minutes.",
            'context': "Urgent threat"
        },
        {
            'scammer_msg': "Please confirm your details for verification.",
            'context': "Polite request"
        },
        {
            'scammer_msg': "I'm here to help you with your account issue.",
            'context': "Helpful tone"
        },
        {
            'scammer_msg': "Congratulations! You've won a prize!",
            'context': "Reward scam"
        },
        {
            'scammer_msg': "This is urgent. Act now or face consequences.",
            'context': "Pressure tactic"
        },
        {
            'scammer_msg': "We need to update your information in our system.",
            'context': "Routine update"
        },
        {
            'scammer_msg': "Click the link to verify your account status.",
            'context': "Link phishing"
        },
        {
            'scammer_msg': "For security purposes, we need to confirm a few things.",
            'context': "Security framing"
        },
        {
            'scammer_msg': "Your payment is pending. Complete the process now.",
            'context': "Payment urgency"
        }
    ]

    print("All scenarios are missing ONLY phone number (all other intel collected)")
    print("="*80 + "\n")

    responses = []
    conversation_history = []

    for idx, scenario in enumerate(test_scenarios, 1):
        print(f"Test {idx}/10: {scenario['context']}")
        print(f"  Scammer: \"{scenario['scammer_msg']}\"")

        # Generate response using heuristic (for consistency)
        response = agent._build_contextual_extraction_heuristic(
            missing_intel_dict=missing_intel_dict,
            scam_type='phishing',
            message=scenario['scammer_msg'],
            conversation_history=conversation_history
        )

        print(f"  Honeypot: \"{response}\"")

        # Check if it asks for phone
        if any(word in response.lower() for word in ['phone', 'number', 'call', 'contact']):
            print(f"  ✅ Asks for phone number\n")
            responses.append(response)
        else:
            print(f"  ⚠️  Doesn't explicitly ask for phone\n")

        # Update conversation
        conversation_history.append({'sender': 'user', 'message': scenario['scammer_msg']})
        conversation_history.append({'sender': 'assistant', 'message': response})

    # Analyze variety
    print("="*80)
    print("VARIETY ANALYSIS")
    print("="*80 + "\n")

    unique_responses = len(set(responses))
    total_responses = len(responses)

    print(f"📊 Statistics:")
    print(f"   • Total responses: {total_responses}")
    print(f"   • Unique responses: {unique_responses}")
    print(f"   • Variety rate: {(unique_responses/total_responses)*100:.0f}%")

    if unique_responses == total_responses:
        print(f"\n✅ PERFECT VARIETY - Every test case got a different message!")
    elif unique_responses >= total_responses * 0.8:
        print(f"\n👍 GOOD VARIETY - {unique_responses} different messages across {total_responses} tests")
    elif unique_responses >= total_responses * 0.5:
        print(f"\n😐 MODERATE VARIETY - Some repetition detected")
    else:
        print(f"\n⚠️  LOW VARIETY - Too much repetition")

    print(f"\n📝 All unique responses generated:")
    print("─" * 80)
    for i, response in enumerate(set(responses), 1):
        print(f"{i}. \"{response}\"")

    print("\n" + "="*80)
    print("HOW VARIETY WORKS")
    print("="*80 + "\n")

    print("🎲 Random Selection from Template Pool:")
    print("   • Bank Account: 8 different templates")
    print("   • IFSC Code: 8 different templates")
    print("   • UPI ID: 14 different templates (7 for payment, 7 for verification)")
    print("   • Phishing Link: 5 different templates")
    print("   • Phone Number: 8 different templates")

    print("\n🔄 Additional Variety Sources:")
    print("   • Emotional prefix varies based on scammer's tone (5 options per emotion)")
    print("   • LLM generates unlimited unique variations (when enabled)")
    print("   • Context-aware selection based on message content")

    print("\n📈 Expected Variety Across Multiple Runs:")
    print("   • Heuristic (same scenario): ~70-80% unique (random.choice)")
    print("   • LLM (same scenario): ~95-100% unique (creative generation)")
    print("   • Different scenarios: 100% unique (different contexts trigger different responses)")

    print("\n" + "="*80 + "\n")

def test_same_scenario_repetition():
    """Test if same scenario produces different messages"""
    agent = AIHoneypotAgent()

    print("\n" + "="*80)
    print("SAME SCENARIO REPETITION TEST")
    print("="*80)
    print("\nRunning the EXACT same scenario 10 times to test variety\n")

    missing_intel_dict = {
        'bankAccounts': ['123'],
        'ifscCodes': ['SBIN'],
        'upiIds': ['scammer@upi'],
        'phoneNumbers': [],  # Missing
        'links': ['http://fake']
    }

    scammer_msg = "Send the OTP immediately!"
    conversation_history = []

    responses = []

    for i in range(10):
        response = agent._build_contextual_extraction_heuristic(
            missing_intel_dict=missing_intel_dict,
            scam_type='phishing',
            message=scammer_msg,
            conversation_history=conversation_history
        )
        responses.append(response)
        print(f"Run {i+1}: \"{response}\"")

    unique = len(set(responses))
    print(f"\n📊 Out of 10 runs: {unique} unique responses ({(unique/10)*100:.0f}% variety)")

    if unique >= 8:
        print("✅ Excellent variety - random.choice() working perfectly!")
    elif unique >= 5:
        print("👍 Good variety - some repetition is normal")
    else:
        print("⚠️  Low variety - may need more template options")

    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    test_phone_extraction_variety()
    test_same_scenario_repetition()
