
"""
Gemini Client Wrapper
Centralized access to Google Gemini API with safety wrappers and timeouts.
"""

import os
import logging
import google.generativeai as genai
from typing import Optional, Dict, Any
from llm_safety import safe_llm_call, is_llm_available

logger = logging.getLogger(__name__)

# Configure Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning("⚠️ GEMINI_API_KEY not found in environment variables. LLM features will be disabled.")


class GeminiClient:
    def __init__(self):
        self.model = genai.GenerativeModel("models/gemini-flash-latest")

    async def generate_response(self, prompt: str, operation_name: str = "generator") -> Optional[str]:
        """
        Generate text response using Gemini with safety wrapper.

        Args:
            prompt: The input prompt
            operation_name: Name for circuit breaker ("generator", "classifier", "extractor")

        Returns:
            Generated text or None if failed
        """
        if not GEMINI_API_KEY:
            logger.warning(f"Skipping {operation_name} - API key missing")
            return None

        if not is_llm_available(operation_name):
            logger.warning(f"Skipping {operation_name} - Circuit breaker open")
            return None

        async def _call_gemini():
            response = await self.model.generate_content_async(prompt)
            return response.text

        try:
            # Use safe_llm_call for timeout and circuit breaker protection
            result = await safe_llm_call(
                _call_gemini,
                timeout=3.0 if operation_name == "generator" else 2.0,
                fallback_value=None,
                operation_name=operation_name
            )
            return result
        except Exception as e:
            logger.error(f"Gemini error in {operation_name}: {e}")
            return None

# Global instance
gemini_client = GeminiClient()
