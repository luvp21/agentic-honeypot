"""
Final Callback Dispatcher
Sends results to GUVI evaluation platform
CRITICAL: This is MANDATORY for hackathon scoring
"""

import requests
import logging
from typing import Dict, List
from models import FinalCallbackPayload, ExtractedIntelligence

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Official callback endpoint
CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"


def map_intelligence_to_camelcase(extracted_data: dict) -> ExtractedIntelligence:
    """
    Map snake_case intelligence fields to camelCase for callback.

    Args:
        extracted_data: Intelligence dict from extractor (snake_case)

    Returns:
        ExtractedIntelligence model with camelCase fields
    """
    return ExtractedIntelligence(
        bankAccounts=extracted_data.get("bank_accounts", []),
        upiIds=extracted_data.get("upi_ids", []),
        phishingLinks=extracted_data.get("phishing_links", []),
        phoneNumbers=extracted_data.get("phone_numbers", []),
        suspiciousKeywords=extracted_data.get("suspicious_keywords", [])
    )


def generate_agent_notes(
    scam_type: str,
    total_messages: int,
    intelligence: ExtractedIntelligence,
    conversation_history: List = None
) -> str:
    """
    Generate behavioral summary for agentNotes field.

    Args:
        scam_type: Type of scam detected
        total_messages: Number of messages exchanged
        intelligence: Extracted intelligence data
        conversation_history: Optional conversation history

    Returns:
        Human-readable summary of scammer behavior
    """
    # Count intelligence items
    intel_count = (
        len(intelligence.bankAccounts) +
        len(intelligence.upiIds) +
        len(intelligence.phishingLinks) +
        len(intelligence.phoneNumbers)
    )

    notes = f"Detected {scam_type} scam attempt. "
    notes += f"Engaged scammer through {total_messages} message exchanges. "
    notes += f"Successfully extracted {intel_count} intelligence items including "

    items = []
    if intelligence.bankAccounts:
        items.append(f"{len(intelligence.bankAccounts)} bank account(s)")
    if intelligence.upiIds:
        items.append(f"{len(intelligence.upiIds)} UPI ID(s)")
    if intelligence.phishingLinks:
        items.append(f"{len(intelligence.phishingLinks)} phishing link(s)")
    if intelligence.phoneNumbers:
        items.append(f"{len(intelligence.phoneNumbers)} phone number(s)")

    if items:
        notes += ", ".join(items) + ". "

    # Add behavioral insights
    if intelligence.suspiciousKeywords:
        notes += f"Scammer used urgency tactics: {', '.join(intelligence.suspiciousKeywords[:3])}. "

    notes += "Agent maintained believable persona throughout engagement."

    return notes


def send_final_callback(
    session_id: str,
    scam_detected: bool,
    total_messages: int,
    extracted_intelligence: dict,
    scam_type: str = "unknown",
    conversation_history: List = None
) -> bool:
    """
    Send final results to GUVI evaluation platform.

    CRITICAL: This is MANDATORY for hackathon scoring.
    Must be sent ONCE per session after scam engagement.

    Args:
        session_id: Session ID from platform
        scam_detected: Must be True
        total_messages: Total message count
        extracted_intelligence: Intelligence dict (snake_case)
        scam_type: Type of scam
        conversation_history: Optional conversation data

    Returns:
        True if callback successful, False otherwise
    """

    # Validation: Only send if scam detected
    if not scam_detected:
        logger.warning(f"Callback not sent for session {session_id}: scam not detected")
        return False

    try:
        # Map intelligence to camelCase
        intelligence = map_intelligence_to_camelcase(extracted_intelligence)

        # Generate agent notes
        agent_notes = generate_agent_notes(
            scam_type=scam_type,
            total_messages=total_messages,
            intelligence=intelligence,
            conversation_history=conversation_history
        )

        # Create payload
        payload = FinalCallbackPayload(
            sessionId=session_id,
            scamDetected=scam_detected,
            totalMessagesExchanged=total_messages,
            extractedIntelligence=intelligence,
            agentNotes=agent_notes
        )

        # Log payload for debugging
        logger.info(f"Sending callback for session {session_id}")
        logger.debug(f"Payload: {payload.model_dump_json(indent=2)}")

        # Send POST request
        response = requests.post(
            CALLBACK_URL,
            json=payload.model_dump(),
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        # Check response
        response.raise_for_status()

        logger.info(
            f"✅ Callback successful for session {session_id} "
            f"(Status: {response.status_code})"
        )

        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Callback failed for session {session_id}: {e}")
        return False

    except Exception as e:
        logger.error(f"❌ Unexpected error in callback for session {session_id}: {e}")
        return False


def send_callback_with_retry(
    session_id: str,
    scam_detected: bool,
    total_messages: int,
    extracted_intelligence: dict,
    scam_type: str = "unknown",
    max_retries: int = 3
) -> bool:
    """
    Send callback with retry logic.

    Args:
        session_id: Session ID
        scam_detected: Scam status
        total_messages: Message count
        extracted_intelligence: Intelligence data
        scam_type: Scam type
        max_retries: Maximum retry attempts

    Returns:
        True if successful, False after all retries failed
    """
    for attempt in range(max_retries):
        success = send_final_callback(
            session_id=session_id,
            scam_detected=scam_detected,
            total_messages=total_messages,
            extracted_intelligence=extracted_intelligence,
            scam_type=scam_type
        )

        if success:
            return True

        if attempt < max_retries - 1:
            logger.warning(f"Retry {attempt + 1}/{max_retries} for session {session_id}")

    logger.error(f"All retries failed for session {session_id}")
    return False
