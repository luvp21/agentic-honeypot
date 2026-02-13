"""
Intelligence extraction with context-aware patterns for accurate identification.
"""

import re
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class RawIntel:
    type: str
    value: str
    source: str          # "context", "strict", "fallback"
    confidence_delta: float
    message_index: int


class IntelligenceExtractor:
    """
    Extracts intelligence from messages using context-aware patterns and strict validation.
    """

    def __init__(self):
        # Allowlist for UPI handles
        self.upi_handles = [
            "oksbi", "okaxis", "okicici", "paytm", "upi", "ybl", "ibl", "axl",
            "hdfcbank", "sbi", "icici", "kotak", "axisbank", "freecharge"
        ]

        # Blacklist patterns (OTP, etc.)
        self.blacklist_patterns = [
            r'(?i)\b(?:otp|one\s*time\s*password|verification\s*code)\b',
            r'(?i)\b(?:txn|transaction)\s*(?:id|no|ref)\b',
            r'(?i)\b(?:ref|reference)\s*(?:no|number)\b',
            r'(?i)\border\s*(?:id|no)\b'
        ]

    async def extract(self, text: str, message_index: int = 0, context_window: str = "") -> List[RawIntel]:
        """
        Extract intelligence using Hybrid LLM + Regex approach.
        """
        extracted = []

        # 1. Regex Extraction (Fast, strict)
        regex_extracted = self._extract_regex(text, message_index, context_window)
        extracted.extend(regex_extracted)

        # 2. LLM Extraction (Deep, context-aware)
        # Only use LLM if text has some content and context to avoid empty calls
        if text.strip():
            llm_extracted = await self._extract_with_llm(text, context_window, message_index)
            extracted.extend(llm_extracted)

        # Deduplicate based on value and type
        unique_extracted = []
        seen = set()
        for item in extracted:
            key = (item.type, item.value)
            if key not in seen:
                seen.add(key)
                unique_extracted.append(item)

        return unique_extracted

    def _extract_regex(self, text: str, message_index: int, context_window: str) -> List[RawIntel]:
        """Original regex-based extraction logic"""
        extracted = []
        text_lower = text.lower()
        full_text = f"{context_window} {text}" if context_window else text

        # [Original Regex Logic - Ported from previous extract method]
        # ... (I re-implement the regex logic here for clarity) ...
        # NON-TARGETS Check (from legacy)
        for pattern in self.blacklist_patterns:
            if re.search(pattern, text):
                # If message matches blacklist (like OTP), we might want to be careful
                # For now, we just pass, but it could be used to filter specific matches if implemented per-match
                pass

        # 2.1 Bank Accounts
        # Refined regex to allow for connecting words like "is", "of", ":", "-", etc.
        # Matches: "account number is 1234...", "Acc No: 1234...", "Account # 1234..."
        bank_context_pattern = r'(?i)(?:account\s*(?:number|no\.?|#)|a\/c|acc\.?)(?:\s+(?:is|of|for|:|-))?\s*[:\-]?\s*([0-9]{9,18})'
        for match in re.finditer(bank_context_pattern, text):
            value = match.group(1)
            # Filter out common false positives (like 10-digit mobile numbers starting with 6-9)
            if re.match(r'^[6-9]\d{9}$', value): continue
            extracted.append(RawIntel("bank_accounts", value, "context", 1.0, message_index))

        # 2.2 IFSC Codes
        ifsc_pattern = r'\b([A-Z]{4}0[A-Z0-9]{6})\b'
        for match in re.finditer(ifsc_pattern, text):
            value = match.group(1)
            has_context = bool(re.search(r'(?i)(account|bank|branch|ifsc)', text))
            if not has_context and context_window:
                 has_context = bool(re.search(r'(?i)(account|bank|branch|ifsc)', context_window[-200:]))
            extracted.append(RawIntel("ifsc_codes", value, "context" if has_context else "strict", 1.0 if has_context else 0.5, message_index))

        # 2.3 UPI IDs
        handles_regex = "|".join(self.upi_handles)
        upi_pattern = fr'\b([a-zA-Z0-9.\-_]{{2,}}@(?:{handles_regex}))\b'
        for match in re.finditer(upi_pattern, text):
            extracted.append(RawIntel("upi_ids", match.group(1), "strict", 1.0, message_index))

        # Generic UPI (fallback) - Must contain '@' and be surrounded by word boundaries
        # Validation: 'upi' keyword in context OR strong pattern structure
        if "upi" in full_text.lower() or "pay" in full_text.lower():
            generic_upi_pattern = r'\b([a-zA-Z0-9.\-_]{2,}@[a-zA-Z0-9.\-_]{2,})\b'
            for match in re.finditer(generic_upi_pattern, text):
                val = match.group(1)
                # Skip emails if possible (simple heuristic: upi ids usually don't have .com/org/net/in at end, but some do... relying on 'upi' context)
                if any(x.value == val and x.type == "upi_ids" for x in extracted): continue
                extracted.append(RawIntel("upi_ids", val, "context_fallback", 1.0, message_index))

        # 2.4 Phone Numbers (Legacy Robust Logic)
        phone_pattern = r'(?<!\d)(?:\+91[\s-]?)?([6-9]\d{9})(?!\d)'
        for match in re.finditer(phone_pattern, text):
            value = match.group(0)

            # Legacy Context Check
            start, end = match.span()
            nearby_text = text[max(0, start-30):min(len(text), end+30)].lower()

            # Check for positive phone context
            has_phone_context = any(w in nearby_text for w in ["phone", "mobile", "whatsapp", "call", "contact", "tel"])

            # If it has explicit phone context OR starts with +91, be more lenient
            is_explicit = value.startswith("+91") or has_phone_context

            # Negative Context: If NO phone context and HAS account context (likely an account number)
            if not is_explicit and any(w in nearby_text for w in ["account", "a/c", "ifsc", "upi"]):
                continue

            extracted.append(RawIntel("phone_numbers", value, "strict", 1.0, message_index))

        # 2.5 Phishing Links
        url_pattern = r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)'
        for match in re.finditer(url_pattern, text):
            extracted.append(RawIntel("phishing_links", match.group(1), "strict", 1.0, message_index))

        return extracted

    async def _extract_with_llm(self, text: str, context: str, message_index: int) -> List[RawIntel]:
        """PART 3 - EXTRACTION PROMPT"""
        from gemini_client import gemini_client
        import json

        prompt = f"""
You are an information extraction engine.

Extract ALL possible financial intelligence from the message and conversation context.

Context: "{context}"
Current Message: "{text}"

Look for:
- UPI IDs
- Bank account numbers
- IFSC codes
- Phone numbers
- Payment app handles
- Phishing URLs
- Partial numeric clues

Infer missing types if context strongly implies financial intent.

Return strictly JSON:

{{
"upiIds": [],
"bankAccounts": [],
"ifscCodes": [],
"phoneNumbers": [],
"links": [],
"confidence": 0.0-1.0
}}

Be aggressive but accurate. Do not miss implied payment information.
"""
        try:
            response = await gemini_client.generate_response(prompt, operation_name="extractor")
            if not response:
                return []

            cleaned = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned)

            headers = []

            for item in data.get("upiIds", []):
                headers.append(RawIntel("upi_ids", str(item), "llm", data.get("confidence", 0.8), message_index))

            for item in data.get("bankAccounts", []):
                headers.append(RawIntel("bank_accounts", str(item), "llm", data.get("confidence", 0.8), message_index))

            for item in data.get("ifscCodes", []):
                headers.append(RawIntel("ifsc_codes", str(item), "llm", data.get("confidence", 0.8), message_index))

            for item in data.get("phoneNumbers", []):
                headers.append(RawIntel("phone_numbers", str(item), "llm", data.get("confidence", 0.8), message_index))

            for item in data.get("links", []):
                headers.append(RawIntel("phishing_links", str(item), "llm", data.get("confidence", 0.8), message_index))

            return headers

        except Exception as e:
            # logger.error(f"LLM extraction failed: {e}")
            return []

    async def extract_from_full_history(
        self,
        messages: List,  # List[MessageContent]
        current_index: int
    ) -> List[RawIntel]:
        """
        Extract intelligence from ENTIRE conversation history.
        Used for backfill to ensure nothing is missed across turns.

        This runs periodically (e.g., every 5 turns) to catch:
        - Cross-message references
        - Partial information completion
        - Missed patterns

        Args:
            messages: Full conversation history (MessageContent objects)
            current_index: Current message index

        Returns:
            List of RawIntel from entire history
        """
        all_intel = []

        # Build full conversation text
        full_text = " ".join([msg.text for msg in messages])

        # Extract from full text with current index
        # We'll mark these with a special source "backfill"
        extracted = await self.extract(
            text=full_text,
            message_index=current_index,
            context_window=""
        )

        # Re-mark source as backfill
        for item in extracted:
            if item.source != "backfill":
                item.source = f"backfill_{item.source}"
                # Slight penalty for backfill (already tracked separately)
                item.confidence_delta *= 0.8

        return extracted

        return value.strip().lower()

    def normalize_value(self, value: str, intel_type: str) -> str:
        """
        Normalize values for better deduplication.

        Args:
            value: Raw value
            intel_type: Type of intelligence

        Returns:
            Normalized value
        """
        # Phone numbers: remove spaces, dashes, parentheses
        if intel_type == "phone_numbers":
            return "".join(filter(str.isdigit, value))

        # Bank accounts: digits only
        if intel_type == "bank_accounts":
            return "".join(filter(str.isdigit, value))

        # IFSC: uppercase, no spaces
        if intel_type == "ifsc_codes":
            return value.upper().strip()

        # UPI: lowercase, trim
        if intel_type == "upi_ids":
            return value.lower().strip()

        # URLs: lowercase
        if intel_type in ["phishing_links", "short_urls"]:
            return value.lower().strip()

        # Telegram: remove @, lowercase
        if intel_type == "telegram_ids":
            return value.lstrip("@").lower().strip()

        # QR and Keywords: lowercase
        if intel_type in ["suspicious_keywords", "qr_mentions"]:
            return value.lower().strip()

        # Default: trim and lowercase
        return value.strip().lower()

