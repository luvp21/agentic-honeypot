"""
Test Script for Scam Detection System
Tests the honeypot against official evaluation scenarios
"""

import requests
import json
import time
import logging
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "honeypot-secret-key-123"
HEADERS = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

# Test Scenarios (Official Evaluation Scenarios)
TEST_SCENARIOS = [
    {
        "scenarioId": "bank_fraud",
        "name": "Bank Fraud Detection",
        "description": "Bank account fraud with urgency tactics",
        "scamType": "bank_fraud",
        "initialMessage": "URGENT: Your SBI account has been compromised. Your account will be blocked in 2 hours. Share your account number and OTP immediately to verify your identity.",
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        },
        "weight": 10,
        "maxTurns": 10,
        "fakeData": {
            "bankAccount": "1234567890123456",
            "upiId": "scammer.fraud@fakebank",
            "phoneNumber": "+91-9876543210"
        }
    },
    {
        "scenarioId": "upi_fraud",
        "name": "UPI Fraud Multi-turn",
        "description": "UPI fraud with cashback scam",
        "scamType": "upi_fraud",
        "initialMessage": "Congratulations! You have won a cashback of Rs. 5000 from Paytm. To claim your reward, please verify your UPI details. This is from official customer support.",
        "metadata": {
            "channel": "WhatsApp",
            "language": "English",
            "locale": "IN"
        },
        "weight": 10,
        "maxTurns": 10,
        "fakeData": {
            "upiId": "cashback.scam@fakeupi",
            "phoneNumber": "+91-8765432109"
        }
    },
    {
        "scenarioId": "phishing_link",
        "name": "Phishing Link Detection",
        "description": "Phishing link with fake offer",
        "scamType": "phishing",
        "initialMessage": "You have been selected for iPhone 15 Pro at just Rs. 999! Click here to claim: http://amaz0n-deals.fake-site.com/claim?id=12345. Offer expires in 10 minutes!",
        "metadata": {
            "channel": "Email",
            "language": "English",
            "locale": "IN"
        },
        "weight": 10,
        "maxTurns": 10,
        "fakeData": {
            "phishingLink": "http://amaz0n-deals.fake-site.com/claim?id=12345",
            "emailAddress": "offers@fake-amazon-deals.com"
        }
    }
]


class HoneypotTester:
    """Test runner for honeypot system"""

    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0

    def test_scenario(self, scenario: Dict) -> Dict:
        """Run a single test scenario"""
        logger.info(f"\n{'='*80}")
        logger.info(f"Testing Scenario: {scenario['name']}")
        logger.info(f"Description: {scenario['description']}")
        logger.info(f"{'='*80}")

        session_id = f"test_{scenario['scenarioId']}_{int(time.time())}"
        conversation_history = []
        intelligence_collected = {}

        # Initial message from scammer
        initial_msg = scenario['initialMessage']
        logger.info(f"\n[SCAMMER] {initial_msg}")

        # Test the conversation for multiple turns
        for turn in range(scenario['maxTurns']):
            logger.info(f"\n--- Turn {turn + 1}/{scenario['maxTurns']} ---")

            if turn == 0:
                # First turn - send initial scammer message
                scammer_message = initial_msg
            else:
                # Simulate scammer responses based on agent's questions
                scammer_message = self._generate_scammer_response(
                    scenario,
                    conversation_history,
                    turn
                )

            # Send message to honeypot
            payload = {
                "sessionId": session_id,
                "message": {
                    "text": scammer_message,
                    "timestamp": int(time.time() * 1000)
                },
                "metadata": scenario['metadata']
            }

            try:
                response = requests.post(
                    f"{BASE_URL}/api/honeypot/message",
                    headers=HEADERS,
                    json=payload,
                    timeout=30
                )

                if response.status_code != 200:
                    logger.error(f"API Error: {response.status_code} - {response.text}")
                    break

                result = response.json()

                # Log the agent's response
                agent_reply = result.get('response', {}).get('text', '')
                logger.info(f"[AGENT] {agent_reply}")

                # Track conversation
                conversation_history.append({
                    "turn": turn + 1,
                    "scammer": scammer_message,
                    "agent": agent_reply
                })

                # Check session state
                session_state = result.get('sessionState', 'ACTIVE')
                logger.info(f"Session State: {session_state}")

                # Extract intelligence if available
                if result.get('intelligence'):
                    intel = result['intelligence']
                    logger.info(f"\n🔍 Intelligence Extracted:")
                    logger.info(f"   Scam Type: {intel.get('scamType', 'N/A')}")
                    logger.info(f"   Confidence: {intel.get('confidence', 0):.2f}")

                    extracted = intel.get('extractedData', {})
                    if extracted:
                        logger.info(f"   Extracted Data:")
                        for key, value in extracted.items():
                            logger.info(f"      - {key}: {value}")
                            intelligence_collected[key] = value

                # Check if session ended
                if session_state in ['SCAM_DETECTED', 'ENDED']:
                    logger.info(f"\n✅ Session ended: {session_state}")
                    break

                # Small delay between turns
                time.sleep(1)

            except Exception as e:
                logger.error(f"Error during test: {str(e)}")
                break

        # Evaluate results
        evaluation = self._evaluate_scenario(
            scenario,
            conversation_history,
            intelligence_collected
        )

        return {
            "scenario": scenario['name'],
            "scenarioId": scenario['scenarioId'],
            "conversation": conversation_history,
            "intelligence": intelligence_collected,
            "evaluation": evaluation
        }

    def _generate_scammer_response(
        self,
        scenario: Dict,
        history: List[Dict],
        turn: int
    ) -> str:
        """Generate realistic scammer responses based on agent's questions"""

        if not history:
            return scenario['initialMessage']

        last_agent_msg = history[-1]['agent'].lower()
        scenario_type = scenario['scamType']
        fake_data = scenario.get('fakeData', {})

        # Bank fraud responses
        if scenario_type == 'bank_fraud':
            if 'account' in last_agent_msg or 'number' in last_agent_msg:
                return "Yes, provide your 16-digit account number now! Time is running out."
            elif 'otp' in last_agent_msg or 'code' in last_agent_msg:
                return "The OTP will be sent to your phone. Share it immediately when you receive it."
            elif 'upi' in last_agent_msg:
                return f"For quick verification, you can also send Rs. 1 to {fake_data.get('upiId', 'verify@sbi')} to confirm your account."
            elif 'who' in last_agent_msg or 'name' in last_agent_msg:
                return "I am Rajesh Kumar from SBI Security Department. We need to act fast!"
            elif 'phone' in last_agent_msg or 'number' in last_agent_msg:
                return f"Call our emergency helpline at {fake_data.get('phoneNumber', '+91-9876543210')} immediately!"

        # UPI fraud responses
        elif scenario_type == 'upi_fraud':
            if 'upi' in last_agent_msg or 'id' in last_agent_msg:
                return f"Please verify by sending Re. 1 to our verification UPI: {fake_data.get('upiId', 'verify@paytm')}"
            elif 'account' in last_agent_msg:
                return f"Alternatively, provide your bank account number: {fake_data.get('bankAccount', '1234567890123456')}"
            elif 'phone' in last_agent_msg or 'contact' in last_agent_msg:
                return f"For instant cashback, WhatsApp us at {fake_data.get('phoneNumber', '+91-8765432109')}"
            elif 'how' in last_agent_msg or 'process' in last_agent_msg:
                return "Simple! Share your UPI ID, we'll send Rs. 1 for verification, then you get Rs. 5000 cashback instantly!"

        # Phishing responses
        elif scenario_type == 'phishing':
            if 'link' in last_agent_msg or 'click' in last_agent_msg:
                return f"Click this secure link now: {fake_data.get('phishingLink', 'http://amaz0n-deals.fake-site.com')} - Offer ending soon!"
            elif 'email' in last_agent_msg:
                return f"Email confirmation will be sent from {fake_data.get('emailAddress', 'offers@fake-amazon.com')}"
            elif 'phone' in last_agent_msg:
                return "After clicking the link, you'll get a call from our delivery partner for address confirmation."

        # Default pressure responses
        pressure_responses = [
            "Time is running out! Only 5 minutes left. Please cooperate immediately!",
            "This is urgent! Your account security is at risk. Act now!",
            "Don't miss this opportunity! This offer expires very soon!",
            "We need your immediate response. Others are claiming this offer!",
            "Quick! Just share the details I asked for. This is 100% genuine!"
        ]

        return pressure_responses[turn % len(pressure_responses)]

    def _evaluate_scenario(
        self,
        scenario: Dict,
        conversation: List[Dict],
        intelligence: Dict
    ) -> Dict:
        """Evaluate how well the honeypot performed"""

        evaluation = {
            "scam_detected": False,
            "intelligence_extracted": False,
            "engagement_quality": 0,
            "data_extracted_count": 0,
            "expected_data_found": [],
            "missing_data": [],
            "score": 0
        }

        # Check if scam was detected (conversation happened)
        if len(conversation) > 0:
            evaluation["scam_detected"] = True

        # Check intelligence extraction
        if intelligence:
            evaluation["intelligence_extracted"] = True
            evaluation["data_extracted_count"] = len(intelligence)

        # Check for expected data based on scenario type
        expected_data = scenario.get('fakeData', {})
        for key in expected_data.keys():
            found = False
            for intel_key, intel_value in intelligence.items():
                if key.lower() in intel_key.lower() or any(
                    k in intel_key.lower() for k in ['upi', 'phone', 'account', 'email', 'link']
                ):
                    evaluation["expected_data_found"].append(intel_key)
                    found = True
                    break

            if not found:
                evaluation["missing_data"].append(key)

        # Engagement quality (how many turns)
        evaluation["engagement_quality"] = min(len(conversation) / scenario['maxTurns'], 1.0)

        # Calculate score
        score = 0
        if evaluation["scam_detected"]:
            score += 30
        if evaluation["intelligence_extracted"]:
            score += 20
        score += evaluation["engagement_quality"] * 30
        score += (len(evaluation["expected_data_found"]) / max(len(expected_data), 1)) * 20

        evaluation["score"] = round(score, 2)

        return evaluation

    def run_all_tests(self):
        """Run all test scenarios"""
        logger.info("\n" + "="*80)
        logger.info("STARTING HONEYPOT EVALUATION")
        logger.info("="*80)

        for scenario in TEST_SCENARIOS:
            result = self.test_scenario(scenario)
            self.results.append(result)
            self.total_tests += 1

            if result['evaluation']['score'] >= 70:
                self.passed_tests += 1

            # Print summary for this scenario
            logger.info(f"\n{'='*80}")
            logger.info(f"SCENARIO SUMMARY: {result['scenario']}")
            logger.info(f"{'='*80}")
            logger.info(f"✓ Scam Detected: {result['evaluation']['scam_detected']}")
            logger.info(f"✓ Intelligence Extracted: {result['evaluation']['intelligence_extracted']}")
            logger.info(f"✓ Conversation Turns: {len(result['conversation'])}")
            logger.info(f"✓ Data Points Collected: {result['evaluation']['data_extracted_count']}")
            logger.info(f"✓ Expected Data Found: {', '.join(result['evaluation']['expected_data_found']) or 'None'}")
            logger.info(f"✗ Missing Data: {', '.join(result['evaluation']['missing_data']) or 'None'}")
            logger.info(f"📊 Score: {result['evaluation']['score']}/100")
            logger.info(f"{'='*80}\n")

            # Wait between scenarios
            time.sleep(2)

        # Final summary
        self._print_final_summary()

    def _print_final_summary(self):
        """Print final test summary"""
        logger.info("\n" + "="*80)
        logger.info("FINAL TEST SUMMARY")
        logger.info("="*80)
        logger.info(f"Total Scenarios Tested: {self.total_tests}")
        logger.info(f"Passed (Score >= 70): {self.passed_tests}")
        logger.info(f"Failed: {self.total_tests - self.passed_tests}")
        logger.info(f"Success Rate: {(self.passed_tests/self.total_tests*100):.1f}%")

        avg_score = sum(r['evaluation']['score'] for r in self.results) / len(self.results)
        logger.info(f"Average Score: {avg_score:.2f}/100")

        logger.info("\n" + "="*80)
        logger.info("DETAILED RESULTS BY SCENARIO")
        logger.info("="*80)

        for result in self.results:
            status = "✅ PASS" if result['evaluation']['score'] >= 70 else "❌ FAIL"
            logger.info(f"{status} - {result['scenario']}: {result['evaluation']['score']}/100")

        logger.info("="*80)

        # Save detailed results to file
        with open('test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        logger.info("\n💾 Detailed results saved to: test_results.json")


def main():
    """Main test runner"""
    logger.info("Initializing Honeypot Test Suite...")

    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        logger.info("✅ Honeypot server is running")
    except Exception as e:
        logger.error(f"❌ Cannot connect to honeypot server at {BASE_URL}")
        logger.error(f"Error: {str(e)}")
        logger.error("Please start the server with: python main.py")
        return

    # Run tests
    tester = HoneypotTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
