---
title: Agentic Honeypot API
emoji: 🍯
colorFrom: yellow
colorTo: yellow
sdk: docker
pinned: false
app_port: 7860
---

# 🍯 AI Honeypot System for Scam Detection

An autonomous AI-powered honeypot system that detects scam messages and actively engages scammers using believable personas. The system extracts critical intelligence including bank accounts, UPI IDs, phishing links, and contact information.

## 🚀 Features

✅ **Automated Scam Detection** - Pattern-based detection with 70%+ accuracy
✅ **AI-Powered Engagement** - Believable personas that keep scammers engaged
✅ **Intelligence Extraction** - Automatically extracts bank accounts, UPI IDs, phishing links
✅ **Multiple Scam Types** - Supports 7+ scam categories
✅ **RESTful API** - FastAPI-based with automatic OpenAPI documentation

## 📡 API Endpoints

### Primary Endpoint
```
POST /api/honeypot/message
```

Send a message to the honeypot system for scam detection and AI engagement.

**Headers:**
- `x-api-key`: Your API key (required)

**Request Body:**
```json
{
  "sessionId": "unique-session-id",
  "message": {
    "text": "Your bank account is suspended...",
    "sender": "user",
    "timestamp": "2026-02-05T20:00:00Z"
  },
  "conversationHistory": [],
  "metadata": {}
}
```

**Response:**
```json
{
  "status": "success",
  "reply": "AI-generated response"
}
```

### Health Check
```
GET /health
```

Check if the API is operational.

### Statistics
```
GET /stats
```

Get session statistics (requires API key).

## 🔐 Authentication

All endpoints (except `/` and `/health`) require an API key in the `x-api-key` header.

Default API key: `honeypot-secret-key-123`

**Important:** Change this in production by setting the `API_KEY` environment variable in your Space settings.

## 📖 Documentation

Interactive API documentation is available at:
- Swagger UI: `/docs`
- ReDoc: `/redoc`

## 🎭 Supported Scam Types

- **phishing** - Bank account verification scams
- **lottery** - Fake prize notifications
- **tech_support** - Fake virus alerts
- **investment** - Crypto/trading scams
- **romance** - Emotional manipulation
- **job_offer** - Fake work-from-home offers
- **impersonation** - Government official fraud

## 🔧 Environment Variables

Set these in your Space settings:

- `API_KEY` - Custom API key for authentication (optional, defaults to demo key)
- `CALLBACK_URL` - Webhook URL for scam intelligence callbacks (optional)

## 📊 How It Works

1. **Detection** - Incoming messages are analyzed for scam patterns
2. **Engagement** - AI agent generates contextual responses using personas
3. **Extraction** - System extracts intelligence (bank accounts, UPI IDs, etc.)
4. **Callback** - After sufficient engagement, intelligence is sent to callback URL

## 🛡️ Ethical Use

This system is designed for:
- Research and education
- Scam detection and prevention
- Security awareness training

**Not for:** Unauthorized surveillance or privacy violations.

## 📞 API Usage Example

```python
import requests

url = "https://YOUR_USERNAME-SPACE_NAME.hf.space/api/honeypot/message"
headers = {"x-api-key": "honeypot-secret-key-123"}

data = {
    "sessionId": "test-session-1",
    "message": {
        "text": "Congratulations! You won $10,000. Click here to claim.",
        "sender": "user",
        "timestamp": "2026-02-05T20:00:00Z"
    },
    "conversationHistory": []
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

## 🏗️ Architecture

- **FastAPI** - Modern Python web framework
- **Scam Detector** - Pattern-based detection engine
- **AI Agent** - Persona-based response generator
- **Intelligence Extractor** - Data extraction module
- **Session Manager** - Conversation state management

## 📝 License

Built for educational and research purposes.
