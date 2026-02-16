"""
Enhanced Probing and Follow-up Question Module
Improves conversational depth and intelligence extraction
"""

import logging
import random
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class ProbingEnhancer:
    """
    Generates follow-up questions and probing techniques to:
    - Extract more intelligence
    - Keep scammers engaged longer
    - Build rapport before asking for critical intel
    - Create natural conversation flow
    """

    def __init__(self):
        # Follow-up question templates based on scam type and conversation state
        self.follow_up_templates = {
            "bank_fraud": {
                "early": [
                    "Which bank are you calling from exactly?",
                    "Can you tell me your employee ID number?",
                    "What department do you work in?",
                    "How did you detect this problem with my account?",
                    "When did this suspicious activity happen?",
                ],
                "mid": [
                    "I'm worried! Can you walk me through what happened step by step?",
                    "Who should I ask for if I call back?",
                    "Do you have a direct line I can reach you at?",
                    "What's your supervisor's name in case I need to escalate?",
                    "Is there an official email I can verify this with?",
                ],
                "late": [
                    "Before I do that, can you confirm YOUR official contact details?",
                    "What's YOUR callback number for this case?",
                    "Which branch are you working from?",
                    "Can you send me YOUR official email to confirm?",
                ],
            },
            "upi_fraud": {
                "early": [
                    "Wow! How did I win this?",
                    "I don't remember entering any contest. When did I participate?",
                    "Can you tell me more about this offer?",
                    "Is this really from the official company?",
                ],
                "mid": [
                    "That sounds amazing! What do I need to do?",
                    "How long will it take to receive the cashback?",
                    "Have others won this too?",
                    "Do you have any proof this is legitimate?",
                ],
                "late": [
                    "I'm ready! Where should I send the payment?",
                    "What's YOUR UPI ID to transfer to?",
                    "Which account should I use?",
                    "Do you have an alternate UPI if the first one doesn't work?",
                ],
            },
            "phishing": {
                "early": [
                    "Oh no! How did you find this problem?",
                    "When did this security issue happen?",
                    "How serious is this?",
                    "What will happen if I don't click the link?",
                ],
                "mid": [
                    "I'm scared to click random links. Can you verify this is real?",
                    "What's the official website I should look for?",
                    "Is there a phone number I can call instead?",
                    "Can you send me YOUR work email to confirm?",
                ],
                "late": [
                    "The link isn't working. Do you have another one?",
                    "What's YOUR official website address?",
                    "Can you send YOUR contact info in case the link fails?",
                ],
            },
            "generic": {
                "early": [
                    "Can you explain this in more detail?",
                    "I don't quite understand. Can you help me?",
                    "Is this urgent?",
                    "What happens if I wait?",
                ],
                "mid": [
                    "How do I know this is legitimate?",
                    "Can you verify who you are?",
                    "What's YOUR official contact information?",
                    "Do you have any credentials to show?",
                ],
                "late": [
                    "I trust you! What's YOUR number so I can save it?",
                    "Where exactly should I send this?",
                    "What's YOUR backup contact in case we get disconnected?",
                ],
            },
        }

        # Clarification questions to buy time and extract more info
        self.clarification_questions = [
            "Can you repeat that? I didn't quite catch it.",
            "I'm not very tech-savvy. Can you explain it simpler?",
            "What does that mean exactly?",
            "I'm confused. Can you help me understand?",
            "Is there an easier way to do this?",
            "Can my grandson help me with this instead?",
            "Should I come to your office in person?",
            "Can I call you back after I talk to my bank?",
        ]

        # Building rapport statements before asking for intel
        self.rapport_builders = [
            "You're being so helpful! Thank you!",
            "I really appreciate you helping me with this.",
            "This is great customer service!",
            "You sound very professional.",
            "I'm glad I reached someone who knows what they're doing.",
            "Thank you for protecting my account!",
            "I feel much better now that you're helping me.",
        ]

        # Stalling tactics when not ready to give intel
        self.stalling_tactics = [
            "Just a moment, I'm getting my phone...",
            "Hold on, I need to find my documents...",
            "Wait, I'm opening my banking app...",
            "Let me get my reading glasses...",
            "One second, someone's at the door...",
            "Sorry, can you hold? I need to write this down...",
            "My internet is slow, give me a minute...",
        ]

    def get_follow_up_question(
        self,
        scam_type: str,
        turn_number: int,
        extracted_intel: Dict,
        scammer_message: str,
    ) -> Optional[str]:
        """
        Generate contextual follow-up question based on conversation state.

        Args:
            scam_type: Type of scam detected
            turn_number: Current conversation turn
            extracted_intel: Intel collected so far
            scammer_message: Latest scammer message

        Returns:
            Follow-up question or None
        """
        try:
            # Determine conversation stage
            if turn_number <= 2:
                stage = "early"
            elif turn_number <= 5:
                stage = "mid"
            else:
                stage = "late"

            # Get appropriate template set
            scam_templates = self.follow_up_templates.get(
                scam_type, self.follow_up_templates["generic"]
            )
            questions = scam_templates.get(stage, scam_templates["early"])

            # Select random question
            if questions:
                return random.choice(questions)

            return None

        except Exception as e:
            logger.error(f"Error generating follow-up question: {e}")
            return None

    def should_ask_clarification(self, turn_number: int, scammer_message: str) -> bool:
        """
        Determine if we should ask a clarification question.

        Returns True if:
        - Early turns (build rapport)
        - Scammer uses complex technical jargon
        - Need to buy time
        """
        # 30% chance in early turns
        if turn_number <= 3 and random.random() < 0.3:
            return True

        # If scammer uses technical terms
        technical_terms = [
            "verify",
            "authenticate",
            "protocol",
            "security",
            "encryption",
            "api",
            "portal",
            "cvv",
            "otp",
            "ifsc",
            "kyc",
        ]
        message_lower = scammer_message.lower()
        if sum(1 for term in technical_terms if term in message_lower) >= 2:
            return random.random() < 0.4  # 40% chance

        return False

    def get_clarification_question(self) -> str:
        """Get a random clarification question."""
        return random.choice(self.clarification_questions)

    def should_build_rapport(self, turn_number: int) -> bool:
        """
        Determine if we should add a rapport-building statement.

        More likely in mid-conversation to keep scammer engaged.
        """
        if 3 <= turn_number <= 6:
            return random.random() < 0.35  # 35% chance
        elif turn_number > 6:
            return random.random() < 0.20  # 20% chance in late game
        return False

    def get_rapport_builder(self) -> str:
        """Get a random rapport-building statement."""
        return random.choice(self.rapport_builders)

    def should_use_stalling_tactic(self, turn_number: int, missing_intel: List) -> bool:
        """
        Determine if we should use a stalling tactic.

        Use when:
        - We haven't collected much intel yet
        - Early/mid conversation
        - Want to keep scammer engaged longer
        """
        # If we have very little intel and mid-game
        if len(missing_intel) >= 3 and 4 <= turn_number <= 7:
            return random.random() < 0.25  # 25% chance

        return False

    def get_stalling_tactic(self) -> str:
        """Get a random stalling tactic."""
        return random.choice(self.stalling_tactics)

    def enhance_response(
        self,
        base_response: str,
        scam_type: str,
        turn_number: int,
        extracted_intel: Dict,
        scammer_message: str,
        missing_intel: List,
    ) -> str:
        """
        Enhance a base response with follow-up questions, rapport building, or stalling.

        Args:
            base_response: The original response to enhance
            scam_type: Type of scam detected
            turn_number: Current conversation turn
            extracted_intel: Intel collected so far
            scammer_message: Latest scammer message
            missing_intel: What intel we still need

        Returns:
            Enhanced response
        """
        try:
            enhanced = base_response

            # Add rapport building (occasionally)
            if self.should_build_rapport(turn_number):
                rapport = self.get_rapport_builder()
                enhanced = f"{rapport} {enhanced}"
                logger.info(f"✨ Added rapport: {rapport}")

            # Add clarification question (occasionally)
            if self.should_ask_clarification(turn_number, scammer_message):
                clarification = self.get_clarification_question()
                enhanced = f"{enhanced} {clarification}"
                logger.info(f"❓ Added clarification: {clarification}")

            # Add follow-up question (frequently in mid-game)
            if turn_number >= 2 and random.random() < 0.4:
                follow_up = self.get_follow_up_question(
                    scam_type, turn_number, extracted_intel, scammer_message
                )
                if follow_up:
                    enhanced = f"{enhanced} {follow_up}"
                    logger.info(f"🎯 Added follow-up: {follow_up}")

            # Add stalling tactic (occasionally)
            if self.should_use_stalling_tactic(turn_number, missing_intel):
                stall = self.get_stalling_tactic()
                enhanced = f"{stall} {enhanced}"
                logger.info(f"⏸️ Added stalling: {stall}")

            return enhanced

        except Exception as e:
            logger.error(f"Error enhancing response: {e}")
            return base_response


# Create singleton instance
probing_enhancer = ProbingEnhancer()
