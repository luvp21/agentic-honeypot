"""
session_manager.py — Session state, turn tracking, and intel accumulation.

MAX_TURNS = 10  (hard platform limit — critical redesign from old 18-19 turn system)
FINALIZE_AT = 9 (prepare finalOutput payload on turn 9, send on turn 10)
"""

import re
import time
import uuid
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from models import SessionState

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Critical constants (aligned with GUVI platform limits)
# ---------------------------------------------------------------------------
MAX_TURNS   = 10   # Hard platform cap — never go beyond this
FINALIZE_AT = 9    # Start building finalOutput payload at this turn


# ---------------------------------------------------------------------------
# Session dataclass — single source of truth per conversation
# ---------------------------------------------------------------------------

@dataclass
class Session:
    sessionId: str

    # Turn tracking
    turn_count: int = 0

    # Timing
    start_time:    float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)

    # ── Scam detection ────────────────────────────────────────────────────
    is_scam:          bool  = False
    scam_type:        Optional[str]   = None
    confidence_score: float = 0.0

    # ── Intel store — all 8 types (NEW: caseIds, policyNumbers, orderNumbers) ──
    intel_store: Dict[str, List[str]] = field(default_factory=lambda: {
        "phoneNumbers":   [],
        "bankAccounts":   [],
        "upiIds":         [],
        "phishingLinks":  [],
        "emailAddresses": [],
        "caseIds":        [],   # NEW
        "policyNumbers":  [],   # NEW
        "orderNumbers":   [],   # NEW
    })

    # ── Quality-scoring counters ───────────────────────────────────────────
    # Each is incremented by quality_tracker and surfaced in finalOutput.agentNotes
    questions_asked:           int = 0   # tracks "?" count across all agent replies
    investigative_questions:   int = 0   # asks about identity/company/address/website
    elicitation_attempts:      int = 0   # active probes for phone/ID/company

    # ── Red flag accumulation (across all turns) ───────────────────────────
    red_flags:      List[str]         = field(default_factory=list)
    red_flag_turns: Dict[str, int]    = field(default_factory=dict)

    # ── Conversation history (list of {"role": "user"|"assistant", "content": "..."}) ──
    conversation_history: List[Dict[str, str]] = field(default_factory=list)

    # ── Control flags ─────────────────────────────────────────────────────
    callback_sent: bool = False
    state:         str  = SessionState.INIT

    # ── Sub-tracker instances (attached by main.py on first turn) ─────────
    # _quality_tracker: QualityTracker  (attached dynamically)
    # _red_flag_tracker: RedFlagTracker (attached dynamically)

    # ──────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────

    def update_activity(self) -> None:
        self.last_activity = time.time()

    def get_duration(self) -> float:
        """Wall-clock seconds since session start (includes sleep delays)."""
        return time.time() - self.start_time

    def is_finalizing(self) -> bool:
        """Turn 9 reached — start building finalOutput."""
        return self.turn_count >= FINALIZE_AT

    def is_done(self) -> bool:
        """Turn 10 reached or explicitly marked done."""
        return self.turn_count >= MAX_TURNS or self.state == SessionState.DONE

    def add_intel(self, intel_type: str, values: List[str]) -> None:
        """Merge new values into intel_store, deduplicating."""
        if intel_type not in self.intel_store:
            logger.warning(f"Unknown intel type: {intel_type}")
            return
        if intel_type == "phoneNumbers":
            # Deduplicate by last-10 digits so +919876543210 and +91-9876543210
            # are treated as the same number (keeps the first-seen form)
            existing_last10 = {
                re.sub(r"[^\d]", "", p)[-10:] for p in self.intel_store[intel_type]
            }
            for v in values:
                v = v.strip()
                if not v:
                    continue
                last10 = re.sub(r"[^\d]", "", v)[-10:]
                if last10 and last10 not in existing_last10:
                    self.intel_store[intel_type].append(v)
                    existing_last10.add(last10)
        else:
            existing = set(self.intel_store[intel_type])
            for v in values:
                v = v.strip()
                if v and v not in existing:
                    self.intel_store[intel_type].append(v)
                    existing.add(v)

    def add_red_flag(self, flag: str, turn: int) -> None:
        """Record a red flag if not already seen — preserves first-seen turn."""
        if flag not in self.red_flags:
            self.red_flags.append(flag)
            self.red_flag_turns[flag] = turn

    def total_intel_count(self) -> int:
        """Total number of unique intel items extracted so far."""
        return sum(len(v) for v in self.intel_store.values())

    def get_intel_summary(self) -> str:
        """Short human-readable intel summary for LLM prompts."""
        parts = []
        for k, v in self.intel_store.items():
            if v:
                parts.append(f"{k}: {', '.join(v[:3])}")
        return "; ".join(parts) if parts else "Nothing extracted yet"


# ---------------------------------------------------------------------------
# SessionManager — in-memory dict store (thread-safe enough for single-worker)
# ---------------------------------------------------------------------------

class SessionManager:

    def __init__(self) -> None:
        self._sessions: Dict[str, Session] = {}

    def get_or_create(self, session_id: str) -> Session:
        """Return existing session or create a new one."""
        if session_id not in self._sessions:
            session = Session(sessionId=session_id)
            self._sessions[session_id] = session
            logger.info(f"New session created: {session_id}")
        return self._sessions[session_id]

    def get(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)

    def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def active_count(self) -> int:
        return len(self._sessions)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
session_manager = SessionManager()
