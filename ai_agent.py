"""
AI Honeypot Agent
Uses Claude API to generate realistic victim responses to scammers
"""

import json
import random
from typing import List, Dict, Optional
from datetime import datetime


class AIHoneypotAgent:
    def __init__(self):
        self.personas = {
            "elderly": {
                "traits": "confused, trusting, slow to understand technology",
                "style": "formal, polite, asks clarifying questions",
                "concerns": "worried about losing money, wants to do the right thing",
                "typo_rate": 0.15
            },
            "eager": {
                "traits": "excited about offers, impulsive, optimistic",
                "style": "casual, enthusiastic, uses exclamation marks",
                "concerns": "wants to claim prize quickly, fears missing out",
                "typo_rate": 0.10
            },
            "cautious": {
                "traits": "skeptical but curious, asks verification questions",
                "style": "measured, detailed questions, wants proof",
                "concerns": "worried about scams but tempted by offer",
                "typo_rate": 0.05
            },
            "tech_novice": {
                "traits": "struggles with technology, easily confused",
                "style": "simple language, admits confusion often",
                "concerns": "afraid of making mistakes, needs step-by-step help",
                "typo_rate": 0.20
            }
        }

        # Response strategies based on conversation stage
        self.response_stages = {
            "initial": [
                "Show surprise or interest",
                "Ask basic questions",
                "Express slight confusion"
            ],
            "engagement": [
                "Show growing interest",
                "Ask for more details",
                "Express some concerns but remain interested"
            ],
            "trust_building": [
                "Share fake personal details",
                "Ask about legitimacy",
                "Express willingness to help/participate"
            ],
            "information_gathering": [
                "Ask scammer for their details",
                "Request verification",
                "Delay while appearing cooperative"
            ],
            "extraction": [
                "Pretend technical difficulties",
                "Ask scammer to provide their account details first",
                "Create urgency for scammer to share info"
            ]
        }

    async def generate_response(
        self,
        message: str,
        conversation_history: List[Dict],
        scam_type: str
    ) -> str:
        """
        Generate a realistic response to scammer's message

        Args:
            message: Latest message from scammer
            conversation_history: Previous messages in conversation
            scam_type: Type of scam detected

        Returns:
            AI-generated response
        """

        # Select persona based on scam type
        persona = self._select_persona(scam_type)

        # Determine conversation stage
        stage = self._determine_stage(len(conversation_history))

        # Build system prompt for Claude API
        system_prompt = self._build_system_prompt(persona, stage, scam_type)

        # Build conversation context
        context = self._build_context(conversation_history[-6:])  # Last 3 exchanges

        # Since we're in a hackathon demo, let's use rule-based responses
        # In production, you would call Claude API here
        response = self._generate_rule_based_response(
            message,
            persona,
            stage,
            scam_type,
            len(conversation_history)
        )

        # Add realistic imperfections
        response = self._add_realistic_touches(response, persona)

        return response

    def _select_persona(self, scam_type: str) -> str:
        """Select appropriate persona based on scam type"""
        persona_mapping = {
            "phishing": "cautious",
            "lottery": "eager",
            "tech_support": "tech_novice",
            "romance": "eager",
            "investment": "cautious",
            "fake_job": "eager",
            "impersonation": "elderly"
        }
        return persona_mapping.get(scam_type, "cautious")

    def _determine_stage(self, message_count: int) -> str:
        """Determine conversation stage based on message count"""
        if message_count <= 2:
            return "initial"
        elif message_count <= 4:
            return "engagement"
        elif message_count <= 6:
            return "trust_building"
        elif message_count <= 8:
            return "information_gathering"
        else:
            return "extraction"

    def _build_system_prompt(self, persona: str, stage: str, scam_type: str) -> str:
        """Build system prompt for Claude API"""
        persona_details = self.personas[persona]

        return f"""You are playing the role of a potential scam victim to gather intelligence about scammers.

PERSONA: {persona}
- Traits: {persona_details['traits']}
- Communication style: {persona_details['style']}
- Concerns: {persona_details['concerns']}

SCAM TYPE: {scam_type}
CONVERSATION STAGE: {stage}

OBJECTIVES:
1. Maintain believability - act like a real person would
2. Keep the scammer engaged
3. Gradually try to get the scammer to reveal their:
   - Bank account numbers
   - UPI IDs
   - Phishing links
   - Contact information
   - Payment details

GUIDELINES:
- Never reveal you're an AI or honeypot
- Show appropriate emotions (fear, excitement, confusion)
- Ask questions a real victim would ask
- Make occasional typos and grammar mistakes
- Build trust gradually over multiple messages
- In later stages, create scenarios where scammer needs to provide their details

Generate a realistic response that:
1. Matches the persona
2. Is appropriate for the conversation stage
3. Keeps the scammer engaged
4. Works toward extracting intelligence"""

    def _build_context(self, recent_messages: List[Dict]) -> str:
        """Build conversation context"""
        context = "RECENT CONVERSATION:\n"
        for msg in recent_messages:
            role = "Scammer" if msg["role"] == "scammer" else "You"
            context += f"{role}: {msg['content']}\n"
        return context

    def _generate_rule_based_response(
        self,
        message: str,
        persona: str,
        stage: str,
        scam_type: str,
        turn_number: int
    ) -> str:
        """Generate response using rule-based system (for demo purposes)"""

        message_lower = message.lower()

        # Stage 1: Initial contact - Show interest/confusion
        if stage == "initial":
            responses = {
                "elderly": [
                    "Oh my! I received this message. Is this really true? I'm not very good with these things.",
                    "Hello there. I'm not sure I understand. Could you explain this to me again please?",
                    "This sounds important. I don't want to make any mistakes. What do I need to do?"
                ],
                "eager": [
                    "Wow really?! This is amazing! Tell me more!",
                    "OMG I can't believe it! What do I need to do??",
                    "This is so exciting!! I never win anything! How does this work?"
                ],
                "cautious": [
                    "Interesting. Can you tell me more about this? How did you get my contact information?",
                    "I'd like to know more details before proceeding. What exactly is this about?",
                    "This seems unusual. Can you provide some verification of your identity?"
                ],
                "tech_novice": [
                    "Um, I'm not sure what this means. Can you explain it simply? I'm not good with technology.",
                    "I don't really understand. What is this about? I'm confused.",
                    "Sorry, I need help understanding this. Can you walk me through it step by step?"
                ]
            }
            return random.choice(responses.get(persona, responses["cautious"]))

        # Stage 2: Engagement - Ask questions, show growing interest
        elif stage == "engagement":
            if "click" in message_lower or "link" in message_lower:
                responses = [
                    "I see a link but I'm nervous about clicking it. Is it safe? What happens when I click?",
                    "Before I click anything, can you tell me what I'm supposed to see? I want to make sure it's legitimate.",
                    "My grandson told me to be careful with links. Can you verify who you are first?"
                ]
            elif "account" in message_lower or "bank" in message_lower:
                responses = [
                    "You need my bank account information? That makes me a bit nervous. Why do you need it exactly?",
                    "I have my checkbook here but I want to make sure this is real first. How can I verify this?",
                    "Can you explain why you need my banking details? I've heard about scams and want to be careful."
                ]
            elif "prize" in message_lower or "won" in message_lower:
                responses = [
                    "I really won something? How did I win? I don't remember entering any contest!",
                    "This is exciting but how do I know it's real? Do you have proof?",
                    "What exactly did I win? And how do I claim it? Do I need to pay anything?"
                ]
            else:
                responses = [
                    "OK I'm listening. What are the next steps? I want to make sure I do this correctly.",
                    "This is a lot to take in. Can you break it down for me? I don't want to mess this up.",
                    "Alright, I'm interested but I need more information. Can you explain the process?"
                ]
            return random.choice(responses)

        # Stage 3: Trust building - Share fake details, act cooperative
        elif stage == "trust_building":
            responses = [
                "OK I think I'm understanding now. My name is Robert Johnson and I'm 68 years old. I live in Florida. What information do you need from me?",
                "I'm willing to help but I'm on a fixed income. I can't afford to lose any money. You're sure this is safe?",
                "Alright, I trust you. My email is robertj1956@email.com if you need to send me anything. What's next?",
                "I want to do this right. Can you send me an official letter or email? I like to keep records of these things.",
                "My daughter helps me with these things usually but she's at work. Should I wait for her? Or can we proceed now?"
            ]
            return random.choice(responses)

        # Stage 4: Information gathering - Try to get scammer's details
        elif stage == "information_gathering":
            responses = [
                "Before I send my information, can I have your full name and company details? I want to keep this documented.",
                "My bank requires verification. What's your employee ID number and company phone number?",
                "I need to transfer money but I need your account details first. What bank do you use?",
                "Can you give me your UPI ID so I can send a small test payment first? I want to make sure it works.",
                "What's your official email address? I want to verify this with your company before proceeding.",
                "Do you have a WhatsApp number? My son said everything legitimate has a company WhatsApp these days."
            ]
            return random.choice(responses)

        # Stage 5: Extraction - Create urgency for scammer to share info
        else:
            responses = [
                "I'm ready to proceed but my bank is asking for recipient details. Can you provide your bank account number and IFSC code?",
                "The payment form is asking for beneficiary UPI ID. What should I enter there? Can you share yours?",
                "I'm at the payment screen but it's asking me to verify the recipient. What's your registered mobile number with the bank?",
                "My grandson is helping me now. He says he needs to verify your identity first. What's your company registration number?",
                "I want to send the fee but Google Pay is asking for your UPI. Can you share that? Mine is senior.citizen@paytm if you need it.",
                "The link you sent isn't working. Can you share a different one? Or better yet, give me your account details directly?"
            ]
            return random.choice(responses)

    def _add_realistic_touches(self, response: str, persona: str) -> str:
        """Add typos, delays, and other realistic touches"""

        persona_details = self.personas[persona]
        typo_rate = persona_details["typo_rate"]

        # Add occasional typos
        if random.random() < typo_rate:
            words = response.split()
            if len(words) > 3:
                # Pick a random word to "misspell"
                idx = random.randint(1, len(words) - 1)
                word = words[idx]
                if len(word) > 3:
                    # Simple typo: swap two adjacent characters
                    pos = random.randint(0, len(word) - 2)
                    word_list = list(word)
                    word_list[pos], word_list[pos + 1] = word_list[pos + 1], word_list[pos]
                    words[idx] = ''.join(word_list)
            response = ' '.join(words)

        # Add ellipsis for thinking
        if random.random() < 0.3:
            response = response.replace('. ', '... ', 1)

        return response

    def get_persona_info(self, persona: str) -> Dict:
        """Get information about a specific persona"""
        return self.personas.get(persona, {})

    def list_personas(self) -> List[str]:
        """List all available personas"""
        return list(self.personas.keys())


# Test the agent
if __name__ == "__main__":
    import asyncio

    agent = AIHoneypotAgent()

    async def test_agent():
        print("🤖 Testing AI Honeypot Agent\n")

        test_scenario = {
            "message": "URGENT! Your bank account will be closed in 24 hours. Click here to verify: http://bit.ly/bank123",
            "scam_type": "phishing"
        }

        conversation_history = []

        for i in range(5):
            response = await agent.generate_response(
                message=test_scenario["message"],
                conversation_history=conversation_history,
                scam_type=test_scenario["scam_type"]
            )

            print(f"Turn {i+1}:")
            print(f"Scammer: {test_scenario['message'][:80]}...")
            print(f"AI Agent: {response}")
            print("-" * 80)

            conversation_history.append({
                "role": "scammer",
                "content": test_scenario["message"],
                "timestamp": int(datetime.utcnow().timestamp() * 1000)
            })
            conversation_history.append({
                "role": "ai_agent",
                "content": response,
                "timestamp": int(datetime.utcnow().timestamp() * 1000)
            })

            # Simulate different scammer messages for next turn
            test_scenario["message"] = f"Please provide your account number now. This is urgent! Turn {i+2}"

    asyncio.run(test_agent())
