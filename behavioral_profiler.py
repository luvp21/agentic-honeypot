"""
Behavioral Profiler - Analyzes scammer behavior and tactics
Used to generate rich intelligence summaries in agentNotes
"""

import re
from typing import List
from models import ScammerProfile


class BehavioralProfiler:
    """
    Analyzes scammer behavior to classify tactics, language, and aggression.
    Provides rich context for intelligence reports.
    """

    def __init__(self):
        # Tactic patterns
        self.urgency_patterns = [
            r'\burgent\b', r'\bimmediately\b', r'\bquickly\b', r'\bnow\b',
            r'\basap\b', r'\bexpir(e|ing)\b', r'\bdeadline\b', r'\blimited time\b',
            r'\bhurry\b', r'\bfast\b', r'\btoday only\b'
        ]

        self.fear_patterns = [
            r'\bsuspend(ed)?\b', r'\bblock(ed)?\b', r'\bfrozen\b', r'\bclosed\b',
            r'\bunauthorized\b', r'\bfraud\b', r'\bpolice\b', r'\blegal action\b',
            r'\barrest\b', r'\bpenalty\b', r'\bfine\b', r'\bcourt\b'
        ]

        self.reward_patterns = [
            r'\bwin\b', r'\bprize\b', r'\blottery\b', r'\bcongratulations\b',
            r'\bwinner\b', r'\breward\b', r'\bfree\b', r'\bgift\b',
            r'\bbonus\b', r'\bcashback\b', r'\brefund\b'
        ]

        self.authority_patterns = [
            r'\bbank\b', r'\bgovernment\b', r'\bofficial\b', r'\bmanager\b',
            r'\bofficer\b', r'\bdepartment\b', r'\bRBI\b', r'\bIT department\b',
            r'\bcustomer care\b', r'\bsupport team\b'
        ]

        self.scarcity_patterns = [
            r'\bonly \d+ left\b', r'\blast chance\b', r'\bfinal (offer|warning)\b',
            r'\bexpir(e|ing) (today|soon)\b', r'\blimited (offer|time)\b'
        ]

        # Language indicators
        self.hinglish_indicators = [
            r'\baap\b', r'\bhai\b', r'\bkaro\b', r'\bnahi\b', r'\bji\b',
            r'\bkya\b', r'\bkaise\b', r'\bbhej\b', r'\bjaldi\b'
        ]

        # Aggression indicators
        self.threat_patterns = [
            r'\bor else\b', r'\bmust\b', r'\bhave to\b', r'\bshould\b',
            r'\bfail(ure)? to\b', r'\bconsequence\b', r'\baction will be taken\b'
        ]

    def analyze_tactics(self, message: str) -> List[str]:
        """
        Detect manipulation tactics used by scammer.

        Args:
            message: Scammer message text

        Returns:
            List of detected tactics (URGENCY, FEAR, REWARD, AUTHORITY, SCARCITY)
        """
        tactics = []
        message_lower = message.lower()

        # Check each tactic category
        if any(re.search(p, message_lower) for p in self.urgency_patterns):
            tactics.append("URGENCY")

        if any(re.search(p, message_lower) for p in self.fear_patterns):
            tactics.append("FEAR")

        if any(re.search(p, message_lower) for p in self.reward_patterns):
            tactics.append("REWARD")

        if any(re.search(p, message_lower) for p in self.authority_patterns):
            tactics.append("AUTHORITY")

        if any(re.search(p, message_lower) for p in self.scarcity_patterns):
            tactics.append("SCARCITY")

        return tactics

    def detect_language(self, message: str) -> str:
        """
        Classify message language.

        Args:
            message: Message text

        Returns:
            "English", "Hinglish", or "Hindi"
        """
        # Simple heuristic: check for Hinglish indicators
        hinglish_count = sum(
            1 for pattern in self.hinglish_indicators
            if re.search(pattern, message.lower())
        )

        # If 2+ Hinglish words found, it's Hinglish
        if hinglish_count >= 2:
            return "Hinglish"
        elif hinglish_count == 1:
            return "Hinglish"

        # Check if mostly non-ASCII (Hindi script)
        non_ascii_ratio = sum(1 for c in message if ord(c) > 127) / max(len(message), 1)
        if non_ascii_ratio > 0.3:
            return "Hindi"

        return "English"

    def calculate_aggression_score(self, message: str) -> float:
        """
        Calculate aggression level based on writing style.

        Args:
            message: Message text

        Returns:
            Score from 0.0 (calm) to 1.0 (highly aggressive)
        """
        score = 0.0

        # ALL CAPS ratio
        if len(message) > 0:
            caps_ratio = sum(1 for c in message if c.isupper()) / len(message)
            score += caps_ratio * 0.3  # Max +0.3

        # Exclamation marks
        exclamation_count = message.count('!')
        score += min(exclamation_count * 0.1, 0.3)  # Max +0.3

        # Threat patterns
        threat_count = sum(
            1 for pattern in self.threat_patterns
            if re.search(pattern, message.lower())
        )
        score += min(threat_count * 0.2, 0.4)  # Max +0.4

        return min(score, 1.0)

    def update_profile(
        self,
        profile: ScammerProfile,
        message: str,
        scam_type: str = None
    ) -> ScammerProfile:
        """
        Update scammer profile with new message analysis.

        Args:
            profile: Existing profile to update
            message: New message from scammer
            scam_type: Detected scam type (optional)

        Returns:
            Updated profile
        """
        # Update scam type if provided
        if scam_type:
            profile.scam_type = scam_type

        # Analyze tactics
        new_tactics = self.analyze_tactics(message)
        for tactic in new_tactics:
            if tactic not in profile.tactics:
                profile.tactics.append(tactic)

        # Update language (use most recent)
        profile.language = self.detect_language(message)

        # Update aggression score (running average)
        new_aggression = self.calculate_aggression_score(message)
        if profile.aggression_score == 0.0:
            profile.aggression_score = new_aggression
        else:
            # Weighted average: 70% old, 30% new
            profile.aggression_score = (
                profile.aggression_score * 0.7 + new_aggression * 0.3
            )

        return profile

    def generate_profile_summary(self, profile: ScammerProfile) -> str:
        """
        Generate human-readable summary of scammer behavior.
        Used in agentNotes field of callback.

        Args:
            profile: Scammer profile

        Returns:
            Human-readable summary
        """
        parts = []

        # Scam type
        if profile.scam_type != "unknown":
            parts.append(f"Scam Type: {profile.scam_type}")

        # Tactics
        if profile.tactics:
            tactics_str = ", ".join(profile.tactics)
            parts.append(f"Tactics: {tactics_str}")

        # Language
        if profile.language != "unknown":
            parts.append(f"Language: {profile.language}")

        # Aggression
        if profile.aggression_score > 0:
            aggression_level = "Low"
            if profile.aggression_score > 0.7:
                aggression_level = "High"
            elif profile.aggression_score > 0.4:
                aggression_level = "Medium"
            parts.append(f"Aggression: {aggression_level} ({profile.aggression_score:.2f})")

        if not parts:
            return "No behavioral profile data"

        return " | ".join(parts)


# Test the profiler
if __name__ == "__main__":
    profiler = BehavioralProfiler()

    test_messages = [
        "URGENT! Your account will be suspended immediately if you don't verify now!",
        "Congratulations! You won 10 lakh prize. Send OTP asap.",
        "Aap jaldi karo ji, bank account verify karna hai urgent."
    ]

    for msg in test_messages:
        print(f"\nMessage: {msg}")
        print(f"Tactics: {profiler.analyze_tactics(msg)}")
        print(f"Language: {profiler.detect_language(msg)}")
        print(f"Aggression: {profiler.calculate_aggression_score(msg):.2f}")
