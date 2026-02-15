#!/usr/bin/env python3
"""
Advanced Edge Cases - Ultra-Sophisticated Scam Tactics
Testing against the most subtle and manipulative scam patterns
"""
import asyncio
import sys
sys.path.insert(0, '/home/luv/Desktop/files')

from ai_agent import AIHoneypotAgent

ADVANCED_SCENARIOS = [
    {
        'name': 'Silent Treatment (Minimal Engagement)',
        'messages': [
            "Hi.",
            "Yes.",
            "Okay.",
            "Confirm your details.",
            "Send it now."
        ],
        'challenge': 'Extremely brief messages, no context, minimal keywords'
    },

    {
        'name': 'Relationship Building (Romance Scam)',
        'messages': [
            "I saw your profile and you seem like such a kind person.",
            "I'd love to get to know you better. Tell me about yourself.",
            "You're so wonderful to talk to. I feel like we have a connection.",
            "I'm going through some financial difficulties. Could you help me?",
            "Just need your account details to receive the transfer you offered."
        ],
        'challenge': 'Emotional manipulation, delayed extraction, relationship-focused'
    },

    {
        'name': 'Tech Support (Specific Instructions)',
        'messages': [
            "Hello, Microsoft support here. Your computer has virus alerts.",
            "Please go to your computer and open the browser.",
            "Type in this address and download the remote access tool.",
            "Now I'll need admin access. What's your Windows password?",
            "For billing, provide your payment method for the service."
        ],
        'challenge': 'Step-by-step instructions, technical jargon, delayed credential request'
    },

    {
        'name': 'Fake Job Offer (Professional Recruitment)',
        'messages': [
            "We're impressed with your background and would like to offer you a position.",
            "The salary is excellent with full benefits. Are you interested in proceeding?",
            "Great! We'll need to process your employment paperwork.",
            "For the offer letter, please provide your bank account for salary deposits.",
            "Also, there's a small processing fee. What's your preferred payment method?"
        ],
        'challenge': 'Professional tone, job offer premise, gradual commitment escalation'
    },

    {
        'name': 'Charity Donation (Emotional Appeal)',
        'messages': [
            "We're raising funds for children's education in rural areas.",
            "Your small contribution can change a child's life. Will you help?",
            "Thank you for your generosity! Every rupee counts.",
            "To process your donation, I'll need your account details.",
            "Perfect. And your PAN number for the tax exemption certificate?"
        ],
        'challenge': 'Emotional appeal, charity premise, goodwill exploitation'
    },

    {
        'name': 'Medical Emergency (Family Crisis)',
        'messages': [
            "This is the hospital calling about your family member's emergency.",
            "They need immediate surgery. It's critical.",
            "The procedure costs ₹2 lakhs. We need advance payment right away.",
            "For the payment, what's your account or UPI details?",
            "Hurry, every minute counts for their survival."
        ],
        'challenge': 'Extreme urgency, family crisis, emotional pressure, life-threatening context'
    },

    {
        'name': 'Government Official (Tax/Legal)',
        'messages': [
            "Income Tax Department calling regarding discrepancies in your returns.",
            "You have unpaid taxes of ₹50,000. Legal action will be initiated.",
            "To avoid arrest, you must settle this immediately.",
            "Provide your bank details for the payment settlement.",
            "This is your final notice. Penalties increase after today."
        ],
        'challenge': 'Authority figure, legal threats, tax context, arrest fear'
    },

    {
        'name': 'Package Delivery (Logistics Scam)',
        'messages': [
            "We have a package for you but delivery failed due to incorrect address.",
            "Please confirm your details to reschedule delivery.",
            "There's also a small customs fee of ₹500 to be paid.",
            "For the payment, share your card details or UPI.",
            "The package contains valuable items. Don't you want to receive it?"
        ],
        'challenge': 'Delivery premise, small payment request, package incentive'
    },

    {
        'name': 'Cryptocurrency Investment (Tech-Savvy)',
        'messages': [
            "Amazing Bitcoin investment opportunity with 300% returns guaranteed.",
            "I've made ₹10 lakhs in just 2 months using this platform.",
            "Minimum investment is only ₹5,000. Want to start small?",
            "Create your wallet by sharing your mobile number and email.",
            "For the initial deposit, what's your preferred payment method?"
        ],
        'challenge': 'Investment scam, tech buzzwords, guaranteed returns, FOMO tactics'
    },

    {
        'name': 'Blackmail/Sextortion (Threat-Based)',
        'messages': [
            "I have compromising videos of you from your webcam.",
            "If you don't pay ₹50,000, I'll send these to all your contacts.",
            "You have 24 hours to comply or I'll release everything.",
            "Send the payment to this account or face public humiliation.",
            "Tick tock. Time is running out. Make the transfer now."
        ],
        'challenge': 'Severe threats, blackmail, short deadline, privacy violation fear'
    }
]

async def test_advanced_scenarios():
    agent = AIHoneypotAgent()

    print("\n" + "="*80)
    print("ADVANCED EDGE CASE TESTING")
    print("Ultra-Sophisticated & Manipulative Scam Tactics")
    print("="*80 + "\n")

    results = []

    for idx, scenario in enumerate(ADVANCED_SCENARIOS, 1):
        print(f"{'='*80}")
        print(f"SCENARIO {idx}/10: {scenario['name']}")
        print(f"{'='*80}")
        print(f"🎯 Challenge: {scenario['challenge']}\n")

        conversation_history = []
        missing_intel_dict = {
            'bankAccounts': [],
            'ifscCodes': [],
            'upiIds': [],
            'phoneNumbers': [],
            'links': []
        }

        extraction_count = 0
        llm_count = 0
        heuristic_count = 0

        for turn, scammer_msg in enumerate(scenario['messages'], 1):
            # Determine routing
            use_llm = agent._should_use_llm_for_extraction(
                message=scammer_msg,
                turn_number=turn,
                missing_intel_dict=missing_intel_dict,
                conversation_history=conversation_history
            )

            if use_llm:
                llm_count += 1
            else:
                heuristic_count += 1

            # Generate response
            if use_llm:
                try:
                    response = await agent._build_contextual_extraction_llm(
                        missing_intel_dict=missing_intel_dict,
                        scam_type='phishing',
                        message=scammer_msg,
                        conversation_history=conversation_history
                    )
                except:
                    response = agent._build_contextual_extraction_heuristic(
                        missing_intel_dict=missing_intel_dict,
                        scam_type='phishing',
                        message=scammer_msg,
                        conversation_history=conversation_history
                    )
            else:
                response = agent._build_contextual_extraction_heuristic(
                    missing_intel_dict=missing_intel_dict,
                    scam_type='phishing',
                    message=scammer_msg,
                    conversation_history=conversation_history
                )

            # Check extraction
            response_lower = response.lower()
            asks_for_info = any(pattern in response_lower for pattern in [
                'your account', 'your upi', 'your phone', 'your number',
                'your ifsc', 'your bank', 'your details', 'your contact'
            ])

            if asks_for_info:
                extraction_count += 1

            conversation_history.append({'sender': 'user', 'message': scammer_msg})
            conversation_history.append({'sender': 'assistant', 'message': response})

        success_rate = (extraction_count / len(scenario['messages'])) * 100

        results.append({
            'name': scenario['name'],
            'extraction_rate': success_rate,
            'llm_count': llm_count,
            'heuristic_count': heuristic_count,
            'passed': success_rate >= 80
        })

        status = "✅ PASSED" if success_rate >= 80 else "❌ FAILED"
        print(f"{status} - Extraction: {extraction_count}/5 ({success_rate:.0f}%)")
        print(f"   LLM: {llm_count} | Heuristic: {heuristic_count}\n")

    # Summary
    print("="*80)
    print("ADVANCED TESTING SUMMARY")
    print("="*80)

    passed = sum(1 for r in results if r['passed'])
    print(f"\n✅ Passed: {passed}/10")
    print(f"❌ Failed: {10 - passed}/10\n")

    if passed == 10:
        print("🎉 EXCELLENT! System handles all sophisticated manipulation tactics!")
    elif passed >= 8:
        print("👍 GOOD! System is robust against most advanced scams")
    else:
        print("⚠️  NEEDS IMPROVEMENT - Some sophisticated tactics bypass detection")

    print("\n" + "="*80)
    print("DETAILED RESULTS")
    print("="*80 + "\n")

    for result in results:
        status_icon = "✅" if result['passed'] else "❌"
        print(f"{status_icon} {result['name']}")
        print(f"   Extraction Rate: {result['extraction_rate']:.0f}%")
        print(f"   LLM: {result['llm_count']}, Heuristic: {result['heuristic_count']}")
        if not result['passed']:
            print(f"   ⚠️  Low extraction - needs better handling\n")
        else:
            print()

    print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(test_advanced_scenarios())
