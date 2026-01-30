"""
Scam Detection Module
Analyzes incoming messages to identify scam patterns
"""

import re
from typing import Dict, List
from datetime import datetime


class ScamDetector:
    def __init__(self):
        # Scam indicators with weights
        self.scam_keywords = {
            # Banking/Financial scams
            "urgent": 2,
            "verify your account": 3,
            "suspended account": 3,
            "update your bank": 3,
            "confirm your details": 3,
            "click here immediately": 3,
            "limited time": 2,
            "expires today": 2,
            "verify now": 2,
            "account will be closed": 3,
            
            # Prize/Lottery scams
            "congratulations": 2,
            "you have won": 3,
            "claim your prize": 3,
            "lottery": 2,
            "winner": 2,
            "cash prize": 3,
            "million dollars": 3,
            "inheritance": 3,
            
            # Tech support scams
            "virus detected": 3,
            "system infected": 3,
            "call this number": 2,
            "microsoft support": 3,
            "refund": 2,
            "tech support": 2,
            
            # General scam indicators
            "act now": 2,
            "send money": 3,
            "wire transfer": 3,
            "gift card": 3,
            "bitcoin": 2,
            "cryptocurrency": 2,
            "whatsapp": 1,
            "telegram": 1,
            "do not tell anyone": 3,
            "keep this secret": 3,
            "government official": 2,
            "tax": 2,
            "irs": 2,
            "social security": 2,
            "arrest warrant": 3,
            "legal action": 2,
            "court": 2,
        }
        
        # URL patterns that indicate phishing
        self.suspicious_url_patterns = [
            r'bit\.ly',
            r'tinyurl',
            r'goo\.gl',
            r't\.co',
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',  # IP addresses
            r'[a-z0-9-]+\.(tk|ml|ga|cf|gq)',  # Free domains
        ]
        
        # Scam type patterns
        self.scam_types = {
            "phishing": [
                "verify", "account", "suspended", "click here", "update", 
                "confirm", "bank", "card", "password"
            ],
            "lottery": [
                "won", "prize", "lottery", "winner", "claim", "congratulations"
            ],
            "tech_support": [
                "virus", "infected", "support", "microsoft", "apple", 
                "refund", "subscription"
            ],
            "romance": [
                "love", "lonely", "dating", "meet", "beautiful", "handsome"
            ],
            "investment": [
                "invest", "profit", "guaranteed", "returns", "bitcoin", 
                "cryptocurrency", "trading"
            ],
            "fake_job": [
                "work from home", "easy money", "part time", "hiring", 
                "no experience"
            ],
            "impersonation": [
                "government", "irs", "social security", "police", "court", 
                "arrest", "legal"
            ]
        }
    
    def analyze(self, message: str) -> Dict:
        """
        Analyze a message for scam indicators
        
        Returns:
            Dict with is_scam, confidence_score, scam_type, and indicators
        """
        message_lower = message.lower()
        
        # Calculate scam score
        score = 0
        found_indicators = []
        
        # Check keywords
        for keyword, weight in self.scam_keywords.items():
            if keyword in message_lower:
                score += weight
                found_indicators.append(keyword)
        
        # Check for URLs
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message)
        if urls:
            score += 2
            found_indicators.append("contains_url")
            
            # Check for suspicious URLs
            for url in urls:
                for pattern in self.suspicious_url_patterns:
                    if re.search(pattern, url):
                        score += 3
                        found_indicators.append(f"suspicious_url: {url[:50]}")
                        break
        
        # Check for phone numbers (potential scam contact)
        phone_pattern = r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
        if re.search(phone_pattern, message):
            score += 1
            found_indicators.append("contains_phone_number")
        
        # Check for excessive urgency (multiple exclamation marks, caps)
        if message.count('!') >= 2:
            score += 1
            found_indicators.append("excessive_urgency")
        
        caps_ratio = sum(1 for c in message if c.isupper()) / len(message) if len(message) > 0 else 0
        if caps_ratio > 0.3:
            score += 2
            found_indicators.append("excessive_caps")
        
        # Check for money/payment requests
        money_keywords = ['$', 'rupees', 'rs.', 'inr', 'usd', 'payment', 'pay', 'send money']
        if any(keyword in message_lower for keyword in money_keywords):
            score += 2
            found_indicators.append("money_request")
        
        # Determine scam type
        scam_type = self._identify_scam_type(message_lower)
        
        # Calculate confidence score (0-1)
        confidence_score = min(score / 10, 1.0)
        
        # Determine if it's a scam (threshold: 0.7)
        is_scam = confidence_score >= 0.7
        
        return {
            "is_scam": is_scam,
            "confidence_score": round(confidence_score, 2),
            "scam_type": scam_type if is_scam else "none",
            "indicators": found_indicators,
            "raw_score": score,
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    def _identify_scam_type(self, message: str) -> str:
        """Identify the type of scam based on keywords"""
        type_scores = {}
        
        for scam_type, keywords in self.scam_types.items():
            score = sum(1 for keyword in keywords if keyword in message)
            if score > 0:
                type_scores[scam_type] = score
        
        if not type_scores:
            return "generic"
        
        # Return the scam type with highest score
        return max(type_scores.items(), key=lambda x: x[1])[0]
    
    def get_statistics(self) -> Dict:
        """Get detector statistics and configuration"""
        return {
            "total_keywords": len(self.scam_keywords),
            "scam_types_supported": list(self.scam_types.keys()),
            "detection_threshold": 0.7,
            "suspicious_url_patterns": len(self.suspicious_url_patterns)
        }


# Test the detector
if __name__ == "__main__":
    detector = ScamDetector()
    
    test_messages = [
        "Hi, how are you today?",
        "URGENT! Your bank account has been suspended. Click here to verify: http://bit.ly/fake123",
        "Congratulations! You have won $1,000,000 in our lottery. Call +1-800-123-4567 to claim now!",
        "Your computer is infected with virus. Call Microsoft support immediately at 1-888-999-0000",
        "Dear Sir, I am a Nigerian prince and need your help transferring $50 million USD..."
    ]
    
    print("🔍 Testing Scam Detector\n")
    for i, msg in enumerate(test_messages, 1):
        print(f"Test {i}:")
        print(f"Message: {msg[:80]}...")
        result = detector.analyze(msg)
        print(f"Is Scam: {result['is_scam']}")
        print(f"Confidence: {result['confidence_score']}")
        print(f"Type: {result['scam_type']}")
        print(f"Indicators: {', '.join(result['indicators'][:3])}")
        print("-" * 80)
