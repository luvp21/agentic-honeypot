"""
Session Manager for Honeypot System
Manages session state using sessionId as primary key
"""

from typing import Dict, Optional
from datetime import datetime
from models import SessionState


class SessionManager:
    """
    Manages conversation sessions.
    Stateless design - can reconstruct state from conversationHistory.
    """

    def __init__(self):
        # In-memory session store: {sessionId: SessionState}
        # In production, replace with Redis/database
        self.sessions: Dict[str, SessionState] = {}

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

        for key, value in updates.items():
            if hasattr(session, key):
                setattr(session, key, value)

        session.last_updated = datetime.utcnow()
        return session

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
        return len(conversation_history) + 1

    def should_send_callback(self, session_id: str, min_messages: int = 5) -> bool:
        """
        Determine if callback should be sent for this session.

        INTELLIGENT TRIGGER: Sends callback when sufficient intelligence is extracted,
        not at a fixed message count. This adapts to conversation length.

        Conditions:
        - Scam must be detected
        - Minimum message threshold met (default: 5)
        - Sufficient intelligence extracted (see has_sufficient_intelligence)
        - Callback not already sent

        Args:
            session_id: Session to check
            min_messages: Minimum messages before callback (default: 5)

        Returns:
            True if callback should be sent, False otherwise
        """
        session = self.get_or_create_session(session_id)

        # Check basic conditions
        if not session.is_scam:
            return False

        if session.callback_sent:
            return False

        if session.message_count < min_messages:
            return False

        # INTELLIGENT TRIGGER: Check if we have sufficient intelligence
        return self._has_sufficient_intelligence(session)

    def _has_sufficient_intelligence(self, session: 'SessionState') -> bool:
        """
        Determine if enough intelligence has been extracted to send callback.

        Intelligence is considered "sufficient" if we have:
        - At least 2 different types of critical data (UPIs, bank accounts, phishing links)
        - OR at least 3 total intelligence items

        This ensures we don't send empty/low-value callbacks.

        Args:
            session: Session to check

        Returns:
            True if sufficient intelligence extracted
        """
        intel = session.extracted_intelligence

        # Count critical intelligence types
        critical_types = 0
        total_items = 0

        # Critical data types that indicate scammer has revealed payment info
        if intel.get("upi_ids"):
            critical_types += 1
            total_items += len(intel["upi_ids"])

        if intel.get("bank_accounts"):
            critical_types += 1
            total_items += len(intel["bank_accounts"])

        if intel.get("phishing_links"):
            critical_types += 1
            total_items += len(intel["phishing_links"])

        # Also count other valuable data
        if intel.get("phone_numbers"):
            total_items += len(intel["phone_numbers"])

        if intel.get("ifsc_codes"):
            total_items += len(intel["ifsc_codes"])

        # Send if we have at least 2 critical types OR 3+ total items
        return critical_types >= 2 or total_items >= 3

    def mark_callback_sent(self, session_id: str):
        """
        Mark callback as sent to prevent duplicate sends.

        Args:
            session_id: Session to mark
        """
        session = self.get_or_create_session(session_id)
        session.callback_sent = True

    def get_session_stats(self) -> dict:
        """
        Get statistics about all sessions.
        For monitoring/debugging purposes.

        Returns:
            Dictionary with session statistics
        """
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
