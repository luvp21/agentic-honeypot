"""
Pydantic Models for Honeypot API
STRICTLY MATCHES OFFICIAL HACKATHON SPECIFICATION
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


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
    timestamp: str = Field(..., description="ISO-8601 formatted timestamp")


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
    bankAccounts: List[str] = Field(default_factory=list, description="Extracted bank account numbers")
    upiIds: List[str] = Field(default_factory=list, description="Extracted UPI IDs")
    phishingLinks: List[str] = Field(default_factory=list, description="Phishing URLs")
    phoneNumbers: List[str] = Field(default_factory=list, description="Phone numbers")
    suspiciousKeywords: List[str] = Field(default_factory=list, description="Scam indicators")


class FinalCallbackPayload(BaseModel):
    """
    MANDATORY FINAL CALLBACK PAYLOAD
    Sent to: https://hackathon.guvi.in/api/updateHoneyPotFinalResult
    """
    sessionId: str = Field(..., description="Session ID from platform")
    scamDetected: bool = Field(..., description="Must be True before sending")
    totalMessagesExchanged: int = Field(..., description="Total message count in session")
    extractedIntelligence: ExtractedIntelligence = Field(..., description="All extracted intelligence")
    agentNotes: str = Field(..., description="Summary of scammer behavior and tactics")


# ============================================================================
# INTERNAL STATE MODELS (Not exposed in API)
# ============================================================================

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
    extracted_intelligence: dict = Field(default_factory=dict)
    callback_sent: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
