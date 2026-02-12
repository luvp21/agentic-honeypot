# 🚀 Hybrid Agentic Honeypot - Run & Deployment Guide

## 1️⃣ Prerequisites

### System Requirements
- Python 3.10+
- Git
- Docker (optional but recommended for deployment)
- **Google Gemini API Key** (Essential for Hybrid features)

### API Key Setup
You need a Google Gemini API Key to enable the Agentic features (LLM response generation).
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create an API Key.
3. Save it securely.

---

## 2️⃣ Local Testing (Quick Start)

### Only 3 Steps:

1.  **Clone & Install:**
    ```bash
    git clone https://github.com/your-repo/agentic-honeypot.git
    cd agentic-honeypot
    pip install -r requirements.txt
    ```

2.  **Set Environment Variable:**
    ```bash
    # Linux/Mac
    export GEMINI_API_KEY="your_actual_api_key_here"

    # Windows (PowerShell)
    $env:GEMINI_API_KEY="your_actual_api_key_here"
    ```

3.  **Run the Server:**
    ```bash
    python3 main.py
    ```
    *Server will start at `http://0.0.0.0:8000`*

### Verification
Send a test POST request to verify the system is working:

```bash
curl -X POST "http://localhost:8000/api/honeypot/message" \
     -H "Content-Type: application/json" \
     -d '{
           "sessionId": "test-session-123",
           "message": "Hello, I am calling from the bank regarding your account verify now",
           "sender": "scammer"
         }'
```

**Expected Response (JSON):**
```json
{
  "sessionId": "test-session-123",
  "status": "active",
  "reply": "Oh my goodness, which bank? Is my pension safe?"
}
```

---

## 3️⃣ Hugging Face Spaces Deployment (Official)

**We recommend using Docker for Hugging Face Spaces to ensure all dependencies work perfectly.**

### Step-by-Step Guide:

1.  **Create a New Space:**
    - Go to [Hugging Face Spaces](https://huggingface.co/spaces)
    - Click **"Create new Space"**
    - Name: `agentic-honeypot-v2`
    - SDK: **Docker** (Select "Blank" template)

2.  **Add Your API Key (Critical):**
    - Go to **"Settings"** tab of your Space.
    - Scroll to **"Variables and secrets"**.
    - Click **"New secret"**.
    - Name: `GEMINI_API_KEY`
    - Value: `your_actual_api_key_here`
    - Click **Save**.

3.  **Upload Files:**
    - Go to **"Files"** tab.
    - Click **"Add file"** -> **"Upload files"**.
    - Drag & drop ALL project files (`main.py`, `ai_agent.py`, `models.py`, `requirements.txt`, `Dockerfile`, etc.).
    - Commit changes.

4.  **Wait for Build:**
    - The Space will automatically build the Docker image.
    - It takes 2-3 minutes.
    - Look for **"Running"** status at the top.

5.  **Get Your API URL:**
    - Once running, your API is live at:
    - `https://your-username-agentic-honeypot-v2.hf.space`
    - Add `/docs` to see the Swagger UI:
    - `https://your-username-agentic-honeypot-v2.hf.space/docs`

---

## 4️⃣ Troubleshooting

| Issue | Cause | Fix |
| :--- | :--- | :--- |
| **LLM Failures** | Missing API Key | Check environment variable `GEMINI_API_KEY` |
| **Response >2s** | Network Latency | Circuit breaker handles this automatically |
| **Circuit Breaker Open** | Too many errors | Wait 60s for auto-reset |
| **Build Failures** | Missing dependencies | Check `requirements.txt` has `google-generativeai` |

---

## 5️⃣ Verification Checklist (Before Submission)

- [ ] `GEMINI_API_KEY` is set in Space secrets.
- [ ] `/docs` endpoint is accessible.
- [ ] Test message receives a response.
- [ ] Response time is fast (<2s).

**Good luck on the leaderboard! 🚀**
