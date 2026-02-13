"""
Lightweight Guardrails System with 4-Layer Injection Defense
Sanitizes responses without heavy regeneration loops
"""

import re
import logging
from typing import Tuple
from injection_defense import (
    instruction_sanitizer,
    output_validator,
    injection_handler
)

logger = logging.getLogger(__name__)


class Guardrails:
    """
    Response validation and sanitization with 4-layer injection defense.
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
            r"\bassistant\b",
            r"\blanguage\s+model\b",
            r"\btrained\s+by\b"
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
        """
        Detect prompt injection attempts using Layer A + D.

        Args:
            message: User message to check

        Returns:
            True if injection detected
        """
        return injection_handler.detect_injection(message)

    def sanitize_user_input(self, message: str) -> Tuple[str, bool]:
        """
        Layer A: Sanitize user input BEFORE sending to LLM.

        Args:
            message: Raw user message

        Returns:
            Tuple of (sanitized_message, was_modified)
        """
        return instruction_sanitizer.sanitize(message)

    def sanitize_response(self, response: str) -> Tuple[str, bool]:
        """
        Layer C: Sanitize response by removing forbidden content.

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

        # Additional validation using Layer C
        is_valid, error = output_validator.validate_text(response)
        if not is_valid:
            modified = True
            logger.warning(f"⚠️ Output validation failed: {error}")

        # If heavily modified or empty, append safe fallback
        if modified or len(response) < 20:
            response = response.strip()
            if response:
                response += ". " + self.safe_deflections[0]
            else:
                response = self.safe_deflections[0]
            modified = True

        return response, modified

    def validate_and_fix(
        self,
        response: str,
        is_prompt_injection: bool = False,
        turn_number: int = 0
    ) -> str:
        """
        Main validation method with deterministic deflection.

        Args:
            response: AI-generated response
            is_prompt_injection: If True, use deflection template
            turn_number: Current turn (for deterministic selection)

        Returns:
            Safe response
        """
        # If prompt injection detected, use deterministic safe deflection
        if is_prompt_injection:
            # Deterministic selection instead of random
            index = turn_number % len(self.safe_deflections)
            return self.safe_deflections[index]

        # Otherwise, sanitize
        sanitized, was_modified = self.sanitize_response(response)

        if was_modified:
            logger.info("✅ Response sanitized inline (no regeneration)")

        return sanitized


# Global guardrails instance
guardrails = Guardrails()
