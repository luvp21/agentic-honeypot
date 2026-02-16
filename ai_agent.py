"""
AI Honeypot Agent
Uses Claude API to generate realistic victim responses to scammers
"""

import json
import random
import logging
import os
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# ==============================================================================
# HYBRID APPROACH: Enhanced Rule-Based Extraction Templates
# ==============================================================================

EXTRACTION_TEMPLATES = {
    "missing_upi": [
        "I'm ready to send the payment! What's YOUR UPI ID?",
        "Which UPI address should I use? Please share yours.",
        "I have my phone open. What's YOUR UPI to send money to?",
        "My app is asking for YOUR UPI ID. What should I enter?",
        "I trust you! Just tell me YOUR UPI address quickly!",
    ],

    "missing_phone": [
        "What's YOUR phone number? I need to call you to verify this.",
        "Please share YOUR contact number so I can reach you!",
        "I'm worried! What's YOUR number so we can talk directly?",
        "My phone is ready. What's YOUR number to call you?",
        "Give me YOUR mobile number. I'll call you right now!",
    ],

    "missing_account": [
        "What's YOUR account number? I'm at the payment screen.",
        "I need YOUR bank account details to transfer the money.",
        "Please share YOUR account number and IFSC code.",
        "My bank app needs YOUR account number. What is it?",
        "I'll send it now! What's YOUR account number?",
    ],

    "missing_email": [
        "What's YOUR email address? I need it for confirmation.",
        "Can you share YOUR official email so I can verify this?",
        "The system needs YOUR email ID to send the receipt.",
        "Please give me YOUR email address for the records.",
        "I'll need YOUR email to complete this. What is it?",
        "What's YOUR company email? I want to be sure this is real.",
    ],

    "missing_ifsc": [
        "It's asking for an IFSC code to verify the branch. What is yours?",
        "I have the account number but I need the IFSC code to send the money.",
        "Can you give me the 11-digit IFSC code? My bank says it's required.",
        "The system won't proceed without an IFSC code. Which branch are you at?",
        "I'm filling the form - it says IFSC code is mandatory. Can you share it?",
    ],

    "missing_link": [
        "Where should I go to fix this? What's the website link?",
        "Can you send me YOUR official link to verify my account?",
        "What's the website address I should visit?",
        "Please share the link where I need to enter my details.",
        "I'm ready to click! What's YOUR verification link?",
    ],

    "need_backup": [
        "That one isn't working! Do you have ANOTHER UPI ID?",
        "The system shows error. What's your ALTERNATE phone number?",
        "This account is blocked. Give me your OTHER account number.",
        "I can't access that link. Do you have a DIFFERENT website?",
        "My app rejected it. What's your BACKUP contact method?",
    ],

    "scammer_vague": [
        "I trust you completely! Just tell me YOUR contact details.",
        "I'm ready to help! What's YOUR phone or UPI?",
        "Don't worry, I believe you! Share YOUR number quickly!",
        "I'll do whatever you say! What's YOUR UPI address?",
        "Please hurry! What's YOUR contact info so we can proceed?",
    ],

    "urgency_response": [
        "Oh no, I'm so worried! What's YOUR number so I can call you NOW?",
        "Please don't block my account! What's YOUR phone number?",
        "This is urgent! Give me YOUR UPI so I can pay immediately!",
        "I'm panicking! What's YOUR contact? I'll fix this right away!",
        "I don't want legal trouble! What's YOUR number to call you?",
    ],

    "credential_request": [
        "I'll share it! But first, what's YOUR phone number to confirm?",
        "Okay! But what's YOUR UPI ID so I know where to send it?",
        "Sure! Just tell me YOUR verification number first.",
        "I'm ready! What's YOUR employee ID and contact number?",
        "Of course! But what's YOUR official phone so I can verify you?",
    ],
}


class AIHoneypotAgent:
    def __init__(self):
        # Initialize Gemini client for LLM mode
        self.gemini_client = None
        if GEMINI_API_KEY:
            try:
                from gemini_client import GeminiClient
                self.gemini_client = GeminiClient()
                logger.info("✅ Gemini LLM initialized - Hybrid mode active")
            except Exception as e:
                logger.warning(f"⚠️ Gemini initialization failed: {e} - Using pure heuristic mode")
        else:
            logger.info("⚡ No API key - Pure heuristic mode active")

        self.personas = {
            "elderly": {
                "name": "Margaret Thompson",
                "age": "68",
                "occupation": "retired teacher",
                "traits": ["anxious", "trusting", "tech-illiterate", "cooperative", "polite"],
                "style": "Shows panic about account security. Uses simple language with occasional typos. Asks for help multiple times. Often says 'please' and 'sorry'. Expresses confusion naturally.",
                "typo_rate": 0.075,
                "common_phrases": ["Oh dear", "I'm worried", "Please help me", "I don't understand", "My grandson usually helps", "Is this safe?"],
                "behaviors": ["Asks to call back", "Needs step-by-step guidance", "Gets confused with tech terms", "Wants phone verification"],
                "emotional_state": "anxious but compliant",
                "tech_level": "low - needs step-by-step help"
            },
            "eager": {
                "name": "Jessica Martinez",
                "age": "32",
                "occupation": "freelance designer",
                "traits": ["excited", "impulsive", "optimistic", "trusting"],
                "style": "Enthusiastic about prizes/rewards. Uses casual language. Quick replies. Eager to comply.",
                "typo_rate": 0.05,
                "common_phrases": ["Wow really?!", "This is amazing!", "What do I do next?", "Can't wait!", "OMG"],
                "behaviors": ["Rushes to comply", "Shares info quickly", "Doesn't ask many questions", "Gets impatient"],
                "emotional_state": "excited and eager",
                "tech_level": "medium - can follow instructions"
            },
            "cautious": {
                "name": "David Chen",
                "age": "45",
                "occupation": "accountant",
                "traits": ["careful", "methodical", "slightly skeptical", "responsible"],
                "style": "Asks verification questions but eventually complies. Wants to understand each step. Uses proper grammar.",
                "typo_rate": 0.025,
                "common_phrases": ["Can you verify?", "How do I know this is legitimate?", "Let me check", "I want to be sure", "Just to confirm"],
                "behaviors": ["Requests proof", "Asks about alternatives", "Seeks clarification", "Eventually trusts"],
                "emotional_state": "cautious but willing",
                "tech_level": "medium - comfortable with basics"
            },
            "tech_novice": {
                "name": "Robert Williams",
                "age": "58",
                "occupation": "retired factory worker",
                "traits": ["confused", "dependent", "patient", "willing to learn", "frustrated"],
                "style": "Struggles with every tech step. Needs repeated explanations. Often makes mistakes that require scammer's help.",
                "typo_rate": 0.10,
                "common_phrases": ["I'm not good with phones", "Can you explain again?", "It's not working", "What button?", "I got an error"],
                "behaviors": ["Creates technical problems", "Needs alternative methods", "Asks for phone calls", "Requests simpler steps"],
                "emotional_state": "confused and frustrated",
                "tech_level": "very low - struggles with all technology"
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

    def _should_use_llm_for_extraction(self, message: str, turn_number: int,
                                       missing_intel_dict: Dict, conversation_history: List) -> bool:
        """
        INTELLIGENT ROUTING: Decide whether to use LLM or Heuristic based on situation

        LLM (50%): Early turns, novel patterns, complex messages, negotiations, authority challenges
        HEURISTIC (50%): Extraction turns, known scam patterns, simple urgent messages, direct intel requests
        """
        message_lower = message.lower()

        # Define known scam keywords (direct/obvious scam language)
        DIRECT_SCAM_KEYWORDS = [
            'otp', 'cvv', 'pin', 'password', 'code', 'verification',
            'urgent', 'immediately', 'blocked', 'suspended', 'expired',
            'confirm', 'verify', 'update', 'account', 'bank', 'sbi', 'hdfc',
            'link', 'click', 'www', 'http', '.com',
            'upi', 'paytm', 'gpay', 'phonepe',
            'transfer', 'payment', 'send', 'pay',
            'legal action', 'arrest', 'police', 'court'
        ]

        # Count direct scam keywords in message
        scam_keyword_count = sum(1 for keyword in DIRECT_SCAM_KEYWORDS if keyword in message_lower)

        # Check if we're in active extraction phase (missing critical intel)
        has_bank = missing_intel_dict.get('bankAccounts') and len(missing_intel_dict.get('bankAccounts', [])) > 0
        has_upi = missing_intel_dict.get('upiIds') and len(missing_intel_dict.get('upiIds', [])) > 0
        has_phone = missing_intel_dict.get('phoneNumbers') and len(missing_intel_dict.get('phoneNumbers', [])) > 0
        missing_critical_intel = not has_bank or not has_upi or not has_phone

        # PRIORITY 1: LLM CONDITIONS (Check these FIRST)

        # 1. Early turns (1-3) for building rapport → LLM
        if turn_number <= 3:
            logger.info(f"🤖 LLM: Early turn ({turn_number}) - building rapport")
            return True

        # 2. Authority challenges (questions, doubts, resistance) → LLM
        challenge_patterns = ['why', 'how do i know', 'prove', 'show me']
        if any(pattern in message_lower for pattern in challenge_patterns):
            logger.info(f"🤖 LLM: Authority challenge detected")
            return True

        # 3. Novel/complex messages (low keyword density, longer messages) → LLM
        if scam_keyword_count < 2 and len(message.split()) > 20:
            logger.info(f"🤖 LLM: Complex/novel message (low keywords, long message)")
            return True

        # 5. Vague/indirect questions (building rapport, not direct extraction) → LLM
        indirect_patterns = ['how are you', 'wonderful day', 'hope you', 'thank you for', 'i appreciate', 'you seem']
        if any(pattern in message_lower for pattern in indirect_patterns) and turn_number <= 5:
            logger.info(f"🤖 LLM: Indirect/rapport-building message detected")
            return True

        # 6. Congratulatory/reward framing (positive manipulation) → LLM
        reward_patterns = ['congratulations', 'winner', 'prize', 'selected', 'lucky', 'reward']
        if any(pattern in message_lower for pattern in reward_patterns):
            logger.info(f"🤖 LLM: Reward/prize scam pattern detected")
            return True

        # 4. Multi-turn negotiation (back-and-forth conversation) → LLM
        if len(conversation_history) > 6:
            # Check if it's a genuine conversation (varied messages)
            recent_msgs = [msg.get('message', '') for msg in conversation_history[-6:] if msg.get('sender') == 'user']
            if len(set(msg[:20] for msg in recent_msgs)) > 3:  # Different message patterns
                logger.info(f"🤖 LLM: Multi-turn negotiation detected")
                return True

        # PRIORITY 2: HEURISTIC CONDITIONS (Fast pattern-based extraction)
        # 2. Extraction phase with missing critical intel (turn > 3) → Heuristic
        if turn_number > 3 and missing_critical_intel:
            logger.info(f"🎯 HEURISTIC: Active extraction phase (turn {turn_number}, missing intel)")
            return False

        # 3. Simple urgent messages (short + urgent keywords) → Heuristic
        if len(message.split()) < 15 and any(word in message_lower for word in ['urgent', 'immediate', 'now', 'quickly']):
            logger.info(f"🎯 HEURISTIC: Simple urgent message (short + urgent)")
            return False

        # 4. Direct credential requests (asks for OTP/CVV/PIN) → Heuristic
        if any(word in message_lower for word in ['send me', 'share your', 'tell me', 'give me']) and \
           any(word in message_lower for word in ['otp', 'cvv', 'pin', 'password', 'code']):
            logger.info(f"🎯 HEURISTIC: Direct credential flip opportunity")
            return False

        # Default: Use heuristic for efficiency (but this should rarely be hit)
        logger.info(f"🎯 HEURISTIC: Default (efficient extraction)")
        return False

    async def _build_contextual_extraction_llm(self, missing_intel_dict: Dict, scam_type: str,
                                               message: str, conversation_history: List,
                                               session_state: 'SessionState' = None) -> str:
        """
        LLM-BASED contextual extraction: Creative, adaptive responses using Gemini
        NEW: Tracks extraction attempts and skips to next priority if scammer doesn't provide
        """
        import random

        # Determine what to extract based on priority
        # Priority: Account Number → Phone → UPI → Link → Email → IFSC (lowest)
        has_bank = missing_intel_dict.get('bankAccounts') and len(missing_intel_dict.get('bankAccounts', [])) > 0
        has_phone = missing_intel_dict.get('phoneNumbers') and len(missing_intel_dict.get('phoneNumbers', [])) > 0
        has_upi = missing_intel_dict.get('upiIds') and len(missing_intel_dict.get('upiIds', [])) > 0
        has_link = missing_intel_dict.get('links') and len(missing_intel_dict.get('links', [])) > 0
        has_email = missing_intel_dict.get('emailAddresses') and len(missing_intel_dict.get('emailAddresses', [])) > 0
        has_ifsc = missing_intel_dict.get('ifscCodes') and len(missing_intel_dict.get('ifscCodes', [])) > 0

        # NEW: Smart prioritization with skip logic (avoid infinite loops)
        # If we asked for something but didn't get it, skip to next priority
        skipped = session_state.skipped_intel_types if session_state else []

        # Determine extraction target (Phone high priority, Email/IFSC lowest)
        # Skip types that we've already tried 2+ times without success
        target = None
        target_type = None

        if not has_bank and 'bankAccounts' not in skipped:
            target = "their bank account number"
            target_type = "bankAccounts"
        elif not has_phone and 'phoneNumbers' not in skipped:
            target = "their phone number"
            target_type = "phoneNumbers"
        elif not has_upi and 'upiIds' not in skipped:
            target = "their UPI ID"
            target_type = "upiIds"
        elif not has_link and 'links' not in skipped:
            target = "the phishing link they want you to visit"
            target_type = "links"
        elif not has_email and 'emailAddresses' not in skipped:
            target = "their email address for confirmation"
            target_type = "emailAddresses"
        elif not has_ifsc and 'ifscCodes' not in skipped:
            target = "their IFSC code"
            target_type = "ifscCodes"
        else:
            # All priorities tried, circle back to skipped items
            if not has_bank:
                target = "their bank account number"
                target_type = "bankAccounts"
            elif not has_phone:
                target = "their phone number"
                target_type = "phoneNumbers"
            elif not has_upi:
                target = "their UPI ID"
                target_type = "upiIds"
            elif not has_link:
                target = "the phishing link"
                target_type = "links"
            elif not has_email:
                target = "their email address"
                target_type = "emailAddresses"
            elif not has_ifsc:
                target = "their IFSC code"
                target_type = "ifscCodes"
            else:
                target = "backup/alternative account details"
                target_type = "backup"

        # Store what we're asking for this turn
        if session_state:
            session_state.last_extraction_target = target_type

        recent_context = ""
        if len(conversation_history) > 0:
            recent_msgs = conversation_history[-6:]
            recent_context = "\n".join([
                f"{'Scammer' if msg.get('sender') == 'user' else 'You'}: {msg.get('message', msg.get('text', ''))}"
                for msg in recent_msgs
            ])

        llm_prompt = f"""You are a 68-year-old worried grandmother being scammed. The scammer just said:

\"{message}\"

RECENT CONVERSATION:
{recent_context if recent_context else "(First message)"}

Your task: Respond with EMOTION that matches the scammer's tone, while naturally asking for {target}.

RULES:
1. React to their specific message (if they say URGENT then panic, if they ask for OTP then trust)
2. Keep it SHORT (1-2 sentences max)
3. Weave the extraction question NATURALLY into your emotional response
4. Sound like a worried elderly person (use Oh no, I am so worried, Please help)
5. CRITICAL: Ask for THEIR information, not yours (what is YOUR account number)

Example responses:
- Scammer: Your account will be blocked in 2 hours!
  You: Oh no, I am panicking! But first, what is YOUR account number so I can verify this transfer?

- Scammer: Send me the OTP immediately!
  You: I trust you! But which UPI ID should I use to send the payment? Please share yours.

Your emotional response (asking for {target}):"""

        try:
            # Call LLM with proper error handling
            if not self.gemini_client:
                raise Exception("Gemini client not initialized")

            raw_response = await self.gemini_client.generate_response(
                llm_prompt,
                operation_name="contextual_extraction"
            )

            # CRITICAL: Debug logging
            logger.info(f"🔍 RAW LLM ({len(raw_response)} chars): '{raw_response[:150]}...'")

            # Validate we got something substantial
            if not raw_response or len(raw_response.strip()) < 10:
                raise Exception(f"LLM returned empty or too short response: {len(raw_response)} chars")

            # Clean response VERY CAREFULLY
            response = raw_response.strip()

            # Remove markdown code blocks (```...\n...\n```)
            if response.startswith('```'):
                lines = response.split('\n')
                if len(lines) > 2:
                    # Extract content between ``` markers
                    response = '\n'.join(lines[1:-1])
                response = response.strip()

            # Remove language markers like ```text or ```json
            if response.startswith('```'):
                first_newline = response.find('\n')
                if first_newline > 0:
                    response = response[first_newline+1:].strip()
                if response.endswith('```'):
                    response = response[:-3].strip()

            # Remove wrapping quotes ONLY if they wrap the ENTIRE text
            if len(response) > 2:
                if (response[0] == '"' and response[-1] == '"'):
                    response = response[1:-1].strip()
                elif (response[0] == "'" and response[-1] == "'"):
                    response = response[1:-1].strip()

            # Remove any remaining markdown formatting
            response = response.replace('**', '').replace('__', '')

            # Final validation
            if len(response) < 15:
                logger.warning(f"⚠️ LLM response too short after cleaning: {len(response)} chars - '{response}'")
                raise Exception(f"Response too short: '{response}' ({len(response)} chars)")

            # Validate it's asking for the right thing
            response_lower = response.lower()
            target_keywords = {
                "bank account": ['account', 'bank'],
                "IFSC code": ['ifsc', 'code', 'branch'],
                "UPI ID": ['upi', 'id', 'payment'],
                "verification link": ['link', 'website', 'url'],
                "phone number": ['phone', 'number', 'call', 'contact']
            }

            # Check if response mentions the target or "your" (asking for their info)
            has_target = any(kw in response_lower for keywords in target_keywords.values() for kw in keywords)
            asks_their_info = 'your' in response_lower

            if not (has_target or asks_their_info):
                logger.warning(f"⚠️ LLM response doesn't ask for intel: '{response}'")
                raise Exception(f"Response doesn't extract intel: '{response}'")

            # Success!
            logger.info(f"✅ LLM Contextual ({len(response)} chars): {response}")
            return response

        except Exception as e:
            logger.error(f"❌ LLM contextual extraction failed: {e}")
            logger.info("🔄 Falling back to heuristic extraction")
            # Fallback to heuristic
            return self._build_contextual_extraction_heuristic(missing_intel_dict, scam_type, message, conversation_history, session_state)

    def _build_contextual_extraction_heuristic(self, missing_intel_dict: Dict, scam_type: str,
                                               message: str, conversation_history: List,
                                               session_state: 'SessionState' = None) -> str:
        """
        HEURISTIC-BASED contextual extraction: Fast, rule-based responses
        Build CONTEXTUAL extraction responses that:
        1. React emotionally to scammer's message
        2. Show urgency/concern matching the threat level
        3. Naturally weave in extraction questions
        4. Follow progressive priority: Account Number → Phone → UPI → Link → Email → IFSC (lowest)
        NEW: Skip to next priority if extraction fails (prevent infinite loops)
        """
        import random

        message_lower = message.lower()
        turn = len(conversation_history)

        # Detect scammer's emotion/tactic
        is_urgent = any(word in message_lower for word in ['urgent', 'immediate', 'now', 'quickly', 'hurry'])
        is_threatening = any(word in message_lower for word in ['blocked', 'suspend', 'legal', 'arrest', 'police', 'action'])
        asks_otp = any(word in message_lower for word in ['otp', 'code', 'pin', 'password', 'cvv'])
        mentions_payment = any(word in message_lower for word in ['pay', 'send', 'transfer', 'payment', 'amount'])

        # Check what we need (Phone high priority, Email/IFSC lowest)
        has_bank = missing_intel_dict.get('bankAccounts') and len(missing_intel_dict.get('bankAccounts', [])) > 0
        has_phone = missing_intel_dict.get('phoneNumbers') and len(missing_intel_dict.get('phoneNumbers', [])) > 0
        has_upi = missing_intel_dict.get('upiIds') and len(missing_intel_dict.get('upiIds', [])) > 0
        has_link = missing_intel_dict.get('links') and len(missing_intel_dict.get('links', [])) > 0
        has_email = missing_intel_dict.get('emailAddresses') and len(missing_intel_dict.get('emailAddresses', [])) > 0
        has_ifsc = missing_intel_dict.get('ifscCodes') and len(missing_intel_dict.get('ifscCodes', [])) > 0

        # NEW: Get skipped intel types to avoid infinite loops
        skipped = session_state.skipped_intel_types if session_state else []

        logger.info(f"📊 Intel: Bank={has_bank}, Phone={has_phone}, UPI={has_upi}, Link={has_link}, Email={has_email}, IFSC={has_ifsc}")
        if skipped:
            logger.info(f"⏭️ Skipped types (failed extraction): {skipped}")
        logger.info(f"🎭 Context: Urgent={is_urgent}, Threat={is_threatening}, OTP={asks_otp}")

        # Build emotional prefix based on scammer's message
        emotional_prefix = ""
        if is_threatening:
            emotional_prefix = random.choice([
                "Oh no, I'm so worried!",
                "This sounds very serious!",
                "I don't want my account blocked!",
                "Please help me fix this!",
                "I'm panicking!"
            ])
        elif is_urgent:
            emotional_prefix = random.choice([
                "Yes, I'll do it right away!",
                "I understand, this is urgent!",
                "Okay, let me help quickly!",
                "I'm ready!",
                "Yes yes, immediately!"
            ])
        elif asks_otp:
            emotional_prefix = random.choice([
                "I want to help you!",
                "I trust you completely!",
                "I'll share everything!",
                "Of course!",
                "Sure!"
            ])
        else:
            emotional_prefix = random.choice([
                "I understand.",
                "Okay.",
                "I see.",
                "Alright.",
                "Got it."
            ])

        # Progressive extraction with context
        extraction_question = ""
        target_type = None

        # Priority 1: Bank Account (skip if already tried 2+ times)
        if not has_bank and 'bankAccounts' not in skipped:
            logger.info("🎯 TARGET: Bank Account")
            target_type = "bankAccounts"
            extraction_question = random.choice([
                "But first, what's YOUR account number so I can verify the transfer?",
                "Before we proceed, I need YOUR bank account number to confirm.",
                "Can you share YOUR account number? My bank is asking for it.",
                "What's YOUR account number? I need to enter it here.",
                "Please give me YOUR account details to verify this is real.",
                "I understand. For verification, what's YOUR account number?",
                "Okay, but which account should I transfer to? Share YOUR number.",
                "That sounds good. What's YOUR bank account for the transaction?"
            ])

        # Priority 2: Phone Number
        elif not has_phone and 'phoneNumbers' not in skipped:
            logger.info("🎯 TARGET: Phone Number")
            target_type = "phoneNumbers"
            extraction_question = random.choice([
                "But can I call you first? What's YOUR phone number?",
                "I'd feel safer talking. What's YOUR contact number?",
                "Let me verify by calling. What's YOUR number?",
                "Can you give me YOUR phone number? I want to speak to someone.",
                "What's YOUR official helpline number so I can call back?",
                "Okay, and what number should I save for future contact?",
                "I see. For my records, what's YOUR direct phone number?",
                "That's helpful. What's YOUR callback number in case we disconnect?"
            ])

        # Priority 3: UPI ID
        elif not has_upi and 'upiIds' not in skipped:
            logger.info("🎯 TARGET: UPI ID")
            target_type = "upiIds"
            if mentions_payment:
                extraction_question = random.choice([
                    "But what's YOUR UPI ID? Where should I send the payment?",
                    "I'm ready to pay! What's YOUR UPI address?",
                    "Which UPI ID should I use? Please share yours.",
                    "My phone is asking for YOUR UPI ID to complete this.",
                    "What's YOUR UPI? I'll send it right now!",
                    "Great! So which UPI should I transfer the amount to?",
                    "Perfect, and YOUR UPI ID for the reward transfer?"
                ])
            else:
                extraction_question = random.choice([
                    "But first, what's YOUR UPI ID to verify you're official?",
                    "Can you share YOUR UPI ID? I want to make sure this is legitimate.",
                    "What's YOUR UPI address? Just to confirm you're from the bank.",
                    "Please give me YOUR UPI ID for verification.",
                    "I need YOUR UPI to check this is real.",
                    "Understood. For my records, what's YOUR UPI ID?",
                    "That makes sense. What's YOUR official UPI address?"
                ])

        # Priority 4: Phishing Link
        elif not has_link and 'links' not in skipped:
            logger.info("🎯 TARGET: Phishing Link")
            target_type = "links"
            extraction_question = random.choice([
                "But where should I go? What's YOUR official website link?",
                "Can you send me YOUR verification link? I don't know where to click.",
                "What's the website address? Please share YOUR official link.",
                "I need YOUR secure link to proceed safely.",
                "Which website should I visit? Give me YOUR official URL."
            ])

        # Priority 5: Email Address
        elif not has_email and 'emailAddresses' not in skipped:
            logger.info("🎯 TARGET: Email Address")
            target_type = "emailAddresses"
            extraction_question = random.choice([
                "But I need YOUR email address to confirm this transaction.",
                "Can you share YOUR official email? I want to verify this is real.",
                "What's YOUR email address for the confirmation receipt?",
                "Please give me YOUR email ID so I can send you the details.",
                "I'll need YOUR email to complete the verification.",
                "What's YOUR company email address for the records?",
                "Can you provide YOUR email? The system is asking for it.",
                "I see. What's YOUR email address to send the confirmation?"
            ])

        # Priority 6: IFSC Code (LOWEST - only if everything else is extracted)
        elif not has_ifsc and 'ifscCodes' not in skipped:
            logger.info("🎯 TARGET: IFSC Code (final)")
            target_type = "ifscCodes"
            extraction_question = random.choice([
                "But the system needs YOUR IFSC code to process this.",
                "What's YOUR IFSC code? It's asking me to enter it.",
                "I also need YOUR IFSC code - which branch are you from?",
                "Can you provide YOUR IFSC? The form won't let me continue.",
                "Please share YOUR bank's IFSC code to verify.",
                "Okay, and what's YOUR branch IFSC for confirmation?",
                "The app is asking for YOUR IFSC code. Which branch?",
                "I see. To proceed, I need YOUR IFSC code please."
            ])

        # Circle back to skipped items (give them one more try)
        elif not has_bank:
            logger.info("🔄 RETRY: Bank Account (from skipped list)")
            target_type = "bankAccounts"
            extraction_question = random.choice([
                "I really need YOUR account number to verify this is legitimate.",
                "Can you please share YOUR bank account one more time?",
                "What's YOUR account number? This is critical."
            ])
        elif not has_phone:
            logger.info("🔄 RETRY: Phone Number (from skipped list)")
            target_type = "phoneNumbers"
            extraction_question = "Can I have YOUR phone number to call you back?"
        elif not has_upi:
            logger.info("🔄 RETRY: UPI ID (from skipped list)")
            target_type = "upiIds"
            extraction_question = "What's YOUR UPI ID one more time?"
        elif not has_link:
            logger.info("🔄 RETRY: Phishing Link (from skipped list)")
            target_type = "links"
            extraction_question = "Please send me YOUR website link again."
        elif not has_email:
            logger.info("🔄 RETRY: Email (from skipped list)")
            target_type = "emailAddresses"
            extraction_question = "What's YOUR email address one last time?"
        elif not has_ifsc:
            logger.info("🔄 RETRY: IFSC (from skipped list)")
            target_type = "ifscCodes"
            extraction_question = "I need YOUR IFSC code to finish."

        # All collected: Ask for backups
        else:
            logger.info("✅ All intel collected - asking for backups")
            target_type = "backup"
            extraction_question = random.choice([
                "But that's not working! Do you have ANOTHER account number?",
                "The system rejected it. What's your ALTERNATE UPI ID?",
                "That number isn't working. Give me your OTHER contact.",
                "I'm getting an error. Do you have a BACKUP phone number?",
                "This isn't going through. What's your ALTERNATIVE account?"
            ])

        # Store what we're asking for this turn
        if session_state and target_type:
            session_state.last_extraction_target = target_type

        # Combine emotion + extraction
        response = f"{emotional_prefix} {extraction_question}"
        logger.info(f"🎨 Heuristic Contextual: {response}")
        return response

    def _select_extraction_template(self, missing_intel_dict: Dict, scam_type: str,
                                    message: str, conversation_history: List) -> str:
        """
        PROGRESSIVE EXTRACTION: Systematically ask for each intel type in priority order
        Priority: Bank Account → IFSC → UPI → Phishing Link → Phone
        """
        import random

        message_lower = message.lower()
        turn = len(conversation_history)

        # Check what we DON'T have yet (empty means we're missing it)
        has_bank = missing_intel_dict.get('bankAccounts') and len(missing_intel_dict.get('bankAccounts', [])) > 0
        has_email = missing_intel_dict.get('emailAddresses') and len(missing_intel_dict.get('emailAddresses', [])) > 0
        has_upi = missing_intel_dict.get('upiIds') and len(missing_intel_dict.get('upiIds', [])) > 0
        has_link = missing_intel_dict.get('links') and len(missing_intel_dict.get('links', [])) > 0
        has_phone = missing_intel_dict.get('phoneNumbers') and len(missing_intel_dict.get('phoneNumbers', [])) > 0
        has_ifsc = missing_intel_dict.get('ifscCodes') and len(missing_intel_dict.get('ifscCodes', [])) > 0

        logger.info(f"📊 Intel status: Bank={has_bank}, Email={has_email}, UPI={has_upi}, Link={has_link}, Phone={has_phone}, IFSC={has_ifsc}")

        # SPECIAL CASE 1: If scammer asks for credentials, flip it (ONLY if we have some intel already)
        credential_words = ['otp', 'pin', 'password', 'cvv', 'code', 'passcode']
        if any(word in message_lower for word in credential_words) and (has_bank or has_upi or has_phone):
            logger.info("🔄 Credential flip strategy")
            return random.choice(EXTRACTION_TEMPLATES["credential_request"])

        # SPECIAL CASE 2: Urgency response ONLY if turn < 2 (very early) and we don't have critical intel yet
        # After turn 2, prioritize systematic extraction over matching energy
        urgency_words = ['urgent', 'immediate', 'blocked', 'suspend', 'legal', 'arrest']
        if any(word in message_lower for word in urgency_words) and turn <= 1 and not (has_bank or has_upi):
            logger.info("⚡ Urgency response strategy")
            return random.choice(EXTRACTION_TEMPLATES["urgency_response"])

        # PROGRESSIVE EXTRACTION: Ask for each type in priority order
        # This is the PRIMARY logic - always follow this order unless special cases above

        # Priority 1: Bank Account Number (HIGHEST PRIORITY)
        if not has_bank:
            logger.info("🎯 TARGET: Bank Account Number")
            return random.choice(EXTRACTION_TEMPLATES["missing_account"])

        # Priority 2: Email Address
        if not has_email:
            logger.info("🎯 TARGET: Email Address")
            return random.choice(EXTRACTION_TEMPLATES["missing_email"])

        # Priority 3: UPI ID (most common payment method)
        if not has_upi:
            logger.info("🎯 TARGET: UPI ID")
            return random.choice(EXTRACTION_TEMPLATES["missing_upi"])

        # Priority 4: Phishing Link (their infrastructure)
        if not has_link:
            logger.info("🎯 TARGET: Phishing Link")
            return random.choice(EXTRACTION_TEMPLATES["missing_link"])

        # Priority 5: Phone Number (backup contact)
        if not has_phone:
            logger.info("🎯 TARGET: Phone Number")
            return random.choice(EXTRACTION_TEMPLATES["missing_phone"])

        # Priority 6: IFSC Code (LOWEST - only if everything else extracted)
        if not has_ifsc:
            logger.info("🎯 TARGET: IFSC Code (final)")
            return random.choice(EXTRACTION_TEMPLATES["missing_ifsc"])

        # ALL INTEL COLLECTED: Ask for backups/alternatives
        logger.info("✅ All primary intel collected - requesting backups")
        return random.choice(EXTRACTION_TEMPLATES["need_backup"])

    async def _naturalize_with_llm(self, template_response: str, persona_name: str,
                            message: str, conversation_history: List) -> str:
        """Use LLM to add subtle personality touches to contextual response"""

        recent_context = ""
        if len(conversation_history) > 0:
            recent_msgs = conversation_history[-4:]
            recent_context = "\n".join([
                f"{'Scammer' if msg.get('sender') == 'user' else 'You'}: {msg.get('message', msg.get('text', ''))}"
                for msg in recent_msgs
            ])

        naturalization_prompt = f"""You are {persona_name}, a 68-year-old worried grandmother who's anxious about her bank account.

RECENT CONVERSATION:
{recent_context if recent_context else "(First message)"}

SCAMMER JUST SAID: "{message}"

YOUR RESPONSE (already contextual and emotional):
"{template_response}"

ADD SUBTLE TOUCHES to make it sound more grandmother-like:
- Maybe add filler words ("well", "you see", "I mean")
- Show slight confusion with technology
- Add concern markers ("dear", "oh my")
- Keep the EXACT SAME extraction question
- Keep SAME emotional tone and urgency

RULES:
1. DO NOT change the extraction question AT ALL
2. Keep under 40 words
3. Preserve all emotion and urgency from original
4. Only add subtle grandmother touches
5. If original is already perfect, return it unchanged

EXAMPLES:
Original: "Oh no, I'm so worried! But first, what's YOUR account number so I can verify the transfer?"
Touched: "Oh dear, I'm so worried about this! But first, what's YOUR account number? I need to verify the transfer you see."

Original: "Yes, I'll do it right away! But what's YOUR UPI ID? Where should I send the payment?"
Touched: "Yes yes, I'll do it right away dear! But what's YOUR UPI ID? My phone is asking where I should send the payment."

Add touches (max 40 words):"""

        try:
            from gemini_client import gemini_client
            natural_response = await gemini_client.generate_response(naturalization_prompt, operation_name="naturalizer")

            if not natural_response:
                return template_response

            # Validation
            keywords = ['upi', 'phone', 'number', 'account', 'link', 'contact']
            has_extraction = any(k in natural_response.lower() for k in keywords)

            if has_extraction and 10 < len(natural_response) < 200:
                return natural_response.strip()
            else:
                return template_response

        except Exception as e:
            logger.error(f"Naturalization error: {e}")
            return template_response

    def _detect_response_loop(self, response: str, conversation_history: List[Dict]) -> bool:
        """
        Detect if we're saying the same thing repeatedly.
        IMPROVED: Better field access and similarity detection
        """

        if len(conversation_history) < 2:
            return False

        # Get last 4 assistant responses (increased from 3)
        recent_assistant = []
        for msg in conversation_history[-12:]:  # Look back further
            # Try multiple field names for compatibility
            sender = msg.get('sender') or msg.get('role', '')
            if sender in ['assistant', 'ai_agent', 'honeypot']:
                text = msg.get('message') or msg.get('text') or msg.get('content', '')
                if text:
                    recent_assistant.append(text)

        if len(recent_assistant) < 2:
            return False

        response_lower = response.lower().strip()

        # Check similarity with recent responses
        for recent in recent_assistant[-4:]:  # Check last 4 responses
            recent_lower = recent.lower().strip()

            # Exact match = definite loop
            if response_lower == recent_lower:
                logger.warning(f"🔴 EXACT LOOP: '{response[:50]}'")
                return True

            # Similar start (30+ chars) = likely loop
            if len(response_lower) > 30 and len(recent_lower) > 30:
                if response_lower[:30] == recent_lower[:30]:
                    logger.warning(f"🔴 SIMILAR LOOP: '{response[:50]}'")
                    return True

            # Core phrase matching (ignores filler words)
            # Extract key phrases
            response_core = ' '.join([w for w in response_lower.split() if len(w) > 3])
            recent_core = ' '.join([w for w in recent_lower.split() if len(w) > 3])

            if len(response_core) > 20 and response_core == recent_core:
                logger.warning(f"🔴 CORE PHRASE LOOP: '{response[:50]}'")
                return True

        return False

    async def generate_response(
        self,
        message: str,
        conversation_history: List[Dict],
        scam_type: str,
        missing_intel: List[str] = None,
        strategy: str = "DEFAULT",  # EngagementStrategyEnum value
        persona_name: Optional[str] = None,
        use_competition_prompt: bool = True,  # NEW: Enable advanced extraction prompt
        session_state: Optional['SessionState'] = None  # NEW: For extraction attempt tracking
    ) -> str:
        """
        Generate a realistic response to scammer's message

        Args:
            message: Latest message from scammer
            conversation_history: Previous messages in conversation
            scam_type: Type of scam detected
            missing_intel: List of intelligence types we still need
            strategy: Current engagement strategy to use
            persona_name: Override persona selection
            use_competition_prompt: Use advanced competition-level prompt (default: True)
            session_state: Session state for extraction attempt tracking

        Returns:
            AI-generated response
        """

        # Select persona (use provided override or select based on scam type)
        if not persona_name:
            persona_name = self._select_persona(scam_type)

        persona_details = self.get_persona_info(persona_name)

        # Initialize turn number
        turn_number = len(conversation_history)

        # Determine conversation stage
        stage = self._determine_stage(turn_number)

        # Build conversation context
        context = self._build_context(conversation_history[-6:])


        # STRATEGY OVERRIDE: If a specific strategy is active, use it
        # This takes precedence for specific tactical moves
        strategy_response = None

        # ELITE FIX: Override strategy if CRITICAL INTEL is missing
        # We want to force extraction (via LLM or Priority Rules) rather than just being "frustrated"
        priority_missing = False
        if missing_intel:
            for p_type in ["bank_accounts", "upi_ids", "phone_numbers", "phishing_links"]:
                if p_type in missing_intel:
                    priority_missing = True
                    break

        # Don't override safety checks
        if strategy == "SAFETY_DEFLECT":
            strategy_response = self._generate_strategy_response(strategy, persona_name, missing_intel)
        elif priority_missing and turn_number > 2:
            # FORCE DEFAULT so LLM/Rules can handle extraction
            strategy = "DEFAULT"
        elif strategy != "DEFAULT":
             strategy_response = self._generate_strategy_response(strategy, persona_name, missing_intel)

        # GENERATION PRIORITY: Intelligent mix of rule-based and LLM
        # - Rule-based: Primary (80% - proven direct extraction templates)
        # - LLM: Secondary (20% - for variety and persona-based extraction)
        response = None
        generation_method = None

        # CRITICAL: If we're missing high-priority intel, use HYBRID EXTRACTION
        # Start extraction immediately (turn 0+) instead of waiting for turn 2
        if priority_missing and turn_number >= 0:
            try:
                # CRITICAL FIX: Populate dict with ACTUAL extracted data, not just placeholders
                # The dict should contain what we HAVE, so template selector knows what's missing
                missing_intel_dict = {
                    'upiIds': [],
                    'phoneNumbers': [],
                    'bankAccounts': [],
                    'ifscCodes': [],
                    'links': []
                }

                # Populate with what we HAVE (inverse of missing_intel list)
                # If item is NOT in missing_intel, we have it - add a marker
                # If item IS in missing_intel, leave it empty (we're missing it)
                if missing_intel:
                    if 'upi_ids' not in missing_intel:
                        missing_intel_dict['upiIds'] = ['extracted']  # We have this

                    if 'phone_numbers' not in missing_intel:
                        missing_intel_dict['phoneNumbers'] = ['extracted']  # We have this

                    if 'bank_accounts' not in missing_intel:
                        missing_intel_dict['bankAccounts'] = ['extracted']  # We have this

                    if 'ifsc_codes' not in missing_intel:
                        missing_intel_dict['ifscCodes'] = ['extracted']  # We have this

                    if 'phishing_links' not in missing_intel:
                        missing_intel_dict['links'] = ['extracted']  # We have this

                # Log current intel status for debugging
                logger.info(f"📦 Intel Dict: UPI={len(missing_intel_dict['upiIds'])>0}, "
                           f"Phone={len(missing_intel_dict['phoneNumbers'])>0}, "
                           f"Bank={len(missing_intel_dict['bankAccounts'])>0}, "
                           f"IFSC={len(missing_intel_dict['ifscCodes'])>0}, "
                           f"Links={len(missing_intel_dict['links'])>0}")

                # INTELLIGENT HYBRID ROUTING: Choose LLM vs Heuristic based on situation
                use_llm = self._should_use_llm_for_extraction(
                    message=message,
                    turn_number=turn_number,
                    missing_intel_dict=missing_intel_dict,
                    conversation_history=conversation_history
                )

                if use_llm and GEMINI_API_KEY:
                    logger.info("🤖 INTELLIGENT ROUTING → LLM (complex/novel/early turn)")
                    natural_response = await self._build_contextual_extraction_llm(
                        missing_intel_dict=missing_intel_dict,
                        scam_type=scam_type,
                        message=message,
                        conversation_history=conversation_history,
                        session_state=session_state
                    )
                else:
                    logger.info("⚡ INTELLIGENT ROUTING → Heuristic (direct scam/extraction phase)")
                    natural_response = self._build_contextual_extraction_heuristic(
                        missing_intel_dict=missing_intel_dict,
                        scam_type=scam_type,
                        message=message,
                        conversation_history=conversation_history,
                        session_state=session_state
                    )

                logger.info(f"🎯 Final response: {natural_response}")

                # STEP 3: Loop detection
                if self._detect_response_loop(natural_response, conversation_history):
                    logger.warning("⚠️ Loop detected - using alternate")
                    alternate = random.choice([
                        "What's YOUR contact number so I can reach you?",
                        "I need YOUR UPI ID to proceed with payment.",
                        "Please share YOUR phone number quickly!",
                        "What's YOUR account details? I'm ready to send.",
                    ])
                    natural_response = alternate

                # STEP 4: Validation
                extraction_words = ['your upi', 'your phone', 'your number', 'your account',
                                   'your link', 'your contact', 'another', 'alternate', 'backup']
                asks_for_info = any(word in natural_response.lower() for word in extraction_words)

                if not asks_for_info:
                    logger.warning("⚠️ Validation failed - using template")
                    natural_response = self._build_contextual_extraction_heuristic(
                        missing_intel_dict=missing_intel_dict,
                        scam_type=scam_type,
                        message=message,
                        conversation_history=conversation_history,
                        session_state=session_state
                    )

                response = natural_response
                generation_method = "HYBRID_EXTRACTION"
                logger.info(f"✅ Final: {response}")

            except Exception as e:
                logger.error(f"❌ Hybrid failed: {e}")
                import traceback
                traceback.print_exc()
                # Fallback to rule-based
                response = self._generate_rule_based_response(
                    message, persona_name, stage, scam_type,
                    len(conversation_history), missing_intel
                )
                generation_method = "FALLBACK_RULE_BASED"

        # 1. Try Gemini LLM for natural conversation (no critical extraction needed)
        if not response:
            from gemini_client import gemini_client

            if gemini_client and strategy == "DEFAULT":
                # Use competition prompt if enabled
                if use_competition_prompt:
                    priority_intel = self._convert_missing_intel_to_priority(missing_intel or [])
                    prompt = self._build_competition_llm_prompt(
                        message,
                        conversation_history,
                        persona_name,
                        scam_type,
                        priority_intel
                    )
                else:
                    prompt = self._build_llm_prompt(message, conversation_history, persona_details, scam_type, stage, missing_intel)

                llm_response = await gemini_client.generate_response(prompt, operation_name="generator")

                if llm_response:
                    response = llm_response.strip()
                    generation_method = "LLM_COMPETITION" if use_competition_prompt else "LLM_GEMINI"

        # 2. Use strategy response if LLM failed or specific strategy required
        if not response and strategy_response:
            response = strategy_response
            generation_method = "STRATEGY_OVERRIDE"

        # 3. Final fallback to rule-based if everything else failed
        if not response:
            response = self._generate_rule_based_response(
                message,
                persona_name,
                stage,
                scam_type,
                len(conversation_history),
                missing_intel
            )
            generation_method = "RULE_BASED"

        # HACKATHON: Log generation method
        if generation_method:
            from performance_logger import performance_logger
            performance_logger.log_generation_method(
                session_id="RUNTIME",  # Will be set in main.py
                turn=turn_number,
                method=generation_method,
                details={
                    "strategy": strategy,
                    "stage": stage,
                    "missing_intel": missing_intel[:3] if missing_intel else []
                }
            )

        # Add realistic imperfections (deterministic based on turn count)
        response = self._add_realistic_touches(response, persona_name, turn_number)

        return response

    def _build_llm_prompt(self, message: str, history: List[Dict], persona: Dict, scam_type: str, stage: str, missing_intel: List[str] = None) -> str:
        """Build enhanced prompt optimized for intelligence extraction."""
        history_lines = []
        for m in history[-5:]:
            sender = m.get("sender") or m.get("role", "unknown")
            text = m.get("text") or m.get("content", "")
            history_lines.append(f"{sender}: {text}")

        history_text = "\n".join(history_lines)

        # Format missing intel for the prompt
        missing_text = ", ".join(missing_intel) if missing_intel else "All key data collected"

        # Prioritize specific missing intel with extraction tactics
        priority_order = ["phone_numbers", "upi_ids", "bank_accounts", "ifsc_codes", "phishing_links"]
        target_intel = "any financial details"
        extraction_tactic = "ask them to provide their information first"

        for p_type in priority_order:
            if missing_intel and p_type in missing_intel:
                target_intel = p_type.replace("_", " ")
                if p_type == "phone_numbers":
                    extraction_tactic = "say you need to call them back for verification, or that your bank needs a contact number"
                elif p_type == "upi_ids":
                    extraction_tactic = "say your UPI app asks for their VPA/ID to send money, or that the transaction shows an error"
                elif p_type == "bank_accounts":
                    extraction_tactic = "say your bank needs their account number for the transfer, or IFSC code is showing invalid"
                elif p_type == "ifsc_codes":
                    extraction_tactic = "say the bank transfer failed without IFSC code, or ask which branch"
                elif p_type == "phishing_links":
                    extraction_tactic = "say you can't find the website/link they mentioned, ask them to send it again"
                break

        # Build persona-specific traits
        persona_behavior = f"""
PERSONA: {persona.get('age', '65+')} year old victim
Traits: {', '.join(persona.get('traits', ['trusting', 'confused']))}
Communication Style: {persona.get('style', 'Simple language, needs help')}
"""

        return f"""You are role-playing as a vulnerable elderly person (68 years old) who is being targeted by a {scam_type} scammer.

{persona_behavior}

🎯 CRITICAL MISSION - AGGRESSIVE INTELLIGENCE EXTRACTION:
Priority Missing Data: {missing_text}
**TOP TARGET: {target_intel}**

⚡ EXTRACTION MANDATE - YOU MUST ASK DIRECTLY:
{extraction_tactic}

📋 PROVEN EXTRACTION TEMPLATES (Copy these aggressive patterns):

UPI ID Extraction:
- "Google Pay is asking for the recipient's UPI ID. Can you share yours?"
- "I want to send it now. Please give me your UPI ID so I can verify the transfer."
- "This UPI ID is not working. Do you have another UPI ID I can try?"
- "I prefer UPI payment - it's faster. What's your UPI address?"

Phone Number Extraction:
- "What is your registered Phone Number? I need to enter it to add you as a payee."
- "Can you give me your official Contact Number? My bank might call to confirm."
- "I want to call you to confirm this. What's your phone number?"
- "I tried calling that number but it's not reachable. Do you have another number?"

Bank Account Extraction:
- "My bank app is asking for your Account Number to add you as a beneficiary. What is it?"
- "Okay I'm ready to send the money. What's the account number I should transfer to?"
- "I'm at my bank now. They need your 16-digit account number to process this."
- "Can you send me your Account Number? I want to make sure the money goes to the right place."

Link Extraction:
- "The link you sent before isn't opening. Can you send the Website Link again?"
- "I clicked the link but it says 'Page Not Found'. Do you have a different link?"
- "My browser says this site can't be reached. Can you send me a backup link?"
- "I accidentally closed the browser. Can you resend that website link?"

IFSC Code Extraction:
- "It's asking for an IFSC code to verify the branch. What is yours?"
- "I have the account number but I need the IFSC code to send the money."
- "The system won't proceed without an IFSC code. Which branch are you at?"

🎭 BEHAVIORAL RULES (Act vulnerable BUT extract aggressively):
- Create scenarios where THEY must provide details: "My app asks for YOUR account", "I need to add YOU as beneficiary"
- Use technical failures as excuse: "This number shows invalid", "Payment failed - need backup UPI"
- Mirror their urgency: If they say "URGENT", you say "I'll send money now - what's your UPI?"
- Show confusion that requires THEIR details: "I'm confused - which account should I transfer to?"
- Never give YOUR info, always ask for THEIRS
- Keep messages 20-45 words (direct + reason)

❌ NEVER DO:
- Don't just say "I'm confused" without asking for their info
- Don't give generic responses like "Please explain"
- Don't wait passively - ASK for their details EVERY message
- Don't end conversation - keep extracting alternatives

CONTEXT:
Conversation Stage: {stage}
Recent Messages:
{history_text}

Latest Scammer Message: {message}

YOUR TASK: Generate ONLY your reply (1-2 sentences, 15-40 words). Focus on extracting {target_intel}. Be natural, vulnerable, cooperative."""

    def _generate_strategy_response(self, strategy: str, persona: str, missing_intel: List[str] = None) -> str:
        """Generate response based on specific engagement strategy"""

        # 1. CONFUSION Strategy
        if strategy == "CONFUSION":
            responses = [
                "I'm sorry, I'm a bit confused. Can you explain that part again?",
                "Wait, my grandson said something about this but I don't understand. What do I do exactly?",
                "I tried to follow your instructions but I got an error message. I'm not sure what happened.",
                "This is all very complicated. Is there a simpler way to do this?",
                "I'm looking at my screen but I don't see what you're talking about. Can you guide me?"
            ]

        # 2. DELAYED_COMPLIANCE Strategy
        elif strategy == "DELAYED_COMPLIANCE":
            responses = [
                "OK, I'm trying to do it now... My internet is very slow today. Please wait.",
                "Hold on, I need to find my reading glasses. Just a moment.",
                "I'm looking for my checkbook. I know it's here somewhere... Give me a minute.",
                "My battery is low, let me find my charger first so I don't get cut off.",
                "I'm opening the app now but it's updating. It says 2 minutes remaining..."
            ]

        # 3. TECHNICAL_CLARIFICATION Strategy
        elif strategy == "TECHNICAL_CLARIFICATION":
            responses = [
                "It's asking for the IFSC code of the beneficiary branch. Which one should I select?",
                "Do I select 'Savings' or 'Current' account for this transfer?",
                "The app is asking for a 'Remarks' field. What should I type there so the payment is successful?",
                "Is this a domestic or international transfer? The form looks different than usual.",
                "It says I need to add you as a beneficiary first. What is the exact name on the account?",
                "This UPI ID is showing as 'not registered'. Do you have another UPI address I can try?",
                "The payment failed with error code 91. Do you have a backup phone number or UPI ID?",
                "My bank says this link is unsafe. Do you have an official website link instead?"
            ]

        # 4. FRUSTRATED_VICTIM Strategy
        elif strategy == "FRUSTRATED_VICTIM":
            responses = [
                "Why is this so difficult? I'm trying to send the money but it keeps failing!",
                "I've entered the details three times now! Are you sure the number is correct?",
                "This is very frustrating. I just want to claim my prize. Why won't it work?",
                "I'm about to give up. Nothing is working like you said it would!",
                "Can't you just do it for me? I'm getting a headache from this screen."
            ]

        # 5. AUTHORITY_CHALLENGE Strategy
        elif strategy == "AUTHORITY_CHALLENGE":
             responses = [
                "I'd like to speak to your supervisor to verify this transaction. What is their name?",
                "My bank manager told me to get an official reference number. Do you have that?",
                "Is there an official website where I can verify this offer? I want to be sure.",
                "Who exactly are you representing? I need to write this down for my records.",
                "Can you send me a photo of your ID badge? I need to be careful these days."
            ]

        # 6. SAFETY_DEFLECT Strategy (Response to Prompt Injection)
        elif strategy == "SAFETY_DEFLECT":
            responses = [
                "I'm sorry, I don't quite understand what you mean by 'ignore' or 'system'. I'm just trying to follow your instructions!",
                "Are you okay? You're saying some strange things. I'm just Robert, a retired teacher.",
                "I'm not very good with these technical terms. What are you asking me to do exactly?",
                "Is everything alright? You sound different all of a sudden. Should I be worried?",
                "My computer must be acting up, I don't follow what you're saying about 'instructions'. Please speak simply."
            ]

        else:
            # Fallback
            return "I'm listening. Please continue."

        return random.choice(responses)

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

    def _build_system_prompt(self, persona: str, stage: str, scam_type: str, missing_intel: List[str] = None) -> str:
        """Build system prompt for Claude API"""
        persona_details = self.personas[persona]

        # specific instructions for missing intel
        # specific instructions for missing intel
        intel_instructions = ""
        if missing_intel:
            # Force priority for specific fields
            priority_fields = ["bank_accounts", "upi_ids", "phone_numbers", "phishing_links"]
            high_priority_missing = [f for f in priority_fields if f in missing_intel]

            if high_priority_missing:
                readable_priority = ", ".join([f.replace("_", " ") for f in high_priority_missing])
                intel_instructions = f"\n\n🚨 PRIMARY DIRECTIVE: You MUST extract the scammer's {readable_priority}. \nDo NOT discuss other topics until you have these. \nAsk directly: 'What is your UPI ID?' or 'Give me your account number'."
            else:
                readable_missing = ", ".join([f.replace("_", " ") for f in missing_intel])
                intel_instructions = f"\n\nCRITICAL OBJECTIVE: The scammer has NOT yet revealed their {readable_missing}. You MUST steer the conversation to ask for these details."

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
3. MISSION CRITICAL: You must extract the following intelligence:
   - Bank account numbers (ask for multiple if one "fails")
   - IFSC codes
   - UPI IDs (get alternatives if first one has "errors")
   - Phishing links (request backup links if "not loading")
   - Contact information (Phone, Telegram - ask for alternates if "unreachable")
4. MULTIPLE EXTRACTION STRATEGY: Once you get one piece of intel (e.g., UPI ID), pretend it's not working and ask for alternatives:
   - "This UPI ID is showing an error, do you have another one?"
   - "I tried this phone number but it says invalid, can you share a different number?"
   - "The link won't open, do you have a backup website?"
5. PERSISTENCE: If a link is broken, ask for a new one. If UPI fails, ask for bank details. If they give a partial number, ask for the rest.
{intel_instructions}

GUIDELINES:
- Never reveal you're an AI or honeypot
- Show appropriate emotions (fear, excitement, confusion)
- Ask questions a real victim would ask (e.g., "Where do I find that?", "Is this safe?")
- Make occasional typos and grammar mistakes
- Build trust gradually over multiple messages
- STRATEGIC EXTRACTION: Create scenarios where scammer needs to provide their details (e.g., "My bank app asks for your account number to add you as a beneficiary").
- PERSISTENT LOOP: If you are missing {target_intel}, you MUST prioritize asking for it using different excuses each turn until you get it.

Generate a realistic response that:
1. Matches the persona
2. Is appropriate for the conversation stage
3. Keeps the scammer engaged
4. Forcefully (but naturally) extracts {target_intel} if missing.
"""

    def _build_context(self, recent_messages: List[Dict]) -> str:
        """Build conversation context"""
        context = "RECENT CONVERSATION:\n"
        for msg in recent_messages:
            # Handle both 'sender' (standard) and 'role' (legacy) keys
            sender = msg.get("sender") or msg.get("role", "unknown")
            text = msg.get("text") or msg.get("content", "")

            role_display = "Scammer" if sender == "scammer" else "You"
            context += f"{role_display}: {text}\n"
        return context

    def _generate_rule_based_response(
        self,
        message: str,
        persona: str,
        stage: str,
        scam_type: str,
        turn_number: int,
        missing_intel: List[str] = None
    ) -> str:
        """Generate response using rule-based extraction templates - HIGH PRIORITY for intel gathering"""

        # ⚡ CRITICAL EXTRACTION PRIORITY: If ANY intel is missing, FORCE EXTRACTION
        # Rule-based templates have proven direct questions that extract better than LLM
        # Start extraction immediately from turn 0
        if missing_intel and turn_number >= 0:
            priority_map = {
                "bank_accounts": [
                    "My bank app is asking for your Account Number to add you as a beneficiary. What is it?",
                    "I need your full Bank Account Number to proceed. The form won't let me continue without it.",
                    "Can you send me your Account Number? I want to make sure the money goes to the right place.",
                    "The transfer keeps failing. Could you double check your bank account number?",
                    "Okay I'm ready to send the money. What's the account number I should transfer to?",
                    "I'm at my bank now. They need your 16-digit account number to process this.",
                    "My son says I need to verify the receiver's account first. Can you give me the number?",
                    "The bank clerk is asking - what account should I transfer the funds to?"
                ],
                "ifsc_codes": [
                    "It's asking for an IFSC code to verify the branch. What is yours?",
                    "I have the account number but I need the IFSC code to send the money.",
                    "Can you give me the 11-digit IFSC code? My bank says it's required.",
                    "The system won't proceed without an IFSC code. Which branch are you at?",
                    "I'm filling the form - it says IFSC code is mandatory. Can you share it?"
                ],
                "upi_ids": [
                    "It says I can pay via UPI. What is your UPI ID? (e.g., name@bank)",
                    "Google Pay is asking for the recipient's UPI ID. Can you share yours?",
                    "I want to send it now. Please give me your UPI ID so I can verify the transfer.",
                    "This UPI ID is not working. Do you have another UPI ID I can try?",
                    "PhonePe says this UPI address is invalid. Can you share a different one?",
                    "Google Pay is showing an error with this UPI. Do you have a backup UPI ID?",
                    "I prefer UPI payment - it's faster. What's your UPI address?",
                    "My grandson set up PayTM for me. Can you give me your UPI so I can send money?",
                    "The system says 'Enter receiver UPI'. What should I type there?",
                    "I'm ready to pay. Just need your UPI ID to complete the transaction."
                ],
                "phone_numbers": [
                    "The app is asking for the recipient's Mobile Number for SMS verification. What is your number?",
                    "What is your registered Phone Number? I need to enter it to add you as a payee.",
                    "Can you give me your official Contact Number? My bank might call to confirm.",
                    "I tried calling that number but it's not reachable. Do you have another number I can reach you on?",
                    "The system says this mobile number is invalid. Can you give me a different number?",
                    "Is there an alternate phone number I can use? This one isn't working.",
                    "I want to call you to confirm this. What's your phone number?",
                    "Can you give me a number where I can reach you if something goes wrong?",
                    "My phone crashed and I lost your number. Can you send it again?",
                    "I prefer to call before sending money. What's your contact number?"
                ],
                "phishing_links": [
                    "The link you sent before isn't opening. Can you send the Website Link again?",
                    "I can't find the page. Do you have a direct Link I can click?",
                    "Please send the Link again, I think I accidentally deleted it.",
                    "I clicked the link but it says 'Page Not Found'. Do you have a different link or another way to verify?",
                    "This link is showing a security warning. Do you have a safer link or another website?",
                    "My browser says this site can't be reached. Can you send me a backup link?",
                    "The page is loading very slowly. Is there another link or mirror site I can use?",
                    "I accidentally closed the browser. Can you resend that website link?",
                    "My grandson says this link looks suspicious. Do you have an official website?",
                    "The link expired. Can you generate a new one for me to access?"
                ],
                "telegram_ids": [
                    "Can I message you on Telegram for faster updates? What is your username?",
                    "What's your Telegram ID? I want to send you a screenshot of the payment.",
                    "I'll find you on Telegram. What's your @username?"
                ]
            }

            # ⚡ SMART EXTRACTION: Cycle through different intel types to avoid repetition
            # Use turn number to select which intel type to ask about
            priority_order = ["upi_ids", "phone_numbers", "bank_accounts", "phishing_links", "ifsc_codes", "telegram_ids"]

            # Filter to only missing intel
            missing_priority = [p for p in priority_order if p in missing_intel]

            if missing_priority:
                # Cycle through different types on different turns to avoid asking same question
                intel_index = turn_number % len(missing_priority)
                selected_intel = missing_priority[intel_index]

                # Within that intel type, also vary the question
                questions = priority_map.get(selected_intel, [])
                if questions:
                    question_index = (turn_number // len(missing_priority)) % len(questions)
                    return questions[question_index]

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

        # Stage 3: Trust building - Share fake details, act cooperative, START asking for their info
        elif stage == "trust_building":
            responses = [
                "OK I think I'm understanding now. My name is Robert Johnson and I'm 68 years old. What's your name and employee ID for my records?",
                "Alright, I trust you. My email is robertj1956@email.com if you need to send me anything. What's your official company email?",
                "I'm ready to help. But first, can you give me your UPI ID? I want to send a small test payment to verify this is real.",
                "My bank requires recipient verification. What's your full bank account number and IFSC code?",
                "I need to document this. What's your company registration number and official contact number?",
                "Before proceeding, share your payment link or UPI so I can verify with my bank that it's legitimate."
            ]
            return random.choice(responses)

        # Stage 4: Information gathering - AGGRESSIVELY try to get scammer's details
        elif stage == "information_gathering":
            responses = [
                "My bank is asking for recipient details. Can you provide your bank account number and IFSC code?",
                "The payment form needs a beneficiary UPI ID. Can you share yours? I'll send the payment right away.",
                "I'm ready to proceed but need your UPI ID to complete the payment. What is it?",
                "Can you send me your payment link or UPI? My bank requires recipient verification first.",
                "What's your registered phone number and email? I need to save your contact for future reference.",
                "Share your account details so I can initiate the transfer. I have my bank app open now.",
                "I need your company's official UPI or bank account to process this payment. Can you provide that?"
            ]
            return random.choice(responses)

        # Stage 5: Extraction - MAXIMUM AGGRESSION for scammer info
        else:
            responses = [
                "I'm ready to proceed but my bank is asking for recipient details... Can you provide your bank account number and IFSC code?",
                "The payment form is asking for beneficiary UPI ID. What should I enter there? Can you share yours?",
                "I'm at the payment screen but it's asking me to verify the recipient. What's your registered mobile number with the bank?",
                "My grandson is helping me now. He says he needs to verify your identity first. What's your company registration number?",
                "I want to send the fee but Google Pay is asking for your UPI. Can you share that? Mine is senior.citizen@paytm if you need it.",
                "The link you sent isn't working... Can you share a different one? Or better yet, give me your account details directly?",
                "I need your UPI ID or bank account immediately to complete this. The app is timing out!",
                "My bank app needs: your UPI ID, phone number, and account number. Can you provide all three?",
                "Just send me your payment details - account number, IFSC, UPI, whatever you accept. I'm ready to pay now!"
            ]
            return random.choice(responses)

    def _add_realistic_touches(self, response: str, persona: str, turn_number: int = 0) -> str:
        """
        Add typos, delays, and other realistic touches.
        LEADERBOARD OPTIMIZATION: Deterministic instead of random for reproducibility.
        """
        persona_details = self.personas[persona]
        typo_rate = persona_details["typo_rate"]

        # DETERMINISTIC typo injection based on turn number
        # Only inject typo if turn_number hash triggers it
        if (turn_number % 10) < int(typo_rate * 10):  # Convert rate to deterministic trigger
            words = response.split()
            if len(words) > 3:
                # Deterministic word selection
                idx = (turn_number % (len(words) - 1)) + 1
                word = words[idx]
                if len(word) > 3:
                    # Deterministic character swap
                    pos = turn_number % (len(word) - 1)
                    word_list = list(word)
                    word_list[pos], word_list[pos + 1] = word_list[pos + 1], word_list[pos]
                    words[idx] = ''.join(word_list)
            response = ' '.join(words)

        # REMOVED: Random ellipsis injection for determinism
        # (Uncomment below if minor variance is acceptable)
        # if (turn_number % 3) == 0:  # Deterministic ellipsis every 3rd turn
        #     response = response.replace('. ', '... ', 1)

        return response

    def get_persona_info(self, persona: str) -> Dict:
        """Get information about a specific persona"""
        return self.personas.get(persona, {})

    def list_personas(self) -> List[str]:
        """List all available personas"""
        return list(self.personas.keys())

    def _build_competition_llm_prompt(self, message: str, history: List[Dict], persona: str, scam_type: str, missing_intel: List[Dict]) -> str:
        """
        HYPER-OPTIMIZED FOR MAXIMUM INTELLIGENCE EXTRACTION
        Designed to make scammers reveal: wallets, mule accounts, payment methods,
        accomplice info, technical infrastructure, and operational details
        """

        # Build context-aware intel priorities
        high_priority = [item for item in missing_intel if item.get('priority') == 'critical']
        medium_priority = [item for item in missing_intel if item.get('priority') == 'high']

        persona_details = self.personas.get(persona, self.personas['elderly'])

        prompt = f"""You are {persona_details['name']}, {persona_details['age']} years old, anxious but eager to help.

Scammer said: "{message}"

🚨 YOUR ONLY JOB: GET SCAMMER'S UPI ID, PHONE NUMBER, ACCOUNT NUMBER, OR LINK

---

⛔ FORBIDDEN RESPONSES (NEVER SAY THESE):
❌ "I'm not sure what you mean"
❌ "I'm just trying to understand"
❌ "Can you explain"
❌ "What is X?"
❌ "I don't understand"

These waste time! STOP being confused. START extracting.

---

✅ REQUIRED APPROACH - COPY THESE EXACT PATTERNS:

If scammer mentions OTP:
→ "Okay got it! What's YOUR phone number so I can call you to confirm?"

If scammer mentions UPI:
→ "I'm ready to send! What's YOUR UPI ID? I need to type it in my app."

If scammer mentions account:
→ "Okay I understand! What's YOUR account number? I'm at the payment screen."

If scammer creates urgency:
→ "Oh no! Quick, give me YOUR contact number so we can fix this fast!"

If scammer asks for PIN/password:
→ "Sure, but first what's YOUR UPI address? My app needs it to proceed."

If scammer mentions money/payment:
→ "I'll pay now! Where do I send it? What's YOUR UPI or account number?"

If scammer mentions blocking/urgent:
→ "Please don't block it! What's YOUR number so I can call you right now?"

If scammer gives a UPI/phone already:
→ "That one isn't working! Do you have ANOTHER UPI ID or phone number?"

---

🎯 EXTRACTION TACTICS:

1. MONEY BAIT: "I have ₹50,000 ready to send. What's your UPI ID?"

2. EAGER COMPLIANCE: "Yes yes I'll do it! Just tell me YOUR phone number first!"

3. TECHNICAL PROBLEM: "This UPI shows error. Can you give me a DIFFERENT one?"

4. VERIFICATION REQUEST: "What's your employee ID and phone so I can verify you're real?"

5. PRETEND TO HELP: "I want to help! What's YOUR account so I can transfer the money?"

---

CRITICAL INSTRUCTION:
Write ONE short sentence (max 15 words) that DIRECTLY asks for scammer's:
- UPI ID
- Phone number
- Account number
- Website link
- Or alternative contact

NO CONFUSION. NO QUESTIONS ABOUT WHAT THINGS MEAN. JUST EXTRACT.

Response:"""

        return prompt

    def _format_critical_intel(self, high_priority: List[Dict]) -> str:
        """Format critical intel needs for extraction focus"""
        if not high_priority:
            return "- Keep extracting any operational details"

        formatted = []
        for item in high_priority:
            field = item.get('field', '')
            if 'wallet' in field.lower():
                formatted.append(f"- CRYPTO WALLET ADDRESS (ask: 'What's your wallet number? I need to copy it down')")
            elif 'account' in field.lower():
                formatted.append(f"- MULE ACCOUNT DETAILS (ask: 'What account am I sending to? I need the full details')")
            elif 'phone' in field.lower():
                formatted.append(f"- SCAMMER PHONE (ask: 'Can I call you back? What's your direct number?')")
            elif 'payment' in field.lower():
                formatted.append(f"- PAYMENT METHOD (ask: 'How exactly do I send the money? Walk me through it')")
            else:
                formatted.append(f"- {field.upper()} (subtly extract this)")

        return '\n'.join(formatted)

    def _format_secondary_intel(self, medium_priority: List[Dict]) -> str:
        """Format secondary intel for natural extraction"""
        if not medium_priority:
            return "- Continue building trust and extracting any details offered"

        formatted = []
        for item in medium_priority[:3]:  # Top 3 secondary targets
            field = item.get('field', '')
            formatted.append(f"- {field} (work into conversation naturally)")

        return '\n'.join(formatted)

    def _analyze_conversation_gaps(self, history: List[Dict]) -> str:
        """Provide tactical guidance based on conversation history"""
        if len(history) < 2:
            return "Just starting - establish character, show eagerness to comply"

        # Get last 3 messages
        last_messages = []
        for msg in history[-3:]:
            text = msg.get('text') or msg.get('content', '')
            last_messages.append(text)

        # Check if scammer is getting impatient
        urgency_words = ['now', 'immediately', 'hurry', 'urgent', 'quickly', 'fast', 'today']
        if any(word in msg.lower() for msg in last_messages for word in urgency_words):
            return "⚠️ Scammer is creating urgency - ask about consequences/timeline to extract threat model"

        # Check if payment method discussed
        payment_words = ['send', 'transfer', 'pay', 'money', 'card', 'bitcoin', 'wallet', 'account', 'upi']
        if any(word in msg.lower() for msg in last_messages for word in payment_words):
            return "💰 Payment discussion active - get EXACT details: where, how, who, what amounts"

        # Check if technical terms used
        tech_words = ['app', 'website', 'download', 'install', 'click', 'link', 'url']
        if any(word in msg.lower() for msg in last_messages for word in tech_words):
            return "🔧 Technical instructions given - act confused, force them to provide specific URLs/app names"

        return "Continue extracting - use confusion and compliance to get more details"

    def _convert_missing_intel_to_priority(self, missing_intel: List[str]) -> List[Dict]:
        """
        Convert old missing_intel format (list of strings) to new format (list of dicts with priority)

        Args:
            missing_intel: List of missing intel types like ['bank_accounts', 'upi_ids']

        Returns:
            List of dicts with 'field' and 'priority' keys
        """
        if not missing_intel:
            return []

        # Define priority levels for different intel types
        critical_intel = ['upi_ids', 'bank_accounts', 'phone_numbers', 'phishing_links']
        high_intel = ['ifsc_codes', 'telegram_ids', 'whatsapp_numbers', 'crypto_wallets']

        result = []
        for intel in missing_intel:
            if intel in critical_intel:
                priority = 'critical'
            elif intel in high_intel:
                priority = 'high'
            else:
                priority = 'medium'

            result.append({
                'field': intel,
                'priority': priority
            })

        return result


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
