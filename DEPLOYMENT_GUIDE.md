# 🚀 Quick Deployment Guide

## Option 1: Railway (Recommended - Easiest)

### Step 1: Prepare Repository
```bash
# Ensure Dockerfile exists (already present)
# Ensure requirements.txt exists (already present)
git add .
git commit -m "Ready for deployment"
git push origin main
```

### Step 2: Deploy on Railway
1. Go to [railway.app](https://railway.app)
2. Sign in with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your repository
6. Railway will auto-detect Dockerfile
7. Click "Deploy"

### Step 3: Set Environment Variables
In Railway dashboard:
```
GEMINI_API_KEY=your_gemini_api_key_here
API_KEY=honeypot-secret-key-123
```

### Step 4: Get Public URL
- Railway will provide a URL like: `https://your-app.railway.app`
- Your endpoint will be: `https://your-app.railway.app/api/honeypot/message`

---

## Option 2: Render

### Step 1: Create account
1. Go to [render.com](https://render.com)
2. Sign up with GitHub

### Step 2: New Web Service
1. Click "New +"
2. Select "Web Service"
3. Connect your GitHub repository
4. Settings:
   - Name: `honeypot-api`
   - Environment: `Docker`
   - Instance Type: `Free`

### Step 3: Environment Variables
```
GEMINI_API_KEY=your_gemini_api_key_here
API_KEY=honeypot-secret-key-123
```

### Step 4: Deploy
- Click "Create Web Service"
- Wait for deployment (5-10 minutes)
- Get URL: `https://honeypot-api.onrender.com`

---

## Option 3: Google Cloud Run

### Step 1: Install gcloud CLI
```bash
# Install if not already installed
curl https://sdk.cloud.google.com | bash
gcloud init
```

### Step 2: Build and Push
```bash
cd /home/luv/Desktop/files

# Set project
gcloud config set project YOUR_PROJECT_ID

# Build container
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/honeypot-api

# Deploy
gcloud run deploy honeypot-api \
  --image gcr.io/YOUR_PROJECT_ID/honeypot-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your_key,API_KEY=honeypot-secret-key-123
```

---

## Option 4: Local Testing (Before Deployment)

### Start Server
```bash
cd /home/luv/Desktop/files
python3 main.py
```

### Test with ngrok (Make localhost public)
```bash
# Install ngrok
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xvzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin/

# Sign up at ngrok.com and get auth token
ngrok config add-authtoken YOUR_AUTH_TOKEN

# Expose port 8000
ngrok http 8000
```

Your public URL will be shown: `https://abc123.ngrok.io`

---

## 🧪 Test Your Deployment

### Test 1: Basic Health Check
```bash
curl https://your-deployment-url.com/
```

Expected: Some response (200 OK)

### Test 2: API Endpoint Test
```bash
curl -X POST https://your-deployment-url.com/api/honeypot/message \
  -H "Content-Type: application/json" \
  -H "x-api-key: honeypot-secret-key-123" \
  -d '{
    "sessionId": "test-session-123",
    "message": {
      "sender": "scammer",
      "text": "URGENT: Your bank account is compromised!",
      "timestamp": 1707654321000
    },
    "conversationHistory": [],
    "metadata": {
      "channel": "SMS",
      "language": "English",
      "locale": "IN"
    }
  }'
```

Expected response:
```json
{
  "status": "success",
  "reply": "What? I don't understand..."
}
```

### Test 3: Run Full Compliance Test
```bash
# Update endpoint in test file
vim test_submission_compliance.py
# Change ENDPOINT_URL to your deployment URL

python3 test_submission_compliance.py
```

Expected: All tests pass ✅

---

## 📋 Deployment Checklist

Before submitting:
- [ ] Deployment is live and responding
- [ ] Endpoint URL is HTTPS (not HTTP)
- [ ] API key environment variable is set
- [ ] Response time is under 30 seconds
- [ ] Test with curl shows correct response format
- [ ] GitHub repository is public
- [ ] README is up to date

---

## 🔧 Troubleshooting

### Issue: "Connection refused"
- Check if deployment is running
- Verify URL is correct
- Check firewall settings

### Issue: "Timeout"
- Increase timeout in deployment settings
- Optimize LLM calls
- Check if LLM API is responding

### Issue: "500 Internal Server Error"
- Check deployment logs
- Verify environment variables are set
- Test locally first

### Issue: "Invalid API Key"
- Ensure x-api-key header is sent
- Verify API_KEY environment variable matches

---

## 🎯 Final Submission Format

```json
{
  "deployed_url": "https://your-app.railway.app/api/honeypot/message",
  "api_key": "honeypot-secret-key-123",
  "github_url": "https://github.com/username/honeypot-api"
}
```

---

## 📞 Support Resources

- Railway Docs: https://docs.railway.app
- Render Docs: https://render.com/docs
- Google Cloud Run: https://cloud.google.com/run/docs
- Docker Docs: https://docs.docker.com

---

**Deployment Time Estimate:**
- Railway: 5-10 minutes
- Render: 10-15 minutes
- Google Cloud Run: 15-20 minutes
- ngrok (local): 2 minutes

**Recommended for Hackathon:** Railway or Render (free tier, easy setup)
