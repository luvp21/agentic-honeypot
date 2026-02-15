# Hackathon Performance Tracking System

## Overview
Comprehensive logging and analytics system to track all aspects of your honeypot performance during hackathon testing.

## What Gets Logged

### 1. **Response Generation Methods**
- `LLM_GEMINI`: When Gemini LLM successfully generates response
- `RULE_BASED`: When rule-based fallback is used
- `STRATEGY_OVERRIDE`: When specific engagement strategy takes precedence

### 2. **Intelligence Extraction**
- What: bank_accounts, upi_ids, phone_numbers, phishing_links, ifsc_codes, etc.
- When: Turn number and extraction method (CONTINUOUS vs BACKFILL)
- How many: Count per extraction event

### 3. **Scam Detection**
- Detection confidence score
- Scam type identified
- Turn when detection occurred

### 4. **Strategy Changes**
- When engagement strategy changes (e.g., CONFUSION → TECHNICAL_CLARIFICATION)
- Why it changed (reason)
- Turn number

### 5. **Session Finalization**
- Trigger: What caused finalization (hard_limit, idle_timeout, intelligent, etc.)
- Intelligence summary at finalization
- Turn count

### 6. **Callback Performance**
- Success/failure status
- HTTP status code
- Response time in milliseconds

### 7. **API Response Times**
- Per-request response time
- Turn number
- Success/error status

## Usage

### During Testing

1. **Run your tests** - The system automatically logs to `hackathon_performance.log`

2. **Check real-time logs** - Standard output shows:
   ```
   🔵 [HACKATHON] Processing message for session abc123, turn 5
   ```

3. **Monitor API endpoint** - Check performance stats:
   ```bash
   curl -H "x-api-key: YOUR_KEY" https://your-api.com/hackathon/performance
   ```

### After 10 Test Runs

1. **Analyze performance:**
   ```bash
   python3 analyze_logs.py
   ```

2. **Review the report:**
   ```
   📊 OVERALL METRICS
      Total Sessions: 10
      Total Generations: 143
      Total Extractions: 58

   🤖 GENERATION METHOD BREAKDOWN
      LLM (Gemini): 95 (66.4%)
      Rule-Based: 48 (33.6%)

   🔍 INTELLIGENCE EXTRACTION
      bank_accounts: 12
      upi_ids: 15
      phone_numbers: 8
      phishing_links: 10

   📞 CALLBACK PERFORMANCE
      Success: 10
      Failed: 0
      Success Rate: 100.0%
   ```

### What to Look For

#### ✅ Good Indicators
- **LLM Usage > 60%**: LLM is working well
- **Callback Success Rate = 100%**: All callbacks delivered
- **Avg Response Time < 3000ms**: Fast responses
- **High extraction counts**: Getting lots of intelligence

#### ⚠️ Warning Signs
- **LLM Usage < 40%**: Gemini may be throttled/failing - check API quota
- **Callback Failures**: Network issues or endpoint problems
- **Low Phone/UPI Extraction**: Strategy needs tuning
- **High Response Times**: Performance optimization needed

## Log Files

- **hackathon_performance.log**: Structured JSON logs for analysis
- **Standard logs**: Regular application logs with 🔵 [HACKATHON] markers

## Key Metrics for Leaderboard

Based on problem statement evaluation criteria:

1. **Scam Detection Accuracy**: Logged in DETECTION events
2. **Engagement Duration**: Total turns in SESSION_SUMMARY
3. **Intelligence Quality**: Extraction counts by type
4. **API Stability**: Response times in API logs
5. **Callback Reliability**: Success rate in CALLBACK logs

## Optimization Tips

### If LLM Usage is Low:
- Check Gemini API key and quota
- Review LLM_FAILURE logs for error patterns
- Consider increasing timeout values

### If Extraction is Low:
- Review which turns extract intelligence (EXTRACTION logs)
- Check if prompts are asking for the right information
- Verify regex patterns in intelligence_extractor.py

### If Callbacks Fail:
- Check network connectivity to hackathon endpoint
- Verify payload structure matches spec
- Review CALLBACK logs for error messages

### If Response Time is High:
- Check which operations are slow (GENERATION vs EXTRACTION)
- Consider caching or parallel processing
- Review backfill extraction frequency

## Example Analysis Workflow

After running 10 initial test cases:

```bash
# 1. Analyze logs
python3 analyze_logs.py

# 2. Check specific session
curl -H "x-api-key: YOUR_KEY" \
  https://your-api.com/debug/session/SESSION_ID

# 3. Get live performance stats
curl -H "x-api-key: YOUR_KEY" \
  https://your-api.com/hackathon/performance

# 4. Review full log file
grep "LLM_FAILURE" hackathon_performance.log | head -5
grep "EXTRACTION" hackathon_performance.log | grep "phone_numbers"
```

## Pre-Submission Checklist

- [ ] LLM usage > 60%
- [ ] Callback success rate = 100%
- [ ] Average extractions > 5 per session
- [ ] All critical intel types being extracted
- [ ] Response time < 3 seconds (P95)
- [ ] No repeated failures in logs
- [ ] Strategy changes happening appropriately
- [ ] Finalization triggers are balanced (not all hard_limit)

## Questions to Answer from Logs

1. **Is the LLM working?** → Check GENERATION logs for LLM_GEMINI percentage
2. **Are we extracting enough?** → Check EXTRACTION totals by type
3. **Are callbacks succeeding?** → Check CALLBACK success rate
4. **Is the system fast enough?** → Check API response times
5. **Are we adapting strategies?** → Check STRATEGY change frequency
6. **When do sessions end?** → Check FINALIZATION triggers

## Additional Tools

- **grep for patterns**: `grep "phone_numbers" hackathon_performance.log`
- **Count events**: `grep -c "CALLBACK:" hackathon_performance.log`
- **Find failures**: `grep "LLM_FAILURE\|error\|failed" hackathon_performance.log`
- **Track session**: `grep "SESSION_ID" hackathon_performance.log`

Good luck in the hackathon! 🏆
