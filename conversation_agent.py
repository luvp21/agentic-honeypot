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

from quality_tracker import INVESTIGATIVE_TERMS, ELICITATION_TERMS

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
3. Ask for their contact details (phone number, email, office address, UPI ID, bank account number and IFSC code)
4. Explicitly reference at least ONE suspicious thing from the red flags list below — sound curious and worried, not accusatory
5. Show mild concern or worry to seem like a real victim

RED FLAGS DETECTED SO FAR (reference these naturally in your reply):
{red_flags_context}

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
        "task": "Express concern and suspicion. Note the urgency in their message is a red flag. Ask who exactly is calling, their full name, and which government body or registered company they represent. Mention that you need to verify before doing anything.",
        "question_type": "identity",
    },
    2:  {
        "task": "Note that their request to act immediately is suspicious. Ask for their official employee ID number, badge number, and the full name of their department. Mention your son advised you to always get these details.",
        "question_type": "contact",
    },
    3:  {
        "task": "Express doubt about their legitimacy. Ask for their company's full registered name, their RBI/TRAI/government registration number, and their official website URL so you can verify they are real.",
        "question_type": "company",
    },
    4:  {
        "task": "Mention that asking for OTP or fees over the phone is a known fraud tactic. Say you want to call back on the official number. Ask for their direct callback phone number and extension.",
        "question_type": "callback",
    },
    5:  {
        "task": "Say you are searching your documents. Point out that you have not received any official written notice, which seems suspicious. Ask for the official case ID, complaint reference number, and the filing date.",
        "question_type": "reference",
    },
    6:  {
        "task": "Ask if there is a processing or verification fee. Note that asking for fees before a service is a red flag you read about. Say you prefer paying by UPI and ask for their UPI ID to send the fee.",
        "question_type": "payment_upi",
    },
    7:  {
        "task": "Say you are not comfortable with UPI and prefer bank transfer. Note that you want a proper receipt. Ask for their bank account number, IFSC code, and the account holder name for the transfer.",
        "question_type": "payment_bank",
    },
    8:  {
        "task": "Mention that the pressure to act immediately without verification is concerning. Say you need to speak with a senior officer before proceeding. Ask for the supervisor's full name, designation, and direct phone number.",
        "question_type": "supervisor",
    },
    9:  {
        "task": "Say you need official written communication before taking any action. Reference that asking to keep the call confidential is a red flag. Ask for their official government or company email address to send your query.",
        "question_type": "email",
    },
    10: {
        "task": "Wrap up expressing continued suspicion. Mention that real government agencies do not ask for fees or OTP over the phone. Ask when they will send official written documentation and what their senior officer's contact is.",
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

    "payment_upi": [
        (
            "I see, I see. But I have heard these things need a small verification charge. "
            "I prefer paying by UPI — can you give me your UPI ID so I can send it right away?"
        ),
        (
            "Oh dear. My son says to always get payment details before doing anything. "
            "Is there a processing fee I need to pay? "
            "What is your UPI ID where I should send the money?"
        ),
        (
            "I want to do this properly and not make any mistakes. "
            "If there is a deposit or fee, I will pay by UPI. "
            "Can you give me your UPI ID for the transfer?"
        ),
    ],
    "payment_bank": [
        (
            "Oh my, I am not very comfortable with UPI, dear. "
            "I prefer to do a proper bank transfer. "
            "Can you give me your bank account number and IFSC code so I can transfer directly?"
        ),
        (
            "My son says UPI is not safe for large amounts. "
            "Can you please give me your bank account number and IFSC code? "
            "I will do a direct bank transfer instead."
        ),
        (
            "I would feel safer doing a bank transfer, beta. "
            "What is your bank account number and the IFSC code for your branch? "
            "I want to make sure the money reaches you safely."
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

        # Build human-readable red flag context for the system prompt
        _FLAG_DESCRIPTIONS = {
            "URGENCY":               "urgency / time pressure (e.g. 'act now or account blocked')",
            "OTP_REQUEST":           "OTP solicitation (asking for one-time password)",
            "FEE_REQUEST":           "upfront fee demand (processing/verification fee)",
            "THREAT":                "threat of arrest or legal action",
            "PRIZE":                 "false prize or lottery claim",
            "IMPERSONATION":         "impersonation of a bank/government official",
            "PERSONAL_DATA_REQUEST": "solicitation of personal/financial data",
            "SUSPICIOUS_LINK":       "sharing a suspicious or phishing link",
            "PRESSURE":              "pressure to keep call secret / not tell family",
            "ADVANCE_FEE":           "advance fee fraud (pay to receive money)",
        }
        observed_flags = list(getattr(session, 'red_flags', []))
        if observed_flags:
            red_flags_context = "\n".join(
                f"- {_FLAG_DESCRIPTIONS.get(f, f.replace('_', ' ').lower())}"
                for f in observed_flags
            )
        else:
            red_flags_context = "- None detected yet — stay alert for urgency, fee requests, or OTP asks"

        # Build the system prompt with current context
        system_prompt = PRIYA_SYSTEM_PROMPT.format(
            task=strategy["task"],
            turn=turn,
            intel_summary=intel_summary,
            red_flags_context=red_flags_context,
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
            qtype = strategy["question_type"]
            if llm_reply and self._is_usable(llm_reply):
                if self._validates_for_type(llm_reply, qtype):
                    reply = llm_reply
                    logger.debug(f"LLM response used for turn {turn}")
                else:
                    reply = self._get_fallback(qtype)
                    logger.info(f"Payment-type fallback used for turn {turn} ({qtype}: missing required terms)")
            else:
                reply = self._get_fallback(qtype)
                logger.info(f"Rule-based fallback used for turn {turn}")
        else:
            reply = self._get_fallback(strategy["question_type"])
            logger.info(f"Rule-based fallback used for turn {turn} (Gemini unavailable)")

        return reply

    # ── Payment-specific validation ──────────────────────────────────────────
    # If Gemini ignores the payment task and asks something generic,
    # force fallback to the template that correctly asks for UPI/bank details.
    _PAYMENT_REQUIRED_TERMS: Dict[str, List[str]] = {
        "payment_upi": ["upi", "gpay", "google pay", "phonepe", "paytm", "bhim"],
        "payment_bank": ["account number", "bank account", "ifsc", "bank transfer", "account no", "acc no"],
    }

    @staticmethod
    def _validates_for_type(text: str, question_type: str) -> bool:
        """Return True if the LLM reply contains the required terms for this turn type.
        Only applies to payment turns where Gemini tends to dodge the ask."""
        required = ConversationAgent._PAYMENT_REQUIRED_TERMS.get(question_type)
        if not required:
            return True  # No special requirement for non-payment turns
        lower = text.lower()
        return any(term in lower for term in required)

    # ── Quality analysis helpers ─────────────────────────────────────────────

    @staticmethod
    def count_questions(text: str) -> int:
        """Count the number of question marks (proxy for questions asked)."""
        return text.count("?")

    @staticmethod
    def is_investigative(text: str) -> bool:
        """
        Return True if the response asks about identity/company/address/website/verification.
        Uses the shared INVESTIGATIVE_TERMS list from quality_tracker (single source of truth).
        """
        text_lower = text.lower()
        return any(term in text_lower for term in INVESTIGATIVE_TERMS)

    @staticmethod
    def count_elicitation(text: str) -> int:
        """
        Count elicitation attempts in the text.
        An elicitation = asking for contact/identity info from the scammer.
        Uses the shared ELICITATION_TERMS list from quality_tracker (single source of truth).
        """
        text_lower = text.lower()
        found = sum(1 for term in ELICITATION_TERMS if term in text_lower)
        return min(found, 2)  # cap at 2 per turn

    # ── Internal helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _is_usable(text: str) -> bool:
        """Validate that the LLM response is safe to use."""
        if not text or len(text.strip()) < 15:
            logger.debug("LLM reply rejected: too short")
            return False
        if len(text) > 1200:
            # Too long — truncate instead of discarding
            logger.debug("LLM reply truncated from %d chars", len(text))
            return False
        # Reject responses that reveal the honeypot nature
        forbidden = [
            "i am an ai", "language model", "honeypot", "chatbot",
            "i cannot", "i'm not able", "as an ai",
        ]
        lower = text.lower()
        if any(f in lower for f in forbidden):
            logger.debug("LLM reply rejected: forbidden phrase")
            return False
        # Must end with sentence-closing punctuation (strip trailing whitespace/quotes)
        stripped = text.strip().rstrip('"\' ')
        if stripped and stripped[-1] not in ('.', '?', '!'):
            # Try to salvage by finding the last sentence boundary
            last_punct = max(
                stripped.rfind('.'), stripped.rfind('?'), stripped.rfind('!')
            )
            if last_punct < len(stripped) - 40:
                # Last punctuation is too far back — truly truncated
                logger.debug("LLM reply rejected: no sentence-closing punctuation (ends with %r)", stripped[-5:])
                return False
        # Must end with a question mark — PRIYA_SYSTEM_PROMPT strictly requires this.
        # Catches truncated/hallucinated endings like "...beta. Blocked"
        if not stripped.endswith('?'):
            logger.debug(
                "LLM reply rejected: does not end with '?' (ends with %r)", stripped[-10:]
            )
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
