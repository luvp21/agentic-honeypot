"""
models.py — Pydantic data models for the Agentic Honeypot system.
All request/response schemas and shared data structures live here.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any, Union
from enum import Enum


# ---------------------------------------------------------------------------
# Session state machine
# ---------------------------------------------------------------------------

class SessionState(str, Enum):
    INIT       = "INIT"       # Session just created, no turns yet
    DETECTING  = "DETECTING"  # First turn — scam detection running
    ENGAGING   = "ENGAGING"   # Actively keeping scammer engaged
    FINALIZING = "FINALIZING" # Turn 9 — preparing finalOutput
    DONE       = "DONE"       # Turn 10+ or isLastTurn — all done


# ---------------------------------------------------------------------------
# GUVI message object (official request format from evaluation platform)
# ---------------------------------------------------------------------------

class MessageContent(BaseModel):
    """
    The message object sent by the GUVI evaluation platform.
    Official format: {"sender": "scammer", "text": "...", "timestamp": "..."}
    GUVI sends timestamp as epoch ms integer or ISO string — accept both.
    """
    sender:    str = "scammer"
    text:      str
    timestamp: Optional[Any] = None  # epoch ms (int) or ISO string


class ConversationEntry(BaseModel):
    """One entry in the conversationHistory array sent by the platform."""
    sender:    str
    text:      str
    timestamp: Optional[Any] = None   # epoch ms (int) or ISO string


class RequestMetadata(BaseModel):
    """Optional metadata block included by GUVI in every request."""
    channel:  Optional[str] = None   # e.g. "SMS", "WhatsApp"
    language: Optional[str] = None   # e.g. "English"
    locale:   Optional[str] = None   # e.g. "IN"


# ---------------------------------------------------------------------------
# Inbound request model — matches the official GUVI evaluation platform format
# ---------------------------------------------------------------------------

class MessageRequest(BaseModel):
    """
    Incoming request from the GUVI evaluation platform.

    Official format (from evaluation docs):
    {
      "sessionId": "uuid-v4-string",
      "message": {"sender": "scammer", "text": "...", "timestamp": "..."},
      "conversationHistory": [{"sender": "...", "text": "...", "timestamp": "..."}],
      "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
    }

    Also accepts legacy plain-string message for backward compatibility.
    """
    sessionId:           str
    # GUVI sends message as object; also accept plain string for local testing
    message:             Union[MessageContent, str]
    conversationHistory: Optional[List[ConversationEntry]] = None
    metadata:            Optional[RequestMetadata] = None
    # Extra fields kept for backward compatibility / local testing
    turn:                Optional[int]  = None
    isLastTurn:          Optional[bool] = False

    def get_message_text(self) -> str:
        """Extract the plain text regardless of whether message is object or string."""
        if isinstance(self.message, str):
            return self.message
        return self.message.text

    def get_platform_history(self) -> List[Dict[str, str]]:
        """
        Convert the platform-supplied conversationHistory into our internal format
        [{"role": "user"|"assistant", "content": "..."}].
        scammer = user, honeypot/user = assistant.
        Returns empty list if no history supplied.
        """
        if not self.conversationHistory:
            return []
        result = []
        for entry in self.conversationHistory:
            role = "user" if entry.sender.lower() == "scammer" else "assistant"
            result.append({"role": role, "content": entry.text})
        return result


# ---------------------------------------------------------------------------
# Intel / output models
# ---------------------------------------------------------------------------

class ExtractedIntelligence(BaseModel):
    """All 8 intelligence types extracted from conversation. (30 pts)"""
    phoneNumbers:   List[str] = Field(default_factory=list)
    bankAccounts:   List[str] = Field(default_factory=list)
    upiIds:         List[str] = Field(default_factory=list)
    phishingLinks:  List[str] = Field(default_factory=list)
    emailAddresses: List[str] = Field(default_factory=list)
    caseIds:        List[str] = Field(default_factory=list)   # NEW — was missing in old system
    policyNumbers:  List[str] = Field(default_factory=list)   # NEW
    orderNumbers:   List[str] = Field(default_factory=list)   # NEW


class EngagementMetrics(BaseModel):
    """Nested engagement metrics block (Engagement Quality scoring section)."""
    engagementDurationSeconds: float
    totalMessagesExchanged:    int


class FinalOutput(BaseModel):
    """
    Complete finalOutput payload POSTed to GUVI session log.

    Structure scoring (10 pts total):
      Required (2 pts each): sessionId, scamDetected, extractedIntelligence
      Optional (1 pt each):  totalMessagesExchanged+engagementDurationSeconds,
                             agentNotes, scamType, confidenceLevel

    Extra field (not in structure rubric but aids Red Flag Identification scoring):
      redFlags — deduplicated list of all flag labels detected across conversation
    """
    # ── Required (2 pts each) ─────────────────────────────────────────────
    sessionId:                 str
    scamDetected:              bool
    extractedIntelligence:     ExtractedIntelligence
    # ── Required for 1-pt combined optional score ─────────────────────────
    totalMessagesExchanged:    int
    engagementDurationSeconds: float
    # ── Optional (1 pt each) ─────────────────────────────────────────────
    scamType:                  Optional[str]   = None
    confidenceLevel:           Optional[float] = None
    agentNotes:                Optional[str]   = None
    # ── Engagement Quality section nested block ────────────────────────────
    engagementMetrics:         Optional[EngagementMetrics] = None
    # ── Extra: aids Red Flag Identification sub-score in quality section ───
    redFlags:                  List[str] = Field(default_factory=list)


class HoneypotResponse(BaseModel):
    """Standard per-turn response returned to the evaluation platform."""
    status:      str
    reply:       str
    sessionId:   str
    turn:        int
    isFinal:     bool = False
    finalOutput: Optional[Dict[str, Any]] = None
