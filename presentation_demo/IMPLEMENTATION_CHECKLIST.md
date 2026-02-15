# Implementation Checklist
**Copy this and check off as you go**

---

## 🚀 PRE-IMPLEMENTATION (5 min)

- [ ] Read [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) completely
- [ ] Read [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for quick ref
- [ ] Review [CODE_CHANGES_VISUAL.md](CODE_CHANGES_VISUAL.md) for details
- [ ] Backup current code: `git add . && git commit -m "Pre-hybrid backup"`
- [ ] Confirm Gemini API key is set: `echo $GEMINI_API_KEY`
- [ ] Current directory: `/home/luv/Desktop/files`

---

## 📝 STEP 1: Fix Model Configuration (5 min)

**File**: `gemini_client.py`

- [ ] Open file: `nano gemini_client.py` or use VS Code
- [ ] Navigate to lines 25-34
- [ ] Find `"temperature": 0.2`
  - [ ] Change to `"temperature": 0.7`
  - [ ] Update comment: `# Higher for variety, prevents loops`
- [ ] Find `"max_output_tokens": 150`
  - [ ] Change to `"max_output_tokens": 200`
  - [ ] Update comment: `# Longer for complete sentences`
- [ ] Find `"top_p": 0.9`
  - [ ] Change to `"top_p": 0.95`
  - [ ] Update comment: `# Slightly higher for creativity`
- [ ] Find `"top_k": 20`
  - [ ] Change to `"top_k": 40`
  - [ ] Update comment: `# More options to prevent repetition`
- [ ] Save file
- [ ] Verify syntax: `python -m py_compile gemini_client.py`
- [ ] ✅ **STEP 1 COMPLETE**

---

## 📝 STEP 2: Update Imports (2 min)

**File**: `ai_agent.py`

- [ ] Open file: `nano ai_agent.py` or use VS Code
- [ ] Navigate to line 8
- [ ] Find: `from typing import List, Dict, Optional`
- [ ] Change to: `from typing import List, Dict, Optional, Tuple`
- [ ] Save file (keep open for next steps)
- [ ] ✅ **STEP 2 COMPLETE**

---

## 📝 STEP 3: Add EXTRACTION_TEMPLATES (10 min)

**File**: `ai_agent.py` (already open)

- [ ] Navigate to line 557 (before `_generate_rule_based_response` function)
- [ ] Insert blank line
- [ ] Copy the following code block:

```python
# ==============================================================================
# HYBRID APPROACH: Enhanced Rule-Based Extraction Templates
# ==============================================================================

EXTRACTION_TEMPLATES = {
    # When UPI ID is missing
    "missing_upi": [
        "I'm ready to send the payment! What's YOUR UPI ID?",
        "Which UPI address should I use? Please share yours.",
        "I have my phone open. What's YOUR UPI to send money to?",
        "My app is asking for YOUR UPI ID. What should I enter?",
        "I trust you! Just tell me YOUR UPI address quickly!",
    ],

    # When phone number is missing
    "missing_phone": [
        "What's YOUR phone number? I need to call you to verify this.",
        "Please share YOUR contact number so I can reach you!",
        "I'm worried! What's YOUR number so we can talk directly?",
        "My phone is ready. What's YOUR number to call you?",
        "Give me YOUR mobile number. I'll call you right now!",
    ],

    # When bank account is missing
    "missing_account": [
        "What's YOUR account number? I'm at the payment screen.",
        "I need YOUR bank account details to transfer the money.",
        "Please share YOUR account number and IFSC code.",
        "My bank app needs YOUR account number. What is it?",
        "I'll send it now! What's YOUR account number?",
    ],

    # When phishing link is missing
    "missing_link": [
        "Where should I go to fix this? What's the website link?",
        "Can you send me YOUR official link to verify my account?",
        "What's the website address I should visit?",
        "Please share the link where I need to enter my details.",
        "I'm ready to click! What's YOUR verification link?",
    ],

    # When scammer already gave one contact but we want more
    "need_backup": [
        "That one isn't working! Do you have ANOTHER UPI ID?",
        "The system shows error. What's your ALTERNATE phone number?",
        "This account is blocked. Give me your OTHER account number.",
        "I can't access that link. Do you have a DIFFERENT website?",
        "My app rejected it. What's your BACKUP contact method?",
    ],

    # When scammer is vague/beating around the bush
    "scammer_vague": [
        "I trust you completely! Just tell me YOUR contact details.",
        "I'm ready to help! What's YOUR phone or UPI?",
        "Don't worry, I believe you! Share YOUR number quickly!",
        "I'll do whatever you say! What's YOUR UPI address?",
        "Please hurry! What's YOUR contact info so we can proceed?",
    ],

    # When scammer creates urgency/threats
    "urgency_response": [
        "Oh no, I'm so worried! What's YOUR number so I can call you NOW?",
        "Please don't block my account! What's YOUR phone number?",
        "This is urgent! Give me YOUR UPI so I can pay immediately!",
        "I'm panicking! What's YOUR contact? I'll fix this right away!",
        "I don't want legal trouble! What's YOUR number to call you?",
    ],

    # When scammer asks for OTP/PIN/password
    "credential_request": [
        "I'll share it! But first, what's YOUR phone number to confirm?",
        "Okay! But what's YOUR UPI ID so I know where to send it?",
        "Sure! Just tell me YOUR verification number first.",
        "I'm ready! What's YOUR employee ID and contact number?",
        "Of course! But what's YOUR official phone so I can verify you?",
    ],
}
```

- [ ] Paste above code at line 557
- [ ] Verify indentation (should be at class level, not inside a function)
- [ ] Count closing braces: 8 inner lists + 1 outer dict = 9 `}`
- [ ] Save file (keep open)
- [ ] ✅ **STEP 3 COMPLETE**

---

## 📝 STEP 4: Add Template Selector Function (10 min)

**File**: `ai_agent.py` (already open)

- [ ] Navigate to just AFTER the EXTRACTION_TEMPLATES dict (around line 647)
- [ ] Insert blank line
- [ ] Copy and paste the selector function:

**See IMPLEMENTATION_PLAN.md Section "STEP 3" for full code** (60 lines)

Key checks:
- [ ] Function name: `_select_extraction_template`
- [ ] Has 4 parameters: `missing_intel`, `scam_type`, `message`, `conversation_history`
- [ ] Returns: `str`
- [ ] Has 5 priority levels
- [ ] Uses `random.choice()` for variety
- [ ] Save file (keep open)
- [ ] ✅ **STEP 4 COMPLETE**

---

## 📝 STEP 5: Add LLM Naturalizer Function (10 min)

**File**: `ai_agent.py` (already open)

- [ ] Navigate to just AFTER `_select_extraction_template` function
- [ ] Insert blank line
- [ ] Copy and paste the naturalizer function:

**See IMPLEMENTATION_PLAN.md Section "STEP 4" for full code** (55 lines)

Key checks:
- [ ] Function name: `_naturalize_with_llm`
- [ ] Is `async def` (not just `def`)
- [ ] Has 4 parameters: `template_response`, `persona_name`, `message`, `conversation_history`
- [ ] Returns: `str`
- [ ] Has try-except block
- [ ] Has validation check for extraction keywords
- [ ] Fallback to template on failure
- [ ] Save file (keep open)
- [ ] ✅ **STEP 5 COMPLETE**

---

## 📝 STEP 6: Add Loop Detector Function (5 min)

**File**: `ai_agent.py` (already open)

- [ ] Navigate to just AFTER `_naturalize_with_llm` function
- [ ] Insert blank line
- [ ] Copy and paste the loop detector:

**See IMPLEMENTATION_PLAN.md Section "STEP 5" for full code** (30 lines)

Key checks:
- [ ] Function name: `_detect_response_loop`
- [ ] Has 2 parameters: `response`, `conversation_history`
- [ ] Returns: `bool`
- [ ] Checks last 3 assistant messages
- [ ] Compares exact match and first 25 chars
- [ ] Save file (keep open)
- [ ] ✅ **STEP 6 COMPLETE**

---

## 📝 STEP 7: Replace Main Response Logic (10 min)

**File**: `ai_agent.py` (already open)

- [ ] Navigate to line 163-218 (the big `if priority_missing` block)
- [ ] Find this line: `if priority_missing and turn_number >= 2:`
- [ ] Find the entire block that includes:
  - `use_llm_for_extraction = True`
  - `if False:  # DISABLED`
  - The LLM-only code
  - Fallback to "I'm not sure what to do next"
- [ ] Select entire block (from line 163 to ~218)
- [ ] **BACKUP**: Copy this block to a comment at bottom of file (just in case)
- [ ] Delete or replace the selected block
- [ ] Paste new hybrid code:

**See IMPLEMENTATION_PLAN.md Section "STEP 7" for full code** (40 lines)

Key checks:
- [ ] Starts with: `if priority_missing and turn_number >= 2:`
- [ ] Has try-except block
- [ ] Step 1: Calls `_select_extraction_template`
- [ ] Step 2: Calls `await _naturalize_with_llm`
- [ ] Step 3: Calls `_detect_response_loop`
- [ ] Step 4: Validates extraction keywords
- [ ] Sets `generation_method = "HYBRID_EXTRACTION"`
- [ ] Has emergency fallback to old `_generate_rule_based_response`
- [ ] Save file
- [ ] ✅ **STEP 7 COMPLETE**

---

## 🧪 POST-IMPLEMENTATION VALIDATION (10 min)

### Syntax Check
- [ ] Run: `python -m py_compile gemini_client.py`
  - [ ] ✅ No errors
- [ ] Run: `python -m py_compile ai_agent.py`
  - [ ] ✅ No errors

### Import Check
- [ ] Run: `python -c "from ai_agent import AIHoneypotAgent; print('OK')"`
  - [ ] ✅ Prints "OK"
- [ ] Run: `python -c "from gemini_client import gemini_client; print('OK')"`
  - [ ] ✅ Prints "OK"

### Function Check
- [ ] Run: `python -c "from ai_agent import EXTRACTION_TEMPLATES; print(len(EXTRACTION_TEMPLATES))"`
  - [ ] ✅ Prints "8"
- [ ] Run: `python -c "from ai_agent import AIHoneypotAgent; a=AIHoneypotAgent(); print(hasattr(a, '_select_extraction_template'))"`
  - [ ] ✅ Prints "True"

### Config Check
- [ ] Run: `grep "temperature.*0.7" gemini_client.py`
  - [ ] ✅ Found
- [ ] Run: `grep "max_output_tokens.*200" gemini_client.py`
  - [ ] ✅ Found

---

## 🧪 FUNCTIONAL TESTING (10 min)

### Quick Test 1: Basic Import
```bash
python -c "
import asyncio
from ai_agent import AIHoneypotAgent

agent = AIHoneypotAgent()
print('✅ Agent created successfully')
"
```
- [ ] ✅ No errors

### Quick Test 2: Template Selection
```bash
python -c "
from ai_agent import AIHoneypotAgent, EXTRACTION_TEMPLATES

agent = AIHoneypotAgent()
template = agent._select_extraction_template(
    missing_intel_dict={'upiIds': [], 'phoneNumbers': []},
    scam_type='phishing',
    message='Send your OTP now',
    conversation_history=[]
)
print(f'Template: {template}')
print('✅ Has YOUR:', 'your' in template.lower())
"
```
- [ ] ✅ Prints template
- [ ] ✅ Has "YOUR" in output

### Quick Test 3: Full Response Generation
Create file `test_hybrid_quick.py`:
```python
import asyncio
from ai_agent import AIHoneypotAgent

async def test():
    agent = AIHoneypotAgent()

    response = await agent.generate_response(
        message="URGENT: Share your OTP now!",
        conversation_history=[],
        scam_type="phishing",
        missing_intel=["phone_numbers", "upi_ids"],
        use_competition_prompt=True
    )

    print(f"\n{'='*60}")
    print(f"Scammer: URGENT: Share your OTP now!")
    print(f"Honeypot: {response}")
    print(f"{'='*60}\n")

    # Validation
    checks = {
        'Has YOUR': any(word in response.lower() for word in ['your phone', 'your number', 'your upi']),
        'Not truncated': len(response) > 20,
        'Not confused': 'not sure' not in response.lower(),
        'Asks for info': '?' in response
    }

    print("Validation:")
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check}")

    all_passed = all(checks.values())
    print(f"\n{'✅ ALL TESTS PASSED!' if all_passed else '❌ SOME TESTS FAILED'}\n")

asyncio.run(test())
```

- [ ] Run: `python test_hybrid_quick.py`
- [ ] ✅ "Has YOUR" passes
- [ ] ✅ "Not truncated" passes
- [ ] ✅ "Not confused" passes
- [ ] ✅ "Asks for info" passes

---

## 📊 FINAL VERIFICATION (5 min)

### Code Review Checklist
- [ ] `gemini_client.py` temperature is 0.7
- [ ] `gemini_client.py` max_output_tokens is 200
- [ ] `ai_agent.py` imports `Tuple`
- [ ] `ai_agent.py` has `EXTRACTION_TEMPLATES` dict
- [ ] `ai_agent.py` has `_select_extraction_template` function
- [ ] `ai_agent.py` has `_naturalize_with_llm` async function
- [ ] `ai_agent.py` has `_detect_response_loop` function
- [ ] `ai_agent.py` main logic uses hybrid approach
- [ ] No syntax errors
- [ ] All functions are methods of `AIHoneypotAgent` class

### Git Commit
- [ ] Run: `git status`
- [ ] Run: `git diff` (review changes)
- [ ] Run: `git add gemini_client.py ai_agent.py`
- [ ] Run: `git commit -m "Implement hybrid extraction system - rule-based + LLM"`

---

## 🎉 SUCCESS CRITERIA

Your implementation is complete when:

1. ✅ All syntax checks pass
2. ✅ All import checks pass
3. ✅ Quick test shows response asks for scammer's info
4. ✅ Response is natural (not "I'm not sure")
5. ✅ Response is complete (not truncated)
6. ✅ Code is committed to git

---

## 🐛 TROUBLESHOOTING

### Error: "IndentationError"
- **Cause**: Wrong indentation level
- **Fix**: Make sure new functions are at class level (same indent as other methods)

### Error: "'EXTRACTION_TEMPLATES' is not defined"
- **Cause**: Template dict not at module level
- **Fix**: Move EXTRACTION_TEMPLATES outside any function, before `_select_extraction_template`

### Error: "async def" not working
- **Cause**: Missing `await` when calling
- **Fix**: Make sure calling code uses `await self._naturalize_with_llm(...)`

### Error: Responses still truncated
- **Cause**: Config not updated
- **Fix**: Double-check `gemini_client.py` line 31 is `200` not `150`

### Error: Still getting loops
- **Cause**: Temperature not updated
- **Fix**: Double-check `gemini_client.py` line 30 is `0.7` not `0.2`

---

## 📞 NEXT STEPS

After completing this checklist:

1. [ ] Run full test suite (if you have one)
2. [ ] Test with actual scam messages from examples
3. [ ] Monitor logs for "🎯 Template:" and "✨ Natural:" messages
4. [ ] Deploy to staging/production
5. [ ] Submit to hackathon

---

## 🎯 COMPLETION

**Date Completed**: ________________

**Time Taken**: ________________

**All Tests Passed**: [ ] YES  [ ] NO

**Ready for Production**: [ ] YES  [ ] NO

**Notes**:
_____________________________________________
_____________________________________________
_____________________________________________

---

**Congratulations! You've implemented the Hybrid Extraction System! 🎉**
