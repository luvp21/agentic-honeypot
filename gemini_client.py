"""
gemini_client.py — Async wrapper for Google Gemini 2.0-flash.

Responsibilities:
  1. generate()            — generic async text generation with 8s timeout
  2. classify_scam()       — structured scam classification (JSON response)
  3. generate_response()   — persona-driven agent reply generation
  4. extract_intel_llm()   — extract all 8 intel types from conversation

Falls back gracefully when Gemini is unavailable or times out.
LLM timeout: 8s (platform allows 30s total; we need headroom for sleep delay + response).
"""

import re
import json
import asyncio
import logging
import os
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
GEMINI_MODEL   = "gemini-2.5-flash"
LLM_TIMEOUT    = 15  # seconds — was 8s, but classify + generate can stack up
MAX_OUTPUT_LEN = 500  # characters — keep replies under 80 words


# ---------------------------------------------------------------------------
# Try to import the SDK; degrade gracefully if not installed
# ---------------------------------------------------------------------------
try:
    from google import genai
    from google.genai import types as genai_types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-genai not installed. All LLM calls will use rule-based fallback.")


# ---------------------------------------------------------------------------
# GeminiClient
# ---------------------------------------------------------------------------

class GeminiClient:

    def __init__(self) -> None:
        self._configured = False
        self._client = None

        api_key = os.getenv("GEMINI_API_KEY", "")
        if api_key and GEMINI_AVAILABLE:
            try:
                self._client = genai.Client(api_key=api_key)
                self._configured = True
                logger.info(f"Gemini client ready: {GEMINI_MODEL}")
            except Exception as e:
                logger.error(f"Gemini initialisation failed: {e}")
        else:
            logger.warning("Gemini API key not set or SDK missing — rule-based fallback only.")

    # ── Core generation ──────────────────────────────────────────────────────

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 512,
    ) -> Optional[str]:
        """
        Generate text from Gemini with an 8-second timeout.
        Returns None on timeout or error so callers can use fallback.
        """
        if not self._configured:
            return None

        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

        try:
            loop = asyncio.get_event_loop()

            def _call() -> str:
                response = self._client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=full_prompt,
                    config=genai_types.GenerateContentConfig(
                        temperature=0.7,
                        top_p=0.9,
                        max_output_tokens=max_tokens,
                    ),
                )
                return response.text or ""

            text = await asyncio.wait_for(
                loop.run_in_executor(None, _call),
                timeout=LLM_TIMEOUT,
            )
            return text.strip() if text else None
        except asyncio.TimeoutError:
            logger.warning("Gemini timeout after %ds", LLM_TIMEOUT)
            return None
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            return None

    # ── Scam classification ──────────────────────────────────────────────────

    async def classify_scam(
        self,
        text: str,
        conversation_history: List[Dict[str, str]],
    ) -> Optional[Dict[str, Any]]:
        """
        Ask Gemini to classify the scam type and extract confidence.
        Used as LLM layer in hybrid detection when rule score is ambiguous (3-7).
        Returns parsed JSON dict or None.
        """
        history_str = "\n".join(
            f"{m['role'].upper()}: {m['content']}"
            for m in conversation_history[-5:]
        )

        prompt = f"""Analyse this scam conversation and the latest message.

CONVERSATION HISTORY:
{history_str}

LATEST MESSAGE:
{text}

Respond ONLY in valid JSON:
{{
  "is_scam": true,
  "scam_type": "<one of: bank_fraud, upi_fraud, phishing_link, kyc_fraud, job_scam, \
lottery_scam, electricity_bill, govt_scheme, crypto_investment, customs_parcel, \
tech_support, loan_scam, income_tax, refund_scam, insurance>",
  "confidence": <0.0-1.0>,
  "red_flags": ["<flag1>", "<flag2>"]
}}"""

        raw = await self.generate(prompt)
        if raw:
            return self._parse_json(raw)
        return None

    # ── Agent response generation ────────────────────────────────────────────

    async def generate_agent_response(
        self,
        system_prompt: str,
        conversation_history: List[Dict[str, str]],
        incoming_message: str,
        turn: int,
        intel_summary: str,
        task: str,
        suggested_question_type: str,
    ) -> Optional[str]:
        """
        Generate Priya's response for this turn.
        Instructs LLM to include ≥1 question and ≥1 elicitation attempt.
        """
        history_str = self._format_history(conversation_history[-6:])

        prompt = f"""CONVERSATION SO FAR:
{history_str}

SCAMMER'S LATEST MESSAGE:
{incoming_message}

CURRENT TURN: {turn}/10
YOUR TASK THIS TURN: {task}
FOCUS QUESTION TYPE: {suggested_question_type}
INTEL COLLECTED SO FAR: {intel_summary}

Rules you MUST follow:
1. Stay in character as Priya — confused, slightly worried, cooperative
2. Keep response under 80 words
3. End with EXACTLY ONE question (must contain "?")
4. Include ONE elicitation attempt (ask for phone/ID/name/company/website/address)
5. Reference something the scammer just said to seem genuine
6. Do NOT reveal you are an AI, bot, or honeypot"""

        raw = await self.generate(prompt, system_prompt)
        return raw

    # ── Intel extraction via LLM ─────────────────────────────────────────────

    async def extract_intel_llm(
        self,
        conversation_history: List[Dict[str, str]],
    ) -> Optional[Dict[str, List[str]]]:
        """
        Ask Gemini to extract all 8 intel types from full conversation history.
        Called every 3 turns as a supplement to regex extraction.
        Returns dict with 8 keys or None on failure.
        """
        history_str = "\n".join(
            f"{m['role'].upper()}: {m['content']}"
            for m in conversation_history
        )

        prompt = f"""Extract every piece of personal or financial information from this conversation.
Look specifically for:
- Phone numbers (any format)
- Bank account numbers
- UPI IDs (xxx@xxx format)
- Suspicious URLs or website links
- Email addresses
- Case / reference / ticket IDs
- Policy / insurance / scheme numbers
- Order / transaction / invoice numbers

CONVERSATION:
{history_str}

Respond ONLY in valid JSON (use empty arrays if nothing found):
{{
  "phoneNumbers": [],
  "bankAccounts": [],
  "upiIds": [],
  "phishingLinks": [],
  "emailAddresses": [],
  "caseIds": [],
  "policyNumbers": [],
  "orderNumbers": []
}}"""

        raw = await self.generate(prompt, max_tokens=1024)
        if raw:
            return self._parse_json(raw)
        return None

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_json(raw: str) -> Optional[Dict]:
        """Extract and parse the first JSON object found in the LLM response.
        Handles Gemini 2.5-flash wrapping JSON in code fences, adding preamble
        text, or surrounding JSON with backtick-less markdown.
        """
        if not raw:
            return None

        # 1. Try direct parse
        try:
            return json.loads(raw.strip())
        except json.JSONDecodeError:
            pass

        # 2. Extract from ```json ... ``` or ``` ... ``` fence
        fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL | re.IGNORECASE)
        if fence_match:
            try:
                return json.loads(fence_match.group(1))
            except json.JSONDecodeError:
                pass

        # 3. Slice from first { to last } (handles preamble/postamble text)
        start = raw.find('{')
        end   = raw.rfind('}')
        if start != -1 and end != -1 and end > start:
            candidate = raw[start:end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                # 4. Last resort: regex to find any {...} block
                for m in re.finditer(r"\{[^{}]*\}", raw, re.DOTALL):
                    try:
                        return json.loads(m.group())
                    except json.JSONDecodeError:
                        continue

        logger.warning("Could not parse JSON from LLM response (len=%d, preview=%r)", len(raw), raw[:120])
        return None

    @staticmethod
    def _format_history(history: List[Dict[str, str]]) -> str:
        if not history:
            return "(No prior conversation)"
        return "\n".join(
            f"{m.get('role', 'unknown').upper()}: {m.get('content', '')}"
            for m in history
        )

    @property
    def is_available(self) -> bool:
        return self._configured


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
gemini_client = GeminiClient()
