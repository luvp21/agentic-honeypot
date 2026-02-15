#!/usr/bin/env python3
"""
Diagnose your current codebase structure
Run this to understand your setup before implementing fixes
"""

import sys
import os
import inspect

print("="*80)
print("CODEBASE DIAGNOSTIC TOOL")
print("="*80 + "\n")

# Check 1: Find and analyze gemini_client.py
print("📁 CHECK 1: Gemini Client Analysis")
print("-" * 80)

try:
    from gemini_client import GeminiClient

    print("✅ gemini_client.py found and imports successfully")

    # Check methods
    client = GeminiClient()
    methods = [method for method in dir(client) if not method.startswith('_')]
    print(f"📋 Available methods: {', '.join(methods)}")

    # Check if methods are async
    for method_name in ['generate_text', 'generate_response', 'generate']:
        if hasattr(client, method_name):
            method = getattr(client, method_name)
            is_async = inspect.iscoroutinefunction(method)
            print(f"   - {method_name}(): {'async' if is_async else 'sync'}")

    # Check model config
    if hasattr(client, 'model'):
        config = client.model._generation_config if hasattr(client.model, '_generation_config') else None
        if config:
            print(f"⚙️  Current config:")
            print(f"   - Temperature: {getattr(config, 'temperature', 'unknown')}")
            print(f"   - Max tokens: {getattr(config, 'max_output_tokens', 'unknown')}")

except ImportError as e:
    print(f"❌ Cannot import gemini_client: {e}")
    print("   Make sure gemini_client.py exists in the same directory")
except Exception as e:
    print(f"⚠️  Import succeeded but error analyzing: {e}")

print()

# Check 2: Find and analyze ai_agent.py
print("🤖 CHECK 2: AI Agent Analysis")
print("-" * 80)

try:
    from ai_agent import AIAgent

    print("✅ ai_agent.py found and imports successfully")

    # Check main method
    agent = AIAgent()

    if hasattr(agent, 'generate_response'):
        method = agent.generate_response
        is_async = inspect.iscoroutinefunction(method)
        print(f"📋 generate_response(): {'async' if is_async else 'sync'}")

        # Try to get signature
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())
        print(f"   Parameters: {', '.join(params)}")

    # Check for key methods
    key_methods = [
        '_generate_rule_based_response',
        '_generate_llm_response',
        '_build_competition_llm_prompt',
        'EXTRACTION_TEMPLATES'
    ]

    print(f"📋 Key components present:")
    for item in key_methods:
        exists = hasattr(agent, item) or hasattr(AIAgent, item)
        print(f"   {'✅' if exists else '❌'} {item}")

except ImportError as e:
    print(f"❌ Cannot import ai_agent: {e}")
except Exception as e:
    print(f"⚠️  Import succeeded but error analyzing: {e}")

print()

# Check 3: Detect async patterns
print("🔄 CHECK 3: Async/Await Detection")
print("-" * 80)

async_keywords_found = False
files_to_check = ['ai_agent.py', 'gemini_client.py', 'main.py']

for filename in files_to_check:
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            content = f.read()
            has_async = 'async def' in content
            has_await = 'await ' in content
            has_asyncio = 'import asyncio' in content

            if has_async or has_await or has_asyncio:
                print(f"📄 {filename}:")
                print(f"   - async def: {'✅ Found' if has_async else '❌ Not found'}")
                print(f"   - await calls: {'✅ Found' if has_await else '❌ Not found'}")
                print(f"   - asyncio import: {'✅ Found' if has_asyncio else '❌ Not found'}")
                async_keywords_found = True

if not async_keywords_found:
    print("✅ No async patterns detected - codebase is SYNCHRONOUS")
else:
    print("⚠️  Async patterns detected - codebase uses ASYNC/AWAIT")

print()

# Check 4: Current extraction logic
print("🎯 CHECK 4: Current Extraction Logic")
print("-" * 80)

try:
    with open('ai_agent.py', 'r') as f:
        content = f.read()

        # Check if rule-based is enabled
        if 'if False:  # DISABLED' in content:
            print("⚠️  Rule-based extraction is DISABLED (if False)")
        elif 'use_llm_for_extraction = True' in content:
            print("⚠️  LLM-only mode is ACTIVE")

        # Check for hybrid approach
        if 'HYBRID_EXTRACTION' in content:
            print("✅ Hybrid approach already implemented")
        else:
            print("❌ Hybrid approach NOT implemented yet")

        # Check temperature and tokens
        with open('gemini_client.py', 'r') as g:
            gemini_content = g.read()

            import re
            temp_match = re.search(r'"temperature":\s*([\d.]+)', gemini_content)
            token_match = re.search(r'"max_output_tokens":\s*(\d+)', gemini_content)

            if temp_match:
                temp = float(temp_match.group(1))
                print(f"⚙️  Current temperature: {temp} {'⚠️ TOO LOW (causes loops)' if temp < 0.5 else '✅ Good'}")

            if token_match:
                tokens = int(token_match.group(1))
                print(f"⚙️  Current max_tokens: {tokens} {'⚠️ TOO LOW (causes truncation)' if tokens < 200 else '✅ Good'}")

except FileNotFoundError:
    print("❌ Could not find ai_agent.py or gemini_client.py")
except Exception as e:
    print(f"⚠️  Error analyzing files: {e}")

print()

# Summary
print("="*80)
print("🎯 SUMMARY & RECOMMENDATION")
print("="*80)
print()
print("Based on the analysis above, you need to:")
print()
print("1. Share these specific sections from your code:")
print("   - gemini_client.py: The GeminiClient class definition")
print("   - ai_agent.py: The imports and generate_response function")
print()
print("2. Or just tell me:")
print("   - Is your code async or sync? (Look at CHECK 3 above)")
print("   - What method do you use to call Gemini? (Look at CHECK 1 above)")
print()
print("Then I'll give you EXACT fixes that will work with your setup!")
print()
