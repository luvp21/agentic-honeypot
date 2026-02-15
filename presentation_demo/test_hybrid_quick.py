#!/usr/bin/env python3
"""Quick test for hybrid extraction system"""
import asyncio
import sys
import os

# Make sure we can import from current directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_hybrid():
    from ai_agent import AIHoneypotAgent, EXTRACTION_TEMPLATES

    print("\n" + "="*80)
    print("HYBRID SYSTEM TEST")
    print("="*80 + "\n")

    # Test 1: Templates exist
    print(f"✓ Templates loaded: {len(EXTRACTION_TEMPLATES)} categories")
    for cat in EXTRACTION_TEMPLATES.keys():
        print(f"  - {cat}: {len(EXTRACTION_TEMPLATES[cat])} templates")

    # Test 2: Agent initializes
    agent = AIHoneypotAgent()
    print("\n✓ Agent initialized")

    # Test 3: Template selection
    print("\n--- Template Selection Test ---")
    test_msg = "URGENT: Send OTP now!"
    template = agent._select_extraction_template(
        missing_intel_dict={'upiIds': [], 'phoneNumbers': []},
        scam_type='phishing',
        message=test_msg,
        conversation_history=[]
    )
    print(f"Message: '{test_msg}'")
    print(f"✓ Template: {template}")
    has_your = 'YOUR' in template or 'your' in template.lower()
    print(f"  Asks for scammer's info: {'✓' if has_your else '✗'}")

    # Test 4: Loop detection
    print("\n--- Loop Detection Test ---")
    test_response = "What's your phone?"
    history_with_loop = [
        {'sender': 'assistant', 'message': "What's your phone?"},
        {'sender': 'user', 'message': "I don't have one"},
    ]
    loop_detected = agent._detect_response_loop(test_response, history_with_loop)
    print(f"Response: '{test_response}'")
    print(f"History contains same response: Yes")
    print(f"✓ Loop detected: {loop_detected}")

    # Test without loop
    history_no_loop = [
        {'sender': 'assistant', 'message': "What's your UPI?"},
        {'sender': 'user', 'message': "I don't have one"},
    ]
    loop_detected = agent._detect_response_loop(test_response, history_no_loop)
    print(f"✓ Loop not detected when different: {not loop_detected}")

    # Test 5: Full response generation
    print("\n--- Full Response Generation Test ---")
    try:
        test_cases = [
            {
                "message": "Your account will be blocked!",
                "scam_type": "phishing",
                "missing": ['upi_ids', 'phone_numbers']
            },
            {
                "message": "Send ₹500 to claim prize",
                "scam_type": "prize",
                "missing": ['upi_ids']
            },
            {
                "message": "Share your OTP immediately",
                "scam_type": "otp_theft",
                "missing": ['phone_numbers']
            }
        ]

        for i, test in enumerate(test_cases, 1):
            print(f"\nTest {i}: {test['message']}")
            response = await agent.generate_response(
                message=test['message'],
                conversation_history=[],
                scam_type=test['scam_type'],
                missing_intel=test['missing']
            )
            print(f"Response: {response}")

            # Check if it asks for scammer's info
            extraction_keywords = ['your upi', 'your phone', 'your number', 'your account',
                                  'your contact', 'your link']
            asks_for_info = any(word in response.lower() for word in extraction_keywords)

            # Check if complete (not truncated)
            is_complete = len(response) > 20 and not response.endswith('...')

            # Check not confused
            not_confused = 'not sure' not in response.lower() and "don't understand" not in response.lower()

            print(f"  ✓ Asks for scammer info: {asks_for_info}")
            print(f"  ✓ Complete sentence: {is_complete}")
            print(f"  ✓ Not confused: {not_confused}")

            if asks_for_info and is_complete and not_confused:
                print(f"  ✅ TEST {i} PASSED")
            else:
                print(f"  ❌ TEST {i} FAILED")

    except Exception as e:
        print(f"✗ Response generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    return True

if __name__ == "__main__":
    success = asyncio.run(test_hybrid())
    sys.exit(0 if success else 1)
