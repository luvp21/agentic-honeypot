"""
Verification Script for Honeypot Upgrade
"""

import sys
import logging
from session_manager import SessionManager
from models import IntelItem
from intelligence_extractor import IntelligenceExtractor, RawIntel

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def verify_upgrade():
    print("🚀 Starting Verification...")

    session_mgr = SessionManager()
    extractor = IntelligenceExtractor()
    session_id = "test_session_v2"

    # Init session as scam
    session = session_mgr.get_or_create_session(session_id)
    session_mgr.update_session(session_id, is_scam=True)

    conversation_history = []

    def add_message(text):
        conversation_history.append(text)
        # Build context (last 5)
        context = " ".join(conversation_history[-5:])
        msg_idx = len(conversation_history) - 1
        return text, msg_idx, context

    # ====================================================================
    # SCENARIO 1: Split Context Extraction
    # ====================================================================
    print("\n[Scenario 1] Split Context Extraction")

    # Message 1: Context set up
    text, idx, ctx = add_message("My account number is")
    intel = extractor.extract(text, idx, ctx)
    session_mgr.update_intel_graph(session_id, intel)
    print(f"Msg 1 ('{text}'): Found {len(intel)} items")

    # Message 2: The number (should be extracted due to context in previous msg)
    text, idx, ctx = add_message("12345678912")
    intel = extractor.extract(text, idx, ctx)
    print(f"Msg 2 ('{text}'): Found {len(intel)} items")
    for item in intel:
        print(f"  - {item.type}: {item.value} (Source: {item.source})")

    session_mgr.update_intel_graph(session_id, intel)

    # Verify Graph
    session = session_mgr.get_session(session_id)
    accts = session.intel_graph.get("bank_accounts", [])
    if accts and accts[0].value == "12345678912":
        print("✅ SUCCESS: Extracted account number using split context")
    else:
        print("❌ FAILED: Did not extract account number")

    # ====================================================================
    # SCENARIO 2: Preliminary Callback Trigger
    # ====================================================================
    print("\n[Scenario 2] Preliminary Callback Trigger")

    # Msg 3: Critical Intel (UPI)
    text, idx, ctx = add_message("Please pay to upi: scammer@okaxis")
    intel = extractor.extract(text, idx, ctx)
    session_mgr.update_intel_graph(session_id, intel)

    status = session_mgr.should_send_callback(session_id, idx)
    print(f"Callback Status after UPI: {status}")

    if status["send"] and status["type"] == "preliminary":
        print("✅ SUCCESS: Triggered Preliminary Callback")
        session_mgr.mark_callback_sent(session_id, "preliminary")
    else:
        print(f"❌ FAILED: Expected Preliminary Callback, got {status}")

    # ====================================================================
    # SCENARIO 3: Stability & Confidence
    # ====================================================================
    print("\n[Scenario 3] Stability & Confidence")

    # Msg 4: Repeat UPI (Boost confidence)
    text, idx, ctx = add_message("scammer@okaxis")
    intel = extractor.extract(text, idx, ctx)
    session_mgr.update_intel_graph(session_id, intel)

    upi_item = session.intel_graph["upi_ids"][0]
    print(f"UPI Confidence after repeat: {upi_item.confidence}")

    if upi_item.confidence > 1.0:
        print("✅ SUCCESS: Confidence boosted")
    else:
        print("❌ FAILED: Confidence not boosted")

    # Msg 5, 6, 7: Filler messages to create stability window (3 messages)
    add_message("Hello")
    add_message("Are you there?")
    text, idx, ctx = add_message("Waiting")

    status = session_mgr.should_send_callback(session_id, idx)
    print(f"Callback Status after stability wait: {status}")

    if status["send"] and status["type"] == "final":
        print("✅ SUCCESS: Triggered Final Callback due to stability")
    else:
        print(f"❌ FAILED: Expected Final Callback, got {status}")

if __name__ == "__main__":
    verify_upgrade()
