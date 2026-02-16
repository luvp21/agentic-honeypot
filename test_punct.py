"""Test punctuation stripping"""
import re

text = "My UPI ID is scammer.fraud@fakebank."

pattern = r'\b([a-zA-Z0-9.\-_]{2,}@[a-zA-Z0-9.\-_]{2,})\b'
matches = re.findall(pattern, text)
print(f"Raw matches: {matches}")

for match in matches:
    cleaned = re.sub(r'[.,;:!?]+$', '', match.lower())
    print(f"'{match}' → '{cleaned}' (len={len(cleaned)})")
