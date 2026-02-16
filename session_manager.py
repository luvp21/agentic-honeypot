"""
Session Manager for Honeypot System
Manages session state using sessionId as primary key with explicit state machine
"""

from typing import Dict, Optional, List
from datetime import datetime, timedelta
from models import SessionState, IntelItem, SessionStateEnum, MessageContent, ScammerProfile, EngagementStrategyEnum
from behavioral_profiler import BehavioralProfiler
import logging

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages conversation sessions with explicit state machine lifecycle.
    Tracks full conversation history and behavioral profiles.
    """

    def __init__(self):
        # In-memory session store: {sessionId: SessionState}
        # In production, replace with Redis/database
        self.sessions: Dict[str, SessionState] = {}

        # Behavioral profiler for scammer analysis
        self.profiler = BehavioralProfiler()

        # Configuration - Extract intelligence until turn 18-19 before finalizing
        self.SOFT_FINALIZE = 18   # Start trying to finalize with sufficient intel
        self.HARD_FINALIZE = 19    # Force finalization even without intel
        self.MAX_TURNS_THRESHOLD = 25  # Emergency safety net
        self.IDLE_TIMEOUT_SECONDS = 60  # Max idle time before finalization

    def get_or_create_session(self, session_id: str) -> SessionState:
        """
        Get existing session or create new one.

        Args:
            session_id: Unique session identifier from platform

        Returns:
            SessionState object
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionState(sessionId=session_id)

        return self.sessions[session_id]

    def get_session(self, session_id: str) -> Optional[SessionState]:
        """Get session if exists."""
        return self.sessions.get(session_id)

    def update_session(
        self,
        session_id: str,
        **updates
    ) -> SessionState:
        """
        Update session state with new data.

        Args:
            session_id: Session to update
            **updates: Key-value pairs to update

        Returns:
            Updated SessionState
        """
        session = self.get_or_create_session(session_id)

        # FREEZE: Ignore updates if already finalized (state machine stability)
        if session.state == SessionStateEnum.FINALIZED:
            logger.warning(
                f"🔒 [STATE FREEZE] Ignoring update to finalized session {session_id}. "
                f"Attempted updates: {list(updates.keys())}"
            )
            return session

        for key, value in updates.items():
            if hasattr(session, key):
                setattr(session, key, value)

        session.last_updated = datetime.utcnow()
        return session

    def apply_suspicion_decay(self, session_id: str, has_suspicious_signal: bool):
        """
        ELITE REFINEMENT 5: Suspicion Decay Mechanism

        Apply light decay for non-suspicious turns to prevent runaway suspicion.
        Decay only applied if:
        - No regex hit
        - No urgency term
        - No payment term
        - No injection detected

        Args:
            session_id: Session to decay
            has_suspicious_signal: Whether current message has suspicious indicators
        """
        session = self.get_or_create_session(session_id)

        # Only decay if session is active (not finalized) and no suspicious signal
        if session.state != SessionStateEnum.FINALIZED and not has_suspicious_signal:
            original_score = session.suspicion_score
            session.suspicion_score *= 0.9  # 10% decay
            session.suspicion_score = min(session.suspicion_score, 2.0)  # Maintain cap

            if original_score > 0.1:  # Only log meaningful decays
                logger.info(
                    f"🔄 [SUSPICION DECAY] {session_id}: {original_score:.2f} → {session.suspicion_score:.2f}"
                )

    def is_first_message(self, conversation_history: list) -> bool:
        """
        Check if this is the first message in the conversation.

        Args:
            conversation_history: List from request

        Returns:
            True if empty array (first message), False otherwise
        """
        return len(conversation_history) == 0

    def calculate_total_messages(self, conversation_history: list) -> int:
        """
        Calculate total messages exchanged.

        Args:
            conversation_history: List from request

        Returns:
            Total message count (history + current message)
        """
        # conversationHistory contains all previous messages
        # Add 1 for the current message
        # The history passed in is usually just the Scammer's turns or pairs?
        # Actually, if history is [Scammer, Agent, Scammer, Agent], then len is accurate.
        # But if it's counting "turns" (pairs), we want individual messages.

        # ELITE FIX: The 'message_count' in SessionState should reflect TOTAL EXCHANGES
        # User (Scammer) sends 1, Agent sends 1 = 2 messages per "turn".
        # If 'conversation_history' is a list of PAIRS or just Scammer messages?
        # Typically it's a list of dicts. If it includes Agent responses, len() is fine.
        # But if the caller only passes Scammer history, we need to estimate.

        # Assuming history is full conversation:
        return len(conversation_history) + 1

    def calculate_engagement_duration(self, session_id: str) -> int:
        """
        Calculate engagement duration in seconds from first to last message.
        CRITICAL for hackathon scoring - worth 10 points.

        Args:
            session_id: Session identifier

        Returns:
            Duration in seconds (0 if less than 2 messages)
        """
        session = self.get_session(session_id)
        if not session or not session.conversation_full or len(session.conversation_full) < 2:
            return 0

        try:
            # Get first and last message timestamps (epoch milliseconds)
            first_msg = session.conversation_full[0]
            last_msg = session.conversation_full[-1]

            # Convert epoch milliseconds to seconds
            first_time = first_msg.timestamp / 1000.0
            last_time = last_msg.timestamp / 1000.0

            # Calculate duration
            duration = int(last_time - first_time)

            # Ensure non-negative
            return max(0, duration)

        except (AttributeError, TypeError, ZeroDivisionError) as e:
            logger.error(f"Error calculating duration for {session_id}: {e}")
            return 0

    def transition_state(
        self,
        session_id: str,
        new_state: SessionStateEnum
    ) -> bool:
        """
        Transition session to new state with validation.
        Enforces proper state machine flow.

        Args:
            session_id: Session identifier
            new_state: Target state

        Returns:
            True if transition successful, False if invalid
        """
        session = self.get_or_create_session(session_id)
        old_state = session.state

        # Define valid transitions
        valid_transitions = {
            SessionStateEnum.INIT: [SessionStateEnum.SCAM_DETECTED],
            SessionStateEnum.SCAM_DETECTED: [SessionStateEnum.ENGAGING, SessionStateEnum.FINALIZED],
            SessionStateEnum.ENGAGING: [SessionStateEnum.EXTRACTING, SessionStateEnum.FINALIZED],
            SessionStateEnum.EXTRACTING: [SessionStateEnum.FINALIZED],
            SessionStateEnum.FINALIZED: []  # Terminal state
        }

        # Check if transition is valid
        if new_state not in valid_transitions.get(old_state, []):
            logger.warning(
                f"Invalid state transition for {session_id}: "
                f"{old_state} → {new_state}"
            )
            return False

        # Perform transition
        session.state = new_state
        session.last_updated = datetime.utcnow()

        logger.info(
            f"State transition for {session_id}: {old_state} → {new_state}"
        )

        return True

    def is_finalized(self, session_id: str) -> bool:
        """
        Check if session should be finalized based on thresholds.

        PRODUCTION REFINEMENTS - Less Rigid Termination:
        A) No new intel for 3 turns AND totalTurns >= 8
        B) Hard limit at 15 turns
        C) Extracted unique intelligence types >= 3 AND totalTurns >= 8 (ELITE FIX: balanced)
        D) Idle timeout exceeded (60s)
        E) Already in FINALIZED state

        Args:
            session_id: Session to check

        Returns:
            True if should finalize
        """
        session = self.get_or_create_session(session_id)

        # Already finalized
        if session.state == SessionStateEnum.FINALIZED:
            return True

        # Not a scam - don't finalize
        if not session.is_scam:
            return False

        # Intelligent finalization based on turn count and intelligence gathered
        intel_count = sum(len(items) for items in session.intel_graph.values())

        # Soft finalization: have good intel and reached soft limit (18 turns)
        if session.message_count >= self.SOFT_FINALIZE and intel_count >= 5:
            logger.info(
                f"✅ Session {session_id} reached soft limit ({self.SOFT_FINALIZE} turns) "
                f"with {intel_count} intel items - finalizing"
            )
            return True

        # Hard finalization: reached hard limit (19 turns) regardless of intel
        if session.message_count >= self.HARD_FINALIZE:
            logger.info(
                f"⏱️ Session {session_id} reached hard limit ({self.HARD_FINALIZE} turns) - "
                f"force finalizing with {intel_count} intel items"
            )
            return True

        # Emergency Safety Net (25 turns) - prevents infinite loops
        if session.message_count >= self.MAX_TURNS_THRESHOLD:
            logger.warning(
                f"⚠️ Session {session_id} reached emergency safety limit: {session.message_count} turns. "
                "This should rarely happen - check if finalization logic is working."
            )
            return True

        # Criterion D: Idle timeout - if scammer stops replying, finalize with whatever intel we have
        # Shorter timeout if we already have some intelligence (scammer went silent)
        has_any_intel = any(session.intel_graph.values())
        idle_timeout_threshold = 30 if has_any_intel else self.IDLE_TIMEOUT_SECONDS

        idle_time = datetime.utcnow() - session.last_activity_time
        if idle_time.total_seconds() >= idle_timeout_threshold:
            logger.info(
                f"Session {session_id} exceeded idle timeout: {idle_time.total_seconds()}s "
                f"(threshold: {idle_timeout_threshold}s, has_intel: {has_any_intel})"
            )
            return True

        # Criterion C: ENHANCED - Wait for ALL possible intel extraction
        # Check all trackable intelligence types
        has_links = bool(session.intel_graph.get("phishing_links")) or bool(session.intel_graph.get("short_urls"))
        has_ifsc = bool(session.intel_graph.get("ifsc_codes"))
        has_phone = bool(session.intel_graph.get("phone_numbers"))
        has_upi = bool(session.intel_graph.get("upi_ids"))
        has_bank = bool(session.intel_graph.get("bank_accounts"))
        has_email = bool(session.intel_graph.get("email_addresses"))
        has_telegram = bool(session.intel_graph.get("telegram_ids"))

        # Count ALL intel types we've extracted
        critical_count = sum([has_links, has_ifsc, has_phone, has_upi, has_bank, has_email, has_telegram])
        unique_intel_types = sum(1 for items in session.intel_graph.values() if items)

        # If ANYTHING is missing from the critical 6 (phone, UPI, bank, email, IFSC, links), delay callback
        # NEW: Added email to core critical types (was missing before!)
        core_critical = [has_phone, has_upi, has_bank, has_email, has_ifsc, has_links]
        missing_count = sum(1 for x in core_critical if not x)

        # HIGH-PRIORITY intel types (most valuable for investigation)
        high_priority = [has_links, has_phone, has_upi]
        high_priority_count = sum(1 for x in high_priority if x)
        missing_high_priority = sum(1 for x in high_priority if not x)

        # Only finalize if:
        # 1. We have ALL 6 core critical types AND ALL 3 high-priority types AND reached turn 16+
        #    (give more time to collect MULTIPLE items per high-value type)
        # 2. We have ALL 6 types but missing high-priority → wait until turn 17
        # 3. We have 5+ types AND reached turn 18 (very close to hard limit)
        # PRIORITY: Links, Phone Numbers, UPI IDs are most valuable - wait longer to get multiples

        if missing_count == 0 and missing_high_priority == 0 and session.message_count >= 16:
            # Have everything including all high-priority types
            logger.info(
                f"Session {session_id} extracted ALL 6 core intel types (including high-priority) at turn {session.message_count}"
            )
            return True
        elif missing_count == 0 and session.message_count >= 17:
            # Have all 6 types but give extra time for high-priority items
            logger.info(
                f"Session {session_id} extracted ALL 6 core intel types at turn {session.message_count}"
            )
            return True
        elif unique_intel_types >= 5 and session.message_count >= 18:
            logger.info(
                f"Session {session_id} extracted {unique_intel_types} intel types at turn {session.message_count} (near limit)"
            )
            return True

        # Criterion A: No new intel for X turns AND turns >= Y
        # Only trigger if we're very close to hard limit (turn 18+)
        min_turns_a = 18
        stall_threshold = 5  # More patience for stalled extraction

        turns_since_new_intel = session.message_count - session.last_new_intel_turn
        if turns_since_new_intel >= stall_threshold and session.message_count >= min_turns_a:
            logger.info(
                f"Intelligent termination for {session_id}: "
                f"no new intel for {turns_since_new_intel} turns, total={session.message_count}"
            )
            return True

        return False

    def update_scammer_profile(
        self,
        session_id: str,
        message: str,
        scam_type: str = None
    ) -> None:
        """
        Update behavioral profile based on scammer message.

        Args:
            session_id: Session identifier
            message: Scammer message text
            scam_type: Detected scam type (optional)
        """
        session = self.get_or_create_session(session_id)

        # Update profile using behavioral profiler
        session.scammer_profile = self.profiler.update_profile(
            session.scammer_profile,
            message,
            scam_type
        )

        session.last_updated = datetime.utcnow()

    def update_strategy(self, session_id: str, is_prompt_injection: bool = False) -> str:
        """
        PRODUCTION REFINEMENT: Strategy Escalation Engine

        Escalation ladder: CONFUSION → TECHNICAL_CLARIFICATION → FRUSTRATED_VICTIM → AUTHORITY_CHALLENGE
        Escalate after 2 turns of stalled extraction.

        Logic:
        - Prompt Injection → SAFETY_DEFLECT (protect persona)
        - Otherwise: Use escalation ladder based on session.strategy_level
        - Escalate when extraction stalls for 2+ turns
        """
        session = self.get_or_create_session(session_id)
        profile = session.scammer_profile

        # 0. Prompt Injection Check (Top Priority)
        if is_prompt_injection:
            session.engagement_strategy = EngagementStrategyEnum.SAFETY_DEFLECT
            return "SAFETY_DEFLECT"

        # Check for extraction stall (2+ turns without new intel)
        # ELITE FIX: Don't escalate before turn 4 to maintain natural tone
        turns_since_new_intel = session.message_count - session.last_new_intel_turn
        if turns_since_new_intel >= 2 and session.message_count >= 4:
            # Escalate strategy level
            session.strategy_level = min(session.strategy_level + 1, 3)
            logger.info(
                f"Strategy escalated to level {session.strategy_level} "
                f"(stalled for {turns_since_new_intel} turns)"
            )

        # Define escalation ladder
        escalation_ladder = [
            "CONFUSION",                  # Level 0: Basic stalling
            "TECHNICAL_CLARIFICATION",    # Level 1: Fish for details
            "FRUSTRATED_VICTIM",          # Level 2: Pressure reversal
            "AUTHORITY_CHALLENGE"         # Level 3: Demand verification
        ]

        # Select strategy from ladder
        new_strategy = escalation_ladder[session.strategy_level]

        # Update session
        if new_strategy in EngagementStrategyEnum.__members__:
            session.engagement_strategy = EngagementStrategyEnum(new_strategy)

        return session.engagement_strategy

    def store_full_message(
        self,
        session_id: str,
        message: MessageContent
    ) -> None:
        """
        Store complete message in session history for backfill extraction.

        Args:
            session_id: Session identifier
            message: Message to store
        """
        session = self.get_or_create_session(session_id)
        session.conversation_full.append(message)
        session.last_activity_time = datetime.utcnow()
        session.last_updated = datetime.utcnow()

    def update_idle_time(self, session_id: str) -> None:
        """
        Update last activity time for idle detection.

        Args:
            session_id: Session identifier
        """
        session = self.get_or_create_session(session_id)
        session.last_activity_time = datetime.utcnow()

    def update_intel_graph(self, session_id: str, new_intel_list: list) -> None:
        """
        Update session's intelligence graph with new extraction results.
        PRODUCTION REFINEMENT: Track last_new_intel_turn for termination logic.

        Args:
            session_id: Session identifier
            new_intel_list: List of RawIntel objects from extractor
        """
        session = self.get_or_create_session(session_id)
        new_intel_added = False

        for raw_item in new_intel_list:
            # Normalized value for deduplication (remove spaces, lowercase)
            norm_value = raw_item.value.lower().strip()
            if raw_item.type in ["bank_accounts", "phone_numbers", "ifsc_codes"]:
                 norm_value = "".join(filter(str.isalnum, norm_value))

            # Check if this value already exists in the graph for this type
            existing_items = session.intel_graph.get(raw_item.type, [])
            match_found = False

            for item in existing_items:
                # Compare normalized values
                item_norm = item.value.lower().strip()
                if raw_item.type in ["bank_accounts", "phone_numbers", "ifsc_codes"]:
                    item_norm = "".join(filter(str.isalnum, item_norm))

                if item_norm == norm_value:
                    # Update existing item
                    match_found = True

                    # Log source if new
                    if raw_item.source not in item.sources:
                        item.sources.append(raw_item.source)

                    if item.confidence < 2.0:
                        # Only update timestamp if we are still building confidence
                        # This prevents "Stability Deadlock" where repetitive high-conf intel
                        # keeps last_seen_msg fresh, preventing the stability window from closing.
                        item.last_seen_msg = max(item.last_seen_msg, raw_item.message_index)

                        item.confidence += 0.3
                        item.confidence = min(item.confidence, 2.0)

                    break

            if not match_found:
                # Create new IntelItem
                new_intel_added = True
                # Base confidence depends on source/validation
                confidence = 1.0  # Default base for valid extraction

                # Apply delta from extractor (e.g., +0.5 for context, -0.2 for fallback)
                confidence += raw_item.confidence_delta

                # Cap/Floor
                confidence = max(0.1, min(confidence, 2.0))

                new_item = IntelItem(
                    value=raw_item.value,
                    type=raw_item.type,
                    confidence=confidence,
                    first_seen_msg=raw_item.message_index,
                    last_seen_msg=raw_item.message_index,
                    sources=[raw_item.source]
                )

                if raw_item.type not in session.intel_graph:
                    session.intel_graph[raw_item.type] = []
                session.intel_graph[raw_item.type].append(new_item)

        # PRODUCTION REFINEMENT: Update last_new_intel_turn
        # Reset stall counter if ANY intel was extracted (new or re-confirmed)
        # This prevents premature finalization when scammer repeats info
        if new_intel_added:
            session.intel_stall_counter = 0
            session.last_new_intel_turn = session.message_count
            logger.info(
                f"New intel extracted for {session_id} at turn {session.message_count}"
            )
        elif new_intel_list:  # Intel was extracted but it was duplicates
            # Don't fully reset, but slow down the stall counter growth
            # This acknowledges the scammer is still engaging with data
            if session.intel_stall_counter > 0:
                session.intel_stall_counter -= 1
            logger.info(
                f"Intel re-confirmed for {session_id} at turn {session.message_count} (stall counter: {session.intel_stall_counter})"
            )

        # Update backward compatibility dict
        self._sync_backward_compat(session)
        session.last_updated = datetime.utcnow()

    def _sync_backward_compat(self, session: SessionState):
        """Sync intel_graph to extracted_intelligence for backward compatibility."""
        flat_dict = {}
        for type_key, items in session.intel_graph.items():
            flat_dict[type_key] = [item.value for item in items]
        session.extracted_intelligence = flat_dict

    def get_extracted_intel_types(self, session_id: str) -> List[str]:
        """Get list of intelligence types that have been extracted."""
        session = self.get_or_create_session(session_id)
        return [intel_type for intel_type, items in session.intel_graph.items() if items]

    def should_send_callback(self, session_id: str, current_msg_index: int) -> dict:
        """
        NEW LOGIC: Only send callback if session is FINALIZED.

        This ensures maximum engagement before callback.
        Callback sent when:
        1. State == FINALIZED (via is_finalized() checks)
        2. Callback not already sent
        3. Has minimum intelligence

        Returns:
            {"send": bool, "type": "final"}
        """
        session = self.get_or_create_session(session_id)

        # Must be scam
        if not session.is_scam:
            return {"send": False, "type": "none"}

        # Already sent
        if session.callback_sent:
            return {"send": False, "type": "none"}

        # Must be in FINALIZED state
        if session.state != SessionStateEnum.FINALIZED:
            return {"send": False, "type": "none"}

        # Check if we have ANY intelligence (even minimal)
        has_intel = False
        for items in session.intel_graph.values():
            if items:
                has_intel = True
                break

        if not has_intel:
            logger.warning(
                f"Session {session_id} finalized but no intelligence extracted"
            )
            # Still send callback to report the scam even without intel

        logger.info(
            f"Callback trigger for {session_id}: "
            f"State={session.state}, Messages={session.message_count}, "
            f"Intel types={len(session.intel_graph)}"
        )

        return {"send": True, "type": "completed"}

    def mark_callback_sent(self, session_id: str, phase: str):
        """Update callback phase."""
        session = self.get_or_create_session(session_id)
        session.callback_phase = phase
        session.callback_sent = True  # Legacy flag

    def get_session_stats(self) -> dict:
        """Get statistics about all sessions."""
        total_sessions = len(self.sessions)
        scam_sessions = sum(1 for s in self.sessions.values() if s.is_scam)
        callbacks_sent = sum(1 for s in self.sessions.values() if s.callback_sent)

        return {
            "total_sessions": total_sessions,
            "scam_sessions": scam_sessions,
            "callbacks_sent": callbacks_sent,
            "active_sessions": total_sessions - callbacks_sent
        }


# Global session manager instance
session_manager = SessionManager()
