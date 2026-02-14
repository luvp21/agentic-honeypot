"""
Test Logger - Minimal stub for production deployment
Provides no-op logging interface to prevent import errors
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class TestLogger:
    """Minimal test logger stub for production deployment"""

    def __init__(self):
        self.enabled = False

    def log_request(self, session_id: str, request_data: Dict[str, Any], response_data: Dict[str, Any]) -> None:
        """No-op request logging"""
        pass

    def finalize_session(self, session_id: str, callback_data: Dict[str, Any]) -> None:
        """No-op session finalization"""
        pass


# Global instance
test_logger = TestLogger()
