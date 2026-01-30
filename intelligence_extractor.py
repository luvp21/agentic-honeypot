"""
Intelligence Extractor
Extracts sensitive information from scammer messages:
- Bank account numbers
- UPI IDs
- Phishing links
- Phone numbers
- Email addresses
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
                r'account\s*(?:number|no|#)?\s*:?\s*(\d{9,18})',  # With "account number" label
                r'A/C\s*:?\s*(\d{9,18})',  # A/C format
            ],
            "upi_ids": [
                r'\b[\w\.-]+@[\w\.-]+\b',  # Generic UPI format (looks like email)
                r'\b[\w\.-]+@(?:paytm|phonepe|googlepay|amazonpay|bhim|ybl|okaxis|oksbi|okhdfcbank|okicici)\b',
            ],
            "phone_numbers": [
                r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # International format
                r'\b\d{10}\b',  # 10 digit Indian number
                r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # US format
            ],
            "email_addresses": [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            ],
            "phishing_links": [
                r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
                r'www\.[a-zA-Z0-9-]+\.[a-zA-Z]{2,}',
            ],
            "ifsc_codes": [
                r'\b[A-Z]{4}0[A-Z0-9]{6}\b',  # Indian IFSC code format
            ],
            "cryptocurrency": [
                r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b',  # Bitcoin address
                r'\b0x[a-fA-F0-9]{40}\b',  # Ethereum address
            ],
            "payment_apps": [
                r'\b(?:paytm|phonepe|googlepay|gpay|whatsapp\s*pay|bhim)\b',
            ]
        }
        
        # Additional context patterns
        self.context_patterns = {
            "urgency": r'\b(?:urgent|immediately|now|asap|today|within\s*\d+\s*hours?)\b',
            "money_mention": r'\b(?:\$|rs\.?|rupees?|inr|usd|amount|payment|transfer)\s*\d+',
            "verification": r'\b(?:verify|confirm|update|validate|authenticate)\b',
        }
    
    def extract(self, message: str) -> Dict:
        """
        Extract all intelligence from a message
        
        Args:
            message: Text message to analyze
        
        Returns:
            Dictionary with extracted data categorized by type
        """
        extracted = {}
        
        # Extract each data type
        for data_type, patterns in self.patterns.items():
            matches = []
            for pattern in patterns:
                found = re.findall(pattern, message, re.IGNORECASE)
                if found:
                    # Clean and deduplicate
                    matches.extend([self._clean_match(m) for m in found])
            
            # Remove duplicates and filter
            matches = list(set(matches))
            matches = [m for m in matches if self._is_valid(m, data_type)]
            
            if matches:
                extracted[data_type] = matches
        
        # Special handling for UPI IDs vs Email addresses
        # UPI IDs look like emails but have specific payment handles
        if "upi_ids" in extracted and "email_addresses" in extracted:
            # Remove UPI IDs from email list
            upi_set = set(extracted["upi_ids"])
            extracted["email_addresses"] = [
                email for email in extracted["email_addresses"] 
                if email not in upi_set
            ]
            if not extracted["email_addresses"]:
                del extracted["email_addresses"]
        
        # Add metadata
        if extracted:
            extracted["_metadata"] = {
                "extracted_at": datetime.utcnow().isoformat(),
                "message_length": len(message),
                "has_urgency": bool(re.search(self.context_patterns["urgency"], message, re.IGNORECASE)),
                "mentions_money": bool(re.search(self.context_patterns["money_mention"], message, re.IGNORECASE)),
            }
        
        return extracted
    
    def _clean_match(self, match: str) -> str:
        """Clean extracted match"""
        # Remove extra whitespace
        cleaned = ' '.join(match.split())
        # Remove trailing/leading punctuation
        cleaned = cleaned.strip('.,;:!?')
        return cleaned
    
    def _is_valid(self, value: str, data_type: str) -> bool:
        """Validate extracted value based on its type"""
        
        if not value or len(value) < 3:
            return False
        
        # Type-specific validation
        if data_type == "bank_accounts":
            # Must be numeric and reasonable length
            if not value.replace(' ', '').isdigit():
                return False
            digit_count = len(value.replace(' ', ''))
            return 9 <= digit_count <= 18
        
        elif data_type == "upi_ids":
            # Must have @ symbol and valid handle
            if '@' not in value:
                return False
            parts = value.split('@')
            if len(parts) != 2:
                return False
            # Check if it's a known UPI handle
            valid_handles = [
                'paytm', 'phonepe', 'googlepay', 'gpay', 'amazonpay',
                'bhim', 'ybl', 'okaxis', 'oksbi', 'okhdfcbank', 'okicici',
                'axisbank', 'hdfcbank', 'icici', 'sbi', 'pnb'
            ]
            return any(handle in parts[1].lower() for handle in valid_handles)
        
        elif data_type == "phone_numbers":
            # Remove non-digits and check length
            digits = re.sub(r'\D', '', value)
            return 10 <= len(digits) <= 15
        
        elif data_type == "email_addresses":
            # Basic email validation
            return '@' in value and '.' in value.split('@')[1]
        
        elif data_type == "phishing_links":
            # Must be a valid URL format
            return value.startswith(('http://', 'https://', 'www.'))
        
        elif data_type == "ifsc_codes":
            # IFSC code format: 4 letters, 0, 6 alphanumeric
            return len(value) == 11 and value[4] == '0' and value[:4].isalpha()
        
        return True
    
    def extract_with_context(self, message: str) -> Dict:
        """
        Extract intelligence with surrounding context
        
        Returns:
            Dict with extracted data and context snippets
        """
        base_extraction = self.extract(message)
        
        if not base_extraction or "_metadata" not in base_extraction:
            return base_extraction
        
        # Add context for each extracted item
        for data_type, values in base_extraction.items():
            if data_type == "_metadata":
                continue
            
            contexts = []
            for value in values:
                context = self._get_context(message, value)
                if context:
                    contexts.append(context)
            
            if contexts:
                base_extraction[f"{data_type}_context"] = contexts
        
        return base_extraction
    
    def _get_context(self, message: str, value: str, window: int = 50) -> str:
        """Get surrounding context for extracted value"""
        try:
            pos = message.lower().find(value.lower())
            if pos == -1:
                return ""
            
            start = max(0, pos - window)
            end = min(len(message), pos + len(value) + window)
            
            context = message[start:end]
            # Add ellipsis if truncated
            if start > 0:
                context = "..." + context
            if end < len(message):
                context = context + "..."
            
            return context
        except:
            return ""
    
    def get_statistics(self, extracted_data: Dict) -> Dict:
        """Get statistics about extracted intelligence"""
        stats = {
            "total_items": 0,
            "by_type": {}
        }
        
        for key, value in extracted_data.items():
            if key.startswith("_") or key.endswith("_context"):
                continue
            if isinstance(value, list):
                count = len(value)
                stats["by_type"][key] = count
                stats["total_items"] += count
        
        return stats
    
    def format_for_export(self, extracted_data: Dict) -> Dict:
        """Format extracted data for export/reporting"""
        formatted = {
            "timestamp": datetime.utcnow().isoformat(),
            "intelligence": {}
        }
        
        # Organize by criticality
        critical = ["bank_accounts", "upi_ids", "cryptocurrency"]
        high = ["phishing_links", "ifsc_codes"]
        medium = ["phone_numbers", "email_addresses"]
        
        for priority, types in [("critical", critical), ("high", high), ("medium", medium)]:
            priority_data = {}
            for data_type in types:
                if data_type in extracted_data:
                    priority_data[data_type] = extracted_data[data_type]
            if priority_data:
                formatted["intelligence"][priority] = priority_data
        
        # Add metadata
        if "_metadata" in extracted_data:
            formatted["metadata"] = extracted_data["_metadata"]
        
        return formatted


# Test the extractor
if __name__ == "__main__":
    extractor = IntelligenceExtractor()
    
    test_messages = [
        "Please transfer Rs 5000 to account number 1234567890123 IFSC: SBIN0001234",
        "Send payment to my UPI: scammer123@paytm or call +91-9876543210",
        "Click here to verify: https://fake-bank.com/verify?id=123 or email me at scammer@evil.com",
        "My account details: 9988776655443322, Phone: 1-800-123-4567",
        "Send Bitcoin to: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
    ]
    
    print("🔍 Testing Intelligence Extractor\n")
    
    for i, msg in enumerate(test_messages, 1):
        print(f"\nTest {i}:")
        print(f"Message: {msg}")
        print("-" * 80)
        
        extracted = extractor.extract(msg)
        
        if extracted:
            for key, value in extracted.items():
                if not key.startswith("_"):
                    print(f"{key}: {value}")
            
            if "_metadata" in extracted:
                print(f"\nMetadata:")
                for k, v in extracted["_metadata"].items():
                    print(f"  {k}: {v}")
            
            stats = extractor.get_statistics(extracted)
            print(f"\nStats: {stats['total_items']} items extracted")
        else:
            print("No intelligence extracted")
        
        print("=" * 80)
