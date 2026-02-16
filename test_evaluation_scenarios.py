"""
Test the honeypot system with the three official evaluation scenarios
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import List, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the components
from models import HoneypotRequest, MessageContent
from scam_detector import ScamDetector
from ai_agent import AIHoneypotAgent
from intelligence_extractor import IntelligenceExtractor
from session_manager import session_manager, SessionStateEnum

# Test scenarios from the evaluation
EVALUATION_SCENARIOS = [
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

# Simulated scammer responses for multi-turn conversation
SCAMMER_RESPONSES = {
    "bank_fraud": [
        "URGENT: Your SBI account has been compromised. Your account will be blocked in 2 hours. Share your account number and OTP immediately to verify your identity.",
        "Sir, please hurry! I am from SBI Fraud Department. Give me your account number now to verify.",
        "Your account will be permanently closed if you don't share your account number and OTP in next 30 minutes.",
        "This is final warning! Share your UPI ID and phone number for verification or account will be blocked forever.",
        "I need your IFSC code and branch details to restore your account access immediately.",
        "Please confirm your account number ending with XXXX and your registered mobile number.",
        "Sir, do you want your hard-earned money to be lost? Share your account details now!",
        "We have detected suspicious withdrawal. Confirm your bank account number quickly.",
        "I am sending a verification link to your email. What is your email address?",
        "Final chance! Share your details or we will freeze your account in 10 minutes."
    ],
    "upi_fraud": [
        "Congratulations! You have won a cashback of Rs. 5000 from Paytm. To claim your reward, please verify your UPI details. This is from official customer support.",
        "Great! To transfer Rs. 5000 to your account, please share your UPI ID.",
        "I see you're interested! What is your registered phone number for UPI verification?",
        "Perfect! Now I need your bank account number to credit the cashback amount.",
        "To complete the process, please share your UPI PIN for one-time verification.",
        "The system is asking for your email address to send the confirmation receipt.",
        "Almost done! Please confirm your IFSC code to finalize the transfer.",
        "Sir/Madam, this is a limited time offer. Share your alternate UPI ID if the first one doesn't work.",
        "We need to verify your identity. Please share your phone number and email address.",
        "Last step! Share your bank details and we will credit Rs. 5000 immediately."
    ],
    "phishing": [
        "You have been selected for iPhone 15 Pro at just Rs. 999! Click here to claim: http://amaz0n-deals.fake-site.com/claim?id=12345. Offer expires in 10 minutes!",
        "This is a genuine Amazon offer! Just click the link and enter your payment details.",
        "Hurry! Only 2 devices left. What is your email address to send the invoice?",
        "Great! Now share your phone number for delivery confirmation.",
        "Please provide your shipping address and contact number for delivery.",
        "To complete the order, we need your UPI ID for payment of Rs. 999.",
        "The payment page is not loading? Let me send you an alternate link. What's your email?",
        "Sir/Madam, this offer is about to expire! Share your bank account details for instant payment.",
        "We have your order ready. Just need your account number for COD option.",
        "Final confirmation needed! Share your phone number and UPI ID to claim your iPhone."
    ]
}


class EvaluationTester:
    """Test the honeypot system with evaluation scenarios"""

    def __init__(self):
        self.detector = ScamDetector()
        self.agent = AIHoneypotAgent()
        self.extractor = IntelligenceExtractor()
        self.results = []

    async def test_scenario(self, scenario: Dict) -> Dict:
        """Test a single scenario"""
        scenario_id = scenario["scenarioId"]
        max_turns = scenario["maxTurns"]

        logger.info(f"\n{'='*80}")
        logger.info(f"Testing Scenario: {scenario['name']}")
        logger.info(f"{'='*80}\n")

        # Create session
        session_id = f"eval_{scenario_id}_{int(datetime.now().timestamp())}"
        session = session_manager.get_or_create_session(session_id)

        conversation_history = []
        scammer_responses = SCAMMER_RESPONSES.get(scenario["scamType"], SCAMMER_RESPONSES["bank_fraud"])

        scam_detected = False
        total_intel_extracted = 0
        detection_score = 0
        extraction_score = 0
        engagement_score = 0

        # Run conversation for max_turns
        for turn in range(min(max_turns, len(scammer_responses))):
            scammer_msg = scammer_responses[turn]

            logger.info(f"\n--- Turn {turn + 1}/{max_turns} ---")
            logger.info(f"Scammer: {scammer_msg}")

            # Step 1: Detect scam
            try:
                detection_result = await self.detector.analyze(scammer_msg, conversation_history)
                scam_detected = detection_result.get("is_scam", False)
                scam_type = detection_result.get("scam_type", "unknown")
                confidence = detection_result.get("confidence_score", 0)

                logger.info(f"Detection: Scam={scam_detected}, Type={scam_type}, Confidence={confidence:.2f}")

                # Award detection score (10 points if detected correctly on first message)
                if turn == 0 and scam_detected:
                    detection_score = 10
                elif turn <= 2 and scam_detected:
                    detection_score = max(detection_score, 8)
                elif scam_detected:
                    detection_score = max(detection_score, 5)

            except Exception as e:
                logger.error(f"Detection failed: {e}")
                detection_result = {"is_scam": False, "confidence_score": 0}

            # Step 2: Extract intelligence
            try:
                context_window = " ".join([m.get("text", "") for m in conversation_history[-3:]])
                extracted = await self.extractor.extract(scammer_msg, turn, context_window)

                if extracted:
                    for item in extracted:
                        logger.info(f"Extracted: {item.type} = {item.value} (source: {item.source})")
                        total_intel_extracted += 1
                        session_manager.update_intel_graph(session_id, extracted)

                # Award extraction score (up to 30 points)
                extraction_score = min(total_intel_extracted * 6, 30)

            except Exception as e:
                logger.error(f"Extraction failed: {e}")

            # Step 3: Generate agent response
            try:
                agent_response = await self.agent.generate_response(
                    message=scammer_msg,
                    conversation_history=conversation_history,
                    scam_type=scam_type if scam_detected else None,
                    session_id=session_id
                )

                logger.info(f"Agent: {agent_response}")

                # Award engagement score based on response quality
                if len(agent_response) > 20:  # Not too short
                    engagement_score = min(engagement_score + 3, 20)
                if any(word in agent_response.lower() for word in ["your", "you", "?"]):
                    engagement_score = min(engagement_score + 2, 20)

            except Exception as e:
                logger.error(f"Agent response failed: {e}")
                agent_response = "I'm sorry, could you repeat that?"

            # Update conversation history
            conversation_history.append({
                "sender": "user",
                "text": scammer_msg,
                "timestamp": int(datetime.now().timestamp() * 1000)
            })
            conversation_history.append({
                "sender": "agent",
                "text": agent_response,
                "timestamp": int(datetime.now().timestamp() * 1000)
            })

            # Update session
            session_manager.update_session(session_id, message_count=len(conversation_history))

        # Calculate final scores
        total_score = detection_score + extraction_score + engagement_score

        # Get final extracted intelligence
        session = session_manager.get_session(session_id)
        final_intel = session.extracted_intelligence if session else {}

        result = {
            "scenario": scenario["name"],
            "scenario_id": scenario_id,
            "scam_detected": scam_detected,
            "detection_score": detection_score,
            "extraction_score": extraction_score,
            "engagement_score": engagement_score,
            "total_score": total_score,
            "max_score": 60,
            "percentage": round((total_score / 60) * 100, 2),
            "turns_completed": len(conversation_history) // 2,
            "intel_extracted": total_intel_extracted,
            "final_intelligence": final_intel
        }

        logger.info(f"\n{'='*80}")
        logger.info(f"Scenario Results: {scenario['name']}")
        logger.info(f"{'='*80}")
        logger.info(f"Detection Score: {detection_score}/10")
        logger.info(f"Extraction Score: {extraction_score}/30")
        logger.info(f"Engagement Score: {engagement_score}/20")
        logger.info(f"Total Score: {total_score}/60 ({result['percentage']}%)")
        logger.info(f"Intelligence Extracted: {total_intel_extracted} items")
        logger.info(f"{'='*80}\n")

        return result

    async def run_all_scenarios(self):
        """Run all evaluation scenarios"""
        logger.info(f"\n{'#'*80}")
        logger.info("Starting Evaluation Tests")
        logger.info(f"{'#'*80}\n")

        for scenario in EVALUATION_SCENARIOS:
            result = await self.test_scenario(scenario)
            self.results.append(result)

        # Print overall summary
        self.print_summary()

    def print_summary(self):
        """Print overall test summary"""
        logger.info(f"\n{'#'*80}")
        logger.info("OVERALL EVALUATION SUMMARY")
        logger.info(f"{'#'*80}\n")

        total_detection = sum(r["detection_score"] for r in self.results)
        total_extraction = sum(r["extraction_score"] for r in self.results)
        total_engagement = sum(r["engagement_score"] for r in self.results)
        total_overall = sum(r["total_score"] for r in self.results)
        max_overall = sum(r["max_score"] for r in self.results)
        avg_percentage = total_overall / max_overall * 100 if max_overall > 0 else 0

        logger.info(f"Scenarios Tested: {len(self.results)}")
        logger.info(f"Total Detection Score: {total_detection}/{len(self.results) * 10}")
        logger.info(f"Total Extraction Score: {total_extraction}/{len(self.results) * 30}")
        logger.info(f"Total Engagement Score: {total_engagement}/{len(self.results) * 20}")
        logger.info(f"Overall Score: {total_overall}/{max_overall} ({avg_percentage:.2f}%)")

        logger.info(f"\nPer-Scenario Breakdown:")
        for result in self.results:
            logger.info(f"  {result['scenario']}: {result['total_score']}/{result['max_score']} ({result['percentage']}%)")

        logger.info(f"\n{'#'*80}\n")

        # Save results to file
        with open("evaluation_results.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "scenarios": self.results,
                "summary": {
                    "total_score": total_overall,
                    "max_score": max_overall,
                    "percentage": avg_percentage,
                    "detection_score": total_detection,
                    "extraction_score": total_extraction,
                    "engagement_score": total_engagement
                }
            }, f, indent=2)

        logger.info("Results saved to evaluation_results.json")


async def main():
    """Main test function"""
    tester = EvaluationTester()
    await tester.run_all_scenarios()


if __name__ == "__main__":
    asyncio.run(main())
