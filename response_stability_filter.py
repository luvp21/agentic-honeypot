"""
ELITE REFINEMENT 6: Response Stability Filter

Enforces personality rigidity by rejecting AI-like responses.
"""

import re
import logging

logger = logging.getLogger(__name__)


class ResponseStabilityFilter:
    """Filter to ensure responses maintain rigid persona and avoid AI leakage."""

    MAX_WORDS = 150
    MAX_APOLOGIES = 2

    FORBIDDEN_PHRASES = [
        "as an ai",
        "i am an ai",
        "i'm a language model",
        "as a language model",
        "i don't have",
        "i cannot",
        "i'm not able to",
        "my purpose is",
        "i was trained",
        "my training"
    ]

    ANALYTICAL_INDICATORS = [
        "it appears that",
        "upon analysis",
        "this suggests",
        "based on the information",
        "from my perspective",
        "in my assessment"
    ]

    def is_valid(self, response: str) -> tuple[bool, str]:
        """
        Validate response against stability criteria.

        Args:
            response: LLM-generated response

        Returns:
            tuple of (is_valid, rejection_reason)
        """
        response_lower = response.lower()

        # Check 1: Word count
        word_count = len(response.split())
        if word_count > self.MAX_WORDS:
            return False, f"TOO_LONG ({word_count} words)"

        # Check 2: Excessive apologies
        apology_count = sum(1 for phrase in ["sorry", "apologize", "apologies"] if phrase in response_lower)
        if apology_count > self.MAX_APOLOGIES:
            return False, f"EXCESSIVE_APOLOGIES ({apology_count})"

        # Check 3: AI self-reference
        for phrase in self.FORBIDDEN_PHRASES:
            if phrase in response_lower:
                return False, f"AI_LEAKAGE: '{phrase}'"

        # Check 4: Analytical tone
        for indicator in self.ANALYTICAL_INDICATORS:
            if indicator in response_lower:
                return False, f"ANALYTICAL_TONE: '{indicator}'"

        return True, "VALID"

    def apply_filter(self, response: str, fallback: str) -> tuple[str, bool]:
        """
        Apply filter and return fallback if invalid.

        Args:
            response: LLM response
            fallback: Fallback response (deterministic persona template)

        Returns:
            tuple of (final_response, was_rejected)
        """
        is_valid, reason = self.is_valid(response)

        if not is_valid:
            logger.warning(f"⚠️ [RESPONSE STABILITY FILTER] Rejected: {reason}")
            return fallback, True

        return response, False


# Global instance
response_stability_filter = ResponseStabilityFilter()
