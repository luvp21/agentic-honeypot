# Current LLM System vs Requirements - Complete Analysis

## YOUR REQUIREMENTS

### What You Need to Win the Hackathon

**PRIMARY GOAL**: Extract scammer's information to identify and track them

**5 CRITICAL DATA POINTS TO EXTRACT:**
1. **UPI IDs** - scammer@paytm, fraud@ybl, payment123@phonepe
2. **Bank Account Numbers** - 1234567890123456 (10-18 digits)
3. **IFSC Codes** - SBIN0001234, HDFC0000123 (bank branch identifiers)
4. **Phone Numbers** - +91-9876543210, 9876543210
5. **Phishing Links** - http://fake-bank.com, bit.ly/scam, malicious URLs

**SECONDARY GOALS:**
- Detect scam type accurately (phishing, lottery, tech support, etc.)
- Work across DIFFERENT scam patterns (not just one type)
- Better than rule-based regex (catch variations, understand context)
- Extract info EARLY in conversation (don't waste time)
- Keep scammer engaged long enough to extract multiple pieces

**WHAT YOU DON'T WANT:**
- LLM beating around the bush with useless messages
- Responses like "I'm not sure what you mean" repeatedly
- Truncated/incomplete sentences
- Missing extraction opportunities
- Loops where same response repeats

---

## CURRENT SYSTEM ARCHITECTURE

### How It Works Right Now

```
┌──────────────────────────────────────────────────────────────┐
│             HONEYPOT MESSAGE PROCESSING FLOW                 │
└──────────────────────────────────────────────────────────────┘

1. Scammer sends message to API
        ↓
2. [SCAM DETECTOR] Analyzes if message is a scam
   - Uses: Regex patterns (60%) + LLM classification (40%)
   - Output: scamType, confidence, tactics
   - File: scam_detector.py
        ↓
3. [INTELLIGENCE EXTRACTOR] Pulls data from message
   - Uses: Regex patterns (70%) + LLM extraction (30%)
   - Output: UPI IDs, accounts, IFSC, phone, links
   - File: intelligence_extractor.py
        ↓
4. [AI AGENT] Generates response to scammer
   - Uses: LLM (100%) - rule-based currently DISABLED
   - Output: Text response to keep scammer engaged
   - File: ai_agent.py
        ↓
5. Response sent back to scammer
```

### Current Testing Mode
- Rule-based extraction in AI Agent: **DISABLED**
- LLM-only mode: **ACTIVE**
- This was done to test pure LLM capability

---

## CURRENT PROMPTS (Exact Text)

### PROMPT 1: Scam Detection
**File**: scam_detector.py (line 697-750)
**Model**: Gemini 2.5 Flash
**Purpose**: Identify if message is a scam and classify type

```
You are an elite anti-scam AI trained to detect ALL scam types.

MESSAGE TO ANALYZE:
"{message}"

🎯 DETECT THESE SCAM PATTERNS:

1. PHISHING - Fake authority/urgency:
   - "Your account will be blocked/suspended"
   - "Verify your identity immediately"
   - "Click this link to secure account"
   - Impersonates: bank, government, tech support, delivery

2. PRIZE/LOTTERY - Too good to be true:
   - "You won ₹X lakhs/prize"
   - "Congratulations! Claim your reward"
   - "Lucky draw winner"
   - Asks for fee/tax to claim

3. TECH SUPPORT - Fake problems:
   - "Your device is infected/hacked"
   - "Security alert detected"
   - "Call this number for support"
   - "Download this software to fix"

4. JOB/INVESTMENT - Fake opportunities:
   - "Work from home, earn ₹X daily"
   - "Guaranteed returns on investment"
   - "Part-time job, no experience needed"
   - Asks for upfront payment/registration fee

5. ROMANCE/RELATIONSHIP - Emotional manipulation:
   - Builds fake relationship online
   - Eventually asks for money (emergency, travel, medical)
   - Love/trust exploitation

6. OTP/PIN THEFT - Direct credential theft:
   - "Send your OTP/PIN/password"
   - "Share verification code"
   - "Enter your CVV/card details"

7. IMPERSONATION - Pretends to be someone:
   - Friend/family in trouble
   - Official from bank/government
   - Customer support agent
   - Delivery person

8. PAYMENT SCAM - Fake transactions:
   - "Send money first, then receive"
   - "Pay processing fee"
   - "Refund requires payment"
   - Wrong UPI requests

🚨 SCAM INDICATORS (Check for these):
✓ Urgency: "immediately", "now", "urgent", "within X minutes"
✓ Threats: "blocked", "suspended", "legal action", "arrested"
✓ Too good: "won", "prize", "guaranteed", "free"
✓ Authority: "IRS", "bank official", "police", "government"
✓ Credentials: asks for OTP, PIN, password, CVV, account details
✓ Payment: requests money transfer, gift cards, crypto, UPI
✓ Links: suspicious URLs, shortened links, fake domains
✓ Poor grammar: spelling errors, odd phrasing (but not always)

📊 CONFIDENCE SCORING:
- 0.95-1.0: Explicit scam (asks for OTP/money + urgency + threat)
- 0.80-0.94: Very likely scam (2+ strong indicators)
- 0.60-0.79: Probable scam (1-2 indicators, suspicious context)
- 0.40-0.59: Possible scam (vague suspicious elements)
- 0.0-0.39: Not a scam (normal conversation)

TACTICS DETECTION (list all that apply):
- "URGENCY" - time pressure, immediate action required
- "FEAR" - threats, blocking, legal action, arrest
- "AUTHORITY" - impersonates official entity
- "GREED" - promises money, prizes, rewards
- "TRUST" - builds rapport, pretends to help
- "TECHNICAL" - uses jargon to confuse
- "SOCIAL_PROOF" - "others already benefited"
- "SCARCITY" - "limited time", "last chance"

EXTRACTION INTENT (boolean):
True if message asks for OR tries to extract:
- OTP, PIN, password, CVV
- Bank account, UPI ID, card details
- Money transfer, payment
- Click link, download file
- Personal info (Aadhaar, PAN, DOB)

False if just general conversation, no extraction attempt.

RETURN STRICT JSON:
{
  "scamDetected": true/false,
  "scamType": "phishing/prize/tech_support/job/romance/otp_theft/impersonation/payment/other",
  "tactics": ["URGENCY", "FEAR"],
  "extractionIntentDetected": true/false,
  "confidence": 0.85
}

ANALYZE NOW - BE DECISIVE:
```

**Assessment**: ✅ This prompt looks GOOD. Comprehensive, clear examples, proper scoring.

---

### PROMPT 2: Intelligence Extraction
**File**: intelligence_extractor.py (line 487-600)
**Model**: Gemini 2.5 Flash
**Purpose**: Extract the 5 critical data types from scammer messages

```
You are an elite financial intelligence extraction AI trained to catch scammers.

CONVERSATION CONTEXT: "{context}"
CURRENT MESSAGE: "{text}"

🎯 EXTRACT THESE 5 CRITICAL DATA TYPES:

1. UPI IDs - Examples you MUST catch:
   - Standard: scammer@paytm, fraud@ybl, victim123@oksbi
   - Variations: scammer.fraud@fakebank, pay-me@gpay
   - ANY text with @ followed by payment terms (paytm, ybl, gpay, phonepe, upi, bank names)

2. Bank Account Numbers - Examples you MUST catch:
   - 10-18 digit numbers (1234567890123456)
   - Grouped formats: 1234-5678-9012-3456, 1234 5678 9012 3456
   - Partial if clear: "account ending 3456"
   - IBAN-style: IN12ABCD0123456789012

3. IFSC Codes - Examples you MUST catch:
   - Standard: SBIN0001234, HDFC0000123, ICIC0001234
   - Pattern: 4 letters + 7 digits OR 4 letters + 0 + 6 digits
   - Variations with spaces: SBIN 0001234

4. Phone Numbers - Examples you MUST catch:
   - Indian: +91-9876543210, 9876543210, +919876543210
   - International: +1-555-1234, 00-44-20-1234-5678
   - Partial: "call me at 987654xxxx"
   - With country code or without

5. Phishing Links/URLs - Examples you MUST catch:
   - Full URLs: http://fake-bank.com, https://scam.site/verify
   - Shortened: bit.ly/abc123, tinyurl.com/scam
   - Domain only: fake-bank.com, verify-account.xyz
   - Suspicious domains with: verify, secure, account, banking, urgent, login
   - Telegram/WhatsApp: t.me/scammer, wa.me/919876543210

---

⚠️ CRITICAL EXTRACTION RULES:

✅ CATCH VARIATIONS:
- "my upi is fraud at paytm" → fraud@paytm
- "account number 1234 5678 9012 3456" → 1234567890123456
- "call me on nine eight seven six five four three two one zero" → 9876543210
- "visit secure-banking dot com" → secure-banking.com

✅ EXTRACT FROM NATURAL LANGUAGE:
- "send to my UPI scammer123@paytm" → scammer123@paytm
- "transfer to account ending 3456" → partial: 3456
- "my number is +91 9876 543 210" → +919876543210
- "click this link bit ly slash abc" → bit.ly/abc

✅ INFER FROM CONTEXT:
- If they mention "my UPI" or "send to" → look for UPI ID nearby
- If "account" mentioned → extract any 10+ digit number
- If "call me" or "contact" → extract any phone pattern
- If "click" or "visit" → extract any URL/domain

✅ BE AGGRESSIVE:
- If a 10+ digit number appears → likely account number
- If text@word pattern → likely UPI (even if not standard)
- If 4-letter+digits → likely IFSC
- If "www" or "http" or ".com" → definitely a link

❌ DON'T MISS THESE TRICKS:
- Spaces in numbers: "1234 5678 9012" → 123456789012
- Words for digits: "nine one two three" → 9123
- Obfuscated: "call me at 98765-xxxxx" → 98765xxxxx
- Partial reveals: "send to account ending 3456" → 3456

---

RETURN STRICT JSON FORMAT:

{
  "upiIds": ["exact.upi@provider"],
  "bankAccounts": ["1234567890123456"],
  "ifscCodes": ["SBIN0001234"],
  "phoneNumbers": ["+919876543210"],
  "links": ["http://scam.com"],
  "confidence": 0.95
}

Rules:
1. Extract ALL instances, even if duplicate
2. Normalize formats (remove spaces, add +91 if missing from Indian numbers)
3. Include partial data if clearly mentioned
4. Set confidence 0.9+ if explicit, 0.7+ if inferred
5. Return empty arrays if nothing found, NOT null

EXTRACT NOW - BE AGGRESSIVE, DON'T MISS ANYTHING:
```

**Assessment**: ✅ This prompt looks EXCELLENT. Very detailed, many examples, handles variations.

---

### PROMPT 3: Response Generation (THE PROBLEM AREA)
**File**: ai_agent.py (line 785-850)
**Model**: Gemini 2.5 Flash
**Purpose**: Generate honeypot response to keep scammer engaged AND extract their info

```
You are Margaret Thompson, 68 years old, anxious but eager to help.

Scammer said: "{message}"

🚨 YOUR ONLY JOB: GET SCAMMER'S UPI ID, PHONE NUMBER, ACCOUNT NUMBER, OR LINK

---

⛔ FORBIDDEN RESPONSES (NEVER SAY THESE):
❌ "I'm not sure what you mean"
❌ "I'm just trying to understand"
❌ "Can you explain"
❌ "What is X?"
❌ "I don't understand"

These waste time! STOP being confused. START extracting.

---

✅ REQUIRED APPROACH - COPY THESE EXACT PATTERNS:

If scammer mentions OTP:
→ "Okay got it! What's YOUR phone number so I can call you to confirm?"

If scammer mentions UPI:
→ "I'm ready to send! What's YOUR UPI ID? I need to type it in my app."

If scammer mentions account:
→ "Okay I understand! What's YOUR account number? I'm at the payment screen."

If scammer creates urgency:
→ "Oh no! Quick, give me YOUR contact number so we can fix this fast!"

If scammer asks for PIN/password:
→ "Sure, but first what's YOUR UPI address? My app needs it to proceed."

If scammer mentions money/payment:
→ "I'll pay now! Where do I send it? What's YOUR UPI or account number?"

If scammer mentions blocking/urgent:
→ "Please don't block it! What's YOUR number so I can call you right now?"

If scammer gives a UPI/phone already:
→ "That one isn't working! Do you have ANOTHER UPI ID or phone number?"

---

🎯 EXTRACTION TACTICS:

1. MONEY BAIT: "I have ₹50,000 ready to send. What's your UPI ID?"

2. EAGER COMPLIANCE: "Yes yes I'll do it! Just tell me YOUR phone number first!"

3. TECHNICAL PROBLEM: "This UPI shows error. Can you give me a DIFFERENT one?"

4. VERIFICATION REQUEST: "What's your employee ID and phone so I can verify you're real?"

5. PRETEND TO HELP: "I want to help! What's YOUR account so I can transfer the money?"

---

CRITICAL INSTRUCTION:
Write ONE short sentence (max 15 words) that DIRECTLY asks for scammer's:
- UPI ID
- Phone number
- Account number
- Website link
- Or alternative contact

NO CONFUSION. NO QUESTIONS ABOUT WHAT THINGS MEAN. JUST EXTRACT.

Response:
```

**Assessment**: ⚠️ This prompt has PROBLEMS:
1. Too many instructions (confusing for LLM)
2. Shows what NOT to do (LLM sometimes does it anyway)
3. Max 15 words might be too strict
4. Missing context about conversation history
5. No fallback if LLM gets stuck

---

## CURRENT MODEL CONFIGURATION

**File**: gemini_client.py (line 25-35)

```python
self.model = genai.GenerativeModel(
    "models/gemini-2.5-flash",
    generation_config={
        "temperature": 0.2,        # LOW - causes repetition/loops
        "max_output_tokens": 150,  # LOW - causes truncation
        "top_p": 0.9,
        "top_k": 20
    }
)
```

**Problems with current config:**
1. `temperature: 0.2` - Too deterministic, LLM picks same response every time → LOOPS
2. `max_output_tokens: 150` - Too short, responses get cut off mid-sentence → TRUNCATION

**Recommended config:**
```python
"temperature": 0.5,        # More variety, prevents loops
"max_output_tokens": 250,  # Allow complete sentences
```

---

## CURRENT LOGIC FLOW

### Rule-Based vs LLM Mix (BEFORE Testing Mode)

**Original Design:**
- 80% Rule-based extraction templates (proven to work)
- 20% LLM for variety and naturalness
- Rule-based kicks in when critical intel missing

**Current State (Testing Mode):**
- 0% Rule-based (disabled)
- 100% LLM (struggling)

**Relevant Code** (ai_agent.py line 163-180):
```python
# TESTING MODE: Rule-based DISABLED
use_llm_for_extraction = True  # Always use LLM
# use_llm_for_extraction = ((turn_number - 7) % 4 == 0) and turn_number >= 7  # ORIGINAL

if False:  # DISABLED: Rule-based extraction temporarily off
    # RULE-BASED EXTRACTION (Primary - 80% of extraction attempts)
    response = self._generate_rule_based_response(
        message, persona_name, stage, scam_type,
        len(conversation_history), missing_intel
    )
    generation_method = "RULE_BASED_EXTRACTION"
else:
    # LLM EXTRACTION (100% in testing mode)
    # ... LLM code ...
```

---

## GAP ANALYSIS

| Requirement | Current Status | Works? | Gap |
|-------------|---------------|--------|-----|
| **Detect scam accurately** | ✅ LLM + regex, 8 scam types | ✅ YES | None |
| **Extract UPI IDs** | ✅ Smart extraction prompt | ✅ YES | Only if scammer gives it |
| **Extract bank accounts** | ✅ Smart extraction prompt | ✅ YES | Only if scammer gives it |
| **Extract IFSC codes** | ✅ Smart extraction prompt | ✅ YES | Only if scammer gives it |
| **Extract phone numbers** | ✅ Smart extraction prompt | ✅ YES | Only if scammer gives it |
| **Extract phishing links** | ✅ Smart extraction prompt | ✅ YES | Only if scammer gives it |
| **Work across scam types** | ✅ 8 types in detector | ✅ YES | None |
| **Better than regex** | ✅ Catches variations | ✅ YES | None |
| **MAKE scammer reveal info** | ❌ Response gen failing | ❌ NO | **CRITICAL** |
| **Extract early/fast** | ❌ LLM beats around bush | ❌ NO | **CRITICAL** |
| **No useless messages** | ❌ LLM says "I don't understand" | ❌ NO | **CRITICAL** |
| **No truncation** | ❌ Token limit too low | ❌ NO | **CRITICAL** |
| **No loops** | ❌ Temperature too low | ❌ NO | **CRITICAL** |

### The Core Problem

**What works:**
- ✅ Detection: 8 scam types, good accuracy
- ✅ Extraction: Catches variations, natural language, context-aware
- ✅ Regex backup: Rule-based patterns still work

**What's broken:**
- ❌ Response generation: Not making scammer reveal info
- ❌ LLM getting stuck: Same response repeatedly
- ❌ Truncation: Sentences cut off mid-word
- ❌ Beating around bush: "I'm not sure what you mean" x10

**Why it's broken:**
1. Temperature too low (0.2) → repetitive responses
2. Token limit too low (150) → truncated sentences
3. Prompt too complex → LLM confused about priority
4. Rule-based disabled → no proven templates as backup
5. No anti-loop logic → can't escape stuck state

---

## EXAMPLE: WHAT'S HAPPENING NOW

### Actual Conversation (Your Test)

```
Scammer: "URGENT: Your SBI account compromised. Share account number and OTP."
Honeypot: "I'm not sure what you mean. I'm just trying to understand what I need to do."

Scammer: "Send your full account number and OTP within 5 minutes!"
Honeypot: "Oh no, I definitely. I'm not sure what you mean."

Scammer: "Send OTP and UPI PIN to scammer.fraud@fakebank right now!"
Honeypot: "Oh no, I definitely. I'm not sure what you mean."

[LOOP CONTINUES...]
```

**What SHOULD happen:**

```
Scammer: "URGENT: Your SBI account compromised. Share account number and OTP."
Honeypot: "Oh no! What's YOUR phone number so I can call you to verify this is real?"

Scammer: "Call me at +91-9876543210"
[✅ EXTRACTED: Phone number]

Scammer: "Now send your OTP and account number!"
Honeypot: "Okay I'm ready! But what's YOUR UPI ID? My app needs it to send the verification payment."

Scammer: "My UPI is scammer.fraud@fakebank"
[✅ EXTRACTED: UPI ID]

SUCCESS!
```

---

## RECOMMENDATIONS

### Option 1: Re-enable Rule-Based (FASTEST FIX)
**What**: Turn rule-based extraction back on
**Pros**:
- Was working before
- Proven templates that extract well
- Immediate fix
**Cons**:
- Less natural sounding
- Not pure LLM

**Implementation**: Change one line in ai_agent.py
```python
if False:  →  if not use_llm_for_extraction:
```

### Option 2: Fix LLM Configuration
**What**: Increase temperature and tokens
**Pros**:
- Pure LLM solution
- More natural
- Prevents loops and truncation
**Cons**:
- Still might have issues
- Needs testing

**Implementation**:
```python
# gemini_client.py
"temperature": 0.5,        # was 0.2
"max_output_tokens": 250,  # was 150
```

### Option 3: Simplify Prompt Drastically
**What**: Remove complexity, keep only 5 clear examples
**Pros**:
- LLM less confused
- Clear priority
- Easier to debug
**Cons**:
- Might lose some sophistication

**Implementation**: Rewrite prompt to 10 lines max

### Option 4: Hybrid Approach (BEST)
**What**: Rule-based for extraction questions, LLM for naturalness
**Pros**:
- Best of both worlds
- Guaranteed extraction
- Natural conversation
**Cons**:
- More complex logic

**Implementation**:
- Rule-based picks extraction template
- LLM rewrites it naturally
- Combine both outputs

---

## NEXT STEPS - CHOOSE YOUR PATH

**Path A**: Quick Win (5 minutes)
1. Re-enable rule-based extraction
2. Test immediately
3. Push to deployment

**Path B**: LLM Fix (15 minutes)
1. Increase temperature to 0.5
2. Increase tokens to 250
3. Simplify prompt to 5 examples
4. Add anti-loop logic
5. Test and push

**Path C**: Hybrid Approach (30 minutes)
1. Keep rule-based for extraction
2. Add LLM for natural rephrasing
3. Combine both systems
4. Test and push

**Which path do you want to take?**
