#!/usr/bin/env python3
"""Final check that everything is working"""
import sys
import asyncio

def check_config():
    """Check gemini_client.py configuration"""
    print("\n" + "="*80)
    print("1. CHECKING GEMINI CLIENT CONFIGURATION")
    print("="*80)

    try:
        from gemini_client import GeminiClient
        client = GeminiClient()

        # Try to access config
        config = client.model._generation_config
        temp = getattr(config, 'temperature', None)
        tokens = getattr(config, 'max_output_tokens', None)

        print(f"Temperature: {temp}", end="")
        if temp and temp >= 0.7:
            print(" ✅ CORRECT (0.7+)")
        else:
            print(f" ❌ WRONG (should be 0.7, is {temp})")
            return False

        print(f"Max tokens: {tokens}", end="")
        if tokens and tokens >= 200:
            print(" ✅ CORRECT (200+)")
        else:
            print(f" ❌ WRONG (should be 200, is {tokens})")
            return False

        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def check_templates():
    """Check extraction templates exist"""
    print("\n" + "="*80)
    print("2. CHECKING EXTRACTION TEMPLATES")
    print("="*80)

    try:
        from ai_agent import EXTRACTION_TEMPLATES

        categories = len(EXTRACTION_TEMPLATES)
        total_templates = sum(len(v) for v in EXTRACTION_TEMPLATES.values())

        print(f"Categories: {categories}", end="")
        if categories == 8:
            print(" ✅ CORRECT")
        else:
            print(f" ❌ WRONG (should be 8)")
            return False

        print(f"Total templates: {total_templates}", end="")
        if total_templates >= 40:
            print(" ✅ CORRECT (40+)")
        else:
            print(f" ⚠️  LOW (should be ~40)")

        # Check specific categories
        required = ['missing_upi', 'missing_phone', 'missing_account',
                   'urgency_response', 'credential_request']
        for cat in required:
            if cat in EXTRACTION_TEMPLATES:
                print(f"  ✓ {cat}: {len(EXTRACTION_TEMPLATES[cat])} templates")
            else:
                print(f"  ✗ {cat}: MISSING!")
                return False

        return True

    except ImportError as e:
        print(f"❌ Cannot import EXTRACTION_TEMPLATES")
        print(f"   Error: {e}")
        print(f"\n   Did you add EXTRACTION_TEMPLATES to ai_agent.py?")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def check_methods():
    """Check new methods exist"""
    print("\n" + "="*80)
    print("3. CHECKING NEW METHODS")
    print("="*80)

    try:
        from ai_agent import AIHoneypotAgent
        agent = AIHoneypotAgent()

        required_methods = [
            '_select_extraction_template',
            '_naturalize_with_llm',
            '_detect_response_loop'
        ]

        all_exist = True
        for method in required_methods:
            if hasattr(agent, method):
                print(f"✅ {method}()")
            else:
                print(f"❌ {method}() - MISSING!")
                all_exist = False

        return all_exist

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

async def check_hybrid_logic():
    """Check hybrid extraction is actually being used"""
    print("\n" + "="*80)
    print("4. CHECKING HYBRID LOGIC INTEGRATION")
    print("="*80)

    try:
        from ai_agent import AIHoneypotAgent
        agent = AIHoneypotAgent()

        # Test extraction with missing intel
        print("Testing hybrid extraction with urgent message...")

        response = await agent.generate_response(
            message="URGENT: Your account will be blocked! Send OTP now!",
            conversation_history=[
                {'sender': 'user', 'message': 'Hello'},
                {'sender': 'assistant', 'message': 'Hi there'}
            ],
            scam_type="phishing",
            missing_intel=['upi_ids', 'phone_numbers'],
            use_competition_prompt=True
        )

        if not response:
            print("❌ No response generated")
            return False

        print(f"\nGenerated response:")
        print(f"  '{response}'")

        # Check quality
        checks = {
            "Not empty": len(response) > 0,
            "Not confused": "i'm not sure" not in response.lower(),
            "Not truncated": len(response) > 20,
            "Asks for info": any(word in response.lower() for word in
                                ['your upi', 'your phone', 'your number',
                                 'your account', 'your contact'])
        }

        print("\nQuality checks:")
        all_passed = True
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check}")
            if not passed:
                all_passed = False

        return all_passed

    except Exception as e:
        print(f"❌ ERROR during extraction test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("\n" + "="*80)
    print("FINAL SYSTEM VERIFICATION")
    print("="*80)

    results = []

    # Check 1: Config
    results.append(("Configuration", check_config()))

    # Check 2: Templates
    results.append(("Templates", check_templates()))

    # Check 3: Methods
    results.append(("Methods", check_methods()))

    # Check 4: Hybrid logic
    results.append(("Hybrid Logic", await check_hybrid_logic()))

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")

    all_passed = all(r[1] for r in results)

    print("\n" + "="*80)
    if all_passed:
        print("🎉 ALL CHECKS PASSED - SYSTEM READY!")
        print("="*80)
        print("\nYour hybrid extraction system is working correctly!")
        print("\nNext steps:")
        print("1. Set GEMINI_API_KEY for full LLM naturalization")
        print("2. Test with real scam messages")
        print("3. Deploy to production")
        print("\nWithout API key, system will use templates directly")
        print("(which still extracts perfectly, just less natural)")
    else:
        print("⚠️  SOME CHECKS FAILED - NEEDS FIXING")
        print("="*80)
        print("\nReview the errors above and fix the failing components.")
        print("Then run this check again.")

    return 0 if all_passed else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
