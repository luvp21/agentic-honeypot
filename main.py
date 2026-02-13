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
    MessageContent,
    SessionStateEnum  # NEW
)

# Import components
from session_manager import session_manager
from scam_detector import ScamDetector
from ai_agent import AIHoneypotAgent
from intelligence_extractor import IntelligenceExtractor
from callback import send_callback_with_retry
from test_logger import test_logger  # NEW: Platform test logging
from guardrails import guardrails  # PRODUCTION REFINEMENT
from llm_safety import is_llm_available  # PRODUCTION REFINEMENT
from response_stability_filter import response_stability_filter  # ELITE REFINEMENT

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
        # STEP 1: Session Management + State Tracking
        # ====================================================================

        session = session_manager.get_or_create_session(session_id)

        # Store full message for backfill extraction
        session_manager.store_full_message(session_id, current_message)

        # Update idle tracking
        session_manager.update_idle_time(session_id)

        # Check if first message
        is_first_message = session_manager.is_first_message(conversation_history)

        # Calculate total messages
        total_messages = session_manager.calculate_total_messages(conversation_history)

        # Update message count
        session_manager.update_session(session_id, message_count=total_messages)

        # ====================================================================
        # STEP 1.25: CONTINUOUS Intelligence Extraction (Run BEFORE Termination)
        # ====================================================================

        # Build context window from last 5 messages
        context_msgs = conversation_history[-5:] if conversation_history else []
        context_text = " ".join([m.text for m in context_msgs])

        # Message index is total messages - 1 (0-indexed)
        msg_index = total_messages - 1

        # CRITICAL: Extract from EVERY message (continuous extraction)
        extracted_list = await intel_extractor.extract(
            text=current_message.text,
            message_index=msg_index,
            context_window=context_text
        )

        if extracted_list:
            # Update session graph
            session_manager.update_intel_graph(session_id, extracted_list)
            # Log what was found
            found_types = list(set([x.type for x in extracted_list]))
            logger.info(f"Intelligence extracted for {session_id}: {found_types}")

        # Backfill extraction every 5 turns (full history scan)
        if msg_index % 5 == 0 and msg_index > 0:
            logger.info(f"Running backfill extraction for {session_id} at turn {msg_index}")
            backfill_intel = await intel_extractor.extract_from_full_history(
                session.conversation_full,
                msg_index
            )
            if backfill_intel:
                session_manager.update_intel_graph(session_id, backfill_intel)
                logger.info(f"Backfill found {len(backfill_intel)} additional items")

        # ====================================================================
        # ELITE REFINEMENT 7: Hard Termination Lock (Turn 15 Limit)
        # ====================================================================
        if total_messages >= 15:
            logger.warning(f"🏁 [HARD TERMINATION] Session {session_id} reached 15 turns. Forcing completion.")

            # Force FINALIZED state
            session_manager.transition_state(session_id, SessionStateEnum.FINALIZED)

            # Final reply (Neutral)
            final_reply = "I think I have provided everything needed. Please let me know if there is anything else."

            # Handle callback (ensure sent)
            callback_status = session_manager.should_send_callback(session_id, total_messages - 1)
            if callback_status["send"]:
                send_callback_with_retry(
                    session_id=session_id,
                    scam_detected=session.is_scam,
                    total_messages=total_messages,
                    extracted_intelligence=session.extracted_intelligence,
                    scam_type=session.scam_type,
                    scammer_profile=session.scammer_profile,
                    max_retries=2,
                    status=callback_status["type"]
                )
                session_manager.mark_callback_sent(session_id, callback_status["type"])

            return HoneypotResponse(status="success", reply=final_reply)

        # ====================================================================
        # STEP 1.5: PROMPT INJECTION DEFENSE - Sanitize user input (Layer A)
        # ====================================================================
        is_prompt_injection = guardrails.detect_prompt_injection(current_message.text)

        # Sanitize user input before LLM processing
        sanitized_text, was_sanitized = guardrails.sanitize_user_input(current_message.text)

        if was_sanitized:
            logger.warning(
                f"🛡️ [INJECTION DEFENSE] User input sanitized for session {session_id}"
            )
            # Use sanitized version for detection/extraction
            current_message.text = sanitized_text

        # Apply injection penalty if detected (Layer D)
        if is_prompt_injection:
            session.suspicion_score = min(session.suspicion_score + 0.25, 2.0)
            session.engagement_strategy = "SAFETY_DEFLECT"  # Force defensive mode
            logger.warning(
                f"🚨 [INJECTION DETECTED] Penalty applied: suspicion +0.25 → {session.suspicion_score:.2f}"
            )

        # ====================================================================
        # STEP 2: PRODUCTION - Incremental Scam Detection + Suspicion Accumulation
        # ====================================================================

        scam_result = await scam_detector.analyze(current_message.text, conversation_history)

        # ADAPTING FOR LEGACY RULE SYSTEM:
        # Calculate missing fields for incremental scoring
        normalized_score = scam_result.get("confidence_score", 0.0)
        indicators = scam_result.get("indicators", [])
        has_urgency = "excessive_urgency" in indicators or "urgent" in indicators
        has_payment_terms = "money_request" in indicators

        # HYBRID LAYER: Implemented inside ScamDetector (Hybrid LLM + Heuristic)
        # We use the result directly from scam_detector.analyze


        # PRODUCTION REFINEMENT: Accumulate suspicion score
        # ELITE FIX: Only accumulate if scam not yet confirmed, and cap at 2.0
        if current_message.sender == "scammer" and not session.is_scam:
            # Add rule score * 0.4 to session suspicion
            session.suspicion_score += normalized_score * 0.4

            # Additional suspicion signals
            if has_urgency:
                session.suspicion_score += 0.2
            if has_payment_terms:
                session.suspicion_score += 0.2

            # Check for repeated credential requests
            message_text_lower = current_message.text.lower()
            repeated_requests = sum([
                "otp" in message_text_lower,
                "account" in message_text_lower and "number" in message_text_lower,
                "upi" in message_text_lower,
                "verify" in message_text_lower
            ])
            if repeated_requests >= 2:
                session.suspicion_score += 0.3

            # ELITE FIX: Cap suspicion score to prevent overflow
            session.suspicion_score = min(session.suspicion_score, 2.0)

            logger.info(
                f"Session {session_id} suspicion score: {session.suspicion_score:.2f}"
            )

            # Add suspicious keywords from scam detector (Late Binding)
            if scam_result.get("indicators"):
                from intelligence_extractor import RawIntel
                keyword_intel = []
                for kw in scam_result["indicators"][:5]:
                    keyword_intel.append(RawIntel(
                        type="suspicious_keywords",
                        value=kw,
                        source="scam_detector",
                        confidence_delta=0.5,
                        message_index=msg_index
                    ))
                session_manager.update_intel_graph(session_id, keyword_intel)

        # ═══════════════════════════════════════════════════════════
        # ELITE REFINEMENT 5: Suspicion Decay Mechanism
        # ═══════════════════════════════════════════════════════════
        has_suspicious_signal = (
            scam_result.get("is_scam", False) or
            normalized_score > 0.4 or
            is_prompt_injection or
            has_urgency or
            has_payment_terms
        )
        session_manager.apply_suspicion_decay(session_id, has_suspicious_signal)

        # ====================================================================
        # STEP 2.5: STATE FREEZE - Only accumulate suspicion if not yet confirmed
        # ====================================================================
        # Trigger scam detection via suspicion score OR rule-based
        if not session.is_scam and (scam_result["is_scam"] or session.suspicion_score > 1.2):
            # Scam confirmed!
            detection_method = "rule-based" if scam_result["is_scam"] else "incremental suspicion"

            # Select persona (deterministic mapping)
            scam_type = scam_result.get("scam_type", "unknown")
            assigned_persona = ai_agent._select_persona(scam_type)

            session_manager.update_session(
                session_id,
                is_scam=True,
                scam_type=scam_type,
                persona_name=assigned_persona,
                confidence_score=max(scam_result.get("confidence_score", 0.0), session.suspicion_score / 2)
            )

            # Transition to SCAM_DETECTED state
            session_manager.transition_state(session_id, SessionStateEnum.SCAM_DETECTED)

            # Update behavioral profile
            session_manager.update_scammer_profile(
                session_id,
                current_message.text,
                scam_result.get("scam_type")
            )

            logger.info(
                f"🚨 SCAM DETECTED for {session_id} via {detection_method}: "
                f"type={scam_result.get('scam_type')}, "
                f"confidence={session.confidence_score:.2f}, "
                f"suspicion={session.suspicion_score:.2f}"
            )
        elif session.is_scam:
            # Update behavioral profile on each scammer message
            if current_message.sender == "scammer":
                session_manager.update_scammer_profile(
                    session_id,
                    current_message.text
                )
            logger.info(
                f"Continuing scam session {session_id}: "
                f"message {total_messages}, type={session.scam_type}, state={session.state}"
            )

        if session.is_scam:
            # Transition progression based on turn count
            if total_messages >= 3 and session.state == SessionStateEnum.SCAM_DETECTED:
                session_manager.transition_state(session_id, SessionStateEnum.ENGAGING)
                logger.info(f"Session {session_id} transitioned to ENGAGING phase")

            elif total_messages >= 7 and session.state == SessionStateEnum.ENGAGING:
                session_manager.transition_state(session_id, SessionStateEnum.EXTRACTING)
                logger.info(f"Session {session_id} transitioned to EXTRACTING phase")

        # ====================================================================
        # STEP 4: State Transitions (ENGAGING → EXTRACTING)
        # ====================================================================

        if session.is_scam:
            # Transition progression based on turn count
            if total_messages >= 3 and session.state == SessionStateEnum.SCAM_DETECTED:
                session_manager.transition_state(session_id, SessionStateEnum.ENGAGING)
                logger.info(f"Session {session_id} transitioned to ENGAGING phase")

            elif total_messages >= 7 and session.state == SessionStateEnum.ENGAGING:
                session_manager.transition_state(session_id, SessionStateEnum.EXTRACTING)
                logger.info(f"Session {session_id} transitioned to EXTRACTING phase")

        # ====================================================================
        # STEP 5: Agent Response Generation
        # ====================================================================

        if session.is_scam:
            # Update Engagement Strategy
            current_strategy = session_manager.update_strategy(
                session_id,
                is_prompt_injection=scam_result.get("is_prompt_injection", False)
            )
            logger.info(f"Using strategy {current_strategy} for {session_id}")

            # Determine missing intelligence to guide agent
            missing_intel = []
            features = session.extracted_intelligence

            # Check if we have enough intel to terminate early (Success Condition)
            # If we have Bank OR UPI AND Phone, we can consider wrapping up
            has_payment = bool(features.get("bank_accounts") or features.get("upi_ids"))
            has_contact = bool(features.get("phone_numbers"))

            if has_payment and has_contact and total_messages > 8:
                 logger.info(f"Target intelligence acquired for {session_id}. Initiating wrap-up.")
                 # Could force a specific "wrap up" strategy or just let natural flow handle it

            if not features.get("bank_accounts"):
                missing_intel.append("bank_accounts")
            elif not features.get("ifsc_codes"):
                missing_intel.append("ifsc_codes")

            if not features.get("upi_ids"):
                missing_intel.append("upi_ids")

            if not features.get("phone_numbers"):
                missing_intel.append("phone_numbers")

            if not features.get("phishing_links"):
                missing_intel.append("phishing_links")

            # Convert conversation history to agent format
            agent_history = []
            for msg in conversation_history:
                agent_history.append({
                    "role": "scammer" if msg.sender == "scammer" else "user", # map back to agent expected roles
                    "content": msg.text,
                    "timestamp": msg.timestamp
                })

            # Add current message
            agent_history.append({
                "role": "scammer",
                "content": current_message.text,
                "timestamp": current_message.timestamp
            })

            # Generate response with strategy
            agent_response = await ai_agent.generate_response(
                message=current_message.text,
                conversation_history=agent_history,
                scam_type=session.scam_type,
                missing_intel=missing_intel,
                strategy=current_strategy,
                persona_name=session.persona_name
            )

            # PRODUCTION REFINEMENT: Validate and sanitize with guardrails
            # Use already-detected injection flag from earlier in the pipeline

            agent_response = guardrails.validate_and_fix(
                agent_response,
                is_prompt_injection=is_prompt_injection,
                turn_number=total_messages  # Deterministic deflection selection
            )

            # ═══════════════════════════════════════════════════════════
            # ELITE REFINEMENT 6: Response Stability Filter
            # ═══════════════════════════════════════════════════════════
            persona_name = session.persona_name or "elderly"
            fallback_reply = ai_agent._generate_rule_based_response(
                message=current_message.text,
                persona=persona_name,
                stage=session.state.value if hasattr(session.state, "value") else str(session.state),
                scam_type=session.scam_type,
                turn_number=total_messages,
                missing_intel=missing_intel
            )

            agent_response, was_rejected = response_stability_filter.apply_filter(
                response=agent_response,
                fallback=fallback_reply
            )

            if was_rejected:
                logger.info(f"🛡️ [STABILITY FALLBACK] Replaced AI-like response for {session_id}")

            logger.info(
                f"🤖 Agent response for {session_id}: "
                f"turn {total_messages}, phase: {session.state}, missing: {missing_intel}, "
                f"llm_available: {is_llm_available()}"
            )

        else:
            # No scam detected - neutral response
            agent_response = "Thank you for your message. How can I help you today?"
            logger.info(f"Neutral response for {session_id} (no scam detected)")

        # ====================================================================
        # STEP 6: Check Finalization Criteria
        # ====================================================================

        if session.is_scam and session_manager.is_finalized(session_id):
            # Transition to FINALIZED state
            session_manager.transition_state(session_id, SessionStateEnum.FINALIZED)
            logger.info(
                f"🏁 Session {session_id} FINALIZED at turn {total_messages}"
            )

        # ====================================================================
        # STEP 7: Callback Trigger (ONLY if FINALIZED)
        # ====================================================================

        callback_status = session_manager.should_send_callback(session_id, msg_index)

        if callback_status["send"]:
            callback_type = callback_status["type"]
            logger.info(f"🎯 Callback condition met for {session_id}: {callback_type}")

            # Send callback with scammer profile
            # ELITE FIX: total_messages reflects (history + current_message).
            # We add 1 to account for the agent_response we just generated.
            callback_success = send_callback_with_retry(
                session_id=session_id,
                scam_detected=session.is_scam,
                total_messages=total_messages + 1,
                extracted_intelligence=session.extracted_intelligence,
                scam_type=session.scam_type,
                scammer_profile=session.scammer_profile,
                max_retries=3,
                status=callback_type
            )

            if callback_success:
                session_manager.mark_callback_sent(session_id, callback_type)
                logger.info(f"✅ {callback_type.capitalize()} callback sent for {session_id}")

                # LOG: Record final callback for test analysis
                test_logger.finalize_session(
                    session_id=session_id,
                    callback_data={
                        "scamDetected": session.is_scam,
                        "totalMessagesExchanged": total_messages,
                        "extractedIntelligence": session.extracted_intelligence,
                        "callback_type": callback_type
                    }
                )
            else:
                logger.error(f"❌ Callback failed for {session_id}")

        # Comprehensive per-turn logging
        intel_count = sum(len(v) for v in session.intel_graph.values())
        logger.info(
            f"\n========== TURN {total_messages} SUMMARY - {session_id} ==========\n"
            f"State: {session.state}\n"
            f"Scam Type: {session.scam_type}\n"
            f"Intelligence Items: {intel_count}\n"
            f"Extracted This Turn: {[r.type for r in extracted_list]}\n"
            f"Missing Intel: {missing_intel if session.is_scam else 'N/A'}\n"
            f"Callback Sent: {session.callback_sent}\n"
            f"=========================================================="
        )

        # ====================================================================
        # STEP 8: Log Platform Test Data + Return Official Response Format
        # ====================================================================

        # CRITICAL: Return ONLY status and reply (no extra fields)
        response = HoneypotResponse(
            status="success",
            reply=agent_response
        )

        # LOG: Capture platform test data
        test_logger.log_request(
            session_id=session_id,
            request_data=request.dict(),
            response_data=response.dict()
        )

        return response

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


@app.get("/debug/session/{session_id}")
async def get_session_debug(session_id: str, api_key: str = Depends(verify_api_key)):
    """
    DEBUG ENDPOINT: Get full state of a specific session.
    Use this to verify what intelligence was extracted.
    """
    session = session_manager.get_session(session_id)
    if not session:
        return {"status": "error", "message": "Session not found"}

    return {
        "status": "success",
        "session": {
            "is_scam": session.is_scam,
            "message_count": session.message_count,
            "extracted_intelligence": session.extracted_intelligence,
            "callback_sent": session.callback_sent
        }
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
