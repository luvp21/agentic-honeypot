"""
Intelligence extraction with context-aware patterns for accurate identification.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Set

# ═══════════════════════════════════════════════════════════════════════════
# INDIAN PHONE NUMBER EXTRACTION MODULE
# ═══════════════════════════════════════════════════════════════════════════
# Deterministic extraction of Indian mobile numbers with normalization.
# Supports multiple formats: +91, 0 prefix, various separators (space, hyphen, dot).
# Uses negative lookbehind/lookahead to prevent partial matches from longer digit sequences.
# ═══════════════════════════════════════════════════════════════════════════

# Precompiled regex for Indian phone numbers
# Pattern explanation:
# - (?<!\d): Negative lookbehind - ensures we don't match digits that are part of a longer number
# - (?:\+91[\s.-]*|91[\s.-]*|0)?: Optional group for:
#   - Country code with + (+91)
#   - Country code without + (91)
#   - Trunk prefix (0)
#   All with flexible separators (space, hyphen, dot)
# - [6-9]: First digit must be 6-9 (valid Indian mobile number range)
# - (?:[\s.-]*\d){9}: Nine more digits with optional separators (space, hyphen, dot) between them
# - (?!\d): Negative lookahead - ensures we don't match if followed by more digits
INDIAN_PHONE_REGEX = re.compile(
    r'(?<!\d)(?:\+91[\s.-]*|91[\s.-]*|0)?[6-9](?:[\s.-]*\d){9}(?!\d)',
    re.IGNORECASE
)

def extract_indian_phone_numbers(text: str) -> List[str]:
    """
    Extract and normalize Indian phone numbers from text.

    This is a deterministic, regex-based extraction function that:
    - Finds Indian mobile numbers in various formats
    - Normalizes them to clean 10-digit format (no prefix, no separators)
    - Returns only unique numbers
    - Does NOT use AI/LLM inference

    Args:
        text: Input text to extract phone numbers from

    Returns:
        List of unique normalized phone numbers (10 digits each, as strings)

    Supported formats:
        - 9876543210
        - +919876543210
        - +91 9876543210
        - +91-9876543210
        - +91 98765 43210
        - +91-98765-43210
        - 09876543210
        - 98765 43210
        - 9876 543 210
        - 98765.43210
        - 98765-43210
        - 98765 - 43210
        - 9 8 7 6 5 4 3 2 1 0
        - +91  98765--43210
        - 919876543210 (without +)

    Example:
        >>> extract_indian_phone_numbers("Call me at +91-9876543210")
        ['9876543210']
        >>> extract_indian_phone_numbers("Contact: 98765 43210 or +91 8765432109")
        ['9876543210', '8765432109']
    """
    if not text:
        return []

    # Find all matches using precompiled regex
    matches = INDIAN_PHONE_REGEX.findall(text)

    # Normalize and deduplicate
    normalized_numbers: Set[str] = set()

    for match in matches:
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', match)

        # Handle different prefix scenarios:
        # - If starts with 91 and has 12 digits total (919876543210), strip the 91
        # - If starts with 0 and has 11 digits total (09876543210), strip the 0
        # - Otherwise, it should already be 10 digits

        if len(digits_only) == 12 and digits_only.startswith('91'):
            # Strip country code (91)
            normalized = digits_only[2:]
        elif len(digits_only) == 11 and digits_only.startswith('0'):
            # Strip trunk prefix (0)
            normalized = digits_only[1:]
        else:
            # Already in correct format or close to it
            normalized = digits_only

        # Validate final number is exactly 10 digits and starts with 6-9
        if len(normalized) == 10 and normalized[0] in '6789':
            normalized_numbers.add(normalized)

    # Return as sorted list for deterministic ordering
    return sorted(list(normalized_numbers))


# ═══════════════════════════════════════════════════════════════════════════
# CONTEXT-AWARE UPI ID EXTRACTION MODULE
# ═══════════════════════════════════════════════════════════════════════════
# Deterministic extraction of UPI IDs with payment-intent context validation.
# Uses regex-based extraction combined with keyword-based intent detection.
# Provides risk scoring based on presence of payment keywords.
# Does NOT use AI/LLM inference - purely rule-based.
# ═══════════════════════════════════════════════════════════════════════════

# Precompiled regex for UPI ID extraction
# Pattern explanation:
# - (?<![\w.-]): Negative lookbehind - ensures we don't match inside larger tokens
# - [A-Za-z0-9._-]{2,}: Username part (alphanumeric, dots, underscores, hyphens, min 2 chars)
# - \s*@\s*: @ symbol with optional spaces around it (0 or more)
# - [A-Za-z][A-Za-z0-9]*: Handle/provider part (must start with letter, then alphanumeric, min 2 total)
# - (?![\w.-]): Negative lookahead - ensures we don't match inside larger tokens
# Updated to be more permissive with spaces and avoid edge-case punctuation issues
UPI_ID_REGEX = re.compile(
    r'(?<![\w.-])([A-Za-z0-9._-]{2,})\s*@\s*([A-Za-z]{2,})(?![\w.-])',
    re.IGNORECASE
)

# Payment intent keyword lexicon (deterministic)
PAYMENT_INTENT_KEYWORDS = [
    "send", "transfer", "pay", "payment",
    "gpay", "google pay", "phonepe", "paytm",
    "bhim", "upi", "money", "amount",
    "deposit", "credit", "urgent", "now", "asap"
]

def extract_upi_ids(text: str) -> List[str]:
    """
    Extract and normalize UPI IDs from text.

    This is a deterministic, regex-based extraction function that:
    - Finds UPI IDs in format: username@provider
    - Normalizes them (removes spaces, lowercase, removes trailing punctuation)
    - Returns only unique UPI IDs
    - Does NOT use AI/LLM inference

    Args:
        text: Input text to extract UPI IDs from

    Returns:
        List of unique normalized UPI IDs (as strings)

    Supported formats:
        - user@paytm
        - user.name@gpay
        - user_123@phonepe
        - user-name@ybl
        - username @ provider (spaces around @)
        - User@Provider (case insensitive)

    Example:
        >>> extract_upi_ids("Pay to scammer@paytm")
        ['scammer@paytm']
        >>> extract_upi_ids("Send money to user @ gpay or backup@phonepe")
        ['backup@phonepe', 'user@gpay']
    """
    if not text:
        return []

    # Find all matches using precompiled regex (returns tuples of groups)
    matches = UPI_ID_REGEX.findall(text)

    # Normalize and deduplicate
    normalized_upis: Set[str] = set()

    for match in matches:
        # match is a tuple (username, provider)
        if isinstance(match, tuple) and len(match) == 2:
            username, provider = match
            # Construct normalized UPI ID
            normalized = f"{username}@{provider}".lower()

            # Remove any trailing/leading punctuation
            normalized = re.sub(r'^[.,!;]+', '', normalized)
            normalized = re.sub(r'[.,!;]+$', '', normalized)

            # Validate
            if normalized.count('@') == 1:
                normalized_upis.add(normalized)

    # Return as sorted list for deterministic ordering
    return sorted(list(normalized_upis))


def detect_payment_intent(text: str) -> bool:
    """
    Detect payment intent using deterministic keyword matching.

    This function checks if the text contains any payment-related keywords
    from the predefined lexicon. This is purely keyword-based detection
    without any AI/LLM inference.

    Args:
        text: Input text to analyze for payment intent

    Returns:
        True if payment intent detected, False otherwise

    Example:
        >>> detect_payment_intent("Please send money to my account")
        True
        >>> detect_payment_intent("My UPI ID is user@paytm")
        True
        >>> detect_payment_intent("Hello, how are you?")
        False
    """
    if not text:
        return False

    # Convert to lowercase for case-insensitive matching
    text_lower = text.lower()

    # Check if any payment keyword is present
    for keyword in PAYMENT_INTENT_KEYWORDS:
        if keyword in text_lower:
            return True

    return False


def context_based_upi_detection(text: str) -> dict:
    """
    Perform context-aware UPI detection with risk scoring.

    This function combines UPI extraction with payment intent detection
    to provide a risk assessment. The logic is deterministic and rule-based:

    - If UPI detected AND payment intent detected: High Risk (risk_score += 40)
    - If UPI detected but no payment intent: Medium Risk (risk_score += 15)
    - If no UPI detected: No risk

    Args:
        text: Input text to analyze

    Returns:
        Dictionary with structure:
        {
            "upi_detected": bool,
            "upi_ids": list,
            "intent_detected": bool,
            "risk_score": int,
            "classification": str
        }

    Example:
        >>> context_based_upi_detection("Send money to scammer@paytm urgent!")
        {
            'upi_detected': True,
            'upi_ids': ['scammer@paytm'],
            'intent_detected': True,
            'risk_score': 40,
            'classification': 'High Risk - UPI Payment Request'
        }

        >>> context_based_upi_detection("My ID is user@paytm")
        {
            'upi_detected': True,
            'upi_ids': ['user@paytm'],
            'intent_detected': True,
            'risk_score': 40,
            'classification': 'High Risk - UPI Payment Request'
        }
    """
    # Extract UPI IDs
    upi_ids = extract_upi_ids(text)
    upi_detected = len(upi_ids) > 0

    # Detect payment intent
    intent_detected = detect_payment_intent(text)

    # Initialize result structure
    result = {
        "upi_detected": upi_detected,
        "upi_ids": upi_ids,
        "intent_detected": intent_detected,
        "risk_score": 0,
        "classification": "No UPI Detected"
    }

    # Apply deterministic risk scoring logic
    if upi_detected and intent_detected:
        result["risk_score"] = 40
        result["classification"] = "High Risk - UPI Payment Request"
    elif upi_detected and not intent_detected:
        result["risk_score"] = 15
        result["classification"] = "UPI Mention Without Clear Payment Intent"

    return result


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
        ifsc_pattern = r'(?i)\b([a-z]{4}0[a-z0-9]{6})\b'
        for match in re.finditer(ifsc_pattern, text):
            value = match.group(1).upper() # Normalize to uppercase
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
        if "upi" in full_text.lower() or "pay" in full_text.lower():
            generic_upi_pattern = r'\b([a-zA-Z0-9.\-_]{2,}@[a-zA-Z0-9.\-_]{2,})\b'
            for match in re.finditer(generic_upi_pattern, text):
                val = match.group(1)
                if any(x.value == val and x.type == "upi_ids" for x in extracted): continue
                extracted.append(RawIntel("upi_ids", val, "context_fallback", 1.0, message_index))

        # 2.4 Phone Numbers (Enhanced Robust Logic)
        # Matches +91 with flexible spacing/hyphens, and 10-digit numbers starting with 6-9
        phone_pattern = r'(?i)(?<!\d)(?:\+?[\s\-]*91[\s\-]*)?([6-9]\d{9})(?!\d)'
        for match in re.finditer(phone_pattern, text):
            value = match.group(0)

            start, end = match.span()
            nearby_text = text[max(0, start-30):min(len(text), end+30)].lower()

            # Positive Context
            phone_keywords = ["phone", "mobile", "whatsapp", "call", "contact", "tel", "number"]
            has_phone_context = any(w in nearby_text for w in phone_keywords)

            if not has_phone_context and context_window:
                 has_phone_context = any(w in context_window[-200:].lower() for w in phone_keywords)

            is_explicit = value.startswith("+") or value.startswith("91") or has_phone_context

            if not is_explicit and any(w in nearby_text for w in ["account", "a/c", "ifsc", "upi"]):
                continue

            extracted.append(RawIntel("phone_numbers", value, "strict", 1.0, message_index))

        # 2.5 Phishing Links (Legacy Strict)
        url_pattern = r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)'
        for match in re.finditer(url_pattern, text):
            extracted.append(RawIntel("phishing_links", match.group(1), "strict", 1.0, message_index))

        # 2.6 Short URLs (bit.ly, tinyurl, etc.)
        short_url_pattern = r'\b(?:https?://)?(?:bit\.ly|tinyurl\.com|t\.co|goo\.gl|ow\.ly|is\.gd|buff\.ly|rebrand\.ly)/[a-zA-Z0-9\-_]{3,20}\b'
        for match in re.finditer(short_url_pattern, text):
            extracted.append(RawIntel("short_urls", match.group(), "strict", 1.0, message_index))

        # 2.7 Telegram IDs (@username)
        telegram_pattern = r'(?<!\w)@([a-zA-Z][a-zA-Z0-9_]{4,31})(?!\w)'
        for match in re.finditer(telegram_pattern, text):
            has_context = any(w in text_lower for w in ["telegram", "tg", "contact", "message", "chat"])
            if has_context:
                extracted.append(RawIntel("telegram_ids", match.group(1), "context", 1.0, message_index))

        # 2.8 Holder Name & Branch (Advanced Context Extraction)
        # Patterns for: "name is X", "holder: X", "branch is X"
        holder_pattern = r'(?i)(?:account\s*name|holder|payee)(?:\s*(?:is|of|for|:|-))?\s*([a-z.\s]{2,30}?)(?=[,.]|$|\n)'
        for match in re.finditer(holder_pattern, text):
            name = match.group(1).strip()
            if len(name) > 3:
                extracted.append(RawIntel("suspicious_keywords", f"Holder: {name}", "context", 0.8, message_index))

        branch_pattern = r'(?i)(?:branch|location)(?:\s*(?:is|of|for|:|-))?\s*([a-z.\s]{2,20}?)(?=[,.]|$|\n)'
        for match in re.finditer(branch_pattern, text):
            branch = match.group(1).strip()
            if len(branch) > 2:
                extracted.append(RawIntel("suspicious_keywords", f"Branch: {branch}", "context", 0.7, message_index))

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

