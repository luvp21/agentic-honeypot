"""
Intelligence Extractor with CamelCase Mapping
Extracts sensitive information from scammer messages
ADAPTED FOR HACKATHON COMPLIANCE
"""

import re
from typing import Dict, List, Optional
from datetime import datetime


class IntelligenceExtractor:
    def __init__(self):
        # Regex patterns for different data types
        self.patterns = {
            "bank_accounts": [
                r'\b\d{9,18}\b',  # Generic bank account (9-18 digits)
                r'\b[0-9]{4}[0-9]{4}[0-9]{4}[0-9]{4}\b',  # 16 digit format
                r'account\s*(?:number|no|#)?\s*:?\s*(\d{9,18})',
                r'A/C\s*:?\s*(\d{9,18})',
            ],
            "upi_ids": [
                r'\b[\w\.-]+@(?:paytm|phonepe|googlepay|amazonpay|bhim|ybl|okaxis|oksbi|okhdfcbank|okicici)\b',
            ],
            "phone_numbers": [
                r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
                r'\b\d{10}\b',
                r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
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
        Extract all intelligence from a message.

        Args:
            message: Text message to analyze

        Returns:
            Dictionary with extracted data categorized by type (snake_case keys)
        """
        extracted = {}

        # Extract each data type
        for data_type, patterns in self.patterns.items():
            matches = []
            for pattern in patterns:
                found = re.findall(pattern, message, re.IGNORECASE)
                if found:
                    matches.extend([self._clean_match(m) for m in found])

            # Remove duplicates and filter
            matches = list(set(matches))
            matches = [m for m in matches if self._is_valid(m, data_type)]

            if matches:
                extracted[data_type] = matches

        # Special handling for UPI IDs vs Email addresses
        if "upi_ids" in extracted and "email_addresses" in extracted:
            upi_set = set(extracted["upi_ids"])
            extracted["email_addresses"] = [
                email for email in extracted["email_addresses"]
                if email not in upi_set
            ]
            if not extracted["email_addresses"]:
                del extracted["email_addresses"]

        return extracted

    def _clean_match(self, match: str) -> str:
        """Clean extracted match"""
        cleaned = ' '.join(match.split())
        cleaned = cleaned.strip('.,;:!?')
        return cleaned

    def _is_valid(self, value: str, data_type: str) -> bool:
        """Validate extracted value based on its type"""

        if not value or len(value) < 3:
            return False

        if data_type == "bank_accounts":
            if not value.replace(' ', '').isdigit():
                return False
            digit_count = len(value.replace(' ', ''))
            return 9 <= digit_count <= 18

        elif data_type == "upi_ids":
            if '@' not in value:
                return False
            parts = value.split('@')
            if len(parts) != 2:
                return False
            valid_handles = [
                'paytm', 'phonepe', 'googlepay', 'gpay', 'amazonpay',
                'bhim', 'ybl', 'okaxis', 'oksbi', 'okhdfcbank', 'okicici',
                'axisbank', 'hdfcbank', 'icici', 'sbi', 'pnb'
            ]
            return any(handle in parts[1].lower() for handle in valid_handles)

        elif data_type == "phone_numbers":
            digits = re.sub(r'\D', '', value)
            return 10 <= len(digits) <= 15

        elif data_type == "email_addresses":
            return '@' in value and '.' in value.split('@')[1]

        elif data_type == "phishing_links":
            return value.startswith(('http://', 'https://', 'www.'))

        elif data_type == "ifsc_codes":
            return len(value) == 11 and value[4] == '0' and value[:4].isalpha()

        return True
