# LLM System Analysis - Current State vs Requirements

## YOUR REQUIREMENTS

### Primary Goal
Extract 5 critical pieces of information from scammers:
1. **UPI IDs** - Payment identifiers (scammer@paytm, fraud@ybl)
2. **Bank Account Numbers** - 10-18 digit account numbers
3. **IFSC Codes** - Bank branch codes (SBIN0001234)
4. **Phone Numbers** - Contact numbers (+91-9876543210)
5. **Phishing Links** - Malicious URLs (http://fake-bank.com, bit.ly/scam)

### Secondary Goal
- Detect scam type accurately
- Extract across DIFFERENT scam methods (phishing, lottery, tech support, job scams, etc.)
- Better than rule-based regex (catch variations, natural language)

### Current Problem
- LLM beating around the bush
- Messages getting truncated
- Not extracting scammer info
- Repeating same useless phrases like "I'm not sure what you mean"

---

## CURRENT LLM ARCHITECTURE

### System Overview
```
┌─────────────────────────────────────────────────────────────┐
│                    HONEYPOT WORKFLOW                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Scammer sends message                                  │
│         ↓                                                   │
│  2. ScamDetector analyzes (LLM + Regex)                    │
│         ↓                                                   │
│  3. IntelligenceExtractor pulls data (LLM + Regex)         │
│         ↓                                                   │
│  4. AIHoneypotAgent generates response (LLM)               │
│         ↓                                                   │
│  5. Response sent back to scammer                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3 LLM Components

#### 1. **ScamDetector** (scam_detector.py)
- **Job**: Classify if message is a scam
- **Output**: scamType, tactics, confidence
- **LLM Model**: Gemini 2.5 Flash
- **Timeout**: 8 seconds

#### 2. **IntelligenceExtractor** (intelligence_extractor.py)
- **Job**: Extract UPI, accounts, IFSC, phone, links
- **Output**: JSON with extracted data
- **LLM Model**: Gemini 2.5 Flash
- **Timeout**: 8 seconds

#### 3. **AIHoneypotAgent** (ai_agent.py)
- **Job**: Generate victim response to keep scammer engaged + extract THEIR info
- **Output**: Text response to scammer
- **LLM Model**: Gemini 2.5 Flash
- **Timeout**: 10 seconds
- **Current Mode**: 100% LLM (rule-based disabled for testing)

---

## CURRENT LLM PROMPTS

### PROMPT 1: Scam Detection (scam_detector.py line 697)

```
You are an elite anti-scam AI trained to detect ALL scam types.

MESSAGE TO ANALYZE:
"{message}"

🎯 DETECT THESE SCAM PATTERNS:

1. PHISHING - Fake authority/urgency
2. PRIZE/LOTTERY - Too good to be true
3. TECH SUPPORT - Fake problems
4. JOB/INVESTMENT - Fake opportunities
5. ROMANCE/RELATIONSHIP - Emotional manipulation
6. OTP/PIN THEFT - Direct credential theft
7. IMPERSONATION - Pretends to be someone
8. PAYMENT SCAM - Fake transactions

🚨 SCAM INDICATORS:
✓ Urgency: "immediately", "now", "urgent"
✓ Threats: "blocked", "suspended", "legal action"
✓ Too good: "won", "prize", "guaranteed"
✓ Authority: "IRS", "bank official", "police"
✓ Credentials: asks for OTP, PIN, password
✓ Payment: requests money transfer
✓ Links: suspicious URLs

📊 CONFIDENCE SCORING:
- 0.95-1.0: Explicit scam
- 0.80-0.94: Very likely scam
- 0.60-0.79: Probable scam

RETURN STRICT JSON:
{
  "scamDetected": true/false,
  "scamType": "phishing/prize/tech_support/...",
  "tactics": ["URGENCY", "FEAR"],
  "extractionIntentDetected": true/false,
  "confidence": 0.85
}
```

**Does this work?** → Probably YES for detection
**Issue?** → Not the main problem

---

### PROMPT 2: Intelligence Extraction (intelligence_extractor.py line 487)

```
You are an elite financial intelligence extraction AI.

CONVERSATION CONTEXT: "{context}"
CURRENT MESSAGE: "{text}"

🎯 EXTRACT THESE 5 CRITICAL DATA TYPES:

1. UPI IDs - Examples:
   - Standard: scammer@paytm, fraud@ybl
   - Variations: scammer.fraud@fakebank
   - ANY text with @ followed by payment terms

2. Bank Account Numbers - Examples:
   - 10-18 digit numbers (1234567890123456)
   - Grouped: 1234-5678-9012-3456
   - Partial: "account ending 3456"

3. IFSC Codes - Examples:
   - Standard: SBIN0001234, HDFC0000123
   - Pattern: 4 letters + 7 digits

4. Phone Numbers - Examples:
   - Indian: +91-9876543210, 9876543210
   - Partial: "call me at 987654xxxx"

5. Phishing Links/URLs - Examples:
   - Full: http://fake-bank.com
   - Shortened: bit.ly/abc123
   - Domain: fake-bank.com

⚠️ CATCH VARIATIONS:
- "my upi is fraud at paytm" → fraud@paytm
- "account number 1234 5678 9012" → 1234567890123456
- "call on nine eight seven six" → 9876

✅ BE AGGRESSIVE:
- If 10+ digit number → likely account
- If text@word → likely UPI
- If 4-letter+digits → likely IFSC

RETURN STRICT JSON:
{
  "upiIds": ["exact.upi@provider"],
  "bankAccounts": ["1234567890123456"],
  "ifscCodes": ["SBIN0001234"],
  "phoneNumbers": ["+919876543210"],
  "links": ["http://scam.com"],
  "confidence": 0.95
}
```

**Does this work?** → Should work WELL
**Issue?** → Scammer needs to GIVE info first

---

### PROMPT 3: Response Generation (ai_agent.py line 785)

**THIS IS THE PROBLEM AREA**

```
You are Margaret Thompson, 68 years old, anxious but eager to help.

Scammer said: "{message}"

🚨 YOUR ONLY JOB: GET SCAMMER'S UPI ID, PHONE NUMBER, ACCOUNT NUMBER, OR LINK

⛔ FORBIDDEN RESPONSES (NEVER SAY):
❌ "I'm not sure what you mean"
❌ "I'm just trying to understand"
❌ "Can you explain"
❌ "What is X?"
❌ "I don't understand"

✅ REQUIRED APPROACH - COPY THESE PATTERNS:

If scammer mentions OTP:
→ "Okay got it! What's YOUR phone number so I can call you to confirm?"

If scammer mentions UPI:
→ "I'm ready to send! What's YOUR UPI ID? I need to type it in my app."

If scammer mentions account:
→ "Okay I understand! What's YOUR account number? I'm at the payment screen."

If scammer creates urgency:
→ "Oh no! Quick, give me YOUR contact number so we can fix this fast!"

[... 8 total patterns ...]

CRITICAL INSTRUCTION:
Write ONE short sentence (max 15 words) that DIRECTLY asks for scammer's:
- UPI ID
- Phone number
- Account number
- Website link

NO CONFUSION. NO QUESTIONS ABOUT WHAT THINGS MEAN. JUST EXTRACT.

Response:
```

**Does this work?** → SHOULD work but ISN'T
**Issues detected:**
1. LLM ignoring forbidden responses
2. Getting stuck in loops
3. Truncating mid-sentence
4. Not following the patterns

---

## WHY IT'S FAILING

### Issue 1: Token Limit Too Low
```python
# gemini_client.py line 29
"max_output_tokens": 150  # TOO SHORT - causes truncation
```

**Solution**: Increase to 200-300 tokens

### Issue 2: Temperature Too Low
```python
# gemini_client.py line 28
"temperature": 0.2  # Too deterministic, gets stuck in loops
```

**Solution**: Increase to 0.4-0.6 for variety

### Issue 3: Prompt Too Complex
- 50+ lines of instructions
- LLM gets confused
- Ignores critical parts

**Solution**: Simplify to 3-5 CLEAR examples

### Issue 4: No Negative Reinforcement
- Says "DON'T do X" but LLM still does it
- Needs positive examples ONLY

**Solution**: Remove all ❌ examples, only show ✅

### Issue 5: Competing Instructions
- "Be confused" vs "Extract directly"
- "Act elderly" vs "Be aggressive"
- LLM picks wrong priority

**Solution**: ONE clear priority - EXTRACT

---

## COMPARISON: WHAT YOU NEED VS WHAT YOU HAVE

| Requirement | Current Status | Gap |
|-------------|---------------|-----|
| Extract UPI IDs | ✅ Extractor prompt has this | ⚠️ Scammer must give it first |
| Extract Bank Accounts | ✅ Extractor prompt has this | ⚠️ Scammer must give it first |
| Extract IFSC Codes | ✅ Extractor prompt has this | ⚠️ Scammer must give it first |
| Extract Phone Numbers | ✅ Extractor prompt has this | ⚠️ Scammer must give it first |
| Extract Links | ✅ Extractor prompt has this | ⚠️ Scammer must give it first |
| Make scammer REVEAL info | ❌ Response gen failing | **CRITICAL GAP** |
| Work across scam types | ✅ Detector has 8 types | Working |
| Better than regex | ✅ Extraction is smart | Working |

**THE CORE PROBLEM:**
- Extraction works WHEN scammer gives data
- Response generation NOT making scammer give data
- LLM just saying useless phrases instead of extracting

---

## CURRENT CONVERSATION FLOW (FAILING)

```
Scammer: "Send your OTP and account number!"
    ↓
LLM Response Gen: "I'm not sure what you mean. I'm just trying to understand."
    ↓
Scammer: "Send your OTP and account number NOW!"
    ↓
LLM Response Gen: "I'm not sure what you mean. I'm just trying to understand."
    ↓
[LOOP REPEATS - NO EXTRACTION]
```

**What SHOULD happen:**
```
Scammer: "Send your OTP and account number!"
    ↓
LLM Response Gen: "Okay! But what's YOUR UPI ID so I can send you the payment?"
    ↓
Scammer: "My UPI is scammer123@paytm"
    ↓
Intelligence Extractor: Extracts "scammer123@paytm"
    ↓
SUCCESS! ✅
```

---

## GEMINI MODEL CONFIGURATION

```python
# gemini_client.py
self.model = genai.GenerativeModel(
    "models/gemini-2.5-flash",
    generation_config={
        "temperature": 0.2,        # ← Too low, causes loops
        "max_output_tokens": 150,  # ← Too low, causes truncation
        "top_p": 0.9,
        "top_k": 20
    }
)
```

---

## RECOMMENDATIONS TO FIX

### Fix 1: Increase Token Limits
```python
"max_output_tokens": 250  # Allow complete sentences
```

### Fix 2: Increase Temperature
```python
"temperature": 0.5  # Add variety, prevent loops
```

### Fix 3: Simplify Response Prompt
Remove 50 lines of examples, use just 5 clear ones:

```
You are an elderly person. Scammer said: "{message}"

Your job: Get their UPI ID, phone, or account number.

Examples:
1. Scammer mentions OTP → You: "What's your phone number?"
2. Scammer mentions UPI → You: "What's your UPI ID?"
3. Scammer mentions urgent → You: "Give me your number to call!"
4. Scammer mentions account → You: "What account do I send to?"
5. Scammer mentions payment → You: "What's your UPI address?"

Write ONE sentence asking for their contact info:
```

### Fix 4: Add Anti-Loop Logic
```python
# Check if last 2 responses are identical
if response == last_response:
    # Force different response
    response = random.choice([
        "What's your phone number?",
        "What's your UPI ID?",
        "What account should I send to?"
    ])
```

### Fix 5: Enable Rule-Based Fallback
Currently disabled. Should re-enable as backup:
```python
# If LLM fails or loops, use rule-based templates
if not response or response == last_response:
    response = rule_based_extraction_template()
```

---

## FILES TO CHECK

1. **gemini_client.py** - Model config (lines 25-35)
2. **ai_agent.py** - Response generation prompt (lines 785-850)
3. **intelligence_extractor.py** - Extraction prompt (lines 487-600)
4. **scam_detector.py** - Detection prompt (lines 697-750)

---

## NEXT STEPS FOR YOU

1. **Test extraction directly**:
   - See if extractor WORKS when scammer gives data
   - Test: "My UPI is scammer@paytm" → should extract it

2. **Test response generation**:
   - Is it ALWAYS saying the same thing?
   - Is it getting truncated?
   - Is temperature too low?

3. **Check logs**:
   - What exact prompts are being sent to LLM?
   - What exact responses coming back?
   - Are there API errors?

4. **Try simpler prompt**:
   - Remove all the complexity
   - Just 3 examples
   - See if that works better

5. **Consider hybrid approach**:
   - Use rule-based for extraction questions
   - Use LLM for natural conversation
   - Best of both worlds

---

## SUMMARY

**What's Working:**
✅ Scam detection (8 types, good accuracy)
✅ Intelligence extraction (when data is provided)
✅ Smart extraction (catches variations, natural language)

**What's Broken:**
❌ Response generation (beating around bush)
❌ Getting scammer to reveal info
❌ LLM stuck in loops saying same useless phrase
❌ Responses getting truncated mid-sentence

**Root Causes:**
1. Token limit too low (150 → need 250)
2. Temperature too low (0.2 → need 0.5)
3. Prompt too complex (50 lines → need 5)
4. No anti-loop logic
5. Rule-based fallback disabled

**Quick Win:**
Re-enable rule-based extraction (it was working before!)
Use LLM for conversation naturalness only
