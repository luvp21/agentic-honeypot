#!/usr/bin/env python3
"""
Final Verification Script - Run before submission
Checks all critical requirements are met
"""

import json
import sys
import os
from pathlib import Path

def check_file_exists(filename):
    """Check if a required file exists"""
    exists = Path(filename).exists()
    status = "✅" if exists else "❌"
    print(f"{status} {filename}")
    return exists

def check_models_structure():
    """Verify FinalCallbackPayload doesn't have totalMessagesExchanged at top level"""
    print("\n🔍 Checking FinalCallbackPayload structure...")

    try:
        from models import FinalCallbackPayload, ExtractedIntelligence, EngagementMetrics

        payload = FinalCallbackPayload(
            sessionId="test",
            status="completed",
            scamDetected=True,
            extractedIntelligence=ExtractedIntelligence(),
            engagementMetrics=EngagementMetrics(
                totalMessagesExchanged=10,
                engagementDurationSeconds=60
            ),
            agentNotes="test"
        )

        payload_dict = payload.model_dump()

        # Check top-level fields
        expected_fields = {'sessionId', 'status', 'scamDetected', 'extractedIntelligence', 'engagementMetrics', 'agentNotes'}
        actual_fields = set(payload_dict.keys())

        if actual_fields == expected_fields:
            print("✅ Top-level fields correct:", list(actual_fields))
        else:
            print("❌ Top-level fields incorrect!")
            print(f"   Expected: {expected_fields}")
            print(f"   Got: {actual_fields}")
            return False

        # CRITICAL: Check totalMessagesExchanged is NOT at top level
        if 'totalMessagesExchanged' in payload_dict:
            print("❌ CRITICAL ERROR: 'totalMessagesExchanged' found at top level!")
            return False
        else:
            print("✅ 'totalMessagesExchanged' NOT at top level (correct)")

        # Check it IS in engagementMetrics
        if 'totalMessagesExchanged' in payload_dict.get('engagementMetrics', {}):
            print("✅ 'totalMessagesExchanged' found in engagementMetrics (correct)")
        else:
            print("❌ 'totalMessagesExchanged' NOT in engagementMetrics!")
            return False

        print("✅ FinalCallbackPayload structure is CORRECT")
        return True

    except Exception as e:
        print(f"❌ Error checking models: {e}")
        return False

def check_requirements():
    """Check requirements.txt has all dependencies"""
    print("\n📦 Checking requirements.txt...")

    required_packages = ['fastapi', 'uvicorn', 'pydantic', 'google-generativeai', 'requests']

    try:
        with open('requirements.txt', 'r') as f:
            content = f.read()

        missing = []
        for pkg in required_packages:
            if pkg in content:
                print(f"✅ {pkg}")
            else:
                print(f"❌ {pkg} missing")
                missing.append(pkg)

        return len(missing) == 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_readme():
    """Check README has essential sections"""
    print("\n📖 Checking README.md...")

    try:
        with open('README.md', 'r') as f:
            content = f.read().lower()

        essential_sections = [
            ('features', 'Features section'),
            ('api', 'API documentation'),
            ('setup', 'Setup instructions'),
            ('usage', 'Usage section')
        ]

        for keyword, name in essential_sections:
            if keyword in content:
                print(f"✅ {name}")
            else:
                print(f"⚠️  {name} not found (recommended)")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def run_verification():
    """Run all verification checks"""

    print("=" * 60)
    print("🔍 FINAL VERIFICATION - SUBMISSION READINESS CHECK")
    print("=" * 60)

    results = []

    # Check required files
    print("\n📂 Checking Required Files...")
    required_files = [
        'main.py',
        'callback.py',
        'models.py',
        'requirements.txt',
        'Dockerfile',
        'README.md'
    ]

    for file in required_files:
        results.append(check_file_exists(file))

    # Check model structure
    results.append(check_models_structure())

    # Check requirements
    results.append(check_requirements())

    # Check README
    results.append(check_readme())

    # Summary
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"\nChecks Passed: {passed}/{total}")

    if all(results):
        print("\n🎉 ALL CHECKS PASSED - SUBMISSION READY!")
        print("\nNext Steps:")
        print("1. Deploy to cloud platform (Railway/Render/GCP)")
        print("2. Test deployed endpoint")
        print("3. Push to GitHub and make repository PUBLIC")
        print("4. Submit on hackathon platform")
        return 0
    else:
        print("\n⚠️  SOME CHECKS FAILED - FIX ISSUES BEFORE SUBMISSION")
        return 1

if __name__ == "__main__":
    exit_code = run_verification()
    sys.exit(exit_code)
