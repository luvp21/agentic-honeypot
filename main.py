"""
AI Honeypot System for Scam Detection & Intelligence Extraction
Main FastAPI Application
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
import json
from datetime import datetime
import uuid
import asyncio
from collections import defaultdict

from scam_detector import ScamDetector
from ai_agent import AIHoneypotAgent
from intelligence_extractor import IntelligenceExtractor
from mock_scammer import MockScammer

app = FastAPI(title="AI Honeypot System", version="1.0.0")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global storage (in production, use database)
conversations = {}
intelligence_db = []

# Security
API_KEY_NAME = "X-API-Key"
API_KEY = "honeypot-secret-key-123"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(
        status_code=403,
        detail="Could not validate credentials"
    )

# Initialize components
scam_detector = ScamDetector()
ai_agent = AIHoneypotAgent()
intel_extractor = IntelligenceExtractor()
mock_scammer = MockScammer()


class MessageRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ConversationResponse(BaseModel):
    conversation_id: str
    is_scam: bool
    confidence_score: float
    ai_response: str
    extracted_intelligence: Dict
    conversation_history: List[Dict]


@app.get("/")
async def root():
    return {
        "message": "AI Honeypot System Active",
        "endpoints": {
            "start_conversation": "/api/conversation/start",
            "send_message": "/api/conversation/message",
            "get_intelligence": "/api/intelligence",
            "simulate_scam": "/api/simulate/scam",
            "dashboard_stats": "/api/dashboard/stats"
        }
    }


@app.post("/api/conversation/start")
async def start_conversation():
    """Start a new conversation session"""
    conversation_id = str(uuid.uuid4())
    conversations[conversation_id] = {
        "id": conversation_id,
        "started_at": datetime.utcnow().isoformat(),
        "messages": [],
        "is_scam": False,
        "confidence_score": 0.0,
        "extracted_data": {},
        "status": "active"
    }
    return {"conversation_id": conversation_id, "message": "Conversation started"}


@app.post("/api/conversation/message", response_model=ConversationResponse)
async def process_message(request: MessageRequest, api_key: str = Depends(get_api_key)):
    """Process incoming message and generate AI response"""

    # Create new conversation if needed
    if not request.conversation_id or request.conversation_id not in conversations:
        conversation_id = str(uuid.uuid4())
        conversations[conversation_id] = {
            "id": conversation_id,
            "started_at": datetime.utcnow().isoformat(),
            "messages": [],
            "is_scam": False,
            "confidence_score": 0.0,
            "extracted_data": {},
            "status": "active"
        }
    else:
        conversation_id = request.conversation_id

    conversation = conversations[conversation_id]

    # Step 1: Detect if message is a scam
    scam_result = scam_detector.analyze(request.message)
    conversation["is_scam"] = scam_result["is_scam"]
    conversation["confidence_score"] = scam_result["confidence_score"]
    conversation["scam_type"] = scam_result.get("scam_type", "unknown")

    # Add incoming message to history
    conversation["messages"].append({
        "role": "scammer",
        "content": request.message,
        "timestamp": datetime.utcnow().isoformat()
    })

    # Step 2: Extract intelligence from scammer message
    extracted = intel_extractor.extract(request.message)
    if extracted:
        # Merge with existing extracted data
        for key, value in extracted.items():
            if key not in conversation["extracted_data"]:
                conversation["extracted_data"][key] = []
            if isinstance(value, list):
                conversation["extracted_data"][key].extend(value)
            else:
                conversation["extracted_data"][key].append(value)

    # Step 3: Generate AI response if it's a scam
    if conversation["is_scam"]:
        ai_response = await ai_agent.generate_response(
            message=request.message,
            conversation_history=conversation["messages"],
            scam_type=conversation["scam_type"]
        )
    else:
        ai_response = "Thank you for your message. How can I help you?"

    # Add AI response to history
    conversation["messages"].append({
        "role": "ai_agent",
        "content": ai_response,
        "timestamp": datetime.utcnow().isoformat()
    })

    # Step 4: Save intelligence if significant data extracted
    if conversation["is_scam"] and conversation["extracted_data"]:
        intelligence_record = {
            "conversation_id": conversation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "scam_type": conversation["scam_type"],
            "confidence_score": conversation["confidence_score"],
            "extracted_intelligence": conversation["extracted_data"],
            "message_count": len(conversation["messages"]),
            "threat_level": _calculate_threat_level(conversation["extracted_data"])
        }
        intelligence_db.append(intelligence_record)

    return ConversationResponse(
        conversation_id=conversation_id,
        is_scam=conversation["is_scam"],
        confidence_score=conversation["confidence_score"],
        ai_response=ai_response,
        extracted_intelligence=conversation["extracted_data"],
        conversation_history=conversation["messages"]
    )


@app.get("/api/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get full conversation details"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversations[conversation_id]


@app.get("/api/intelligence")
async def get_intelligence():
    """Get all extracted intelligence"""
    return {
        "total_records": len(intelligence_db),
        "intelligence": intelligence_db
    }


@app.get("/api/intelligence/export")
async def export_intelligence():
    """Export intelligence in structured JSON format"""
    return JSONResponse(
        content={
            "exported_at": datetime.utcnow().isoformat(),
            "total_conversations": len([c for c in conversations.values() if c["is_scam"]]),
            "total_intelligence_records": len(intelligence_db),
            "intelligence_data": intelligence_db
        },
        media_type="application/json"
    )


@app.post("/api/simulate/scam")
async def simulate_scam_conversation(scam_type: str = "phishing", api_key: str = Depends(get_api_key)):
    """Simulate a full scam conversation for demo purposes"""

    conversation_id = str(uuid.uuid4())
    conversations[conversation_id] = {
        "id": conversation_id,
        "started_at": datetime.utcnow().isoformat(),
        "messages": [],
        "is_scam": True,
        "confidence_score": 0.95,
        "extracted_data": {},
        "status": "simulated",
        "scam_type": scam_type
    }

    # Get simulated scam scenario
    scenario = mock_scammer.get_scenario(scam_type)
    conversation_log = []

    for i, scammer_msg in enumerate(scenario["messages"]):
        # Add scammer message
        conversations[conversation_id]["messages"].append({
            "role": "scammer",
            "content": scammer_msg,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Extract intelligence
        extracted = intel_extractor.extract(scammer_msg)
        if extracted:
            for key, value in extracted.items():
                if key not in conversations[conversation_id]["extracted_data"]:
                    conversations[conversation_id]["extracted_data"][key] = []
                if isinstance(value, list):
                    conversations[conversation_id]["extracted_data"][key].extend(value)
                else:
                    conversations[conversation_id]["extracted_data"][key].append(value)

        # Generate AI response
        ai_response = await ai_agent.generate_response(
            message=scammer_msg,
            conversation_history=conversations[conversation_id]["messages"],
            scam_type=scam_type
        )

        conversations[conversation_id]["messages"].append({
            "role": "ai_agent",
            "content": ai_response,
            "timestamp": datetime.utcnow().isoformat()
        })

        conversation_log.append({
            "turn": i + 1,
            "scammer": scammer_msg,
            "ai_agent": ai_response
        })

        # Simulate delay
        await asyncio.sleep(0.5)

    # Save intelligence
    intelligence_record = {
        "conversation_id": conversation_id,
        "timestamp": datetime.utcnow().isoformat(),
        "scam_type": scam_type,
        "confidence_score": 0.95,
        "extracted_intelligence": conversations[conversation_id]["extracted_data"],
        "message_count": len(conversations[conversation_id]["messages"]),
        "threat_level": _calculate_threat_level(conversations[conversation_id]["extracted_data"])
    }
    intelligence_db.append(intelligence_record)

    return {
        "conversation_id": conversation_id,
        "scam_type": scam_type,
        "conversation_log": conversation_log,
        "extracted_intelligence": conversations[conversation_id]["extracted_data"],
        "full_conversation": conversations[conversation_id]
    }


@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    total_conversations = len(conversations)
    scam_conversations = len([c for c in conversations.values() if c["is_scam"]])

    # Count extracted data types
    total_bank_accounts = sum(len(c["extracted_data"].get("bank_accounts", []))
                              for c in conversations.values())
    total_upi_ids = sum(len(c["extracted_data"].get("upi_ids", []))
                       for c in conversations.values())
    total_phishing_links = sum(len(c["extracted_data"].get("phishing_links", []))
                              for c in conversations.values())
    total_phone_numbers = sum(len(c["extracted_data"].get("phone_numbers", []))
                             for c in conversations.values())

    # Scam type distribution
    scam_types = defaultdict(int)
    for c in conversations.values():
        if c["is_scam"]:
            scam_type = c.get("scam_type", "unknown")
            scam_types[scam_type] += 1

    return {
        "total_conversations": total_conversations,
        "scam_conversations": scam_conversations,
        "legitimate_conversations": total_conversations - scam_conversations,
        "detection_rate": (scam_conversations / total_conversations * 100) if total_conversations > 0 else 0,
        "extracted_intelligence": {
            "bank_accounts": total_bank_accounts,
            "upi_ids": total_upi_ids,
            "phishing_links": total_phishing_links,
            "phone_numbers": total_phone_numbers
        },
        "scam_type_distribution": dict(scam_types),
        "recent_intelligence": intelligence_db[-5:] if intelligence_db else []
    }


def _calculate_threat_level(extracted_data: Dict) -> str:
    """Calculate threat level based on extracted data"""
    score = 0

    if extracted_data.get("bank_accounts"):
        score += 3
    if extracted_data.get("upi_ids"):
        score += 3
    if extracted_data.get("phishing_links"):
        score += 2
    if extracted_data.get("phone_numbers"):
        score += 1
    if extracted_data.get("email_addresses"):
        score += 1

    if score >= 6:
        return "critical"
    elif score >= 4:
        return "high"
    elif score >= 2:
        return "medium"
    else:
        return "low"


if __name__ == "__main__":
    print("🚀 Starting AI Honeypot System...")
    print("📊 Dashboard will be available at: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
