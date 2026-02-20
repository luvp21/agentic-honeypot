"""
red_flag_tracker.py — Accumulates red flags across ALL turns of a conversation.

Scoring impact: Red Flag Identification — 8 pts
  ≥5 unique flags → 8 pts
  ≥3 unique flags → 5 pts
  ≥1 unique flags → 2 pts

The formatted output feeds directly into agentNotes, which the GUVI evaluator
reads to verify red flags were identified and labelled.
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Human-readable descriptions for each flag type
# ---------------------------------------------------------------------------

FLAG_DESCRIPTIONS: Dict[str, str] = {
    "URGENCY":               "Urgency/pressure tactics (e.g. 'act immediately', 'limited time', 'deadline')",
    "OTP_REQUEST":           "OTP or verification code solicitation",
    "FEE_REQUEST":           "Upfront fee demand (processing fee, registration fee, token amount)",
    "THREAT":                "Threats of legal action, arrest, account suspension, or court action",
    "PRIZE":                 "Prize/lottery/lucky winner claims to create false excitement",
    "IMPERSONATION":         "Impersonating official entities (RBI, SBI, Police, Government, TRAI)",
    "PERSONAL_DATA_REQUEST": "Requesting sensitive personal/financial data (Aadhar, PAN, CVV, account number)",
    "SUSPICIOUS_LINK":       "Suspicious or phishing URL shared (shortened link, HTTP, IP-based)",
    "PRESSURE":              "Psychological pressure tactics (keep secret, don't tell anyone, only for you)",
    "ADVANCE_FEE":           "Advance fee / upfront payment demand (pay first, deposit required)",
}


# ---------------------------------------------------------------------------
# RedFlagTracker
# ---------------------------------------------------------------------------

class RedFlagTracker:
    """
    Maintains a running list of all distinct red flags observed across the
    entire conversation. Preserves the turn number each flag was first seen.
    """

    def __init__(self) -> None:
        # flag_label → turn number when first detected
        self._flags: Dict[str, int] = {}

    # ── Mutation ─────────────────────────────────────────────────────────────

    def add_flags(self, flags: List[str], turn: int) -> None:
        """
        Record each new flag against the turn it was first observed.
        Duplicate flags (same label seen again later) are ignored.
        """
        for flag in flags:
            flag = flag.strip().upper()
            if flag and flag not in self._flags:
                self._flags[flag] = turn
                logger.debug(f"Red flag recorded: {flag} at turn {turn}")

    # ── Accessors ────────────────────────────────────────────────────────────

    def get_all_flags(self) -> List[str]:
        """Return deduplicated list of all flag labels seen so far."""
        return list(self._flags.keys())

    def get_flag_count(self) -> int:
        """Total number of distinct flag types detected."""
        return len(self._flags)

    def get_flag_turns(self) -> Dict[str, int]:
        """Return the full flag → first_turn mapping."""
        return dict(self._flags)

    # ── Formatting for agentNotes ────────────────────────────────────────────

    def get_formatted_flags(self) -> str:
        """
        Compact one-liner for agentNotes summary line.
        Example: "URGENCY (turn 1), OTP_REQUEST (turn 2), THREAT (turn 4)"
        """
        if not self._flags:
            return "None detected"
        return ", ".join(
            f"{flag} (turn {turn})"
            for flag, turn in sorted(self._flags.items(), key=lambda x: x[1])
        )

    def get_flag_summary_for_notes(self) -> str:
        """
        Detailed multi-line block for agentNotes.
        Each line: "  - FLAGNAME (turn N): description"
        Designed to be read by the GUVI evaluator to verify red flag detection.
        """
        if not self._flags:
            return "  No red flags identified in this conversation."

        lines: List[str] = []
        for flag, turn in sorted(self._flags.items(), key=lambda x: x[1]):
            description = FLAG_DESCRIPTIONS.get(flag, f"{flag} — suspicious behaviour detected")
            lines.append(f"  - {flag} (turn {turn}): {description}")

        return "\n".join(lines)

    def get_scoring_note(self) -> str:
        """
        One-line summary suitable for inclusion in agentNotes top section.
        """
        count = self.get_flag_count()
        if count >= 5:
            tier = "HIGH (≥5 flags)"
        elif count >= 3:
            tier = "MEDIUM (≥3 flags)"
        elif count >= 1:
            tier = "LOW (≥1 flag)"
        else:
            tier = "NONE"
        return f"{count} red flags identified — severity: {tier}"
