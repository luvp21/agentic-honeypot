"""
Performance Logger for Hackathon Testing
Tracks LLM usage, rule-based fallbacks, intelligence extraction, and performance metrics
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class PerformanceLogger:
    """Track all decision points and performance metrics for optimization"""

    def __init__(self, log_file: str = "hackathon_performance.log"):
        self.log_file = log_file
        self.session_metrics = {}

        # Setup structured logging
        self.perf_logger = logging.getLogger("performance")
        self.perf_logger.setLevel(logging.INFO)

        # File handler for structured logs
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.perf_logger.addHandler(handler)

    def log_generation_method(self, session_id: str, turn: int, method: str, details: Dict):
        """
        Log which generation method was used

        Args:
            session_id: Session ID
            turn: Turn number
            method: "LLM_GEMINI" | "RULE_BASED" | "STRATEGY_OVERRIDE"
            details: Additional context
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "turn": turn,
            "event": "RESPONSE_GENERATION",
            "method": method,
            "details": details
        }
        self.perf_logger.info(f"GENERATION: {json.dumps(log_entry)}")

    def log_intelligence_extraction(self, session_id: str, turn: int, extracted: List, method: str = "CONTINUOUS"):
        """
        Log intelligence extraction events

        Args:
            session_id: Session ID
            turn: Turn number
            extracted: List of extracted intelligence items
            method: "CONTINUOUS" | "BACKFILL"
        """
        intel_types = list(set([item.type for item in extracted])) if extracted else []

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "turn": turn,
            "event": "INTELLIGENCE_EXTRACTION",
            "method": method,
            "count": len(extracted),
            "types": intel_types,
            "items": [{"type": item.type, "value": item.value[:20]} for item in extracted[:5]]  # First 5 items
        }
        self.perf_logger.info(f"EXTRACTION: {json.dumps(log_entry)}")

    def log_scam_detection(self, session_id: str, turn: int, detected: bool, confidence: float, scam_type: str):
        """Log scam detection event"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "turn": turn,
            "event": "SCAM_DETECTION",
            "detected": detected,
            "confidence": confidence,
            "scam_type": scam_type
        }
        self.perf_logger.info(f"DETECTION: {json.dumps(log_entry)}")

    def log_strategy_change(self, session_id: str, turn: int, old_strategy: str, new_strategy: str, reason: str):
        """Log engagement strategy changes"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "turn": turn,
            "event": "STRATEGY_CHANGE",
            "old_strategy": old_strategy,
            "new_strategy": new_strategy,
            "reason": reason
        }
        self.perf_logger.info(f"STRATEGY: {json.dumps(log_entry)}")

    def log_finalization(self, session_id: str, turn: int, trigger: str, intel_summary: Dict):
        """Log session finalization"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "turn": turn,
            "event": "SESSION_FINALIZED",
            "trigger": trigger,
            "intelligence_summary": intel_summary
        }
        self.perf_logger.info(f"FINALIZATION: {json.dumps(log_entry)}")

    def log_callback(self, session_id: str, success: bool, status_code: Optional[int], response_time: float):
        """Log callback attempt"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "event": "CALLBACK",
            "success": success,
            "status_code": status_code,
            "response_time_ms": round(response_time * 1000, 2)
        }
        self.perf_logger.info(f"CALLBACK: {json.dumps(log_entry)}")

    def log_api_request(self, session_id: str, turn: int, response_time: float, status: str):
        """Log API request/response metrics"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "turn": turn,
            "event": "API_REQUEST",
            "response_time_ms": round(response_time * 1000, 2),
            "status": status
        }
        self.perf_logger.info(f"API: {json.dumps(log_entry)}")

    def log_llm_failure(self, session_id: str, turn: int, error: str, fallback: str):
        """Log LLM failures and fallbacks"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "turn": turn,
            "event": "LLM_FAILURE",
            "error": error,
            "fallback": fallback
        }
        self.perf_logger.info(f"LLM_FAILURE: {json.dumps(log_entry)}")

    def log_session_summary(self, session_id: str, summary: Dict):
        """Log final session summary"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "event": "SESSION_SUMMARY",
            **summary
        }
        self.perf_logger.info(f"SUMMARY: {json.dumps(log_entry)}")

    def get_session_stats(self, log_file: Optional[str] = None) -> Dict:
        """
        Parse logs and generate statistics

        Returns:
            Dict with aggregated statistics
        """
        if not log_file:
            log_file = self.log_file

        stats = {
            "total_sessions": 0,
            "llm_usage": 0,
            "rule_based_usage": 0,
            "total_extractions": 0,
            "callback_success_rate": 0,
            "avg_turns_per_session": 0,
            "intel_types": {},
            "scam_types": {}
        }

        try:
            with open(log_file, 'r') as f:
                sessions = set()
                callbacks = {"success": 0, "failed": 0}
                turns_total = 0

                for line in f:
                    if "GENERATION:" in line:
                        data = json.loads(line.split("GENERATION: ")[1])
                        sessions.add(data["session_id"])
                        if data["method"] == "LLM_GEMINI":
                            stats["llm_usage"] += 1
                        elif data["method"] == "RULE_BASED":
                            stats["rule_based_usage"] += 1

                    elif "EXTRACTION:" in line:
                        data = json.loads(line.split("EXTRACTION: ")[1])
                        stats["total_extractions"] += data["count"]
                        for intel_type in data["types"]:
                            stats["intel_types"][intel_type] = stats["intel_types"].get(intel_type, 0) + 1

                    elif "CALLBACK:" in line:
                        data = json.loads(line.split("CALLBACK: ")[1])
                        if data["success"]:
                            callbacks["success"] += 1
                        else:
                            callbacks["failed"] += 1

                    elif "SUMMARY:" in line:
                        data = json.loads(line.split("SUMMARY: ")[1])
                        turns_total += data.get("total_turns", 0)
                        scam_type = data.get("scam_type", "unknown")
                        stats["scam_types"][scam_type] = stats["scam_types"].get(scam_type, 0) + 1

                stats["total_sessions"] = len(sessions)
                if callbacks["success"] + callbacks["failed"] > 0:
                    stats["callback_success_rate"] = round(callbacks["success"] / (callbacks["success"] + callbacks["failed"]) * 100, 2)
                if len(sessions) > 0:
                    stats["avg_turns_per_session"] = round(turns_total / len(sessions), 2)

        except FileNotFoundError:
            logger.warning(f"Log file {log_file} not found")

        return stats


# Global instance
performance_logger = PerformanceLogger()
