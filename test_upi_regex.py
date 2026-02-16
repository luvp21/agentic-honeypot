#!/usr/bin/env python3
"""Test UPI extraction with period at end"""
import re

text = "My UPI ID is scammer.fraud@fakebank."

# Current pattern
pattern = r'\b([a-zA-Z0-9.\-_]{2,}@[a-zA-Z0-9.\-_]{2,})\b'
matches = re.findall(pattern, text)
print(f"Current pattern: {matches}")

# Better pattern - exclude trailing punctuation
pattern2 = r'\b([a-zA-Z0-9.\-_]{2,}@[a-zA-Z0-9\-_]{2,})\b'
matches2 = re.findall(pattern2, text)
print(f"Without . in handle: {matches2}")

# Even better - explicit cleanup
pattern3 = r'([a-zA-Z0-9.\-_]+@[a-zA-Z0-9\-_]+)'
matches3 = re.findall(pattern3, text)
print(f"No word boundaries: {matches3}")
