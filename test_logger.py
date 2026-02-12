"""
Request Logger Middleware for Honeypot API
==========================================

Captures all incoming requests and responses from hackathon platform testing.
Stores them for later analysis and metrics generation.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from functools import wraps


class TestDataLogger:
    """Logs all API interactions for analysis"""

    def __init__(self, log_dir: str = "platform_test_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.current_session_logs = {}

    def log_request(self, session_id: str, request_data: Dict[str, Any], response_data: Dict[str, Any]):
        """Log a single API request-response pair"""

        # Initialize session log if first message
        if session_id not in self.current_session_logs:
            self.current_session_logs[session_id] = {
                "session_id": session_id,
                "started_at": datetime.now().isoformat(),
                "exchanges": [],
                "metadata": request_data.get("metadata", {})
            }

        # Extract the message details
        message = request_data.get("message", {})
        conversation_history = request_data.get("conversationHistory", [])

        # Log this exchange
        exchange = {
            "turn": len(self.current_session_logs[session_id]["exchanges"]) + 1,
            "timestamp": datetime.now().isoformat(),
            "incoming_message": {
                "sender": message.get("sender"),
                "text": message.get("text"),
                "timestamp": message.get("timestamp")
            },
            "agent_response": {
                "status": response_data.get("status"),
                "reply": response_data.get("reply")
            },
            "conversation_length": len(conversation_history)
        }

        self.current_session_logs[session_id]["exchanges"].append(exchange)

        # Save updated session log
        self._save_session_log(session_id)

    def _save_session_log(self, session_id: str):
        """Save session log to file AND print to stdout for cloud persistence"""
        if session_id in self.current_session_logs:
            # 1. Save to local file (ephemeral in cloud, persistent if local)
            log_file = self.log_dir / f"{session_id}.json"
            try:
                with open(log_file, 'w') as f:
                    json.dump(self.current_session_logs[session_id], indent=2, fp=f)
            except Exception as e:
                pass # Ignore file write errors in read-only environments

            # 2. Print to stdout with delimiters for easy extraction from HF Logs
            # Only print on completion or major updates to avoid log spam
            if "total_exchanges" in self.current_session_logs[session_id]:
                log_data = json.dumps(self.current_session_logs[session_id])
                print(f"\n@@@TEST_LOG_START@@@\n{log_data}\n@@@TEST_LOG_END@@@\n", flush=True)

    def finalize_session(self, session_id: str, callback_data: Dict[str, Any] = None):
        """Mark session as complete and log final callback data"""
        if session_id in self.current_session_logs:
            self.current_session_logs[session_id]["ended_at"] = datetime.now().isoformat()
            self.current_session_logs[session_id]["total_exchanges"] = len(
                self.current_session_logs[session_id]["exchanges"]
            )

            if callback_data:
                self.current_session_logs[session_id]["final_callback"] = callback_data

            self._save_session_log(session_id)

            # Can remove from memory after finalization
            # del self.current_session_logs[session_id]

    def get_all_session_ids(self):
        """Get list of all logged sessions"""
        return [f.stem for f in self.log_dir.glob("*.json")]

    def get_session_log(self, session_id: str):
        """Retrieve a specific session log"""
        log_file = self.log_dir / f"{session_id}.json"
        if log_file.exists():
            with open(log_file, 'r') as f:
                return json.load(f)
        return None


# Global logger instance
test_logger = TestDataLogger()
