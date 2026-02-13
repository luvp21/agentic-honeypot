
import re

def extract_url_debug(text):
    # Current Regex from intelligence_extractor.py
    # ranges: $-_ includes 36-95, so it includes digits, uppercase, and lots of symbols like ? =
    url_pattern = r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)'

    matches = []
    for match in re.finditer(url_pattern, text):
        matches.append(match.group(1))
    return matches

test_url = "Here’s the link: https://secure-fakebank.com/verify?txn=12345 – click it immediately"
print(f"Testing text: '{test_url}'")
results = extract_url_debug(test_url)
print(f"Extracted: {results}")

if "https://secure-fakebank.com/verify?txn=12345" in results:
    print("✅ Full URL extracted")
else:
    print("❌ URL extraction incomplete or failed")

# Analysis of regex ranges
print("\nRegex Analysis:")
print("Pattern: r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)'")
# The range $-_ (ASCII 36 to 95) covers:
# $ % & ' ( ) * + , - . / 0-9 : ; < = > ? @ A-Z [ \ ] ^ _
# It does NOT cover lowercase a-z (97-122).
# But [a-zA-Z] is also included.
# However, the dash inside [] if not at end/start is a range.
# secure-fakebank.com -> "secure" (lower), "-" (in range), "fakebank" (lower)
# verify -> lower
# ? -> in range
# txn -> lower
# = -> in range
# 12345 -> digits (in range and 0-9)

# It seems it should match. Let's see if the dash is the issue or something else.
