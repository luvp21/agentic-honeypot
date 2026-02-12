# Platform Testing Guide (Passive Mode)

## 🎯 Purpose

This guide explains how to collect accuracy metrics when testing your API directly against the **Hackathon Evaluation Platform**.

Instead of running our own test script, we will:
1. Manually trigger tests on the platform
2. **Passively log** all requests & responses
3. Analyze the logs to generate your accuracy report

---

## 🛠️ How It Works

I've added a **logging middleware** to your API (`main.py`) that automatically captures:
- Every message from the platform
- Your agent's response
- The final callback payload (when the session ends)

All logs are saved to: `platform_test_logs/`

---

## 🚀 Step-by-Step Guide

### Step 1: Deploy & Configure

1. Ensure your API is deployed (e.g., on Hugging Face Spaces).
2. The logging system is **already active** in the code I just updated.

### Step 2: Run Tests on Platform

1. Go to the Hackathon Evaluation Platform.
2. Enter your **API URL** and **API Key**.
3. Run the valid/invalid test cases as provided by the platform.
4. **Repeat this N times** (e.g., 10-20 runs) to build a good dataset.
   - Try different scenarios if the platform allows.
   - Ensure sessions complete (either by reach max turns or success).

### Step 3: Download Logs (If on Cloud)

*If you are running locally:* skip this step.
*If deployed on Hugging Face:*
You'll need to download the `platform_test_logs/` directory.

### Step 4: Generate Accuracy Report

Run the analyzer pointing to your platform logs directory:

```bash
python metrics_analyzer.py platform_test_logs/
```

**Note:** The analyzer automatically detects that these are platform logs (different format) and handles them correctly.

---

## 📊 What Metrics You'll Get

The report will show:

1. **Real-world Accuracy**: How well your agent handled the *actual* platform test cases.
2. **Compliance Check**: Verifies if intelligence was correctly extracted according to platform standards.
3. **Engagement Stats**: Average turns per session on the platform.

### Sample Output

```
📊 KEY METRICS SUMMARY
============================================================

📈 ENGAGEMENT METRICS
   Total Conversations: 15
   Average Turns/Conversation: 8.2

🔍 INTELLIGENCE EXTRACTION
   Conversations with Extraction Attempts: 14/15 (93.3%)

   Extraction by Type:
      bank_accounts: 12/12 (100.0%)
      upi_ids: 10/11 (90.9%)
```

---

## 💡 Tips for Presentation

- **"We tested against the official platform N times..."**
- **"Achieved X% extraction rate on official test cases..."**
- Show the `metrics_report.json` as proof of thorough testing.

---

## ⚠️ Troubleshooting

**"No logs found?"**
- Ensure you commit and push the latest `main.py` changes to your deployment.
- Verify the platform is actually hitting your API (check logs).

**"Analyzer crashing?"**
- Ensure you are pointing it to the correct directory containing `.json` files.
