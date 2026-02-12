# Testing & Metrics Guide

## 🎯 Purpose

This guide will help you test your honeypot API multiple times, collect conversation data, and generate accuracy metrics for your hackathon presentation.

---

## 📦 What's Included

1. **`test_suite.py`** - Automated test runner that:
   - Runs N rounds of test conversations
   - Simulates scam messages across multiple scenarios
   - Logs all exchanges (scammer ↔ agent)
   - Saves results in structured JSON format

2. **`metrics_analyzer.py`** - Analytics tool that:
   - Analyzes intelligence extraction success rate
   - Measures engagement duration
   - Evaluates persona consistency
   - Generates comprehensive reports

---

## 🚀 Quick Start

### Step 1: Configure Test Suite

Edit `test_suite.py` and update these lines:

```python
# Line 18-20
API_URL = "https://your-deployed-api.hf.space/api/conversation/message"
API_KEY = "your-api-key-here"
TEST_ROUNDS = 20  # Number of test conversations
```

### Step 2: Run Tests

```bash
python test_suite.py
```

**What happens:**
- Script will run 20 test conversations
- Each conversation uses a different scam scenario (phishing, lottery, tech support, etc.)
- All messages are logged to `test_results/` directory
- Each round saves to `round_X_session-id.json`

**Expected output:**
```
🚀 Starting 20 test rounds...
============================================================
Round 1 - Scenario: phishing
Session ID: test-session-1-1707725400
============================================================

[Turn 1] Scammer: URGENT: Your SBI account has been compromised...
[Turn 1] Agent: Oh my! Is this really true? I'm not very good with these things.
...
✅ Round 1 complete. Logged to test_results/round_1_test-session-1-1707725400.json
```

### Step 3: Analyze Results

```bash
python metrics_analyzer.py test_results/
```

**What you'll get:**
- Intelligence extraction success rate (%)
- Average conversation length
- Extraction breakdown by type (bank accounts, UPI, phones, links)
- Scenario-wise performance
- Full metrics report saved to `test_results/metrics_report.json`

**Sample output:**
```
📊 KEY METRICS SUMMARY
============================================================

📈 ENGAGEMENT METRICS
   Total Conversations: 20
   Average Turns/Conversation: 4.5
   Range: 3-5 turns

🔍 INTELLIGENCE EXTRACTION
   Conversations with Extraction Attempts: 18/20 (90.0%)

   Extraction by Type:
      bank_accounts: 12/15 (80.0%)
      upi_ids: 14/16 (87.5%)
      phone_numbers: 8/10 (80.0%)
      ifsc_codes: 6/8 (75.0%)
      urls: 15/15 (100.0%)
```

---

## 📊 Understanding the Results

### Test Results Directory Structure

```
test_results/
├── round_1_test-session-1-xxx.json     # Individual conversation log
├── round_2_test-session-2-xxx.json
├── ...
├── summary_timestamp.json              # Overall test summary
└── metrics_report.json                 # Detailed analytics
```

### Individual Conversation Log Format

```json
{
  "session_id": "test-session-1-xxx",
  "scenario_type": "phishing",
  "total_turns": 5,
  "conversation": [
    {
      "turn": 1,
      "scammer": "URGENT: Your account...",
      "agent": "Oh my! I'm confused...",
      "timestamp": "2026-02-12T17:30:00"
    }
  ]
}
```

### Metrics Report Format

```json
{
  "intelligence_extraction": {
    "total_conversations": 20,
    "conversations_with_extractions": 18,
    "extraction_by_type": {
      "bank_accounts": {"available": 15, "extracted": 12},
      "upi_ids": {"available": 16, "extracted": 14}
    }
  },
  "engagement_metrics": {
    "average_turns": 4.5,
    "by_scenario": {
      "phishing": {"avg_turns": 4.2, "count": 8},
      "lottery": {"avg_turns": 4.8, "count": 6}
    }
  }
}
```

---

## 🎓 Using Metrics for Your Presentation

### Key Stats to Highlight

1. **Intelligence Extraction Rate**: "Our system successfully extracted intelligence in **90% of conversations**"

2. **Extraction Accuracy**:
   - Bank Accounts: 80%
   - UPI IDs: 87.5%
   - Phone Numbers: 80%
   - Phishing Links: 100%

3. **Engagement Duration**: "Average conversation length: **4.5 turns**, demonstrating effective scammer engagement"

4. **Scenario Coverage**: "Tested across **4 different scam types** (phishing, lottery, tech support, investment)"

### Creating Visualizations

Use the data from `metrics_report.json` to create charts:

1. **Bar Chart**: Extraction rate by intelligence type
2. **Line Graph**: Conversation length over time
3. **Pie Chart**: Distribution of scam scenarios tested

---

## 🔧 Customization

### Adding More Scam Scenarios

Edit `test_suite.py`, add to the `SCAM_SCENARIOS` list:

```python
{
    "type": "romance",
    "messages": [
        "Hi dear, I'm stuck in Dubai...",
        "I need money for flight ticket...",
        # Add more messages
    ]
}
```

### Adjusting Test Volume

```python
TEST_ROUNDS = 50  # Run 50 test conversations
```

### Testing Specific Scenarios

Modify `run_all_tests()` to use a specific scenario instead of random:

```python
# Line 147 - Replace random.choice with specific scenario
scenario = SCAM_SCENARIOS[0]  # Always use first scenario (phishing)
```

---

## ✅ Best Practices

1. **Start Small**: Run 5-10 rounds first to verify everything works
2. **Check Logs**: Review individual conversation logs to ensure quality
3. **Multiple Runs**: Run tests at different times to average out variance
4. **Save Results**: Archive test results with timestamps for comparison

---

## 🐛 Troubleshooting

### Issue: "Connection Error"
**Solution**: Verify your API URL is correct and the service is running

### Issue: "Empty responses"
**Solution**: Check if API key is correct in headers

### Issue: "No metrics generated"
**Solution**: Ensure `test_results/` contains round_*.json files before running analyzer

---

## 📝 Next Steps

1. Run 20-30 test rounds
2. Analyze results with metrics_analyzer
3. Create presentation slides with key metrics
4. Prepare specific examples from conversation logs
5. Ready to impress your professor! 🎉

---

**Questions?** Review the code comments in `test_suite.py` and `metrics_analyzer.py` for detailed implementation notes.
