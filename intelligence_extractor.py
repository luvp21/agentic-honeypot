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

    def extract(self, text: str, message_index: int = 0, context_window: str = "") -> List[RawIntel]:
        """
        Extract intelligence using strict precedence rules.

        Args:
            text: Current message text
            message_index: Index of current message
            context_window: Rolling window of previous messages (for partial extraction)

        Returns:
            List of RawIntel objects
        """
        extracted = []
        text_lower = text.lower()

        # Combined text for checking cross-message context
        # (For now, we use context_window mostly for proximity checks if not found locally)
        full_text = f"{context_window} {text}" if context_window else text

        # 1. NON-TARGETS Check
        for pattern in self.blacklist_patterns:
            if re.search(pattern, text):
                # If message contains OTP/Txn Ref, be very careful or skip?
                # Requirement: "Hard blacklist extraction if matched"
                # Does it mean blacklist the *message* or just the *value*?
                # "Explicit Non-Targets... Hard blacklist extraction if matched: OTP codes..."
                # I will implement logic to NOT extract values that look like these.
                pass

        # 2. CONTEXT-AWARE EXTRACTION (Highest Priority)

        # 2.1 Bank Accounts (Context Required)
        # Regex: (?i)(account\s*(number|no|#)|a\/c|acc\.?)\s*[:\-]?\s*([0-9]{9,18})
        bank_context_pattern = r'(?i)(?:account\s*(?:number|no\.?|#)|a\/c|acc\.?)\s*[:\-]?\s*([0-9]{9,18})'
        for match in re.finditer(bank_context_pattern, text):
            value = match.group(1)
            # Validate: Not a phone number (10 digits starting with 6-9)
            if re.match(r'^[6-9]\d{9}$', value):
                continue # Likely a phone number

            extracted.append(RawIntel(
                type="bank_accounts",
                value=value,
                source="context",
                confidence_delta=1.0,
                message_index=message_index
            ))

        # 2.2 IFSC Codes (Strict + Context Boost)
        ifsc_pattern = r'\b([A-Z]{4}0[A-Z0-9]{6})\b'
        for match in re.finditer(ifsc_pattern, text):
            value = match.group(1)
            # Check context boost
            has_context = bool(re.search(r'(?i)(account|bank|branch)', text))
            if not has_context and context_window:
                 has_context = bool(re.search(r'(?i)(account|bank|branch)', context_window[-200:])) # Look in recent context

            source = "context" if has_context else "strict"
            delta = 1.0 if has_context else 0.5 # Boost +0.5 if context, else base

            extracted.append(RawIntel(
                type="ifsc_codes",
                value=value,
                source=source,
                confidence_delta=delta,
                message_index=message_index
            ))

        # 2.3 UPI IDs (Strict Handle)
        # Regex: [a-zA-Z0-9.\-_]{2,}@(oksbi|...)\b
        handles_regex = "|".join(self.upi_handles)
        upi_pattern = fr'\b([a-zA-Z0-9.\-_]{{2,}}@(?:{handles_regex}))\b'
        for match in re.finditer(upi_pattern, text):
             extracted.append(RawIntel(
                type="upi_ids",
                value=match.group(1),
                source="strict",
                confidence_delta=1.0,
                message_index=message_index
            ))

        # 2.3.b UPI IDs (Contextual Fallback for Unknown Handles)
        # Allow any handle IF context explicitly mentions "UPI"
        if "upi" in full_text.lower():
            # Regex for generic handle (user@bank)
            generic_upi_pattern = r'\b([a-zA-Z0-9.\-_]{2,}@[a-zA-Z0-9.\-_]{2,})\b'
            for match in re.finditer(generic_upi_pattern, text):
                val = match.group(1)
                # Avoid duplicates with strict extraction
                if any(x.value == val and x.type == "upi_ids" for x in extracted):
                    continue

                extracted.append(RawIntel(
                    type="upi_ids",
                    value=val,
                    source="context_fallback", # Lower confidence source? Or context?
                    # "Context contains UPI" is strong signal.
                    confidence_delta=1.0,
                    message_index=message_index
                ))

        # 2.4 Phone Numbers (Strict + Negative Context)
        # Regex: (?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)
        phone_pattern = r'(?<!\d)(?:\+91[\s-]?)?([6-9]\d{9})(?!\d)'
        for match in re.finditer(phone_pattern, text):
            value = match.group(0) # Keep format or normalize?
            # Negative Context
            start, end = match.span()
            nearby_text = text[max(0, start-20):min(len(text), end+20)].lower()
            if any(w in nearby_text for w in ["account", "a/c", "ifsc", "upi"]):
                continue # Reject if mislabeled as account

            extracted.append(RawIntel(
                type="phone_numbers",
                value=value,
                source="strict",
                confidence_delta=1.0,
                message_index=message_index
            ))

        # 2.5 Phishing Links (Strict)
        url_pattern = r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)'
        for match in re.finditer(url_pattern, text):
            extracted.append(RawIntel(
                type="phishing_links",
                value=match.group(1),
                source="strict",
                confidence_delta=1.0,
                message_index=message_index
            ))

        # 3. CROSS-MESSAGE ENTITY COMPLETION (Bank + IFSC)
        # Checks if we have an orphaned account number in recent context that matches this IFSC
        # Or vice versa.
        # Since RawIntel is stateless, we just return what we found.
        # The SessionManager graph handles the merging of "account" and "ifsc" into the session state.
        # But if we see "account number" in previous message and a number here without context?
        # That's the tricky part.
        # Strategy: If "Bank Fallback" (number with no context) matches criteria AND context has "account", extract it.

        # 4. FALLBACK TIER (Low Confidence)
        if not any(x.type == "bank_accounts" for x in extracted):
             # Try finding loose numbers if context strongly implies bank info was coming
             # "My account number is" (in prev msg) -> "1234..." (in this msg)
             if re.search(r'(?i)account\s*(?:number|no|#)', context_window[-100:]):
                 # Look for numbers
                 fallback_nums = re.findall(r'\b(\d{9,18})\b', text)
                 for num in fallback_nums:
                     # Validate strictness (not phone)
                     if not re.match(r'^[6-9]\d{9}$', num):
                        extracted.append(RawIntel(
                            type="bank_accounts",
                            value=num,
                            source="fallback_context",
                            confidence_delta=0.5, # Boosted fallback
                            message_index=message_index
                        ))

        return extracted
