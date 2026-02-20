"""
guardrails.py — Response validation and safety enforcement.

Ensures every agent response:
  1. Is not too short or too long
  2. Does not contain forbidden phrases (reveals AI/honeypot nature)
  3. Always ends with a question mark (scoring requirement)
  4. Has a safe per-turn fallback if everything else fails

This module is the LAST line of defence before a response reaches the platform.
"""

import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tuning constants
# ---------------------------------------------------------------------------
MIN_RESPONSE_LENGTH = 20    # characters
MAX_RESPONSE_LENGTH = 500   # characters (80-word target ≈ 400-500 chars)


# ---------------------------------------------------------------------------
# Patterns that would reveal the honeypot nature
# ---------------------------------------------------------------------------

FORBIDDEN_PATTERNS = [
    r"\b(?:AI|artificial intelligence|language model|large language model)\b",
    r"\bbot\b",
    r"\bhoneypot\b",
    r"\bchatbot\b",
    r"\bi am an ai\b",
    r"\bi cannot\b",
    r"\bi'm not able\b",
    r"\bas an ai\b",
    r"\bi don'?t have (?:the ability|access|feelings)\b",
    r"\bi'?m (?:a )?(?:virtual|digital) assistant\b",
]

_COMPILED_FORBIDDEN = [re.compile(p, re.IGNORECASE) for p in FORBIDDEN_PATTERNS]


# ---------------------------------------------------------------------------
# Per-turn safe fallback responses
# These are used when both Gemini AND the fallback template produce bad output.
# Each is guaranteed to:
#   - Be in character as Priya
#   - Contain a question ("?")
#   - Make an elicitation attempt
# ---------------------------------------------------------------------------

_SAFE_RESPONSES = {
    1:  "Oh goodness, I am not sure I understand. Who exactly are you and which organisation are you calling from?",
    2:  "I see. But dear, could you please give me your employee ID number so I can verify you?",
    3:  "This is worrying. What is the full name of your company? And do you have an official website I can check?",
    4:  "I need to call my son about this first. Can you give me your direct callback number?",
    5:  "Let me look for my papers. What is the case reference number for this matter?",
    6:  "I want to visit your office directly. What is your office address and city?",
    7:  "My son says always verify. Can you give me a confirmation number and your supervisor's name?",
    8:  "I am not comfortable without speaking to your manager. What is the supervisor's direct number?",
    9:  "Please send me everything in writing. What is your official email address?",
    10: "I am still confused about all this. Can you please call me again tomorrow with more details?",
}

_DEFAULT_SAFE = (
    "Oh dear, I am having some trouble understanding. "
    "Could you please repeat that? "
    "Also, can you tell me your employee ID number and which company you are from?"
)


# ---------------------------------------------------------------------------
# Guardrails
# ---------------------------------------------------------------------------

class Guardrails:

    def validate_response(
        self,
        response: str,
        turn: int = 1,
    ) -> Tuple[bool, str]:
        """
        Validate an agent response.

        Returns (is_valid: bool, final_response: str).
        If invalid, the returned string is a safe fallback — caller should use it.
        """
        # ── Empty / too short ─────────────────────────────────────────────
        if not response or len(response.strip()) < MIN_RESPONSE_LENGTH:
            logger.warning(f"Turn {turn}: Response too short ({len(response) if response else 0} chars)")
            return False, self._safe_for_turn(turn)

        # ── Trim if too long ──────────────────────────────────────────────
        if len(response) > MAX_RESPONSE_LENGTH:
            # Cut at last sentence boundary within the limit
            trimmed = response[:MAX_RESPONSE_LENGTH]
            last_period = trimmed.rfind(".")
            last_question = trimmed.rfind("?")
            cut_at = max(last_period, last_question)
            if cut_at > MIN_RESPONSE_LENGTH:
                response = trimmed[:cut_at + 1]
            else:
                response = trimmed.rstrip() + "."

        # ── Forbidden content ─────────────────────────────────────────────
        for pattern in _COMPILED_FORBIDDEN:
            if pattern.search(response):
                logger.warning(f"Turn {turn}: Forbidden pattern detected — using safe fallback")
                return False, self._safe_for_turn(turn)

        # ── Ensure at least one question mark ─────────────────────────────
        response = self.ensure_question_present(response, turn)

        return True, response

    def ensure_question_present(self, response: str, turn: int = 1) -> str:
        """
        If no "?" is present, append a turn-appropriate question.
        Scoring: every question mark contributes to the Questions Asked score (4 pts).
        """
        if "?" not in response:
            question_additions = {
                1:  " Could you tell me your name and which company you are from?",
                2:  " Can you give me your employee ID number?",
                3:  " What is your company's official website?",
                4:  " What is your direct callback phone number?",
                5:  " Can you provide the case reference number?",
                6:  " What is your office address?",
                7:  " Can you give me a confirmation or authorization number?",
                8:  " What is your supervisor's direct contact number?",
                9:  " What is your official email address?",
                10: " When will you call me again to follow up on this?",
            }
            addition = question_additions.get(turn, " Can you please verify your identity?")
            response = response.rstrip() + addition

        return response

    # ── Internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _safe_for_turn(turn: int) -> str:
        return _SAFE_RESPONSES.get(turn, _DEFAULT_SAFE)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
guardrails = Guardrails()
