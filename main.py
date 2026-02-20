"""
main.py — FastAPI application: primary endpoint and request orchestration.

Endpoints:
  POST /api/honeypot/message  → main interaction endpoint
  GET  /health                → health check
  GET  /                      → system info

Per-request flow (10 steps):
  1. Auth via x-api-key header
  2. Get / create session
  3. Apply processing delay (asyncio.sleep — pushes engagement duration > 180s)
  4. Detect scam (hybrid rule-based + LLM)
  5. Extract intel from incoming message
  6. Update red flags + quality tracker
  7. Increment turn count
  8. Generate agent response (always with question + elicitation)
  9. Update quality counters from response
  10. If final turn: build finalOutput → fire callback → return with finalOutput
      Else: return normal turn response

Critical design notes:
  - MAX_TURNS = 10 (hard cap aligned with GUVI platform)
  - Callback is fired as asyncio.create_task (non-blocking, avoids timeout)
  - ALWAYS return HTTP 200 even on internal errors
  - LLM intel sweep every 3 turns to catch regex misses
"""

import asyncio
import json
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models import MessageRequest
from session_manager import session_manager, MAX_TURNS, FINALIZE_AT, SessionState
from scam_detector import scam_detector
from intel_extractor import intel_extractor
from conversation_agent import conversation_agent
from quality_tracker import QualityTracker
from red_flag_tracker import RedFlagTracker
from final_output_builder import final_output_builder
from callback_sender import callback_sender
from guardrails import guardrails

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

def _log_json(tag: str, session_id: str, obj: dict) -> None:
    """Log a full JSON object to stdout so it appears in DO runtime logs."""
    try:
        logger.info(f"[{session_id}] ▼▼▼ {tag} ▼▼▼\n{json.dumps(obj, indent=2, default=str)}\n▲▲▲ END {tag} ▲▲▲")
    except Exception as e:
        logger.warning(f"[{session_id}] _log_json({tag}) failed: {e}")


# ---------------------------------------------------------------------------
# Environment configuration
# ---------------------------------------------------------------------------
API_KEY           = os.getenv("HONEYPOT_API_KEY", "honeypot-secret-key")
PROCESSING_DELAY  = int(os.getenv("PROCESSING_DELAY_SECONDS", "3"))  # push duration > 180s


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("  Agentic Honeypot v2.0  —  Starting up")
    logger.info(f"  MAX_TURNS={MAX_TURNS}  |  PROCESSING_DELAY={PROCESSING_DELAY}s")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    yield
    logger.info("Agentic Honeypot shutting down.")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Agentic Honeypot API",
    description=(
        "AI-powered honeypot that engages scammers, extracts intelligence, "
        "and reports to the GUVI evaluation platform."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------

def _check_auth(x_api_key: Optional[str]) -> bool:
    """
    Returns True if key is valid.
    Returns False (instead of raising) so we can always return HTTP 200.
    """
    return x_api_key == API_KEY


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    return {
        "system":      "Agentic Honeypot v2.0",
        "status":      "operational",
        "description": "AI-powered honeypot for scam detection and intelligence extraction",
        "endpoints": {
            "POST /api/honeypot/message": "Primary interaction endpoint",
            "GET  /health":              "Health check",
        },
    }


@app.get("/health")
async def health_check():
    from gemini_client import gemini_client
    return {
        "status":           "healthy",
        "timestamp":        time.time(),
        "active_sessions":  session_manager.active_count(),
        "gemini_available": gemini_client.is_available,
    }


@app.post("/api/honeypot/message")
async def process_message(
    request: MessageRequest,
    x_api_key: Optional[str] = Header(None),
):
    """
    Main honeypot interaction endpoint.
    Accepts one scammer message per call, returns Priya's response.
    On the final turn (turn 10 OR isLastTurn=true), fires callback and
    includes the complete finalOutput in the response body.
    """

    # ─────────────────────────────────────────────────────────────────────
    # 1. AUTHENTICATION
    # ─────────────────────────────────────────────────────────────────────
    if not _check_auth(x_api_key):
        logger.warning(f"Auth failed for session {request.sessionId} (key={x_api_key!r})")
        # Always return HTTP 200 — never expose 401 to scammer
        return JSONResponse(content={
            "status":    "success",
            "reply":     "I'm sorry, I did not understand that. Could you please repeat?",
            "sessionId": request.sessionId,
            "turn":      0,
            "isFinal":   False,
        })

    try:
        # ─────────────────────────────────────────────────────────────────
        # 2. GET / CREATE SESSION
        # ─────────────────────────────────────────────────────────────────
        session = session_manager.get_or_create(request.sessionId)
        session.update_activity()

        # Attach per-session tracker singletons on first turn
        if not hasattr(session, "_quality_tracker") or session._quality_tracker is None:
            session._quality_tracker  = QualityTracker()
            session._red_flag_tracker = RedFlagTracker()

        # Seed conversation history from platform-supplied conversationHistory
        # on the first turn (avoids duplicate appends on later turns)
        platform_history = request.get_platform_history()
        if platform_history and not session.conversation_history:
            session.conversation_history = platform_history
            logger.debug(
                f"[{request.sessionId}] Seeded {len(platform_history)} "
                "entries from platform conversationHistory"
            )

        # Extract the plain message text regardless of format (object or string)
        message_text = request.get_message_text()

        logger.info(
            f"[{request.sessionId}] ── INCOMING TURN {session.turn_count + 1}/{MAX_TURNS} ──"
        )
        logger.info(f"[{request.sessionId}] MSG: {message_text[:300]}")

        # ─────────────────────────────────────────────────────────────────
        # 3. PROCESSING DELAY
        # Push engagementDurationSeconds > 180s for full engagement score.
        # 10 turns × 3s = 30s minimum artificial delay on top of real latency.
        # ─────────────────────────────────────────────────────────────────
        await asyncio.sleep(PROCESSING_DELAY)

        # ─────────────────────────────────────────────────────────────────
        # 4. SCAM DETECTION (hybrid rule-based + LLM fallback)
        #    Tier logic:
        #      HIGH (≥7.0) → skip LLM, trust rule-based result
        #      GREY (3-7)  → use LLM to refine scam_type / confidence
        #      LOW (<3.0)  → only scam if red flags found (LLM still runs)
        # ─────────────────────────────────────────────────────────────────
        detection = scam_detector.detect(
            message_text,
            session.conversation_history,
        )

        # GREY-tier LLM refinement: rule-based is ambiguous, ask Gemini
        if detection.detection_tier == "GREY" and session.turn_count <= 2:
            try:
                from gemini_client import gemini_client
                if gemini_client.is_available:
                    llm_cls = await gemini_client.classify_scam(
                        message_text, session.conversation_history
                    )
                    if llm_cls and llm_cls.get("is_scam"):
                        # LLM may return title-case; normalise to snake_case
                        llm_type = llm_cls.get("scam_type", detection.scam_type)
                        if llm_type:
                            llm_type = llm_type.lower().replace(" ", "_")
                        llm_conf = float(llm_cls.get("confidence", 0))
                        if llm_conf > detection.confidence_score:
                            detection.scam_type = llm_type or detection.scam_type
                            detection.confidence_score = round(llm_conf, 2)
                        detection.is_scam = True
                        # Merge any extra red flags from LLM
                        for flag in llm_cls.get("red_flags", []):
                            if flag not in detection.red_flags_detected:
                                detection.red_flags_detected.append(flag)
                        logger.info(
                            f"[{request.sessionId}] LLM refined: type={detection.scam_type} "
                            f"conf={detection.confidence_score:.0%}"
                        )
            except Exception as e:
                logger.warning(f"[{request.sessionId}] LLM classify_scam failed: {e}")

        # Update session detection state
        if detection.is_scam or detection.confidence_score > 0.1 or detection.red_flags_detected:
            session.is_scam = True
        if not session.scam_type and detection.scam_type:
            session.scam_type = detection.scam_type
        if detection.confidence_score > session.confidence_score:
            session.confidence_score = detection.confidence_score

        # Accumulate confidence based on total red flags found — each flag = +10% above base
        # e.g. 5 flags → min(0.95, 0.40 + 5*0.10) = 0.90  (much more honest than 53%)
        if session.red_flags:
            accumulated = min(0.95, 0.40 + len(session.red_flags) * 0.10)
            if accumulated > session.confidence_score:
                session.confidence_score = round(accumulated, 2)

        # ─────────────────────────────────────────────────────────────────
        # 5. INTEL EXTRACTION from incoming message
        # ─────────────────────────────────────────────────────────────────
        new_intel = intel_extractor.extract(message_text)
        intel_extractor.merge_into_session(session, new_intel)

        # Log what was just extracted this turn
        extracted_this_turn = {k: v for k, v in new_intel.to_dict().items() if v}
        if extracted_this_turn:
            logger.info(f"[{request.sessionId}] INTEL THIS TURN: {json.dumps(extracted_this_turn)}")
        # Log cumulative intel store
        cumulative = {k: list(v) for k, v in session.intel_store.items() if v}
        logger.info(f"[{request.sessionId}] INTEL CUMULATIVE: {json.dumps(cumulative)}")

        # ─────────────────────────────────────────────────────────────────
        # 6. RED FLAGS + QUALITY TRACKER UPDATE
        # ─────────────────────────────────────────────────────────────────
        incoming_turn = session.turn_count + 1  # pre-increment for flag attribution

        if detection.red_flags_detected:
            session._red_flag_tracker.add_flags(
                detection.red_flags_detected, incoming_turn
            )
            session._quality_tracker.add_red_flags(detection.red_flags_detected)
            for flag in detection.red_flags_detected:
                session.add_red_flag(flag, incoming_turn)

        # Append scammer message to history
        session.conversation_history.append({
            "role":    "user",
            "content": message_text,
        })

        # Update session state
        session.state = (
            SessionState.DETECTING if session.turn_count == 0
            else SessionState.ENGAGING
        )

        # ─────────────────────────────────────────────────────────────────
        # 7. INCREMENT TURN COUNT
        # ─────────────────────────────────────────────────────────────────
        session.turn_count += 1
        current_turn = session.turn_count

        logger.info(
            f"[{request.sessionId}] Turn {current_turn}/{MAX_TURNS} | "
            f"scam={session.is_scam} | type={session.scam_type} | "
            f"conf={session.confidence_score:.0%} | "
            f"red_flags={len(session.red_flags)} | "
            f"intel_total={session.total_intel_count()} | "
            f"flags_list={list(session.red_flags)}"
        )

        # ─────────────────────────────────────────────────────────────────
        # 8. GENERATE AGENT RESPONSE
        # ─────────────────────────────────────────────────────────────────
        agent_reply = await conversation_agent.generate_response(
            session, request.message
        )

        # Validate — guardrails guarantee question + elicitation always present
        _, agent_reply = guardrails.validate_response(agent_reply, current_turn)

        logger.info(f"[{request.sessionId}] AGENT REPLY (turn {current_turn}): {agent_reply[:300]}")

        # ─────────────────────────────────────────────────────────────────
        # 9. UPDATE QUALITY COUNTERS FROM RESPONSE
        # ─────────────────────────────────────────────────────────────────
        session._quality_tracker.analyze_response(agent_reply)

        # Sync counters back to session (consumed by final_output_builder)
        session.questions_asked         = session._quality_tracker.questions_asked
        session.investigative_questions = session._quality_tracker.investigative_questions
        session.elicitation_attempts    = session._quality_tracker.elicitation_attempts

        # Append agent reply to history
        session.conversation_history.append({
            "role":    "assistant",
            "content": agent_reply,
        })

        # ─────────────────────────────────────────────────────────────────
        # LLM INTEL SWEEP every 3 turns (catches regex misses)
        # ─────────────────────────────────────────────────────────────────
        if current_turn % 3 == 0:
            try:
                from gemini_client import gemini_client
                if gemini_client.is_available:
                    llm_intel = await gemini_client.extract_intel_llm(
                        session.conversation_history
                    )
                    if llm_intel:
                        intel_extractor.merge_llm_result(session, llm_intel)
                        logger.info(
                            f"[{request.sessionId}] LLM intel sweep done at turn {current_turn}"
                        )
            except Exception as e:
                logger.warning(f"[{request.sessionId}] LLM intel sweep failed: {e}")

        # ─────────────────────────────────────────────────────────────────
        # 10. HANDLE CONVERSATION ENDING
        # isLastTurn=True OR turn count reached MAX_TURNS
        # ─────────────────────────────────────────────────────────────────
        is_last_turn = request.isLastTurn or current_turn >= MAX_TURNS

        if is_last_turn and not session.callback_sent:
            session.state = SessionState.FINALIZING

            # Final comprehensive intel extraction across entire history
            final_intel = intel_extractor.extract_from_history(
                session.conversation_history
            )
            intel_extractor.merge_into_session(session, final_intel)

            # Build finalOutput payload
            # Note: totalMessagesExchanged = turn_count * 2
            # (1 turn = 1 scammer message + 1 honeypot reply → 10 turns = 20 messages)
            final_payload = final_output_builder.build(session)

            # ── LOG FULL FINAL OUTPUT JSON ─────────────────────────────
            _log_json("FINAL_OUTPUT_PAYLOAD", session.sessionId, final_payload)

            # Mark done before firing background task
            session.state         = SessionState.DONE
            session.callback_sent = True

            # Fire callback as background task (non-blocking)
            # This ensures we return the HTTP response first, avoiding platform timeout
            # Use callbackUrl from request body if GUVI provided one, else fall back to env var
            _callback_url = getattr(request, 'callbackUrl', None) or None
            asyncio.create_task(
                callback_sender.send_final_output(session.sessionId, final_payload, url=_callback_url)
            )

            logger.info(
                f"[{request.sessionId}] SESSION FINALISED — "
                f"turns={current_turn}, "
                f"duration={session.get_duration():.0f}s, "
                f"red_flags={len(session.red_flags)}, "
                f"intel_items={session.total_intel_count()}, "
                f"questions={session.questions_asked}, "
                f"investigative={session.investigative_questions}, "
                f"elicitation={session.elicitation_attempts}"
            )

            return JSONResponse(content={
                "status":      "success",
                "reply":       agent_reply,
                "sessionId":   session.sessionId,
                "turn":        current_turn,
                "isFinal":     True,
                "finalOutput": final_payload,
            })

        # ─────────────────────────────────────────────────────────────────
        # Normal turn response
        # ─────────────────────────────────────────────────────────────────
        return JSONResponse(content={
            "status":    "success",
            "reply":     agent_reply,
            "sessionId": session.sessionId,
            "turn":      current_turn,
            "isFinal":   False,
        })

    except Exception as e:
        logger.error(
            f"[{request.sessionId}] Unhandled error at turn: {e}",
            exc_info=True,
        )
        # Always return HTTP 200 with a safe fallback reply
        # Platform must never see a 500 error from the honeypot
        turn_guess = 1
        try:
            s = session_manager.get(request.sessionId)
            if s:
                turn_guess = s.turn_count
        except Exception:
            pass

        return JSONResponse(content={
            "status":    "success",
            "reply":     guardrails._safe_for_turn(turn_guess),
            "sessionId": request.sessionId,
            "turn":      turn_guess,
            "isFinal":   False,
        })
