"""
Scam Detection Module
Analyzes incoming messages to identify scam patterns using Hybrid LLM + Heuristic approach
"""

import re
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from gemini_client import gemini_client

logger = logging.getLogger(__name__)

class ScamDetector:
    def __init__(self):
        # Scam indicators with weights (Legacy/Fallback)
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
            "account will be blocked": 3,
            "blocked": 2,
            "compromised": 3,
            "otp": 2,
            "account number": 2,
            "share your": 2,
            "immediately": 1,
            "within": 1,
            "hours": 1,

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

    async def analyze(self, message: str, conversation_history: List[Dict] = None) -> Dict:
        """
        Analyze a message for scam indicators using Hybrid approach (LLM + Regex)

        Returns:
            Dict with is_scam, confidence_score, scam_type, and indicators
        """
        # 1. First run Regex analysis (Fast & cheap)
        regex_result = self._analyze_regex(message)

        # 2. Try LLM Analysis (Deep reasoning)
        llm_result = await self._analyze_with_llm(message, conversation_history, regex_result)

        # 3. Merge results (LLM takes precedence if successful, otherwise Regex)
        if llm_result:
            # Merge indicators
            final_indicators = list(set(regex_result["indicators"] + llm_result.get("tactics", [])))
            
            return {
                "is_scam": llm_result["scamDetected"],
                "confidence_score": llm_result["confidence"],
                "scam_type": llm_result["scamType"],
                "indicators": final_indicators,
                "extraction_intent": llm_result.get("extractionIntentDetected", False),
                "analyzed_at": datetime.utcnow().isoformat(),
                "method": "hybrid_llm"
            }
        
        return regex_result

    def _analyze_regex(self, message: str) -> Dict:
        """Legacy regex-based analysis"""
        message_lower = message.lower()
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
            for url in urls:
                for pattern in self.suspicious_url_patterns:
                    if re.search(pattern, url):
                        score += 3
                        found_indicators.append(f"suspicious_url: {url[:50]}")
                        break

        # Check for phone numbers
        phone_pattern = r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
        if re.search(phone_pattern, message):
            score += 1
            found_indicators.append("contains_phone_number")

        # Check urgency and caps
        if message.count('!') >= 2:
            score += 1
            found_indicators.append("excessive_urgency")

        caps_ratio = sum(1 for c in message if c.isupper()) / len(message) if len(message) > 0 else 0
        if caps_ratio > 0.3:
            score += 2
            found_indicators.append("excessive_caps")

        # Check money requests
        money_keywords = ['$', 'rupees', 'rs.', 'inr', 'usd', 'payment', 'pay', 'send money']
        if any(keyword in message_lower for keyword in money_keywords):
            score += 2
            found_indicators.append("money_request")

        # Calculate confidence
        confidence_score = min(score / 10, 1.0)
        is_scam = confidence_score >= 0.5
        scam_type = self._identify_scam_type(message_lower) if is_scam else "none"

        return {
            "is_scam": is_scam,
            "confidence_score": round(confidence_score, 2),
            "scam_type": scam_type,
            "indicators": found_indicators,
            "raw_score": score,
            "analyzed_at": datetime.utcnow().isoformat(),
            "method": "regex"
        }

    async def _analyze_with_llm(self, message: str, history: List[Dict], regex_result: Dict) -> Optional[Dict]:
        """PART 1 - CLASSIFICATION PROMPT (STRUCTURED REASONING)"""
        try:
            # Prepare context
            history_text = ""
            if history:
                lines = []
                for msg in history[-5:]:
                    sender = msg.get("sender") or msg.get("role", "unknown")
                    text = msg.get("text") or msg.get("content", "")
                    lines.append(f"{sender}: {text}")
                history_text = "\n".join(lines)

            # Strict JSON Prompt
            prompt = f"""
You are a cybersecurity scam intelligence engine.

Analyze the conversation context and latest message.

Context:
{history_text}

Latest Message:
"{message}"

Internally reason step-by-step:
1. Identify scam indicators.
2. Identify psychological manipulation tactics.
3. Determine scam type.
4. Identify if financial extraction attempt is underway.
5. Estimate confidence.

DO NOT output reasoning steps.

Return ONLY valid JSON:

{{
"scamDetected": boolean,
"scamType": "string",
"tactics": [],
"extractionIntentDetected": boolean,
"confidence": 0.0-1.0
}}

Be decisive. Do not hedge. No explanations outside JSON.
"""
            
            response_text = await gemini_client.generate_response(prompt, operation_name="classifier")
            
            if not response_text:
                return None
                
            # Clean and parse JSON
            cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned_text)
            
        except Exception as e:
            logger.error(f"LLM Classification failed: {e}")
            return None

    def _identify_scam_type(self, message: str) -> str:
        """Identify the type of scam based on keywords"""
        type_scores = {}
        for scam_type, keywords in self.scam_types.items():
            score = sum(1 for keyword in keywords if keyword in message)
            if score > 0:
                type_scores[scam_type] = score

        if not type_scores:
            return "generic"
        
        return max(type_scores.items(), key=lambda x: x[1])[0]

    def get_statistics(self) -> Dict:
        return {
            "total_keywords": len(self.scam_keywords),
            "scam_types_supported": list(self.scam_types.keys()),
            "detection_threshold": 0.5,
            "suspicious_url_patterns": len(self.suspicious_url_patterns)
        }

# Test the detector
if __name__ == "__main__":
    import asyncio
    
    async def test():
        detector = ScamDetector()
        
        msg = "URGENT! Your bank account has been suspended. Click here to verify: http://bit.ly/fake123"
        print(f"Testing message: {msg}")
        
        # Test Regex only (no history)
        result = await detector.analyze(msg)
        print("\nResult:")
        print(json.dumps(result, indent=2))

    asyncio.run(test())
