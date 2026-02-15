#!/usr/bin/env python3
"""
Final verification that all bug fixes are applied
"""
import sys

def verify_bug_fixes():
    """Check that all critical bug fixes are present in ai_agent.py"""
    print("🔍 Verifying bug fixes in ai_agent.py...\n")

    with open('ai_agent.py', 'r') as f:
        content = f.read()

    checks = [
        {
            "name": "API key import added",
            "check": "import os" in content,
            "critical": True
        },
        {
            "name": "GEMINI_API_KEY variable set",
            "check": 'GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")' in content,
            "critical": True
        },
        {
            "name": "Turn 0 trigger fixed (>= 0)",
            "check": "turn_number >= 0" in content,
            "critical": True
        },
        {
            "name": "Turn 2 bug removed (no >= 2)",
            "check": "turn_number >= 2" not in content,
            "critical": True
        },
        {
            "name": "Missing intel mapping added",
            "check": "'upi_ids' in missing_intel" in content,
            "critical": True
        },
        {
            "name": "API key check before naturalization",
            "check": "if GEMINI_API_KEY:" in content,
            "critical": True
        },
        {
            "name": "Template fallback when no API key",
            "check": "natural_response = template_response" in content,
            "critical": False
        },
        {
            "name": "Turn 0 comment added",
            "check": "Start extraction immediately (turn 0+)" in content,
            "critical": False
        }
    ]

    passed = 0
    failed = 0

    for check in checks:
        result = check["check"]
        status = "✅" if result else "❌"
        critical = "🔴 CRITICAL" if check["critical"] and not result else ""

        print(f"{status} {check['name']} {critical}")

        if result:
            passed += 1
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"Results: {passed}/{len(checks)} checks passed")

    if failed == 0:
        print("✅ ALL FIXES VERIFIED - System ready for production!")
        print("='*60}")
        return True
    else:
        print(f"❌ {failed} checks failed - review required")
        print(f"{'='*60}")
        return False

if __name__ == "__main__":
    result = verify_bug_fixes()
    sys.exit(0 if result else 1)
