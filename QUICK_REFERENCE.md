# 🎯 Hackathon Quick Reference Card

## Your Submission Details
- **API URL**: `https://luvp2112-agentic-honeypot.hf.space/api/honeypot/message`
- **API Key**: Include as header `x-api-key: honeypot-secret-key-123`
- **Method**: POST
- **Content-Type**: application/json

## After Each Test Run

### 1. Quick Stats Check
```bash
curl -H "x-api-key: honeypot-secret-key-123" \
  https://luvp2112-agentic-honeypot.hf.space/hackathon/performance | jq
```

### 2. Full Analysis (Run Locally)
```bash
# SSH into your server or download logs, then:
python3 analyze_logs.py hackathon_performance.log
```

## Key Metrics to Track

| Metric | Target | Where to Check |
|--------|--------|----------------|
| LLM Usage | >60% | analyze_logs.py output |
| Callback Success | 100% | /hackathon/performance endpoint |
| Avg Extractions/Session | >5 | analyze_logs.py → "Intelligence Extraction" |
| API Response Time | <3s | analyze_logs.py → "API Response Times" |
| Phone Number Extraction | High | Check phone_numbers count |
| UPI ID Extraction | High | Check upi_ids count |

## What to Monitor During 10 Initial Tests

1. **Test 1-3**: Watch for any errors, verify callbacks are sent
2. **Test 4-6**: Check LLM vs rule-based ratios
3. **Test 7-10**: Analyze extraction patterns

## Red Flags 🚩

- ❌ Callback failure rate > 0%
- ❌ LLM usage < 40%
- ❌ Response time > 5 seconds
- ❌ Zero phone_numbers or upi_ids extracted across all tests
- ❌ Sessions ending at turn 1-2 (too early)

## Green Flags ✅

- ✅ 100% callback success
- ✅ LLM usage 60-80%
- ✅ Average 10-13 turns per session
- ✅ 5+ intelligence items per session
- ✅ All critical intel types being extracted
- ✅ Response time <2 seconds

## Optimization Commands

### Check LLM Failures
```bash
grep "LLM_FAILURE" hackathon_performance.log
```

### See What's Being Extracted
```bash
grep "EXTRACTION" hackathon_performance.log | grep "phone_numbers"
grep "EXTRACTION" hackathon_performance.log | grep "upi_ids"
```

### Track Specific Session
```bash
grep "SESSION_ID_HERE" hackathon_performance.log
```

### Count Successful Callbacks
```bash
grep "CALLBACK" hackathon_performance.log | grep "\"success\": true" | wc -l
```

## Pre-Final Submission Checklist

- [ ] Ran 10+ initial test cases
- [ ] Analyzed `analyze_logs.py` output
- [ ] LLM usage is optimal (>60%)
- [ ] Callback success rate is 100%
- [ ] Extraction counts are high
- [ ] No systematic failures in logs
- [ ] Response times are acceptable
- [ ] Tested with different scam types
- [ ] Verified API is publicly accessible
- [ ] Confirmed API key works

## During Leaderboard Phase

### Monitor Live
```bash
# Every 5 minutes, check:
curl -H "x-api-key: honeypot-secret-key-123" \
  https://luvp2112-agentic-honeypot.hf.space/health

curl -H "x-api-key: honeypot-secret-key-123" \
  https://luvp2112-agentic-honeypot.hf.space/stats
```

### If Issues Arise
1. Check Hugging Face Space logs
2. Verify Gemini API quota not exceeded
3. Check callback endpoint connectivity
4. Review recent performance logs

## Scoring Factors (From Problem Statement)

1. **Scam detection accuracy** → Session scam_detected rate
2. **Engagement duration** → Average turns (target: 10-14)
3. **Number of conversation turns** → Logged in SESSION_SUMMARY
4. **Quality of extracted intelligence** → Diversity and count of intel types
5. **API stability** → Response times and error rate

## Good Luck! 🚀

Remember:
- Data beats intuition - use the logs!
- Test early, optimize based on data
- Monitor during live leaderboard phase
- Stay calm, your system is well-built

**Final tip**: After each official test, immediately run `analyze_logs.py` to spot trends!
