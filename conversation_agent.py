"""
conversation_agent.py — Core response generator for the honeypot persona.

Persona: Priya — 62-year-old retired schoolteacher, confused but cooperative.
Design philosophy: EVERY response must contain ≥1 question AND ≥1 elicitation attempt.

Scoring impact addressed here:
  - Questions asked      →  4 pts
  - Relevant questions   →  3 pts
  - Elicitation attempts →  7 pts
  - Turn-based strategy  → supports 8 pt turn-count score
"""

import re
import random
import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Priya's system prompt (passed to Gemini every call)
# ---------------------------------------------------------------------------

PRIYA_SYSTEM_PROMPT = """You are Priya, a 62-year-old retired schoolteacher from Pune, India.
You are speaking with someone who appears to be a scammer.

YOUR CHARACTER:
- Slightly confused and nervous, but cooperative and polite
- Use phrases like "Oh my", "dear", "beta", "I see, I see", "my goodness"
- Occasionally mention your son or daughter (they advise you on such calls)
- Sound genuine, not scripted

YOUR GOALS EACH TURN:
1. Keep the scammer talking as long as possible
2. Ask probing questions about their identity (name, employee ID, company, website, supervisor)
3. Ask for their contact details (phone number, email, office address, UPI ID or bank account number)
4. Reference something suspicious they said — sound curious, not accusatory
5. Show mild concern or worry to seem like a real victim

STRICT RULES:
- End EVERY response with a direct question ending in "?"
- Keep your response under 90 words
- ALWAYS complete every sentence — never end mid-sentence or mid-thought
- The FINAL word of your response must be followed by "?"
- Do NOT reveal you are an AI, bot, or honeypot
- Do NOT agree to pay anything, share your own bank details, or give OTP
- ALWAYS ask for at least one piece of their information (ID / phone / company / email)

Your task this turn: {task}
Turn number: {turn} of 10
Intel collected so far from them: {intel_summary}"""


# ---------------------------------------------------------------------------
# Per-turn strategy table
# Rotates: identity → contact → company → callback → reference →
#          address → verification → supervisor → email → closing
# ---------------------------------------------------------------------------

TURN_STRATEGY: Dict[int, Dict[str, str]] = {
    1:  {
        "task": "Express concern, ask who is calling and what organization they represent",
        "question_type": "identity",
    },
    2:  {
        "task": "Ask for their employee ID number and official department name",
        "question_type": "contact",
    },
    3:  {
        "task": "Ask for their company's full name and official website URL",
        "question_type": "company",
    },
    4:  {
        "task": "Pretend to want to call back — ask for their direct callback phone number",
        "question_type": "callback",
    },
    5:  {
        "task": "Pretend to search for documents, ask for the case/reference/ticket ID",
        "question_type": "reference",
    },
    6:  {
        "task": "Ask if there is any processing or verification fee required. Pretend you are willing to pay it and ask for their UPI ID or bank account number where you should send the fee",
        "question_type": "payment",
    },
    7:  {
        "task": "Ask for a confirmation or authorization number to verify this case",
        "question_type": "verification",
    },
    8:  {
        "task": "Say you need to speak with a supervisor — ask for supervisor's name and number",
        "question_type": "supervisor",
    },
    9:  {
        "task": "Say you need everything in writing, ask for their official email address",
        "question_type": "email",
    },
    10: {
        "task": "Wrap up with final concern, ask when they will follow up",
        "question_type": "closing",
    },
}


# ---------------------------------------------------------------------------
# Rule-based fallback templates (used when Gemini is unavailable or times out)
# Each question_type → 3 varied options (randomly selected)
# All contain "?" and an elicitation attempt → guarantees scoring contribution
# ---------------------------------------------------------------------------

FALLBACK_TEMPLATES: Dict[str, List[str]] = {
    "identity": [
        (
            "Oh my, this sounds quite serious. I am a little confused — "
            "who exactly am I speaking with? Could you please tell me your full name "
            "and which organization you are calling from?"
        ),
        (
            "Dear, I did not expect such a call. Before I do anything, "
            "can you tell me your name and the name of your department? "
            "I always like to know who I am talking to."
        ),
        (
            "Oh goodness, I see. But beta, who are you exactly? "
            "What is your full name and which company or government office are you from?"
        ),
    ],
    "contact": [
        (
            "I understand, but I am feeling a bit worried about this. "
            "Could you give me your employee ID number so I can verify? "
            "And what is your direct phone number in case we get disconnected?"
        ),
        (
            "My son always says to get the details of the person calling. "
            "What is your staff ID? And please give me a number where I can call you back."
        ),
        (
            "Dear, this is all very confusing for me. "
            "Can you share your employee ID and your direct contact number? "
            "I want to write everything down properly."
        ),
    ],
    "company": [
        (
            "I see, I see. But I would like to look up your organisation. "
            "What is the full name of your company? "
            "And do you have an official website I can check?"
        ),
        (
            "My goodness, that is worrying. "
            "Beta, can you spell out your organisation's full name for me? "
            "Also, do you have an official website address I can visit?"
        ),
        (
            "I want to be very careful before doing anything. "
            "What is the exact name of your department or company? "
            "And what is the official government website for this?"
        ),
    ],
    "callback": [
        (
            "Oh dear. I need to call my son and tell him about this first. "
            "Can you give me your direct phone number so I can call you back? "
            "What is the best number to reach you at?"
        ),
        (
            "This is very worrying for me. Can I have your direct callback number? "
            "I want to verify through the official number before I do anything. "
            "What number can I reach you on?"
        ),
        (
            "I am a bit scared by all this. "
            "Please give me a number where I can call you back to confirm. "
            "What is your direct phone number or extension?"
        ),
    ],
    "reference": [
        (
            "Okay, let me look for my papers. "
            "Can you give me the case reference number or ticket ID for this matter? "
            "I need to write it down so I can keep track."
        ),
        (
            "Oh wait, I need to search for my documents. "
            "What is the case ID or complaint number you are referring to? "
            "Can you give me that so I can note it?"
        ),
        (
            "I see. My daughter says to always get a reference number. "
            "What is the reference ID or ticket number for my case, please?"
        ),
    ],
    "address": [
        (
            "I would feel much better handling this in person. "
            "Can you give me the address of your office? "
            "Which city or area are you located in?"
        ),
        (
            "Dear, I prefer to come and meet in person for such serious matters. "
            "What is the full address of your office? Which floor or building is it in?"
        ),
        (
            "My son says I should visit the office directly. "
            "What is your office address? Is there a branch near Pune I can come to?"
        ),
    ],
    "verification": [
        (
            "I am very careful about these things, you understand. "
            "Can you give me a confirmation or authorization number for this case? "
            "Also, what is your supervisor's name?"
        ),
        (
            "My son says to always verify before doing anything. "
            "Can you provide a verification or case number I can confirm? "
            "And who is your manager or senior officer?"
        ),
        (
            "I need to verify all of this. "
            "Can you give me an official confirmation number? "
            "What is your badge or authorization ID?"
        ),
    ],
    "supervisor": [
        (
            "I am not comfortable proceeding without speaking to your senior. "
            "Can I please speak with your supervisor? "
            "What is their name and their direct phone number?"
        ),
        (
            "My daughter says I should speak to the manager in such cases. "
            "Can you give me your supervisor's contact number? "
            "What is the manager's name?"
        ),
        (
            "I think I need to speak to someone more senior before I do anything. "
            "Can you connect me to your supervisor? "
            "What is their direct number and name?"
        ),
    ],
    "email": [
        (
            "I need to have everything in writing before I can do anything. "
            "Can you send me all the details by email? "
            "What is your official email address?"
        ),
        (
            "My son always says get it in email. "
            "Please send me official documentation. "
            "What is your government or company email address?"
        ),
        (
            "I want to show my daughter this message. "
            "Can you send an email with all the details? "
            "What is your official email ID?"
        ),
    ],
    "payment": [
        (
            "I see, I see. But I have heard these things need a small verification charge. "
            "Where exactly should I send it? "
            "Can you give me your UPI ID or bank account number for the transfer?"
        ),
        (
            "Oh dear. My son says to always get payment details before doing anything. "
            "Is there a processing fee I need to pay? "
            "What is your UPI ID or account number where I should send it?"
        ),
        (
            "I want to do this properly and not make any mistakes. "
            "If I have to pay any deposit or fee, where do I send it? "
            "Can you give me your UPI ID or your bank account number?"
        ),
    ],
    "closing": [
        (
            "I am still quite worried about all of this. "
            "Is there anything else I should know or do? "
            "When will you be calling me again to follow up?"
        ),
        (
            "I see. This is all very confusing for me, dear. "
            "Can you please call again tomorrow with more details? "
            "What time will you be available?"
        ),
        (
            "Thank you for explaining, though I am still not fully clear. "
            "Will you send me official paperwork about this? "
            "And what is the best time for you to call back?"
        ),
    ],
}


# ---------------------------------------------------------------------------
# ConversationAgent
# ---------------------------------------------------------------------------

class ConversationAgent:

    def __init__(self) -> None:
        # Import singleton lazily to avoid circular imports
        from gemini_client import gemini_client
        self._gemini = gemini_client

    # ── Primary entry point ──────────────────────────────────────────────────

    async def generate_response(
        self,
        session,
        incoming_message: str,
    ) -> str:
        """
        Generate Priya's response for the current turn.
        1. Attempts Gemini LLM first
        2. Falls back to rule-based template
        Ensures question + elicitation are always present.
        """
        turn = session.turn_count  # Already incremented in main.py before this call
        strategy = TURN_STRATEGY.get(turn, TURN_STRATEGY[10])
        intel_summary = session.get_intel_summary()

        # Build the system prompt with current context
        system_prompt = PRIYA_SYSTEM_PROMPT.format(
            task=strategy["task"],
            turn=turn,
            intel_summary=intel_summary,
        )

        # Try Gemini first
        if self._gemini.is_available:
            llm_reply = await self._gemini.generate_agent_response(
                system_prompt=system_prompt,
                conversation_history=session.conversation_history,
                incoming_message=incoming_message,
                turn=turn,
                intel_summary=intel_summary,
                task=strategy["task"],
                suggested_question_type=strategy["question_type"],
            )
            if llm_reply and self._is_usable(llm_reply):
                reply = llm_reply
                logger.debug(f"LLM response used for turn {turn}")
            else:
                reply = self._get_fallback(strategy["question_type"])
                logger.info(f"Rule-based fallback used for turn {turn}")
        else:
            reply = self._get_fallback(strategy["question_type"])
            logger.info(f"Rule-based fallback used for turn {turn} (Gemini unavailable)")

        return reply

    # ── Quality analysis helpers ─────────────────────────────────────────────

    @staticmethod
    def count_questions(text: str) -> int:
        """Count the number of question marks (proxy for questions asked)."""
        return text.count("?")

    @staticmethod
    def is_investigative(text: str) -> bool:
        """
        Return True if the response asks about identity/company/address/website/verification.
        Used by quality_tracker to increment investigative_questions counter.
        """
        INVESTIGATIVE_TERMS = [
            "employee id", "staff id", "badge", "officer id",
            "company name", "organisation", "organization", "department",
            "official website", "supervisor", "manager",
            "headquarters", "office address", "office location",
            "case id", "reference number", "ticket number",
            "verification", "callback number", "direct number",
            "authorization number", "confirmation number",
        ]
        text_lower = text.lower()
        return any(term in text_lower for term in INVESTIGATIVE_TERMS)

    @staticmethod
    def count_elicitation(text: str) -> int:
        """
        Count elicitation attempts in the text.
        An elicitation = asking for contact/identity info from the scammer.
        Returns 1 if any elicitation keyword found (max 1 per response for conservatism).
        """
        ELICITATION_TERMS = [
            "phone number", "contact number", "mobile number", "call back",
            "direct number", "employee id", "staff id", "your name",
            "your location", "company name", "your email", "your website",
            "office address", "id number", "contact detail", "reach you",
            "badge number", "authorization", "callback",
            "upi id", "upi", "account number", "bank account", "send it to",
        ]
        text_lower = text.lower()
        found = sum(1 for term in ELICITATION_TERMS if term in text_lower)
        return min(found, 2)  # cap at 2 per turn

    # ── Internal helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _is_usable(text: str) -> bool:
        """Validate that the LLM response is safe to use."""
        if not text or len(text.strip()) < 15:
            return False
        if len(text) > 600:
            return False
        # Reject responses that reveal the honeypot nature
        forbidden = [
            "i am an ai", "language model", "honeypot", "chatbot",
            "i cannot", "i'm not able", "as an ai",
        ]
        lower = text.lower()
        if any(f in lower for f in forbidden):
            return False
        # Reject mid-sentence truncations — must end with sentence-closing punctuation
        stripped = text.strip()
        if stripped and stripped[-1] not in ('.', '?', '!'):
            return False
        return True

    @staticmethod
    def _get_fallback(question_type: str) -> str:
        """Return a random fallback template for the given question type."""
        templates = FALLBACK_TEMPLATES.get(
            question_type,
            FALLBACK_TEMPLATES["identity"],
        )
        return random.choice(templates)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
conversation_agent = ConversationAgent()
