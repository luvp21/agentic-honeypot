
"""
Gemini Integration Test
This script directly tests the Gemini Client and AI Agent integration to confirm API connectivity.
"""
import os
import asyncio
import logging
from gemini_client import gemini_client
from ai_agent import AIHoneypotAgent

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_gemini_direct():
    """Test 1: Direct Gemini Client Call"""
    logger.info("--- TEST 1: Direct Gemini Client Check ---")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("❌ GEMINI_API_KEY not found in environment!")
        return False

    masked_key = f"{api_key[:4]}...{api_key[-4:]}"
    logger.info(f"✅ Found API Key: {masked_key}")

    prompt = "Reply with exactly 'Gemini is working' if you can read this."
    logger.info(f"📤 Sending prompt: '{prompt}'")

    try:
        response = await gemini_client.generate_response(prompt, operation_name="test_direct")
        if response and "Gemini is working" in response:
            logger.info(f"✅ Gemini Response: {response}")
            return True
        else:
            logger.warning(f"⚠️ Unexpected Response: {response}")
            return False

    except Exception as e:
        logger.error(f"❌ Exception during Gemini call: {e}")
        return False

async def test_ai_agent_integration():
    """Test 2: AI Agent Integration Check"""
    logger.info("\n--- TEST 2: AI Agent Integration Check ---")

    agent = AIHoneypotAgent()

    # Mock data for a standard scam scenario
    message = "Hello, this is Bank Support. We need you to verify your account immediately."
    history = [{"sender": "scammer", "text": "Hi"}]
    scam_type = "phishing"
    persona = agent._select_persona(scam_type)

    logger.info(f"🎭 Testing Agent with message: '{message}'")
    logger.info(f"📊 Strategy: DEFAULT (Should trigger LLM)")

    # Force strategy to DEFAULT to ensure LLM usage
    response = await agent.generate_response(
        message=message,
        conversation_history=history,
        scam_type=scam_type,
        missing_intel=["upi"],
        strategy="DEFAULT"
    )

    if response:
        logger.info(f"✅ Agent Response: {response}")
        logger.info("NOTE: If this response sounds like a confused elderly person, the LLM is working!")
        return True
    else:
        logger.error("❌ Agent returned empty response")
        return False

async def main():
    logger.info("🚀 Starting Gemini Integration Test...")

    direct_success = await test_gemini_direct()
    if not direct_success:
        logger.error("🛑 Direct API test failed. Aborting agent test.")
        return

    agent_success = await test_ai_agent_integration()

    if direct_success and agent_success:
        logger.info("\n🎉 SUCCESS: Gemini API is fully integrated and working!")
    else:
        logger.error("\n⚠️ FAILURE: Integration issues detected.")

if __name__ == "__main__":
    asyncio.run(main())
