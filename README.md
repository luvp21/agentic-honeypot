---
title: Agentic Honeypot
emoji: 🍯
colorFrom: red
colorTo: pink
sdk: docker
pinned: false
license: mit
app_port: 8000
---

# 🍯 Agentic Honeypot - Enterprise Intelligence Extraction Platform

An enterprise-grade AI-powered honeypot system that autonomously detects scam attempts, engages scammers through multi-turn conversations, and extracts valuable intelligence using advanced behavioral profiling and continuous extraction strategies.

## 🚀 Features

### Core Capabilities
- **🎯 Autonomous Scam Detection**: Real-time pattern matching and ML-based classification
- **🤖 Multi-Turn AI Agent**: Maintains believable personas to maximize engagement
- **📊 Continuous Intelligence Extraction**: Never stops extracting - runs on EVERY turn with backfill
- **🧠 Behavioral Profiling**: Analyzes scammer tactics, language, and aggression patterns
- **🔄 Explicit State Machine**: Proper lifecycle management (INIT → SCAM_DETECTED → ENGAGING → EXTRACTING → FINALIZED)
- **⏱️ Delayed Callback Strategy**: Optimized for maximum engagement (15+ turns or 60s idle)

### Intelligence Extraction
The system extracts and validates:
- 💳 Bank Account Numbers (context-aware, with validation)
- 💰 UPI IDs (strict handle verification)
- 🏦 IFSC Codes (format validation + context boost)
- 📱 Phone Numbers (negative context filtering)
- 🔗 Phishing Links (URL detection)
- 🚨 Suspicious Keywords (urgency/fear tactics)

### Behavioral Analysis
Profiles scammer behavior including:
- **Tactics**: URGENCY, FEAR, REWARD, AUTHORITY, SCARCITY
- **Language**: English, Hinglish, Hindi detection
- **Aggression Score**: 0.0-1.0 based on communication patterns

## 🏗️ Architecture

### State Machine Flow
```
INIT → SCAM_DETECTED → ENGAGING → EXTRACTING → FINALIZED
```

### Core Components
- `models.py` - Data structures with state machine enums
- `behavioral_profiler.py` - Scammer behavior analysis
- `session_manager.py` - State transitions & lifecycle
- `intelligence_extractor.py` - Pattern matching & extraction
- `ai_agent.py` - Response generation
- `callback.py` - External API communication
- `main.py` - FastAPI orchestration

## 🔧 API Usage

### Endpoint
```
POST /api/honeypot/message
```

### Request Format
```json
{
  "sessionId": "unique-session-id",
  "message": {
    "sender": "scammer",
    "text": "URGENT! Your account will be blocked!",
    "timestamp": 1707654321000
  },
  "conversationHistory": []
}
```

### Response Format
```json
{
  "status": "success",
  "reply": "What? I don't understand. What happened to my account?"
}
```

## 📊 Intelligence Output

When finalized (15+ turns or 60s idle), sends callback with:

```json
{
  "sessionId": "session-123",
  "scamDetected": true,
  "totalMessagesExchanged": 18,
  "extractedIntelligence": {
    "bankAccounts": ["9876543210123456"],
    "upiIds": ["scammer.fraud@paytm"],
    "phishingLinks": ["http://fake-bank.com"],
    "phoneNumbers": ["9876543210"],
    "ifscCodes": ["HDFC0001234"],
    "suspiciousKeywords": ["urgent", "verify", "blocked"]
  },
  "agentNotes": "Detected phishing scam. Engaged through 18 turns. Extracted 4 intel items. Scammer employed URGENCY, FEAR tactics. Communication in English. Aggression: high.",
  "status": "final"
}
```

## 🎯 Optimization for Hackathons

The system is optimized for hackathon scoring metrics:
- **Maximum Engagement Duration**: Delays finalization to 15+ turns
- **Continuous Extraction**: Never stops extracting intelligence
- **Backfill Strategy**: Re-scans full conversation every 5 turns
- **Rich Behavioral Insights**: Comprehensive `agentNotes` generation

## 🔐 Security

- API key authentication
- Environment variable configuration
- Rate limiting ready
- Input validation

## 📝 Configuration

Adjust thresholds in `session_manager.py`:
```python
MAX_TURNS_THRESHOLD = 15  # Minimum turns before finalization
IDLE_TIMEOUT_SECONDS = 60  # Max idle time before finalization
```

## 🏆 Built For

**GUVI Hackathon**: Scam Detection & Intelligence Extraction Challenge

## 📄 License

MIT License - See LICENSE file for details

---

**Built with FastAPI, Pydantic, and advanced NLP techniques for enterprise-grade scam intelligence gathering.**
