"""
Pydantic Models for Honeypot API
STRICTLY MATCHES OFFICIAL HACKATHON SPECIFICATION
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum


# ============================================================================
# SESSION STATE MACHINE & BEHAVIORAL PROFILING
# ============================================================================

class SessionStateEnum(str, Enum):
    """
    Explicit session lifecycle states.
    Ensures proper flow: INIT → SCAM_DETECTED → ENGAGING → EXTRACTING → FINALIZED
    """
    INIT = "INIT"
    SCAM_DETECTED = "SCAM_DETECTED"
    ENGAGING = "ENGAGING"
    EXTRACTING = "EXTRACTING"
    FINALIZED = "FINALIZED"


class EngagementStrategyEnum(str, Enum):
    """
    Agent engagement strategies to maximize duration and intelligence extraction.
    """
    DEFAULT = "DEFAULT"
    CONFUSION = "CONFUSION"             # Act confused, force repetition
    DELAYED_COMPLIANCE = "DELAYED_COMPLIANCE"  # "I'm trying, wait..."
    TECHNICAL_CLARIFICATION = "TECHNICAL_CLARIFICATION" # Ask for specific details
    FRUSTRATED_VICTIM = "FRUSTRATED_VICTIM"   # "Why is this not working?"
    AUTHORITY_CHALLENGE = "AUTHORITY_CHALLENGE" # "Who is your supervisor?"
    SAFETY_DEFLECT = "SAFETY_DEFLECT"         # Respond to prompt injection/challenge


class ScammerProfile(BaseModel):
    """
    Behavioral profiling of scammer for intelligence analysis.
    Used to generate rich agentNotes in final callback.
    """
    scam_type: str = "unknown"
    tactics: List[str] = Field(
        default_factory=list,
        description="Detected tactics: URGENCY, FEAR, REWARD, AUTHORITY, SCARCITY"
    )
    language: str = "unknown"  # English, Hinglish, Hindi
    aggression_score: float = Field(
        default=0.0,
        description="Aggression level 0.0-1.0 based on caps, threats, punctuation"
    )


# ============================================================================
# REQUEST MODELS (Official Specification)
# ============================================================================

class MessageContent(BaseModel):
    """
    Message object structure as per official spec.
    Required fields: sender, text, timestamp
    """
    sender: str = Field(..., description="Either 'scammer' or 'user'")
    text: str = Field(..., description="Message content")
    timestamp: int = Field(..., description="Epoch time in milliseconds")


class Metadata(BaseModel):
    """
    Optional metadata about the communication channel.
    All fields are optional as per spec.
    """
    channel: Optional[str] = Field(None, description="SMS, WhatsApp, Email, Chat")
    language: Optional[str] = Field(None, description="Language of communication")
    locale: Optional[str] = Field(None, description="Country or region code")


class HoneypotRequest(BaseModel):
    """
    OFFICIAL API REQUEST FORMAT
    This MUST match the hackathon specification exactly.
    """
    sessionId: str = Field(..., description="Unique session identifier from platform")
    message: MessageContent = Field(..., description="Current incoming message")
    conversationHistory: List[MessageContent] = Field(
        ...,
        description="All previous messages in this session. Empty array for first message."
    )
    metadata: Optional[Metadata] = Field(None, description="Optional channel metadata")


# ============================================================================
# RESPONSE MODELS (Official Specification)
# ============================================================================

class HoneypotResponse(BaseModel):
    """
    OFFICIAL API RESPONSE FORMAT
    MUST contain ONLY these two fields. No additional fields allowed.
    """
    status: str = Field("success", description="Always 'success' for valid requests")
    reply: str = Field(..., description="Agent-generated response text")


class ErrorResponse(BaseModel):
    """
    Error response format for invalid requests.
    """
    status: str = Field("error", description="Always 'error' for failures")
    message: str = Field(..., description="Human-readable error message")


# ============================================================================
# CALLBACK MODELS (Official Specification)
# ============================================================================

class ExtractedIntelligence(BaseModel):
    """
    Intelligence data structure for final callback.
    Field names MUST be camelCase as per spec.
    """
    phoneNumbers: List[str] = Field(default_factory=list, description="Phone numbers")
    bankAccounts: List[str] = Field(default_factory=list, description="Extracted bank account numbers")
    upiIds: List[str] = Field(default_factory=list, description="Extracted UPI IDs")
    phishingLinks: List[str] = Field(default_factory=list, description="Phishing URLs")
    emailAddresses: List[str] = Field(default_factory=list, description="Email addresses")
    ifscCodes: List[str] = Field(default_factory=list, description="Extracted IFSC Codes")
    suspiciousKeywords: List[str] = Field(default_factory=list, description="Scam indicators")
    other: Dict[str, List[str]] = Field(default_factory=dict, description="Other extracted intelligence (telegram IDs, short URLs, QR mentions, etc.)")


class EngagementMetrics(BaseModel):
    """
    Engagement quality metrics for scoring.
    NEW: Required for 20-point engagement quality score.
    """
    totalMessagesExchanged: int = Field(..., description="Total message count")
    engagementDurationSeconds: int = Field(..., description="Duration in seconds from first to last message")


class FinalCallbackPayload(BaseModel):
    """
    MANDATORY FINAL CALLBACK PAYLOAD
    Sent to: https://hackathon.guvi.in/api/updateHoneyPotFinalResult
    """
    sessionId: str = Field(..., description="Session ID from platform")
    status: str = Field("completed", description="Status: completed/final - REQUIRED for 5 points")
    scamDetected: bool = Field(..., description="Must be True before sending")
    totalMessagesExchanged: int = Field(..., description="Total message count in session")
    extractedIntelligence: ExtractedIntelligence = Field(..., description="All extracted intelligence")
    engagementMetrics: Optional[EngagementMetrics] = Field(None, description="Engagement metrics - worth 2.5 points")
    agentNotes: str = Field(..., description="Summary of scammer behavior and tactics")


# ============================================================================
# INTERNAL STATE MODELS (Not exposed in API)
# ============================================================================

class IntelItem(BaseModel):
    """
    Individual piece of extracted intelligence with tracking.
    """
    value: str
    type: str
    confidence: float
    first_seen_msg: int
    last_seen_msg: int
    sources: List[str] = Field(default_factory=list)


class SessionState(BaseModel):
    """
    Internal session state management.
    NOT part of API request/response.
    """
    sessionId: str
    is_scam: bool = False
    scam_type: str = "unknown"
    confidence_score: float = 0.0
    message_count: int = 0

    # State Machine (NEW)
    state: SessionStateEnum = SessionStateEnum.INIT

    # Strategy & Persona (NEW - UPGRADE)
    engagement_strategy: EngagementStrategyEnum = EngagementStrategyEnum.DEFAULT
    persona_name: str = "elderly"
    last_scammer_move: Optional[str] = None # URGENCY, THREAT, etc.
    intel_stall_counter: int = 0             # Turns since last unique intel extraction

    # PRODUCTION REFINEMENTS
    suspicion_score: float = 0.0             # Incremental scam confidence accumulation
    strategy_level: int = 0                  # Strategy escalation ladder (0-3)
    last_new_intel_turn: int = 0             # Track when last NEW intel was found

    # Behavioral Profiling (NEW)
    scammer_profile: ScammerProfile = Field(default_factory=ScammerProfile)

    # Full Conversation History (NEW) - for backfill extraction
    conversation_full: List[MessageContent] = Field(default_factory=list)

    # Idle Detection (NEW)
    last_activity_time: datetime = Field(default_factory=datetime.utcnow)

    # Intelligence Graph (Existing)
    intel_graph: Dict[str, List[IntelItem]] = Field(default_factory=dict)

    # Backward compatibility dict (Existing)
    extracted_intelligence: dict = Field(default_factory=dict)

    # Callback tracking (Existing)
    callback_sent: bool = False
    callback_phase: str = "none"  # none, preliminary, final

    # Timestamps (Existing)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
