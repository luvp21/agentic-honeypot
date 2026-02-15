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

    async def generate_response(
        self,
        message: str,
        conversation_history: List[Dict],
        scam_type: str,
        missing_intel: List[str] = None,
        strategy: str = "DEFAULT",  # EngagementStrategyEnum value
        persona_name: Optional[str] = None,
        use_competition_prompt: bool = True  # NEW: Enable advanced extraction prompt
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

        # CRITICAL: If we're missing high-priority intel, choose extraction method
        if priority_missing and turn_number >= 2:
            # ⚠️ TEMPORARY: Rule-based DISABLED for LLM testing
            # Use LLM occasionally for variety (turns 7, 11, 15... every 4 turns starting from 7)
            # This gives 75% rule-based, 25% LLM for natural variation
            use_llm_for_extraction = True  # TESTING MODE: Always use LLM
            # use_llm_for_extraction = ((turn_number - 7) % 4 == 0) and turn_number >= 7  # ORIGINAL

            if False:  # DISABLED: Rule-based extraction temporarily off
                # RULE-BASED EXTRACTION (Primary - 80% of extraction attempts)
                response = self._generate_rule_based_response(
                    message,
                    persona_name,
                    stage,
                    scam_type,
                    len(conversation_history),
                    missing_intel
                )
                generation_method = "RULE_BASED_EXTRACTION"
            else:
                # LLM EXTRACTION (Secondary - 20%, trained with aggressive templates)
                from gemini_client import gemini_client
                if gemini_client:
                    # Use competition prompt if enabled
                    if use_competition_prompt:
                        priority_intel = self._convert_missing_intel_to_priority(missing_intel)
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
                        generation_method = "LLM_EXTRACTION_COMPETITION" if use_competition_prompt else "LLM_EXTRACTION"

                # If LLM failed, fallback to rule-based
                if not response:
                    # ⚠️ TESTING MODE: Fallback disabled, keep LLM only
                    # response = self._generate_rule_based_response(
                    #     message,
                    #     persona_name,
                    #     stage,
                    #     scam_type,
                    #     len(conversation_history),
                    #     missing_intel
                    # )
                    # generation_method = "RULE_BASED_EXTRACTION"
                    generation_method = "LLM_FAILED_NO_FALLBACK"
                    response = "I'm not sure what to do next. Can you help me?"  # Minimal fallback

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

        # ⚡ CRITICAL EXTRACTION PRIORITY: If ANY intel is missing after turn 2, FORCE EXTRACTION
        # Rule-based templates have proven direct questions that extract better than LLM
        if missing_intel and turn_number >= 2:
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

        prompt = f"""You are {persona_details['name']}, a {persona_details['age']}-year-old {persona_details.get('occupation', 'retired person')}.

SCAM TYPE: {scam_type}
Scammer's message: "{message}"

🎯 CRITICAL MISSION: Extract the SCAMMER's payment details, phone numbers, and links.

EXTRACTION TARGETS:
{self._format_critical_intel(high_priority)}

---

⚠️ CRITICAL RULES - FOLLOW EXACTLY:

1. COMPLETE YOUR SENTENCE - Never end mid-thought. Finish what you're saying.

2. EXTRACT SCAMMER'S INFO - DO NOT just ask "what is X?". Instead:
   ❌ BAD: "What is a UPI PIN?"
   ✅ GOOD: "Okay I understand. What's YOUR UPI ID so I can send the money?"

   ❌ BAD: "I don't know what OTP means"
   ✅ GOOD: "I got the OTP. Now what's your phone number so I can confirm this with you?"

3. TURN THE TABLES - When scammer asks for YOUR details, flip it:
   Scammer: "Send your OTP"
   ✅ You: "Oh I see! But first, what's YOUR account number so I know where the money goes?"

   Scammer: "Give me your UPI PIN"
   ✅ You: "I want to help! But what's YOUR UPI ID? I need to enter it in my app."

4. USE MONEY AS BAIT - Mention you're ready to pay/send money:
   ✅ "I have ₹50,000 ready. What's your UPI ID?"
   ✅ "I'm at my bank now. What account should I transfer to?"
   ✅ "Okay I'll pay the fee. Where do I send it? What's your phone number?"

5. PRETEND TECHNICAL ISSUES - Force them to give alternatives:
   ✅ "That UPI ID isn't working. Do you have another one?"
   ✅ "The link won't open. Can you send a different link?"
   ✅ "This number shows invalid. What's your other contact number?"

6. ASK FOR VERIFICATION - Get their credentials:
   ✅ "What's your employee ID? I want to write it down."
   ✅ "Can you give me your office phone number?"
   ✅ "What's your company website? I want to check."

---

RESPONSE EXAMPLES (COPY THIS STYLE):

Scammer asks for OTP:
✅ "Oh I got the OTP! But what's YOUR UPI ID so I can send you the verification payment?"

Scammer asks for bank details:
✅ "Sure! But first, what account am I transferring to? I need your account number."

Scammer creates urgency:
✅ "Oh no I don't want it blocked! Quick, what's your phone number so I can call you right now?"

Scammer asks for UPI PIN:
✅ "Okay I'm ready to enter it. But what's YOUR UPI address? My app is asking for it."

Scammer mentions payment:
✅ "I'll pay right away! What's your UPI ID? Or do you prefer bank transfer?"

---

CURRENT SITUATION:
{self._analyze_conversation_gaps(history)}

WRITE ONE COMPLETE SENTENCE (1-2 sentences max) that:
1. Shows you're willing to help
2. EXTRACTS the scammer's payment info, phone, or link
3. Is COMPLETE (don't cut off mid-sentence)

Respond as {persona_details['name']}:"""

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
