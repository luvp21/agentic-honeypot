"""
Automated Testing Suite for Honeypot API
=========================================

This script runs automated tests against your deployed honeypot API,
collects all conversation data, and generates accuracy metrics.

Features:
- Run N test rounds with various scam scenarios
- Log all messages exchanged
- Store final callback payloads
- Generate statistical reports
"""

import requests
import json
import time
from datetime import datetime
from typing import List, Dict
import random
from pathlib import Path

# Configuration
API_URL = "https://your-honeypot-api.com/api/conversation/message"  # Update this
API_KEY = "honeypot-secret-key-123"  # Update with your API key
TEST_ROUNDS = 10  # Number of test conversations to run
RESULTS_DIR = Path("test_results")

# Create results directory
RESULTS_DIR.mkdir(exist_ok=True)

# Sample scam messages for testing
SCAM_SCENARIOS = [
    {
        "type": "phishing",
        "messages": [
            "URGENT: Your SBI account has been compromised. Click here to verify: http://fake-sbi.com",
            "Your account will be blocked in 2 hours. Share your account number and OTP immediately.",
            "We need your account number to verify your identity and prevent the block.",
            "Please provide your IFSC code and account details now.",
            "Send the OTP you just received to complete verification."
        ]
    },
    {
        "type": "lottery",
        "messages": [
            "Congratulations! You've won ₹10,00,000 in the Kaun Banega Crorepati lottery!",
            "To claim your prize, you need to pay a processing fee of ₹5,000.",
            "Send the fee to our UPI ID: winner@lottery.com",
            "What's your bank account number for prize transfer?",
            "Hurry! Offer expires in 24 hours!"
        ]
    },
    {
        "type": "tech_support",
        "messages": [
            "WARNING: Your computer has 5 viruses! Call us immediately at +91-9876543210",
            "Click this link to download virus removal tool: http://fake-antivirus.com",
            "You need to pay ₹2,999 for premium antivirus protection.",
            "Share your UPI ID to complete the payment.",
            "What's your email and phone number for registration?"
        ]
    },
    {
        "type": "investment",
        "messages": [
            "Earn 500% returns in crypto trading! Limited slots available!",
            "Invest now in Bitcoin and get guaranteed returns.",
            "Send ₹10,000 to our account: 1234567890123456, IFSC: SBIN0001234",
            "What's your UPI ID? We'll send you the investment confirmation.",
            "Register with your phone number and email to start trading."
        ]
    }
]


class TestRunner:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
        self.test_results = []

    def run_conversation(self, scenario: Dict, round_num: int) -> Dict:
        """Run a single test conversation"""
        session_id = f"test-session-{round_num}-{int(time.time())}"
        conversation_log = []

        print(f"\n{'='*60}")
        print(f"Round {round_num} - Scenario: {scenario['type']}")
        print(f"Session ID: {session_id}")
        print(f"{'='*60}")

        conversation_history = []

        for turn, scammer_msg in enumerate(scenario['messages'], 1):
            print(f"\n[Turn {turn}] Scammer: {scammer_msg[:80]}...")

            # Build message object
            message = {
                "sender": "scammer",
                "text": scammer_msg,
                "timestamp": int(time.time() * 1000)
            }

            # Send to API
            payload = {
                "sessionId": session_id,
                "message": message,
                "conversationHistory": conversation_history,
                "metadata": {
                    "channel": "Testing",
                    "language": "en"
                }
            }

            try:
                response = requests.post(
                    self.api_url,
                    json=payload,
                    headers={"x-api-key": self.api_key},
                    timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    agent_reply = data.get("reply", "")
                    print(f"[Turn {turn}] Agent: {agent_reply[:80]}...")

                    # Log this exchange
                    conversation_log.append({
                        "turn": turn,
                        "scammer": scammer_msg,
                        "agent": agent_reply,
                        "timestamp": datetime.now().isoformat()
                    })

                    # Update conversation history
                    conversation_history.append(message)
                    conversation_history.append({
                        "sender": "user",
                        "text": agent_reply,
                        "timestamp": int(time.time() * 1000)
                    })
                else:
                    print(f"❌ API Error: {response.status_code}")
                    break

            except Exception as e:
                print(f"❌ Exception: {e}")
                break

            # Small delay between messages
            time.sleep(1)

        return {
            "session_id": session_id,
            "scenario_type": scenario['type'],
            "conversation": conversation_log,
            "total_turns": len(conversation_log),
            "timestamp": datetime.now().isoformat()
        }

    def run_all_tests(self, num_rounds: int):
        """Run multiple test rounds"""
        print(f"\n🚀 Starting {num_rounds} test rounds...")
        print(f"Results will be saved to: {RESULTS_DIR}")

        for round_num in range(1, num_rounds + 1):
            # Pick a random scenario
            scenario = random.choice(SCAM_SCENARIOS)

            # Run conversation
            result = self.run_conversation(scenario, round_num)
            self.test_results.append(result)

            # Save individual result
            result_file = RESULTS_DIR / f"round_{round_num}_{result['session_id']}.json"
            with open(result_file, 'w') as f:
                json.dump(result, indent=2, fp=f)

            print(f"\n✅ Round {round_num} complete. Logged to {result_file}")

            # Delay between rounds
            if round_num < num_rounds:
                time.sleep(2)

        # Generate summary
        self.generate_summary()

    def generate_summary(self):
        """Generate test summary and metrics"""
        print(f"\n{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}")

        total_rounds = len(self.test_results)
        total_turns = sum(r['total_turns'] for r in self.test_results)
        avg_turns = total_turns / total_rounds if total_rounds > 0 else 0

        scenario_counts = {}
        for result in self.test_results:
            scenario_type = result['scenario_type']
            scenario_counts[scenario_type] = scenario_counts.get(scenario_type, 0) + 1

        summary = {
            "test_run_timestamp": datetime.now().isoformat(),
            "total_rounds": total_rounds,
            "total_turns": total_turns,
            "average_turns_per_conversation": round(avg_turns, 2),
            "scenarios_tested": scenario_counts,
            "results": self.test_results
        }

        # Save summary
        summary_file = RESULTS_DIR / f"summary_{int(time.time())}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, indent=2, fp=f)

        print(f"\nTotal Rounds: {total_rounds}")
        print(f"Total Turns: {total_turns}")
        print(f"Average Turns/Conversation: {avg_turns:.2f}")
        print(f"\nScenario Distribution:")
        for scenario, count in scenario_counts.items():
            print(f"  - {scenario}: {count} rounds")

        print(f"\n📊 Summary saved to: {summary_file}")
        print(f"\n💡 Next steps:")
        print(f"   1. Review individual conversation logs in {RESULTS_DIR}")
        print(f"   2. Check if agent extracted intelligence successfully")
        print(f"   3. Analyze response quality and persona consistency")
        print(f"   4. Look for patterns in successful vs unsuccessful extractions")


if __name__ == "__main__":
    print("="*60)
    print("HONEYPOT API TESTING SUITE")
    print("="*60)

    # Update these before running
    print("\n⚠️  CONFIGURATION:")
    print(f"   API URL: {API_URL}")
    print(f"   Test Rounds: {TEST_ROUNDS}")
    print(f"   Results Directory: {RESULTS_DIR}")

    confirm = input("\n▶ Proceed with testing? (y/n): ")
    if confirm.lower() != 'y':
        print("Aborted.")
        exit(0)

    runner = TestRunner(API_URL, API_KEY)
    runner.run_all_tests(TEST_ROUNDS)

    print("\n✅ All tests complete!")
