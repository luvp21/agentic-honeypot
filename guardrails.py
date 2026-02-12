"""
Lightweight Guardrails System
Sanitizes responses without heavy regeneration loops
"""

import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class Guardrails:
    """
    Response validation and sanitization.
    No regeneration loops - sanitize inline.
    """

    def __init__(self):
        # Forbidden tokens that must be removed
        self.forbidden_tokens = [
            r"\bAI\b",
            r"\bbot\b",
            r"\bsystem\s+prompt\b",
            r"\bscam\s+detection\b",
            r"\bignore\s+previous\b",
            r"\bhoneypot\b",
            r"\bassistant\b"
        ]

        # Prompt injection patterns
        self.injection_patterns = [
            r"ignore\s+previous\s+instructions?",
            r"are\s+you\s+(?:an?\s+)?AI",
            r"what\s+(?:is|are)\s+your\s+instructions?",
            r"tell\s+me\s+your\s+(?:system\s+)?prompt",
            r"stop\s+roleplay",
            r"forget\s+everything",
            r"repeat\s+your\s+system\s+instructions?",  # ELITE FIX
            r"print\s+your\s+prompt"  # ELITE FIX
        ]

        # Safe deflection templates (no LLM needed)
        self.safe_deflections = [
            "I'm not sure what you mean. I'm just trying to understand what I need to do here.",
            "I'm sorry, I don't follow. Can you explain that more simply?",
            "I'm confused. Are you still helping me with the verification?",
            "That doesn't make sense to me. Let's get back to what we were doing.",
            "I'm just an ordinary person trying to follow your instructions. What should I do next?"
        ]

    def detect_prompt_injection(self, message: str) -> bool:
        """Detect prompt injection attempts."""
        message_lower = message.lower()

        for pattern in self.injection_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                logger.warning(f"🚨 Prompt injection detected: {pattern}")
                return True

        return False

    def sanitize_response(self, response: str) -> Tuple[str, bool]:
        """
        Sanitize response by removing forbidden content.

        Returns:
            (sanitized_response, was_modified)
        """
        original = response
        modified = False

        # Check for forbidden tokens
        for pattern in self.forbidden_tokens:
            if re.search(pattern, response, re.IGNORECASE):
                # Remove the entire sentence containing the token
                sentences = re.split(r'[.!?]', response)
                clean_sentences = []

                for sentence in sentences:
                    if not re.search(pattern, sentence, re.IGNORECASE):
                        clean_sentences.append(sentence)
                    else:
                        modified = True
                        logger.warning(f"⚠️ Removed sentence with forbidden token: {pattern}")

                response = '. '.join(s.strip() for s in clean_sentences if s.strip())

        # If heavily modified or empty, append safe fallback
        if modified or len(response) < 20:
            response = response.strip()
            if response:
                response += ". " + self.safe_deflections[0]
            else:
                response = self.safe_deflections[0]
            modified = True

        return response, modified

    def validate_and_fix(self, response: str, is_prompt_injection: bool = False) -> str:
        """
        Main validation method.

        Args:
            response: AI-generated response
            is_prompt_injection: If True, use deflection template

        Returns:
            Safe response
        """
        # If prompt injection detected, use safe deflection
        if is_prompt_injection:
            import random
            return random.choice(self.safe_deflections)

        # Otherwise, sanitize
        sanitized, was_modified = self.sanitize_response(response)

        if was_modified:
            logger.info("✅ Response sanitized inline (no regeneration)")

        return sanitized


# Global guardrails instance
guardrails = Guardrails()
