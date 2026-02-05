# 🚀 Hugging Face Spaces Deployment Guide

This guide will walk you through deploying your honeypot API to Hugging Face Spaces.

## Prerequisites

- Hugging Face account (free): https://huggingface.co/join
- Git installed on your machine
- Your project files ready

## Step 1: Create a New Space

1. Go to https://huggingface.co/spaces
2. Click **"Create new Space"**
3. Fill in the details:
   - **Owner**: Your username or organization
   - **Space name**: `agentic-honeypot` (or your preferred name)
   - **License**: Choose appropriate license (e.g., Apache 2.0)
   - **Select SDK**: Choose **Docker**
   - **Visibility**: Choose Public or Private
4. Click **"Create Space"**

## Step 2: Set Up Git Repository

After creating the Space, you'll see instructions. Follow these steps:

```bash
# Navigate to your project directory
cd /home/luv/Desktop/files

# Initialize git if not already done
git init

# Add Hugging Face remote (replace USERNAME and SPACE_NAME)
git remote add hf https://huggingface.co/spaces/USERNAME/SPACE_NAME

# Or if you already have a git repo, just add the HF remote
git remote add hf https://huggingface.co/spaces/USERNAME/SPACE_NAME
```

## Step 3: Prepare Files for Deployment

Make sure you have these files in your project:

- ✅ `app.py` - Hugging Face entrypoint
- ✅ `main.py` - Your FastAPI application
- ✅ `Dockerfile` - Container configuration
- ✅ `requirements.txt` - Python dependencies
- ✅ `HF_README.md` - Space description
- ✅ All your modules (scam_detector.py, ai_agent.py, etc.)

### Rename README for Hugging Face

```bash
# Backup your original README
mv README.md README_PROJECT.md

# Use the HF README as the main README
mv HF_README.md README.md
```

## Step 4: Update .gitignore

Create or update `.gitignore` to exclude unnecessary files:

```bash
cat << 'EOF' > .gitignore
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
venv/
env/
.env
*.log
.DS_Store
render.yaml
EOF
```

## Step 5: Commit and Push to Hugging Face

```bash
# Add all files
git add .

# Commit
git commit -m "Initial deployment to Hugging Face Spaces"

# Push to Hugging Face
git push hf main
```

**Note:** If your default branch is `master`, use `git push hf master` instead.

## Step 6: Configure Environment Variables (Optional)

If you want to use a custom API key:

1. Go to your Space on Hugging Face
2. Click on **"Settings"** tab
3. Scroll to **"Repository secrets"**
4. Add new secret:
   - Name: `API_KEY`
   - Value: Your custom API key
5. Click **"Add"**

**Note:** You'll need to modify `main.py` to read from environment variables:

```python
import os
API_KEY = os.getenv("API_KEY", "honeypot-secret-key-123")
```

## Step 7: Wait for Build

Hugging Face will automatically:
1. Detect the Dockerfile
2. Build your container
3. Deploy your app
4. Assign a URL

This usually takes 2-5 minutes. You can watch the build logs in real-time.

## Step 8: Test Your Deployment

Once deployed, your API will be available at:

```
https://USERNAME-SPACE_NAME.hf.space
```

### Test the Health Endpoint

```bash
curl https://USERNAME-SPACE_NAME.hf.space/health
```

### Test the API Documentation

Visit in your browser:
```
https://USERNAME-SPACE_NAME.hf.space/docs
```

### Test the Main Endpoint

```bash
curl -X POST https://USERNAME-SPACE_NAME.hf.space/api/honeypot/message \
  -H "Content-Type: application/json" \
  -H "x-api-key: honeypot-secret-key-123" \
  -d '{
    "sessionId": "test-123",
    "message": {
      "text": "Your account has been suspended. Click here to verify.",
      "sender": "user",
      "timestamp": "2026-02-05T20:00:00Z"
    },
    "conversationHistory": []
  }'
```

## Step 9: Update Test Files

Update your test files with the new URL:

```python
# In test_api_live.py
url = "https://USERNAME-SPACE_NAME.hf.space/api/honeypot/message"
```

## 🔧 Troubleshooting

### Build Failed

- Check the build logs in your Space
- Verify all files are committed and pushed
- Ensure `requirements.txt` has all dependencies
- Check Dockerfile syntax

### App Won't Start

- Verify port 7860 is used (HF Spaces default)
- Check application logs in the Space
- Ensure `app.py` correctly imports from `main.py`

### API Returns 403

- Check your API key is correct
- Verify the `x-api-key` header is properly set
- Make sure authentication is working

### Slow Response Times

- Free tier has limited resources
- Consider upgrading to a paid tier if needed
- Optimize your code for better performance

## 🎯 Next Steps

1. **Update Frontend/Clients**: Change all API calls to new HF URL
2. **Set Up Monitoring**: Use HF analytics to track usage
3. **Configure Secrets**: Add any sensitive environment variables
4. **Test Thoroughly**: Run all your test scripts
5. **Share Your Space**: Make it public or share with team

## 📊 Hugging Face Spaces Features

- **Automatic HTTPS**: All Spaces get SSL certificates
- **Custom Domains**: Available on paid plans
- **Scaling**: Auto-scaling based on usage
- **Analytics**: Built-in usage statistics
- **Collaboration**: Easy team access and permissions

## 💡 Tips

- **Keep it Updated**: Push updates anytime with `git push hf main`
- **Monitor Logs**: Check Space logs regularly for errors
- **Use Secrets**: Never commit API keys or credentials
- **Test Locally**: Always test with Docker locally first
- **Documentation**: Keep your README.md updated

## 🔗 Useful Links

- Hugging Face Spaces Docs: https://huggingface.co/docs/hub/spaces
- Docker SDK Guide: https://huggingface.co/docs/hub/spaces-sdks-docker
- Your Space: https://huggingface.co/spaces/USERNAME/SPACE_NAME

---

**Congratulations!** 🎉 Your honeypot API is now live on Hugging Face Spaces!
