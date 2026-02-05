"""
Intelligence extraction with context-aware patterns for accurate identification.
"""

import re
from typing import Dict, List


class IntelligenceExtractor:
    """
    Extracts intelligence from messages using context-aware patterns.

    STRATEGY:
    1. CONTEXT-AWARE: Look for labeled data ("account number 123", "UPI: xyz@bank")
    2. GENERIC PATTERNS: Fallback to pattern matching for unlabeled data
    3. VALIDATION: Clean and validate all extracted data

    This prevents misidentification (e.g., phone numbers extracted as accounts).
    """

    def __init__(self):
        """Initialize with generic fallback patterns."""
        # These are FALLBACK patterns when context is missing
        self.fallback_patterns = {
            "bank_accounts": [
                r'\b\d{12,18}\b',  # Only longer numbers (avoid phone confusion)
            ],
            "upi_ids": [
                r'\b[\w\.-]+@(?:paytm|phonepe|googlepay|gpay|amazonpay|bhim|ybl|okaxis|oksbi|ok hdfc bank|okicici|axisbank|hdfcbank|sbi|pnb|icici)\b',
                r'\b[\w\.-]+@[a-z]+bank\b',  # Fake banks like @fakebank
                r'\b[\w\.-]+@[\w-]+\b(?=.*(?:upi|pay|wallet))',
            ],
            "phone_numbers": [
                r'\+\d{1,3}[-\s]?\d{10}',  # International format (+91-9876543210)
                r'\b\d{10}\b',  # Standalone 10 digits (less priority)
            ],
            "email_addresses": [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            ],
            "phishing_links": [
                r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
                r'www\.[a-zA-Z0-9-]+\.[a-zA-Z]{2,}',
            ],
            "ifsc_codes": [
                r'\b[A-Z]{4}0[A-Z0-9]{6}\b',
            ],
        }

    def extract(self, message: str) -> Dict:
        """
        Extract intelligence using CONTEXT-AWARE patterns.

        Priority:
        1. Context-labeled data (highest accuracy)
        2. Generic patterns (lower accuracy)
        3. Validation and deduplication

        Args:
            message: Text to analyze

        Returns:
            Dict with categorized intelligence
        """
        extracted = {}
        text_lower = message.lower()

        # ==============================================================
        # STEP 1: CONTEXT-AWARE EXTRACTION (Labeled Data - High Priority)
        # ==============================================================

        # Bank Accounts with context
        account_patterns = [
            r'account\s*(?:number|no|#)?\s*(?:is|:)?\s*(\d{9,18})',
            r'a/?c\s*(?:number|no)?\s*:?\s*(\d{9,18})',
            r'bank\s*account\s*:?\s*(\d{9,18})',
        ]
        for pattern in account_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            if matches:
                if "bank_accounts" not in extracted:
                    extracted["bank_accounts"] = []
                extracted["bank_accounts"].extend(matches)

        # UPI IDs with context
        upi_patterns = [
            r'upi\s*(?:id)?\s*(?:is|:)?\s*([\w\.-]+@[\w-]+)',
            r'(?:my|our)\s*upi\s*:?\s*([\w\.-]+@[\w-]+)',
            r'transfer\s+to\s+([\w\.-]+@[\w-]+)',
        ]
        for pattern in upi_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            if matches:
                if "upi_ids" not in extracted:
                    extracted["upi_ids"] = []
                extracted["upi_ids"].extend(matches)

        # Phone numbers with context
        phone_patterns = [
            r'phone\s*(?:number)?\s*(?:is|:)?\s*([\+\d][\d\s\-\(\)]{8,})',
            r'(?:call|contact)\s+(?:us|me)?\s*(?:at|on)?\s*:?\s*([\+\d][\d\s\-\(\)]{8,})',
            r'mobile\s*(?:number)?\s*:?\s*([\+\d][\d\s\-\(\)]{8,})',
        ]
        for pattern in phone_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            if matches:
                if "phone_numbers" not in extracted:
                    extracted["phone_numbers"] = []
                extracted["phone_numbers"].extend(matches)

        # IFSC codes with context
        ifsc_patterns = [
            r'ifsc\s*(?:code)?\s*(?:is|:)?\s*([A-Z]{4}0[A-Z0-9]{6})',
        ]
        for pattern in ifsc_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            if matches:
                if "ifsc_codes" not in extracted:
                    extracted["ifsc_codes"] = []
                extracted["ifsc_codes"].extend(matches)

        # Links and emails (no context needed - unique enough)
        for pattern in self.fallback_patterns["phishing_links"]:
            matches = re.findall(pattern, message, re.IGNORECASE)
            if matches:
                if "phishing_links" not in extracted:
                    extracted["phishing_links"] = []
                extracted["phishing_links"].extend(matches)

        for pattern in self.fallback_patterns["email_addresses"]:
            matches = re.findall(pattern, message, re.IGNORECASE)
            if matches:
                if "email_addresses" not in extracted:
                    extracted["email_addresses"] = []
                extracted["email_addresses"].extend(matches)

        # ==============================================================
        # STEP 2: GENERIC FALLBACK (Only if context didn't find anything)
        # ==============================================================

        for data_type, patterns in self.fallback_patterns.items():
            # Skip if already extracted via context (higher priority)
            if data_type in extracted and len(extracted[data_type]) > 0:
                continue

            # Skip links/emails (already done above)
            if data_type in ["phishing_links", "email_addresses"]:
                continue

            for pattern in patterns:
                matches = re.findall(pattern, message, re.IGNORECASE)
                if matches:
                    if data_type not in extracted:
                        extracted[data_type] = []
                    extracted[data_type].extend(matches)

        # ==============================================================
        # STEP 3: CLEAN, VALIDATE, DEDUPLICATE
        # ==============================================================

        for data_type in list(extracted.keys()):
            cleaned = []
            seen = set()

            for match in extracted[data_type]:
                clean = self._clean_match(match, data_type)
                if clean and clean not in seen:
                    if self._is_valid(clean, data_type):
                        cleaned.append(clean)
                        seen.add(clean)

            if cleaned:
                extracted[data_type] = cleaned
            else:
                del extracted[data_type]

        # Remove UPI IDs from emails (UPI takes priority)
        if "upi_ids" in extracted and "email_addresses" in extracted:
            upi_set = set(extracted["upi_ids"])
            extracted["email_addresses"] = [
                email for email in extracted["email_addresses"]
                if email not in upi_set
            ]
            if not extracted["email_addresses"]:
                del extracted["email_addresses"]

        return extracted

    def _clean_match(self, match: str, data_type: str) -> str:
        """Clean extracted match."""
        if isinstance(match, tuple):
            match = match[0] if match else ""

        match = match.strip()

        if data_type == "phone_numbers":
            # Keep formatting for readability
            return match
        elif data_type == "bank_accounts":
            # Remove any spaces/dashes
            return re.sub(r'[\s\-]', '', match)

        return match

    def _is_valid(self, value: str, data_type: str) -> bool:
        """Validate extracted value."""
        if not value or len(value) < 2:
            return False

        if data_type == "bank_accounts":
            # Must be 9-18 digits
            digits = re.sub(r'\D', '', value)
            return 9 <= len(digits) <= 18

        elif data_type == "upi_ids":
            # Must have @ symbol and reasonable format
            parts = value.split('@')
            if len(parts) != 2:
                return False
            username, domain = parts
            return len(username) >= 2 and len(domain) >= 3

        elif data_type == "phone_numbers":
            # Must have 10-13 digits
            digits = re.sub(r'\D', '', value)
            return 10 <= len(digits) <= 13

        elif data_type == "ifsc_codes":
            # Exactly 11 characters, 5th must be 0
            return len(value) == 11 and value[4] == '0'

        return True
