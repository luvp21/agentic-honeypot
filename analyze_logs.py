#!/usr/bin/env python3
"""
Hackathon Log Analyzer
Analyzes performance logs after test runs to identify optimization opportunities
"""

import json
import sys
from collections import defaultdict, Counter
from datetime import datetime


def analyze_performance_logs(log_file="hackathon_performance.log"):
    """Analyze performance logs and generate insights"""

    # Metrics
    sessions = set()
    llm_count = 0
    rule_count = 0
    strategy_override_count = 0
    llm_failures = []
    extractions_by_type = Counter()
    extractions_by_turn = defaultdict(int)
    callbacks = {"success": 0, "failed": 0}
    response_times = []
    scam_types = Counter()
    finalization_triggers = Counter()
    strategy_changes = []

    try:
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    # Parse different log types
                    if "GENERATION:" in line:
                        data = json.loads(line.split("GENERATION: ")[1])
                        sessions.add(data["session_id"])

                        if data["method"] == "LLM_GEMINI":
                            llm_count += 1
                        elif data["method"] == "RULE_BASED":
                            rule_count += 1
                        elif data["method"] == "STRATEGY_OVERRIDE":
                            strategy_override_count += 1

                    elif "EXTRACTION:" in line:
                        data = json.loads(line.split("EXTRACTION: ")[1])
                        for intel_type in data["types"]:
                            extractions_by_type[intel_type] += 1
                        extractions_by_turn[data["turn"]] += data["count"]

                    elif "LLM_FAILURE:" in line:
                        data = json.loads(line.split("LLM_FAILURE: ")[1])
                        llm_failures.append(data)

                    elif "CALLBACK:" in line:
                        data = json.loads(line.split("CALLBACK: ")[1])
                        if data["success"]:
                            callbacks["success"] += 1
                        else:
                            callbacks["failed"] += 1

                    elif "API:" in line:
                        data = json.loads(line.split("API: ")[1])
                        response_times.append(data["response_time_ms"])

                    elif "DETECTION:" in line:
                        data = json.loads(line.split("DETECTION: ")[1])
                        scam_types[data["scam_type"]] += 1

                    elif "FINALIZATION:" in line:
                        data = json.loads(line.split("FINALIZATION: ")[1])
                        finalization_triggers[data["trigger"]] += 1

                    elif "STRATEGY:" in line:
                        data = json.loads(line.split("STRATEGY: ")[1])
                        strategy_changes.append(data)

                except (json.JSONDecodeError, KeyError, IndexError):
                    continue

        # Calculate metrics
        total_generations = llm_count + rule_count + strategy_override_count
        llm_percentage = (llm_count / total_generations * 100) if total_generations > 0 else 0
        rule_percentage = (rule_count / total_generations * 100) if total_generations > 0 else 0

        callback_total = callbacks["success"] + callbacks["failed"]
        callback_success_rate = (callbacks["success"] / callback_total * 100) if callback_total > 0 else 0

        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)] if response_times else 0

        # Print analysis report
        print("\n" + "="*80)
        print("🎯 HACKATHON PERFORMANCE ANALYSIS REPORT")
        print("="*80 + "\n")

        print(f"📊 OVERALL METRICS")
        print(f"   Total Sessions: {len(sessions)}")
        print(f"   Total Generations: {total_generations}")
        print(f"   Total Extractions: {sum(extractions_by_type.values())}")
        print(f"   Total Callbacks: {callback_total}\n")

        print(f"🤖 GENERATION METHOD BREAKDOWN")
        print(f"   LLM (Gemini): {llm_count} ({llm_percentage:.1f}%)")
        print(f"   Rule-Based: {rule_count} ({rule_percentage:.1f}%)")
        print(f"   Strategy Override: {strategy_override_count}")
        print(f"   LLM Failures: {len(llm_failures)}\n")

        if llm_failures:
            print(f"⚠️  LLM FAILURE ANALYSIS")
            for failure in llm_failures[:5]:  # Show first 5
                print(f"   Turn {failure['turn']}: {failure['error'][:60]}... → {failure['fallback']}")
            if len(llm_failures) > 5:
                print(f"   ... and {len(llm_failures) - 5} more failures\n")

        print(f"🔍 INTELLIGENCE EXTRACTION")
        for intel_type, count in extractions_by_type.most_common():
            print(f"   {intel_type}: {count}")
        print()

        print(f"📞 CALLBACK PERFORMANCE")
        print(f"   Success: {callbacks['success']}")
        print(f"   Failed: {callbacks['failed']}")
        print(f"   Success Rate: {callback_success_rate:.1f}%\n")

        print(f"⚡ API RESPONSE TIMES")
        print(f"   Average: {avg_response_time:.0f}ms")
        print(f"   P95: {p95_response_time:.0f}ms\n")

        print(f"🎭 SCAM TYPE DISTRIBUTION")
        for scam_type, count in scam_types.most_common():
            print(f"   {scam_type}: {count}")
        print()

        print(f"🏁 FINALIZATION TRIGGERS")
        for trigger, count in finalization_triggers.most_common():
            print(f"   {trigger}: {count}")
        print()

        print(f"💡 RECOMMENDATIONS")
        if llm_percentage < 50:
            print(f"   ⚠️  LLM usage is low ({llm_percentage:.1f}%). Check Gemini API availability.")
        if callback_success_rate < 100:
            print(f"   ⚠️  Some callbacks failed ({callbacks['failed']} failures). Check network/endpoint.")
        if avg_response_time > 5000:
            print(f"   ⚠️  High response time ({avg_response_time:.0f}ms). Consider optimization.")
        if extractions_by_type.get("phone_numbers", 0) < len(sessions):
            print(f"   💡 Phone numbers extraction could be improved.")
        if extractions_by_type.get("upi_ids", 0) < len(sessions):
            print(f"   💡 UPI ID extraction could be improved.")

        print("\n" + "="*80)

    except FileNotFoundError:
        print(f"❌ Error: Log file '{log_file}' not found")
        print("   Make sure you've run some test cases first.")
        sys.exit(1)


if __name__ == "__main__":
    log_file = sys.argv[1] if len(sys.argv) > 1 else "hackathon_performance.log"
    analyze_performance_logs(log_file)
