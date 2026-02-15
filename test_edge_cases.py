#!/usr/bin/env python3
"""
Edge Case Test Scenarios for Honeypot
Testing polite scammers, indirect manipulation, and non-obvious scam patterns
"""
import asyncio
import sys
sys.path.insert(0, '/home/luv/Desktop/files')

from ai_agent import AIHoneypotAgent

# Edge case scenarios that might bypass current detection
EDGE_CASE_SCENARIOS = [
    {
        'name': 'Polite Professional (No Scam Keywords)',
        'category': 'Subtle Manipulation',
        'messages': [
            "Good morning! I'm calling from your bank's customer service. How are you today?",
            "Thank you for your patience. We're conducting a routine security audit of all accounts.",
            "For verification purposes, could you please confirm your account number with me?",
            "Perfect, thank you. And which branch do you primarily use for your transactions?",
            "I see. For our records, what payment apps do you typically use for transfers?",
        ],
        'characteristics': {
            'polite': True,
            'no_urgency': True,
            'low_keyword_density': True,
            'professional_tone': True,
            'indirect_extraction': True
        },
        'challenge': 'No scam keywords, polite tone - might not trigger heuristic patterns'
    },

    {
        'name': 'Social Engineering (Building Trust)',
        'category': 'Trust-Based Manipulation',
        'messages': [
            "Hello! I hope you're having a wonderful day. I'm reaching out regarding an important matter.",
            "I completely understand your concerns. We take security very seriously here.",
            "You seem like a careful person, which is excellent. Many people aren't as vigilant as you.",
            "I appreciate your cooperation. To ensure your account remains safe, I just need a few details.",
            "Your vigilance is commendable. Now, for the final verification step...",
        ],
        'characteristics': {
            'trust_building': True,
            'compliments': True,
            'empathy': True,
            'no_pressure': True,
            'delayed_request': True
        },
        'challenge': 'Builds emotional connection before extracting - low keyword density across conversation'
    },

    {
        'name': 'Technical Support (Helpful Tone)',
        'category': 'Assistance Scam',
        'messages': [
            "Hello, I'm here to help you resolve an issue with your account.",
            "No worries at all, I'll guide you through this step by step. Take your time.",
            "Let's start simple. Can you tell me which bank you use for most transactions?",
            "Great! Now, for me to access your account details on my end, I'll need some information.",
            "Don't worry, this is a secure line. What's the best number to reach you at if we get disconnected?",
        ],
        'characteristics': {
            'helpful': True,
            'patient': True,
            'step_by_step': True,
            'reassuring': True,
            'technical_jargon': False
        },
        'challenge': 'Sounds genuinely helpful - no threatening keywords, low urgency'
    },

    {
        'name': 'Prize Winner (Congratulatory)',
        'category': 'Reward Scam',
        'messages': [
            "Congratulations! You've been selected as a winner in our customer appreciation program!",
            "This is wonderful news! You're one of our valued customers.",
            "To process your reward, I just need to verify a few details with you.",
            "Excellent! For the prize transfer, which payment method would you prefer?",
            "Perfect choice! I'll need your payment details to credit the amount directly.",
        ],
        'characteristics': {
            'positive_tone': True,
            'no_threats': True,
            'reward_focused': True,
            'friendly': True,
            'casual_extraction': True
        },
        'challenge': 'Positive framing, no urgency - victim feels happy, not threatened'
    },

    {
        'name': 'Survey Research (Information Gathering)',
        'category': 'Data Collection Scam',
        'messages': [
            "Good afternoon! I'm conducting a quick survey on behalf of banking institutions.",
            "It'll only take 2 minutes. Your responses will help improve banking services.",
            "First question: What type of account do you primarily use for daily transactions?",
            "Thank you. And which digital payment platforms do you use most frequently?",
            "Last question: For quality assurance, may I have a contact number to follow up?",
        ],
        'characteristics': {
            'survey_format': True,
            'legitimate_sounding': True,
            'gradual_extraction': True,
            'time_bound': True,
            'opt_in_feeling': True
        },
        'challenge': 'Sounds like legitimate market research - indirect information gathering'
    },

    {
        'name': 'Vague Threat (Implicit Urgency)',
        'category': 'Subtle Pressure',
        'messages': [
            "I'm calling about some unusual activity we noticed on your account.",
            "It's probably nothing to worry about, but we do need to verify a few things.",
            "We've had similar cases recently. Better to be safe than sorry, right?",
            "For your protection, let's just confirm your account details quickly.",
            "This won't take long. I just need to verify the information we have on file.",
        ],
        'characteristics': {
            'implicit_threat': True,
            'soft_pressure': True,
            'safety_framing': True,
            'casual_urgency': True,
            'minimal_keywords': True
        },
        'challenge': 'Implied urgency without direct threats - "unusual activity" but no "blocked/suspended"'
    },

    {
        'name': 'Callback Request (Minimal Message)',
        'category': 'Short Message Scam',
        'messages': [
            "Hi, this is from your bank. Please call back at your earliest convenience.",
            "Thank you for calling back. We need to discuss your account.",
            "It's regarding a recent transaction. Do you have a moment?",
            "For verification, could you confirm your account number?",
            "Thank you. And what's the best contact number for you?",
        ],
        'characteristics': {
            'brief_messages': True,
            'callback_pattern': True,
            'minimal_info': True,
            'reactive_approach': True,
            'low_word_count': True
        },
        'challenge': 'Very short messages (< 15 words) but not urgent - might bypass current checks'
    },

    {
        'name': 'Authority Figure (Government/Police)',
        'category': 'Authority Abuse',
        'messages': [
            "This is Officer Kumar from the Cyber Crime Division. I need to speak with you.",
            "We're investigating a case of identity theft linked to your bank account.",
            "For your own safety, I need you to cooperate fully with this investigation.",
            "I'll need your account details to verify if your information has been compromised.",
            "This is a serious matter. What's your registered mobile number for the account?",
        ],
        'characteristics': {
            'authority_claim': True,
            'legal_framing': True,
            'serious_tone': True,
            'investigation_context': True,
            'compliance_pressure': True
        },
        'challenge': 'Authority figure but lower keyword density - investigation context is different from "blocked account"'
    },

    {
        'name': 'Friend Referral (Trust Transfer)',
        'category': 'Social Engineering',
        'messages': [
            "Hello! Your friend Rajesh gave me your number. He said you might be interested in our offer.",
            "He's already signed up and is quite happy with the returns.",
            "It's a great investment opportunity. Very simple process to get started.",
            "I just need some basic details to set up your account.",
            "Your friend mentioned you're quite savvy. What's your preferred payment method?",
        ],
        'characteristics': {
            'referral_based': True,
            'social_proof': True,
            'investment_focus': True,
            'casual_tone': True,
            'trust_by_association': True
        },
        'challenge': 'No bank-related keywords, sounds like legitimate business opportunity'
    },

    {
        'name': 'Multi-Stage Setup (Slow Burn)',
        'category': 'Long-term Grooming',
        'messages': [
            "Hi, I'm following up on the email we sent last week about account upgrades.",
            "Many customers have benefited from our premium features. Are you interested in learning more?",
            "Great! Let me explain the benefits. It includes better interest rates and cashback.",
            "To upgrade your account, I'll need to verify your current account details first.",
            "Perfect. And for the final step, I'll need your UPI ID for the activation bonus.",
        ],
        'characteristics': {
            'multi_stage': True,
            'previous_contact_claim': True,
            'upgrade_pitch': True,
            'benefit_focused': True,
            'gradual_commitment': True
        },
        'challenge': 'References previous contact (fake), builds over multiple stages, low threat level'
    }
]

async def test_edge_cases():
    agent = AIHoneypotAgent()

    print("\n" + "="*80)
    print("EDGE CASE TESTING - Polite & Indirect Scam Patterns")
    print("="*80)
    print("\nTesting honeypot against non-obvious scam tactics\n")

    total_scenarios = len(EDGE_CASE_SCENARIOS)
    passed_scenarios = 0
    failed_scenarios = []

    for idx, scenario in enumerate(EDGE_CASE_SCENARIOS, 1):
        print(f"\n{'='*80}")
        print(f"SCENARIO {idx}/{total_scenarios}: {scenario['name']}")
        print(f"Category: {scenario['category']}")
        print(f"{'='*80}")

        print(f"\n🎯 Challenge: {scenario['challenge']}")
        print(f"\n📋 Characteristics:")
        for key, value in scenario['characteristics'].items():
            print(f"   • {key.replace('_', ' ').title()}: {value}")

        print(f"\n💬 Conversation Flow:")
        print("─" * 80)

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
            print(f"\nTurn {turn}:")
            print(f"  Scammer: \"{scammer_msg}\"")

            # Determine routing
            use_llm = agent._should_use_llm_for_extraction(
                message=scammer_msg,
                turn_number=turn,
                missing_intel_dict=missing_intel_dict,
                conversation_history=conversation_history
            )

            method = "🤖 LLM" if use_llm else "⚡ HEUR"
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

            print(f"  Honeypot ({method}): \"{response}\"")

            # Check if response asks for information
            response_lower = response.lower()
            asks_for_info = any(pattern in response_lower for pattern in [
                'your account', 'your upi', 'your phone', 'your number',
                'your ifsc', 'your bank', 'your details', 'your contact',
                'what is your', 'what\'s your', 'share your'
            ])

            if asks_for_info:
                extraction_count += 1
                print(f"  ✅ Extraction attempt detected")
            else:
                print(f"  ⚠️  No extraction detected")

            # Update conversation
            conversation_history.append({'sender': 'user', 'message': scammer_msg})
            conversation_history.append({'sender': 'assistant', 'message': response})

        # Evaluate scenario
        print(f"\n{'─'*80}")
        print(f"📊 Scenario Results:")
        print(f"   • Total Turns: {len(scenario['messages'])}")
        print(f"   • Extraction Attempts: {extraction_count}/{len(scenario['messages'])}")
        print(f"   • LLM Responses: {llm_count}")
        print(f"   • Heuristic Responses: {heuristic_count}")

        # Success criteria: At least 80% of responses should attempt extraction
        success_rate = (extraction_count / len(scenario['messages'])) * 100
        print(f"   • Extraction Success Rate: {success_rate:.1f}%")

        if success_rate >= 80:
            print(f"   ✅ PASSED - Honeypot handled this edge case well")
            passed_scenarios += 1
        else:
            print(f"   ❌ FAILED - Low extraction rate for edge case")
            failed_scenarios.append({
                'name': scenario['name'],
                'success_rate': success_rate,
                'llm_count': llm_count,
                'heuristic_count': heuristic_count
            })

    # Final summary
    print("\n" + "="*80)
    print("EDGE CASE TESTING SUMMARY")
    print("="*80)
    print(f"\n✅ Passed: {passed_scenarios}/{total_scenarios}")
    print(f"❌ Failed: {len(failed_scenarios)}/{total_scenarios}")

    if failed_scenarios:
        print(f"\n⚠️  FAILED SCENARIOS:")
        for fail in failed_scenarios:
            print(f"\n   • {fail['name']}")
            print(f"     - Success Rate: {fail['success_rate']:.1f}%")
            print(f"     - LLM: {fail['llm_count']}, Heuristic: {fail['heuristic_count']}")
            print(f"     - Issue: Need better handling for this pattern")

    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)

    if len(failed_scenarios) > 0:
        print("\n🔧 Improvements Needed:")
        print("   1. Enhance LLM routing for polite/subtle scammers")
        print("   2. Add indirect extraction patterns to heuristic templates")
        print("   3. Improve detection of trust-building tactics")
        print("   4. Handle multi-stage scams with memory of previous turns")
        print("   5. Better extraction for brief/callback messages")
    else:
        print("\n🎉 All edge cases handled successfully!")
        print("   Current hybrid system is robust against subtle manipulation tactics")

    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(test_edge_cases())
