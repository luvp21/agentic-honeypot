"""
quality_tracker.py — Real-time tracking of all conversation quality metrics.

Scoring section: Conversation Quality → 30 pts total
  a) Turn Count            →  8 pts  (tracked in session.turn_count)
  b) Questions Asked       →  4 pts  (tracked here)
  c) Relevant Questions    →  3 pts  (tracked here)
  d) Red Flag Identification→ 8 pts  (tracked here via red_flag_tracker)
  e) Information Elicitation→ 7 pts  (tracked here)
"""

import re
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Terms that qualify a question as "investigative" (relevant questions rubric)
# ---------------------------------------------------------------------------

INVESTIGATIVE_TERMS: List[str] = [
    "employee id", "staff id", "badge number", "officer id",
    "company name", "organisation", "organization", "department name",
    "official website", "supervisor", "manager name",
    "headquarters", "office address", "office location",
    "case id", "reference number", "ticket number", "complaint id",
    "verification", "callback number", "direct number",
    "authorization number", "confirmation number", "identity",
]


# ---------------------------------------------------------------------------
# Terms that signal an elicitation attempt (asking scammer for their info)
# ---------------------------------------------------------------------------

ELICITATION_TERMS: List[str] = [
    "phone number", "contact number", "mobile number",
    "call back", "callback", "direct number",
    "employee id", "staff id", "badge",
    "your name", "your location", "company name",
    "your email", "your website", "office address",
    "id number", "contact detail", "reach you",
    "authorization", "who are you", "which company",
    "which department", "your office", "your supervisor",
]


# ---------------------------------------------------------------------------
# QualityTracker
# ---------------------------------------------------------------------------

class QualityTracker:
    """
    Tracks all conversation quality metrics in real-time.
    Attached to the session by main.py on the first turn.
    """

    def __init__(self) -> None:
        self.questions_asked:         int = 0
        self.investigative_questions: int = 0
        self.elicitation_attempts:    int = 0
        self.red_flags_identified:    List[str] = []
        self.turn_count:              int = 0

    # ── Called by main.py after generating each agent reply ─────────────────

    def analyze_response(self, agent_reply: str) -> None:
        """
        Parse agent's outgoing reply and update quality counters.
        Should be called EVERY turn after the response is generated.
        """
        self.turn_count += 1
        reply_lower = agent_reply.lower()

        # ── Count questions (any "?") ──────────────────────────────────────
        q_count = agent_reply.count("?")
        self.questions_asked += q_count

        # ── Count investigative questions ──────────────────────────────────
        # A response counts as investigative if it contains a "?" AND
        # references at least one investigative keyword
        if q_count > 0:
            for term in INVESTIGATIVE_TERMS:
                if term in reply_lower:
                    self.investigative_questions += 1
                    break  # one investigative question per response

        # ── Count elicitation attempts ─────────────────────────────────────
        # Counts as an attempt if at least one elicitation term is present
        elicitation_found = any(term in reply_lower for term in ELICITATION_TERMS)
        if elicitation_found:
            self.elicitation_attempts += 1

    # ── Called by main.py when red flags are detected in scammer messages ───

    def add_red_flags(self, flags: List[str]) -> None:
        """Merge new flags (deduplicated) into the running list."""
        for flag in flags:
            if flag not in self.red_flags_identified:
                self.red_flags_identified.append(flag)

    # ── Scoring estimation ───────────────────────────────────────────────────

    def estimate_score(self, turn_count: int) -> Dict[str, int]:
        """
        Estimate the Conversation Quality score (out of 30) based on current state.
        Used for logging/debugging — actual score is computed by GUVI.
        """
        score: Dict[str, int] = {}

        # a) Turn count — 8 pts
        if turn_count >= 8:
            score["turn_count"] = 8
        elif turn_count >= 6:
            score["turn_count"] = 6
        elif turn_count >= 4:
            score["turn_count"] = 3
        else:
            score["turn_count"] = 0

        # b) Questions asked — 4 pts
        if self.questions_asked >= 5:
            score["questions_asked"] = 4
        elif self.questions_asked >= 3:
            score["questions_asked"] = 2
        elif self.questions_asked >= 1:
            score["questions_asked"] = 1
        else:
            score["questions_asked"] = 0

        # c) Relevant/investigative questions — 3 pts
        if self.investigative_questions >= 3:
            score["investigative_questions"] = 3
        elif self.investigative_questions >= 2:
            score["investigative_questions"] = 2
        elif self.investigative_questions >= 1:
            score["investigative_questions"] = 1
        else:
            score["investigative_questions"] = 0

        # d) Red flag identification — 8 pts
        rf = len(self.red_flags_identified)
        if rf >= 5:
            score["red_flags"] = 8
        elif rf >= 3:
            score["red_flags"] = 5
        elif rf >= 1:
            score["red_flags"] = 2
        else:
            score["red_flags"] = 0

        # e) Elicitation — 7 pts (1.5 pts each, max 7)
        score["elicitation"] = min(int(self.elicitation_attempts * 1.5), 7)

        score["total"] = sum(score.values())
        return score

    # ── Summary dict for agentNotes ──────────────────────────────────────────

    def get_quality_summary(self) -> Dict:
        return {
            "questions_asked":         self.questions_asked,
            "investigative_questions": self.investigative_questions,
            "elicitation_attempts":    self.elicitation_attempts,
            "red_flags_identified":    len(self.red_flags_identified),
            "turn_count":              self.turn_count,
        }
