"""
Main FastAPI Application - Honeypot System
STRICTLY COMPLIANT WITH OFFICIAL HACKATHON SPECIFICATION

This is the PRIMARY API that receives requests from the GUVI evaluation platform.
"""

from fastapi import FastAPI, HTTPException, Security, Depends, Header
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from typing import Optional

# Import models (official spec)
from models import (
    HoneypotRequest,
    HoneypotResponse,
    ErrorResponse,
    MessageContent
)

# Import components
from session_manager import session_manager
from scam_detector import ScamDetector
from ai_agent import AIHoneypotAgent
from intelligence_extractor import IntelligenceExtractor
from callback import send_callback_with_retry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Agentic Honeypot System",
    description="AI-powered honeypot for scam detection and intelligence extraction",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# AUTHENTICATION
# ============================================================================

# API Key authentication
API_KEY_NAME = "x-api-key"
API_KEY = "honeypot-secret-key-123"  # In production: use environment variable

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """
    Verify API key from request header.
    Accepts both 'x-api-key' and 'X-API-Key' (case-insensitive).
    """
    if x_api_key == API_KEY:
        return x_api_key

    raise HTTPException(
        status_code=403,
        detail="Invalid or missing API key"
    )


# ============================================================================
# INITIALIZE COMPONENTS
# ============================================================================

scam_detector = ScamDetector()
ai_agent = AIHoneypotAgent()
intel_extractor = IntelligenceExtractor()


# ============================================================================
# PRIMARY API ENDPOINT (Official Specification)
# ============================================================================

@app.post(
    "/api/honeypot/message",
    response_model=HoneypotResponse,
    responses={
        200: {"model": HoneypotResponse},
        400: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def process_message(
    request: HoneypotRequest,
    api_key: str = Depends(verify_api_key)
) -> HoneypotResponse:
    """
    PRIMARY API ENDPOINT - Receives messages from GUVI evaluation platform.

    OFFICIAL SPECIFICATION COMPLIANCE:
    - Request: sessionId, message (object), conversationHistory (array), metadata (optional)
    - Response: ONLY status + reply (no extra fields)
    - Multi-turn: conversationHistory empty = first message, non-empty = follow-up
    - Callback: Triggered after scam detected + sufficient engagement

    Args:
        request: HoneypotRequest with official schema
        api_key: Validated API key

    Returns:
        HoneypotResponse with status='success' and agent reply
    """

    try:
        session_id = request.sessionId
        current_message = request.message
        conversation_history = request.conversationHistory

        logger.info(f"Processing message for session {session_id}")

        # ====================================================================
        # STEP 1: Session Management
        # ====================================================================

        session = session_manager.get_or_create_session(session_id)

        # Check if first message
        is_first_message = session_manager.is_first_message(conversation_history)

        # Calculate total messages
        total_messages = session_manager.calculate_total_messages(conversation_history)

        logger.info(
            f"Session {session_id}: "
            f"Message {total_messages} "
            f"(First: {is_first_message})"
        )

        # ====================================================================
        # STEP 2: Scam Detection
        # ====================================================================

        scam_result = scam_detector.analyze(current_message.text)

        # CRITICAL FIX: Once a session is detected as scam, it stays in scam mode
        # Don't override session.is_scam if it's already True
        if not session.is_scam and scam_result["is_scam"]:
            # First scam detection in this session
            session_manager.update_session(
                session_id,
                is_scam=True,
                scam_type=scam_result.get("scam_type", "unknown"),
                confidence_score=scam_result.get("confidence_score", 0.0),
                message_count=total_messages
            )
            logger.info(
                f"🚨 SCAM DETECTED for {session_id}: "
                f"type={scam_result.get('scam_type')}, "
                f"confidence={scam_result.get('confidence_score')}"
            )
        elif session.is_scam:
            # Session already in scam mode - just update message count
            session_manager.update_session(
                session_id,
                message_count=total_messages
            )
            logger.info(
                f"Continuing scam session {session_id}: "
                f"message {total_messages}, type={session.scam_type}"
            )
        else:
            # Not a scam (yet)
            session_manager.update_session(
                session_id,
                is_scam=False,
                message_count=total_messages
            )
            logger.info(f"No scam detected for {session_id}")

        # ====================================================================
        # STEP 3: Intelligence Extraction
        # ====================================================================

        extracted = intel_extractor.extract(current_message.text)

        if extracted:
            # Merge with existing intelligence
            current_intel = session.extracted_intelligence

            for key, value in extracted.items():
                if key.startswith("_"):  # Skip metadata
                    continue

                if key not in current_intel:
                    current_intel[key] = []

                if isinstance(value, list):
                    current_intel[key].extend(value)
                else:
                    current_intel[key].append(value)

            # Deduplicate
            for key in current_intel:
                if isinstance(current_intel[key], list):
                    current_intel[key] = list(set(current_intel[key]))

            session_manager.update_session(
                session_id,
                extracted_intelligence=current_intel
            )

            logger.info(f"Intelligence extracted for {session_id}: {list(extracted.keys())}")

        # Add suspicious keywords from scam detector
        if scam_result.get("indicators"):
            if "suspicious_keywords" not in session.extracted_intelligence:
                session.extracted_intelligence["suspicious_keywords"] = []

            session.extracted_intelligence["suspicious_keywords"].extend(
                scam_result["indicators"][:5]  # Top 5 indicators
            )
            session.extracted_intelligence["suspicious_keywords"] = list(
                set(session.extracted_intelligence["suspicious_keywords"])
            )

        # ====================================================================
        # STEP 4: Agent Response Generation
        # ====================================================================

        # FIXED: Use AI agent if session is marked as scam (persistent state)
        if session.is_scam:
            # Agent activated - generate contextual response

            # Convert conversationHistory to agent format
            agent_history = []
            for msg in conversation_history:
                agent_history.append({
                    "role": msg.sender,
                    "content": msg.text,
                    "timestamp": msg.timestamp
                })

            # Add current message
            agent_history.append({
                "role": current_message.sender,
                "content": current_message.text,
                "timestamp": current_message.timestamp
            })

            # Generate response
            agent_response = await ai_agent.generate_response(
                message=current_message.text,
                conversation_history=agent_history,
                scam_type=session.scam_type
            )

            logger.info(
                f"🤖 Agent response generated for {session_id} "
                f"(message {total_messages}, scam type: {session.scam_type})"
            )

        else:
            # No scam detected - neutral response
            agent_response = "Thank you for your message. How can I help you today?"
            logger.info(f"Neutral response for {session_id} (no scam detected)")

        # ====================================================================
        # STEP 5: Callback Trigger Check (Intelligent)
        # ====================================================================
        # INTELLIGENT TRIGGER: Sends based on intelligence extracted, not message count
        # Will send when: min 5 msgs + has critical data (UPIs/accounts/links)

        if session_manager.should_send_callback(session_id, min_messages=5):
            logger.info(f"🎯 Callback conditions met for {session_id} (sufficient intelligence extracted)")

            # Send callback
            callback_success = send_callback_with_retry(
                session_id=session_id,
                scam_detected=session.is_scam,
                total_messages=total_messages,
                extracted_intelligence=session.extracted_intelligence,
                scam_type=session.scam_type,
                max_retries=3
            )

            if callback_success:
                session_manager.mark_callback_sent(session_id)
                logger.info(f"✅ Callback sent and marked for {session_id}")
            else:
                logger.error(f"❌ Callback failed for {session_id}")

        # ====================================================================
        # STEP 6: Return Official Response Format
        # ====================================================================

        # CRITICAL: Return ONLY status and reply (no extra fields)
        return HoneypotResponse(
            status="success",
            reply=agent_response
        )

    except Exception as e:
        logger.error(f"Error processing message for {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


# ============================================================================
# UTILITY ENDPOINTS (For testing/monitoring - not part of official spec)
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint - system info"""
    return {
        "service": "Agentic Honeypot System",
        "version": "2.0.0",
        "status": "active",
        "spec_compliant": True,
        "endpoints": {
            "primary": "/api/honeypot/message (POST)",
            "health": "/health (GET)",
            "stats": "/stats (GET)"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "components": {
            "scam_detector": "operational",
            "ai_agent": "operational",
            "intelligence_extractor": "operational",
            "callback_dispatcher": "operational"
        }
    }


@app.get("/stats")
async def get_stats(api_key: str = Depends(verify_api_key)):
    """
    Get session statistics.
    Requires API key authentication.
    """
    stats = session_manager.get_session_stats()
    return {
        "status": "success",
        "statistics": stats
    }


# ============================================================================
# APPLICATION STARTUP
# ============================================================================

if __name__ == "__main__":
    logger.info("🚀 Starting Agentic Honeypot System...")
    logger.info("📊 Primary API: POST /api/honeypot/message")
    logger.info("📖 API Docs: http://localhost:8000/docs")
    logger.info("🔐 API Key Required: x-api-key header")
    logger.info("✅ SPEC COMPLIANT: Official GUVI hackathon format")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
