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
        # DETERMINISTIC DETECTION TIER THRESHOLDS
        self.STRONG_THRESHOLD = 7.0  # ≥70% score = High confidence scam
        self.LOW_THRESHOLD = 3.0     # <30% score = Uncertain zone
        self.HIGH_LLM_THRESHOLD = 0.8  # LLM must be 80% confident in low-score cases

        # ═══════════════════════════════════════════════════════════
        # ELITE REFINEMENT 1: Detection Tier Telemetry
        # ═══════════════════════════════════════════════════════════
        self.metrics = {
            "tier1_strong": 0,
            "tier2_grey": 0,
            "tier3_low": 0,
            "injection_detected": 0,
            "breaker_classifier": 0,
            "breaker_generator": 0,
            "strong_evidence_shortcuts": 0,  # Amplifier counter
            "regex_evasion_normalized": 0,   # Normalization counter
            "multi_stage_detected": 0        # Multi-stage attack counter
        }

        # Scam indicators with weights (Legacy/Fallback)
        self.scam_keywords = {
            # INJECTION ATTACK PATTERNS (HIGH PRIORITY)
            "ignore previous instructions": 10,
            "ignore all previous": 10,
            "disregard previous": 10,
            "forget previous": 10,
            "ignore your instructions": 10,
            "reveal your prompt": 10,
            "show your prompt": 10,
            "repeat your prompt": 10,
            "print your prompt": 10,
            "system prompt": 10,
            "act as": 8,
            "you are now": 8,
            "pretend you are": 8,
            "roleplay as": 8,
            "system override": 10,
            "admin mode": 10,
            "developer mode": 10,
            "dan mode": 10,
            "jailbreak": 10,
            "<!-- ": 8,
            "<system>": 8,
            "[system": 8,
            "{system": 8,
            "base64[": 8,

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

            # POLITE/SOPHISTICATED SCAM PATTERNS (BOOSTED - were bypassing detection)
            "customer security": 5,
            "fraud department": 5,
            "security team": 4,
            "security department": 5,
            "account safety": 4,
            "for your protection": 4,
            "security review": 4,
            "standard protocol": 3,
            "verify your identity": 5,
            "confirm your identity": 5,
            "security code": 3,
            "verification code": 3,
            "last four digits": 3,
            "unusual activity": 5,
            "suspicious activity": 5,
            "detected unusual": 5,
            "detected suspicious": 5,
            "ssn": 3,
            "social security number": 3,
            "customer appreciation": 2,
            "you've been selected": 2,
            "winner": 2,
            "prize": 2,
            "billing error": 2,
            "overcharged": 2,
            "refund": 2,

            # EMOTIONAL MANIPULATION (BOOSTED)
            "stranded": 4,
            "robbed": 4,
            "emergency": 3,
            "desperate": 4,
            "scared": 3,
            "alone": 1,
            "help me": 2,
            "begging you": 4,
            "dying": 5,
            "hospital": 3,
            "mother": 1,  # Not suspicious alone
            "operation": 2,
            "please help": 3,
            "exclusive opportunity": 3,
            "limited spots": 3,
            "don't miss out": 3,
            "others are getting rich": 4,
            "grandma": 2,
            "grandson": 2,
            "in trouble": 3,
            "in jail": 4,
            "ashamed": 2,
            "embarrassed": 2,

            # AUTHORITY IMPERSONATION (BOOSTED)
            "fbi": 5,
            "special agent": 5,
            "cyber crimes": 4,
            "cyber division": 5,
            "officer": 2,
            "badge": 3,
            "circuit court": 4,
            "judge": 2,
            "jury duty": 3,
            "warrant": 4,
            "prosecution": 4,
            "illegal activity": 4,
            "detected illegal": 5,
            "microsoft security": 4,
            "apple support": 3,
            "amazon security": 3,
            "paypal security": 3,
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

    # ═══════════════════════════════════════════════════════════
    # ELITE REFINEMENT 3: Regex Evasion Normalization
    # ═══════════════════════════════════════════════════════════
    def _normalize_for_detection(self, text: str) -> str:
        """
        ENHANCED normalization to defeat advanced evasion tactics.
        Handles: O.T.P, acc0unt, B@nk, A c c o u n t, verify-immediately
        Unicode lookalikes, zero-width characters, HTML injection, etc.

        Args:
            text: Raw input text

        Returns:
            Normalized text for pattern matching
        """
        normalized = text.lower()

        # Remove zero-width characters and invisible unicode
        normalized = re.sub(r'[\u200B\u200C\u200D\u2060\uFEFF]', '', normalized)

        # Remove HTML/XML comments (injection attempts)
        normalized = re.sub(r'<!--.*?-->', ' ', normalized)
        normalized = re.sub(r'<[^>]+>', ' ', normalized)  # Remove all tags

        # Remove JSON/code-like structures
        normalized = re.sub(r'[{}\\[\\]]', ' ', normalized)

        # Enhanced character substitutions (l33t speak & obfuscation) - EXPANDED
        leet_map = {
            '0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's',
            '7': 't', '8': 'b', '9': 'g', '@': 'a', '$': 's',
            '!': 'i', '+': 't', '|': 'l', '6': 'g', '2': 'z'
        }
        for leet, normal in leet_map.items():
            normalized = normalized.replace(leet, normal)

        # Normalize unicode lookalikes (Cyrillic to Latin)
        cyrillic_map = {
            '\u0430': 'a', '\u0435': 'e', '\u0456': 'i', '\u043e': 'o', '\u0440': 'p',
            '\u0441': 'c', '\u0443': 'y', '\u0445': 'x', '\u0455': 's', '\u04bb': 'h'
        }
        for cyrillic, latin in cyrillic_map.items():
            normalized = normalized.replace(cyrillic, latin)

        # Remove separators (spacing evasion)
        normalized = re.sub(r"[.\-_]", "", normalized)  # o.t.p -> otp, verify-now -> verifynow

        # CRITICAL: Remove ALL spacing between characters for evasion detection
        # First try single-char spacing: "A c c o u n t" -> "Account"
        # Use lookahead to handle all single-spaced chars
        normalized = re.sub(r'\b(\w)\s+(?=\w\b|\w\s)', r'\1', normalized)

        # Then collapse multiple spaces
        normalized = re.sub(r"\s+", " ", normalized)

        # Track if normalization occurred
        if normalized != text.lower():
            self.metrics["regex_evasion_normalized"] += 1
            logger.info(f"🛡️ [EVASION NORMALIZED] '{text[:50]}...' → '{normalized[:50]}...'")

        return normalized
    # ═══════════════════════════════════════════════════════════
    # ELITE REFINEMENT 2: Strong Evidence Amplifier
    # ═══════════════════════════════════════════════════════════
    def _detect_strong_evidence_shortcut(self, text: str) -> bool:
        """
        Detect high-confidence scam patterns that force Tier 1 classification.
        Even if regex_score < STRONG_THRESHOLD, these co-occurrences trigger immediate scam.

        Shortcuts:
        - OTP + urgency
        - UPI + payment directive
        - Account blocked + link
        - Verify + immediate + bank

        Returns:
            True if strong evidence shortcut detected
        """
        text_lower = text.lower()

        # Shortcut 1: OTP + Urgency
        has_otp = any(term in text_lower for term in ["otp", "one time password", "verification code"])
        has_urgency = any(term in text_lower for term in ["urgent", "immediately", "asap", "now", "hurry"])
        if has_otp and has_urgency:
            logger.info("🚨 [STRONG EVIDENCE] OTP + Urgency detected → Force Tier 1")
            return True

        # Shortcut 2: UPI + Payment Directive
        has_upi = any(term in text_lower for term in ["upi", "paytm", "phonepe", "gpay"])
        has_payment = any(term in text_lower for term in ["send", "transfer", "pay", "payment"])
        if has_upi and has_payment:
            logger.info("🚨 [STRONG EVIDENCE] UPI + Payment detected → Force Tier 1")
            return True

        # Shortcut 3: Account Blocked + Link
        has_blocked = any(term in text_lower for term in ["blocked", "suspended", "deactivated", "locked"])
        has_link = "http" in text_lower or "bit.ly" in text_lower or "click here" in text_lower
        if has_blocked and has_link:
            logger.info("🚨 [STRONG EVIDENCE] Account Blocked + Link detected → Force Tier 1")
            return True

        # Shortcut 4: Verify + Immediate + Bank
        has_verify = "verify" in text_lower or "confirm" in text_lower
        has_bank = any(term in text_lower for term in ["bank", "account", "card"])
        if has_verify and has_urgency and has_bank:
            logger.info("🚨 [STRONG EVIDENCE] Verify + Immediate + Bank detected → Force Tier 1")
            return True

        return False

    def get_detection_metrics(self) -> Dict:
        """
        Get current detection telemetry.

        Returns:
            Dictionary of detection metrics
        """
        total = sum([
            self.metrics["tier1_strong"],
            self.metrics["tier2_grey"],
            self.metrics["tier3_low"]
        ])

        return {
            "total_analyzed": total,
            "tier1_strong": self.metrics["tier1_strong"],
            "tier2_grey": self.metrics["tier2_grey"],
            "tier3_low": self.metrics["tier3_low"],
            "injection_detected": self.metrics["injection_detected"],
            "multi_stage_detected": self.metrics["multi_stage_detected"],
            "breaker_classifier": self.metrics["breaker_classifier"],
            "breaker_generator": self.metrics["breaker_generator"],
            "strong_evidence_shortcuts": self.metrics["strong_evidence_shortcuts"],
            "regex_evasion_normalized": self.metrics["regex_evasion_normalized"],
            "tier1_percentage": (self.metrics["tier1_strong"] / total * 100) if total > 0 else 0,
            "tier2_percentage": (self.metrics["tier2_grey"] / total * 100) if total > 0 else 0,
            "tier3_percentage": (self.metrics["tier3_low"] / total * 100) if total > 0 else 0
        }

    def get_metrics(self) -> Dict:
        """Alias for get_detection_metrics for consistency"""
        return self.get_detection_metrics()


    async def analyze(self, message: str, conversation_history: List[Dict] = None) -> Dict:
        """
        Analyze a message for scam indicators using DETERMINISTIC TIER SYSTEM.

        Tier 1 (STRONG): regex_score >= 7.0 OR strong evidence → Immediate scam, skip LLM
        Tier 2 (GREY): 3.0 <= regex_score < 7.0 → LLM enhancement
        Tier 3 (LOW): regex_score < 3.0 → LLM classification with high threshold

        Returns:
            Dict with is_scam, confidence_score, scam_type, indicators, and method
        """
        # ═══════════════════════════════════════════════════════════
        # CRITICAL FIX: INJECTION DETECTION FIRST
        # ═══════════════════════════════════════════════════════════
        from injection_defense import InstructionSanitizer
        sanitizer = InstructionSanitizer()
        sanitized_message, injection_detected = sanitizer.sanitize(message)

        if injection_detected:
            self.metrics["injection_detected"] += 1
            logger.warning(f"🛡️ [INJECTION ATTACK] Detected prompt injection attempt")
            return {
                "is_scam": True,
                "confidence_score": 1.0,
                "scam_type": "prompt_injection",
                "indicators": ["prompt_injection_attempt"],
                "raw_score": 10.0,
                "analyzed_at": datetime.utcnow().isoformat(),
                "method": "injection_defense",
                "llm_consulted": False,
                "injection_detected": True
            }

        # ═══════════════════════════════════════════════════════════
        # CRITICAL FIX: MULTI-STAGE ATTACK DETECTION
        # ═══════════════════════════════════════════════════════════
        if conversation_history and len(conversation_history) >= 2:
            multi_stage_risk = self._detect_multi_stage_attack(conversation_history, message)
            if multi_stage_risk["is_multi_stage"]:
                self.metrics["multi_stage_detected"] += 1
                logger.warning(f"🎯 [MULTI-STAGE] Detected multi-stage attack pattern")
                return {
                    "is_scam": True,
                    "confidence_score": multi_stage_risk["confidence"],
                    "scam_type": "multi_stage_attack",
                    "indicators": multi_stage_risk["indicators"],
                    "raw_score": multi_stage_risk["score"],
                    "analyzed_at": datetime.utcnow().isoformat(),
                    "method": "multi_stage_detection",
                    "llm_consulted": False,
                    "multi_stage_pattern": multi_stage_risk["pattern"]
                }

        # ═══════════════════════════════════════════════════════════
        # ELITE REFINEMENT 9: Grey-Zone Volume Protection
        # ═══════════════════════════════════════════════════════════
        # Adaptively reduce grey-zone LLM reliance if volume is too high (>40%)
        total = sum([self.metrics["tier1_strong"], self.metrics["tier2_grey"], self.metrics["tier3_low"]])
        if total > 10:  # Need minimum sample size
            grey_ratio = self.metrics["tier2_grey"] / total
            if grey_ratio > 0.40:
                # Increment LOW_THRESHOLD to push more into Tier 3 (which uses higher LLM guardrails)
                # or just raise Tier 1 threshold to be even stricter?
                # Prompt says: "Automatically raise: LOW_THRESHOLD += 0.5"
                if self.LOW_THRESHOLD < 5.0:  # Cap the adjustment
                    self.LOW_THRESHOLD += 0.5
                    logger.warning(f"🛡️ [GREY-ZONE PROTECTION] High volume ({grey_ratio:.1%}). Raised LOW_THRESHOLD to {self.LOW_THRESHOLD}")

        # ═══════════════════════════════════════════════════════════
        # ELITE REFINEMENT 8: Circuit Breaker Telemetry
        # ═══════════════════════════════════════════════════════════
        from llm_safety import classifier_breaker, generator_breaker
        if not classifier_breaker.should_allow_llm():
            self.metrics["breaker_classifier"] += 1
            logger.warning("[LLM BREAKER] Classifier breaker is OPEN")
        if not generator_breaker.should_allow_llm():
            self.metrics["breaker_generator"] += 1
            logger.warning("[LLM BREAKER] Generator breaker is OPEN")

        # Step 0: Normalize for evasion detection (REFINEMENT 3)
        normalized_message = self._normalize_for_detection(message)

        # Step 0.5: Check for strong evidence shortcuts (REFINEMENT 2)
        has_strong_evidence = self._detect_strong_evidence_shortcut(normalized_message)

        # Step 1: ALWAYS run regex first (deterministic baseline)
        regex_result = self._analyze_regex(normalized_message)
        regex_score = regex_result["raw_score"]

        # ═══════════════════════════════════════════════════════════
        # TIER 1: STRONG RULE WIN (Deterministic Path)
        # ═══════════════════════════════════════════════════════════
        if regex_score >= self.STRONG_THRESHOLD or has_strong_evidence:
            # Increment telemetry
            self.metrics["tier1_strong"] += 1
            if has_strong_evidence:
                self.metrics["strong_evidence_shortcuts"] += 1

            reason = "strong_evidence_shortcut" if has_strong_evidence else "high_score"
            logger.info(
                f"[TIER 1] Strong detection: score={regex_score:.1f}, "
                f"shortcut={has_strong_evidence}, reason={reason} → SCAM (LLM bypassed)"
            )
            return {
                "is_scam": True,
                "confidence_score": min(regex_score / 10, 1.0) if not has_strong_evidence else 0.95,
                "scam_type": regex_result["scam_type"],
                "indicators": regex_result["indicators"],
                "raw_score": regex_score,
                "analyzed_at": datetime.utcnow().isoformat(),
                "method": "deterministic_strong",
                "llm_consulted": False  # Critical: LLM NOT called
            }

        # ═══════════════════════════════════════════════════════════
        # TIER 2: GREY ZONE (LLM Enhancement)
        # ═══════════════════════════════════════════════════════════
        elif self.LOW_THRESHOLD <= regex_score < self.STRONG_THRESHOLD:
            self.metrics["tier2_grey"] += 1  # Telemetry
            logger.info(
                f"[TIER 2] Grey zone: {self.LOW_THRESHOLD} <= {regex_score:.1f} < {self.STRONG_THRESHOLD} → Consulting LLM"
            )

            llm_result = await self._analyze_with_llm(message, conversation_history, regex_result)

            if llm_result:
                # LLM can ONLY increase confidence, never decrease
                final_confidence = max(
                    regex_result["confidence_score"],
                    llm_result["confidence"]
                )

                # Merge indicators (union)
                merged_indicators = list(set(
                    regex_result["indicators"] + llm_result.get("tactics", [])
                ))

                return {
                    "is_scam": llm_result["scamDetected"],
                    "confidence_score": final_confidence,
                    "scam_type": llm_result["scamType"],  # LLM refines type
                    "indicators": merged_indicators,
                    "raw_score": regex_score,
                    "analyzed_at": datetime.utcnow().isoformat(),
                    "method": "hybrid_grey_zone",
                    "llm_consulted": True,
                    "extraction_intent": llm_result.get("extractionIntentDetected", False)
                }
            else:
                # LLM failed → fall back to regex alone
                logger.warning("[TIER 2] LLM failed, falling back to regex")
                return {**regex_result, "method": "regex_fallback", "llm_consulted": False}

        # ═══════════════════════════════════════════════════════════
        # TIER 3: LOW SCORE (LLM Classification Required)
        # ═══════════════════════════════════════════════════════════
        else:  # regex_score < LOW_THRESHOLD
            self.metrics["tier3_low"] += 1  # Telemetry
            logger.info(
                f"[TIER 3] Low score: {regex_score:.1f} < {self.LOW_THRESHOLD} → LLM classification"
            )

            llm_result = await self._analyze_with_llm(message, conversation_history, regex_result)

            if llm_result and llm_result["confidence"] >= self.HIGH_LLM_THRESHOLD:
                # LLM is highly confident → classify as scam
                logger.info(
                    f"[TIER 3] LLM confident: {llm_result['confidence']:.2f} >= {self.HIGH_LLM_THRESHOLD} → SCAM"
                )
                return {
                    "is_scam": True,
                    "confidence_score": llm_result["confidence"],
                    "scam_type": llm_result["scamType"],
                    "indicators": regex_result["indicators"] + llm_result.get("tactics", []),
                    "raw_score": regex_score,
                    "analyzed_at": datetime.utcnow().isoformat(),
                    "method": "llm_low_score",
                    "llm_consulted": True,
                    "extraction_intent": llm_result.get("extractionIntentDetected", False)
                }
            else:
                # ═══════════════════════════════════════════════════════════
                # CRITICAL FIX: INTELLIGENT FALLBACK INSTEAD OF "NOT SCAM"
                # Use enhanced keyword scoring to make better decisions without LLM
                # ═══════════════════════════════════════════════════════════

                # Check if we have ANY scam indicators at all
                has_indicators = len(regex_result["indicators"]) > 0

                # Check for subtle red flags that might not trigger high scores
                message_lower = self._normalize_for_detection(message)

                # Define suspicious patterns that indicate likely scam even with low score
                subtle_scam_signals = [
                    "verify" in message_lower and "account" in message_lower,
                    "urgent" in message_lower and ("click" in message_lower or "link" in message_lower),
                    "suspended" in message_lower or "locked" in message_lower,
                    "confirm" in message_lower and ("identity" in message_lower or "information" in message_lower),
                    "security" in message_lower and "update" in message_lower,
                    "prize" in message_lower or "winner" in message_lower,
                    "refund" in message_lower and "claim" in message_lower,
                    "limited time" in message_lower and "offer" in message_lower,
                    any(pattern in message_lower for pattern in ["click here", "tap here", "go to", "visit now"]),
                    regex_score >= 1.5  # Even low scores above 1.5 deserve suspicion
                ]

                signal_count = sum(subtle_scam_signals)

                # Make intelligent decision based on signals
                if signal_count >= 2 or regex_score >= 2.0:
                    # Multiple subtle signals or moderate score → likely scam
                    logger.warning(
                        f"[TIER 3] Enhanced fallback: {signal_count} signals, score {regex_score:.1f} → SCAM"
                    )
                    return {
                        "is_scam": True,
                        "confidence_score": min(0.65 + (signal_count * 0.05), 0.85),
                        "scam_type": "suspicious_low_score",
                        "indicators": regex_result["indicators"] + ["enhanced_fallback_detection"],
                        "raw_score": regex_score,
                        "analyzed_at": datetime.utcnow().isoformat(),
                        "method": "enhanced_regex_fallback",
                        "llm_consulted": True if llm_result else False
                    }
                else:
                    # Low score, few/no signals → likely legitimate
                    logger.info("[TIER 3] Enhanced fallback: minimal signals → NOT SCAM")
                    return {
                        "is_scam": False,
                        "confidence_score": min(regex_score / 10, 0.3),
                        "scam_type": "none",
                        "indicators": regex_result["indicators"],
                        "raw_score": regex_score,
                        "analyzed_at": datetime.utcnow().isoformat(),
                        "method": "enhanced_safe_fallback",
                        "llm_consulted": True if llm_result else False
                    }



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
        }

    async def _analyze_with_llm(self, message: str, history: List[Dict], regex_result: Dict) -> Optional[Dict]:
        """
        PART 1 - CLASSIFICATION PROMPT (STRUCTURED REASONING)

        ELITE REFINEMENT 4: LLM Drift Guard
        Classifier is STATELESS - sees ONLY latest message + metadata.
        NO conversation history, NO suspicion score, NO prior classifications.
        """
        try:
            # ═══════════════════════════════════════════════════════════
            # DRIFT GUARD: Classifier sees ONLY the current message
            # NO history context to prevent boundary shift
            # ═══════════════════════════════════════════════════════════

            # Strict JSON Prompt (stateless classification)
            prompt = f"""
You are a cybersecurity scam intelligence engine.

Analyze ONLY the following message in isolation:

Message:
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

    def _detect_multi_stage_attack(self, conversation_history: List[Dict], current_message: str) -> Dict:
        """
        Detect multi-stage scam attacks that gradually build trust before striking.

        Patterns detected:
        - Trust building → urgency escalation
        - Casual conversation → information extraction
        - Help offer → payment request
        - Authority building → compliance demand
        """
        score = 0
        indicators = []
        pattern_type = "unknown"

        # Analyze conversation progression
        # conversation_history contains MessageContent objects, not dicts
        messages = [msg.text if hasattr(msg, 'text') else str(msg) for msg in conversation_history[-5:]] + [current_message]
        messages_lower = [msg.lower() for msg in messages]

        # Pattern 1: Trust Building → Financial Request
        early_friendly = sum(1 for msg in messages_lower[:2] if any(
            word in msg for word in ["hello", "hi", "how are you", "nice to meet", "glad", "pleasure"]
        ))
        later_money = sum(1 for msg in messages_lower[-2:] if any(
            word in msg for word in ["payment", "money", "send", "transfer", "urgent", "help me"]
        ))

        if early_friendly >= 1 and later_money >= 1:
            score += 5
            indicators.append("trust_to_money_escalation")
            pattern_type = "trust_building"

        # Pattern 2: Gradual Urgency Escalation
        urgency_scores = []
        for msg in messages_lower:
            urgency = 0
            urgency += msg.count("!")
            urgency += 2 if "urgent" in msg else 0
            urgency += 2 if "immediately" in msg else 0
            urgency += 2 if "hurry" in msg else 0
            urgency += 2 if "right now" in msg else 0
            urgency_scores.append(urgency)

        # Check if urgency increases over time
        if len(urgency_scores) >= 3:
            if urgency_scores[-1] > urgency_scores[0] * 2:
                score += 4
                indicators.append("urgency_escalation")
                pattern_type = "urgency_building"

        # Pattern 3: Information Extraction Progression
        questions = [msg for msg in messages_lower if "?" in msg]
        personal_info_requests = sum(1 for msg in messages_lower[-3:] if any(
            word in msg for word in ["name", "address", "account", "card", "otp", "code", "password", "ssn"]
        ))

        if len(questions) >= 2 and personal_info_requests >= 1:
            score += 5
            indicators.append("progressive_information_extraction")
            pattern_type = "information_harvesting"

        # Pattern 4: Authority Building → Compliance
        early_authority = sum(1 for msg in messages_lower[:3] if any(
            word in msg for word in ["official", "department", "officer", "agent", "representative", "verify"]
        ))
        later_demand = sum(1 for msg in messages_lower[-2:] if any(
            word in msg for word in ["must", "required", "mandatory", "comply", "immediately", "or else"]
        ))

        if early_authority >= 1 and later_demand >= 1:
            score += 6
            indicators.append("authority_to_compliance")
            pattern_type = "authority_abuse"

        # Pattern 5: Help Offer → Exploitation
        early_help = sum(1 for msg in messages_lower[:2] if any(
            word in msg for word in ["help you", "assist", "support", "resolve", "fix"]
        ))
        later_request = sum(1 for msg in messages_lower[-2:] if any(
            word in msg for word in ["need", "send", "provide", "give", "share"]
        ))

        if early_help >= 1 and later_request >= 1:
            score += 4
            indicators.append("help_to_exploitation")
            pattern_type = "fake_helper"

        # Pattern 6: Conversation Length Manipulation
        if len(messages) >= 4:
            # Long conversations that end in sudden urgency/money requests are suspicious
            final_msg = messages_lower[-1]
            if any(word in final_msg for word in ["urgent", "now", "immediately", "money", "payment"]):
                score += 3
                indicators.append("delayed_strike")

        # Pattern 7: Emotional Manipulation Progression
        emotional_words = ["desperate", "stranded", "emergency", "crying", "dying", "sick", "hospital"]
        early_neutral = all(not any(word in msg for word in emotional_words) for msg in messages_lower[:2])
        later_emotional = any(any(word in msg for word in emotional_words) for msg in messages_lower[-2:])

        if early_neutral and later_emotional:
            score += 5
            indicators.append("emotional_manipulation_escalation")
            pattern_type = "emotional_exploitation"

        # Determine if multi-stage attack detected
        is_multi_stage = score >= 5
        confidence = min(score / 15, 1.0)  # Scale to 0-1

        return {
            "is_multi_stage": is_multi_stage,
            "score": score,
            "confidence": confidence,
            "indicators": indicators,
            "pattern": pattern_type,
            "conversation_length": len(messages)
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
