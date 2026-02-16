# 🍯 Agentic Honeypot - AI-Powered Scam Intelligence Platform

An enterprise-grade AI honeypot system that autonomously detects scam attempts, engages scammers through natural multi-turn conversations, and extracts valuable intelligence for fraud prevention.

## 🚀 Quick Start

### Docker Deployment (Recommended)
```bash
docker build -t honeypot .
docker run -p 8000:8000 --env-file .env honeypot
```

### Local Development
```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## 📋 API Specification

### Endpoint
```
POST /api/honeypot/message
```

### Request Format
```json
{
  "sessionId": "uuid-string",
  "message": {
    "sender": "scammer",
    "text": "URGENT: Your account has been compromised!",
    "timestamp": 1707654321000
  },
  "conversationHistory": [
    {
      "sender": "scammer",
      "text": "Previous message...",
      "timestamp": 1707654320000
    }
  ],
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
}
```

### Response Format
```json
{
  "status": "success",
  "reply": "Oh dear, what happened? Can you explain more?"
}
```

## 🎯 Core Features

### Intelligent Scam Detection
- Real-time pattern matching across multiple fraud types
- Multi-stage attack detection
- Context-aware classification

### Continuous Intelligence Extraction
Extracts and validates:
- 💳 Bank Account Numbers
- 💰 UPI IDs
- 🏦 IFSC Codes
- 📱 Phone Numbers
- 🔗 Phishing Links
- 📧 Email Addresses
- 🚨 Suspicious Keywords

### Adaptive AI Agent
- Maintains believable elderly persona
- Context-aware response generation
- Multi-turn conversation handling
- Strategic engagement for maximum intelligence extraction

### Behavioral Profiling
Analyzes scammer tactics:
- URGENCY, FEAR, AUTHORITY patterns
- Aggression scoring
- Language detection (English, Hindi, Hinglish)
- Psychological profiling

## 📊 Final Output Structure

After conversation completion, the system sends a callback with:

```json
{
  "sessionId": "session-id",
  "scamDetected": true,
  "totalMessagesExchanged": 18,
  "extractedIntelligence": {
    "phoneNumbers": ["+91-9876543210"],
    "bankAccounts": ["1234567890123456"],
    "upiIds": ["scammer@bank"],
    "phishingLinks": ["http://malicious-site.com"],
    "emailAddresses": ["scammer@fake.com"],
    "ifscCodes": ["HDFC0001234"],
    "suspiciousKeywords": ["urgent", "verify", "blocked"]
  },
  "agentNotes": "SUMMARY: BANK_FRAUD scam operation targeting elderly persona..."
}
```

## 🏗️ System Architecture

```
┌─────────────────┐
│   FastAPI App   │
└────────┬────────┘
         │
    ┌────┴────────────────────┐
    │                         │
┌───┴─────────┐      ┌────────┴──────┐
│  Scam       │      │   Session     │
│  Detector   │      │   Manager     │
└───┬─────────┘      └────────┬──────┘
    │                         │
    └────────┬────────────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───┴──────────┐  ┌──┴──────────────┐
│ Intelligence │  │   AI Agent      │
│  Extractor   │  │  (LLM-Powered)  │
└──────────────┘  └─────────────────┘
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file:
```env
GEMINI_API_KEY=your_gemini_api_key_here
LLM_ENABLED=true
```

### Key Components
- `main.py` - FastAPI application & orchestration
- `ai_agent.py` - LLM-powered response generation
- `scam_detector.py` - Pattern-based scam detection
- `intelligence_extractor.py` - Data extraction & validation
- `session_manager.py` - State management & lifecycle
- `behavioral_profiler.py` - Scammer behavior analysis
- `callback.py` - External API integration
- `models.py` - Data structures & validation

## 📈 Performance Metrics

- **Engagement Quality**: 15+ turn conversations
- **Extraction Rate**: Continuous on every turn
- **Detection Accuracy**: Multi-pattern rule-based + ML
- **Response Time**: < 5 seconds per turn

## 🔐 Security Features

- Input validation & sanitization
- Injection attack prevention
- Token leakage prevention
- Context-aware safety filters
- Environment-based configuration

## 🏆 Built For

**GUVI Hackathon 2026** - Scam Detection & Intelligence Extraction Challenge

## 📄 License

MIT License

---

**Powered by FastAPI, Google Gemini AI, and Advanced NLP**
