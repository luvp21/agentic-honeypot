"""
intel_extractor.py — Extract all 8 intelligence types from scammer messages.

NEW vs old system:
  - Old extracted 5 types; this extracts 8 (adds caseIds, policyNumbers, orderNumbers)
  - LLM fallback kicks in every 3 turns when regex yields nothing

Scoring impact: 30 pts total (30 ÷ total planted fields = pts per extracted item)
"""

import re
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Import enriched case-ID patterns from scam_detector (compiled below)
try:
    from scam_detector import CASE_ID_PATTERNS as _CASE_ID_PATTERNS
except ImportError:
    _CASE_ID_PATTERNS = [
        r"\b(?:HDFC|SBI|ICICI|AXIS|RBI|TRAI|CBI|ED|IRDAI|NPCI|CBDT|LIC)-[A-Z0-9\-]{4,20}\b",
        r"\b(?:IN-CUST|CBI-TAX|CBI-ED|TRAI-CYBER)-\d{4,10}\b",
        r"\b[A-Z]{2,5}[-/](?:SEC|FRAUD|CASE|REF|COMP)-\d{4,10}\b",
        r"\bCase\s+(?:ID|Ref|Number)[:\s]+([A-Z0-9\-]{6,20})\b",
        r"\bReference\s+(?:ID|Number)[:\s]+([A-Z0-9\-]{6,20})\b",
    ]


# ---------------------------------------------------------------------------
# Result dataclass — mirrors ExtractedIntelligence pydantic model
# ---------------------------------------------------------------------------

@dataclass
class IntelResult:
    phoneNumbers:   List[str] = field(default_factory=list)
    bankAccounts:   List[str] = field(default_factory=list)
    upiIds:         List[str] = field(default_factory=list)
    phishingLinks:  List[str] = field(default_factory=list)
    emailAddresses: List[str] = field(default_factory=list)
    caseIds:        List[str] = field(default_factory=list)   # NEW
    policyNumbers:  List[str] = field(default_factory=list)   # NEW
    orderNumbers:   List[str] = field(default_factory=list)   # NEW

    def to_dict(self) -> Dict[str, List[str]]:
        return {
            "phoneNumbers":   self.phoneNumbers,
            "bankAccounts":   self.bankAccounts,
            "upiIds":         self.upiIds,
            "phishingLinks":  self.phishingLinks,
            "emailAddresses": self.emailAddresses,
            "caseIds":        self.caseIds,
            "policyNumbers":  self.policyNumbers,
            "orderNumbers":   self.orderNumbers,
        }


# ---------------------------------------------------------------------------
# Compiled regex patterns
# ---------------------------------------------------------------------------

# ── Phone numbers ──────────────────────────────────────────────────────────
# Matches: +91-9876543210, 0091 98765 43210, (098) 765-4321, etc.
PHONE_RE = re.compile(
    r"""
    (?<!\d)                       # not a substring of a longer number
    (?:(?:\+|00)91[\s\-]?)?      # optional country code
    (?:0)?                        # optional leading zero
    [6-9]\d{9}(?!\d)              # Indian 10-digit mobile
    |
    \+[1-9][0-9\s\-().]{7,13}[0-9]  # generic international (must have + prefix)
    """,
    re.VERBOSE,
)

# ── Bank account numbers ───────────────────────────────────────────────────
# Context-sensitive: match only when near account-related keywords
BANK_CONTEXT_RE = re.compile(
    r"""
    (?:account|acc|a\/c|a-c|acno|bank\s*(?:acc|account)|account\s*(?:no|number))
    [\s:.\-#]*
    ([0-9]{9,18})
    """,
    re.IGNORECASE | re.VERBOSE,
)
BANK_STANDALONE_RE = re.compile(r"\b[0-9]{11,18}\b")  # standalone long numbers

# ── UPI IDs ────────────────────────────────────────────────────────────────
# Format: localpart@handle  (e.g., user@okaxis, 9876543210@ybl)
UPI_RE = re.compile(
    r"\b[a-zA-Z0-9.\-_+]{3,}@(?:okaxis|okhdfcbank|okicici|oksbi|ybl|upi|paytm|"
    r"ibl|axisbank|hdfcbank|icici|sbi|kotak|indus|rbl|yes|barodampay|"
    r"[a-zA-Z][a-zA-Z0-9]{2,})\b",
    re.IGNORECASE,
)
# Also generic @handle pattern (broader catch)
UPI_GENERIC_RE = re.compile(r"\b[a-zA-Z0-9.\-_+]{3,}@[a-zA-Z][a-zA-Z0-9]{2,}\b")

# Payment-context UPI — captures any @handle after "UPI ID:", "pay to:", etc.
# Handles hackathon fake handles like scammer.fraud@fakebank or @fakebank.com
UPI_PAYMENT_RE = re.compile(
    r"(?:upi\s*(?:id|vpa|no)?|pay\s+to|send\s+to|transfer\s+to)"
    r"[\s:.\-#]*([a-zA-Z0-9.\-_+]{3,}@[a-zA-Z0-9.\-]{3,})",
    re.IGNORECASE,
)

# ── Phishing / suspicious links ────────────────────────────────────────────
URL_RE        = re.compile(r"https?://[^\s<>\"{}|\\^`\[\]]+", re.IGNORECASE)
WWW_RE        = re.compile(r"www\.[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}[^\s]*", re.IGNORECASE)
SHORTENER_RE  = re.compile(
    r"\b(?:bit\.ly|tinyurl\.com|goo\.gl|t\.co|ow\.ly|rb\.gy|shorturl\.at|"
    r"cutt\.ly|is\.gd|tiny\.cc|s\.id)[/\s][^\s]+",
    re.IGNORECASE,
)
# Bare domain (no http/www) — catches things like sbi-security.com in parentheses
# Looks for word boundary + domain with suspicious pattern (hyphens or non-official TLDs)
BARE_DOMAIN_RE = re.compile(
    r"\b([a-zA-Z0-9][a-zA-Z0-9\-]{3,}\.[a-zA-Z]{2,6})\b",
    re.IGNORECASE,
)
# Official domains to exclude from bare domain matching
_OFFICIAL_DOMAINS = frozenset([
    "sbi.co.in", "rbi.org.in", "npci.org.in", "incometax.gov.in",
    "uidai.gov.in", "irctc.co.in", "amazon.in", "flipkart.com",
    "google.com", "paytm.com", "phonepe.com",
])

SUSPICIOUS_TLDS = frozenset([
    ".xyz", ".tk", ".ml", ".cf", ".ga", ".pw", ".gq",
    ".men", ".loan", ".top", ".click", ".download",
])
KNOWN_SHORTENERS = frozenset([
    "bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly",
    "rb.gy", "shorturl.at", "cutt.ly", "is.gd", "tiny.cc",
])

# ── Email addresses ────────────────────────────────────────────────────────
EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
)

# ── Case / Reference IDs ───────────────────────────────────────────────────
# Compiled from the hardened CASE_ID_PATTERNS exported by scam_detector.py
_COMPILED_CASE_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in _CASE_ID_PATTERNS
]
# Legacy fallback pattern (catches anything missed by the specifics above)
CASE_CONTEXT_RE = re.compile(
    r"(?:case|reference|ref|ticket|complaint|id|incident|report)[\s:.\-#]*"
    r"([A-Z]{0,5}[0-9]{4,12}|[A-Z]{2,5}[-/][0-9]{4,12})",
    re.IGNORECASE,
)
CASE_STANDALONE_RE = re.compile(r"\b[A-Z]{2,5}[-/][0-9]{4,12}\b")
# Multi-segment IDs like REF-2023-98765, AUTH-2023-45678, CONF-2024-12345
CASE_COMPOUND_RE = re.compile(
    r"\b[A-Z]{2,6}-[0-9]{4,10}(?:-[0-9]{3,10})+\b",
    re.IGNORECASE,
)

# ── Policy numbers ─────────────────────────────────────────────────────────
POLICY_CONTEXT_RE = re.compile(
    r"(?:policy|insurance|scheme|enrollment|enrolment|policy\s*no|policy\s*number)"
    r"[\s:.\-#]*([A-Z]{0,5}[-]?[0-9]{5,15})",
    re.IGNORECASE,
)
# Also catches LIC/IRDAI style: LIC-884219, IRDAI-2023-55231
POLICY_PREFIX_RE = re.compile(
    r"\b(?:LIC|IRDAI|NIC|HDFC-LIFE|ICICI-PRU|SBI-LIFE|MAX-LIFE)[-/]?([A-Z0-9\-]{5,15})\b",
    re.IGNORECASE,
)

# ── Order / Transaction / Invoice numbers ──────────────────────────────────
# Require at least one digit in suffix — prevents matching plain English words like 'reference'
ORDER_PREFIX_RE = re.compile(
    r"\b(?:ORD|OD|TXN|REF|INV|TXR)(?=[A-Z0-9]*[0-9])[A-Z0-9]{5,15}\b",
    re.IGNORECASE,
)
# \b after keyword — prevents 'ref' matching inside 'reference'
ORDER_CONTEXT_RE = re.compile(
    r"(?:order|transaction|invoice|txn|ref|receipt|payment)\b\s*(?:id|no|number|#)?[\s:.\-#]*"
    r"([A-Z0-9]{6,20})",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _deduplicate(items: List[str]) -> List[str]:
    """Return deduplicated list preserving insertion order."""
    seen: set = set()
    result: List[str] = []
    for item in items:
        clean = item.strip()
        if clean and clean not in seen:
            seen.add(clean)
            result.append(clean)
    return result


def _normalise_phone(raw: str) -> Optional[str]:
    """Strip whitespace/punctuation from phone match, return if ≥9 digits."""
    digits = re.sub(r"[^\d+]", "", raw)
    return digits if len(digits) >= 9 else None


def _is_phishing_url(url: str) -> bool:
    """Return True if the URL looks suspicious (all scammer URLs are flagged)."""
    lower = url.lower()
    for tld in SUSPICIOUS_TLDS:
        if tld in lower:
            return True
    for shortener in KNOWN_SHORTENERS:
        if shortener in lower:
            return True
    if re.match(r"https?://\d{1,3}\.\d{1,3}", url):   # IP-based URL
        return True
    if url.startswith("http://"):
        return True    # Non-HTTPS is suspicious
    return True        # In honeypot context, ALL URLs shared by scammers are flagged


def _clean_case_ids(ids: List[str], phishing_links: List[str]) -> List[str]:
    """
    Post-process extracted case IDs to remove noise:
    - Bare 4-digit years (e.g. '2023')
    - Pure-alphabetic entries with no digits (e.g. 'sbi-security')
    - Entries that are domain names extracted from phishing links
    - Shorter IDs that are prefixes of longer IDs already in the list
    """
    # Build set of domain names from phishing links to exclude
    domain_parts: set = set()
    for link in phishing_links:
        m = re.match(r'(?:https?://|www\.)?([a-zA-Z0-9.\-]+)', link)
        if m:
            domain = m.group(1).lower()
            domain_parts.add(domain)
            base = re.sub(r'\.[a-z]{2,6}$', '', domain)  # strip TLD
            domain_parts.add(base)

    cleaned: List[str] = []
    for cid in ids:
        # Skip bare 4-digit years
        if re.match(r'^\d{4}$', cid):
            continue
        # Skip pure-alphabetic (no digits) — these are likely domain/word fragments
        if not re.search(r'\d', cid):
            continue
        # Skip domain name fragments
        if cid.lower() in domain_parts:
            continue
        cleaned.append(cid)

    # Remove IDs that are strict prefixes of longer IDs in the same list
    final: List[str] = []
    for cid in cleaned:
        is_prefix = any(
            other != cid and other.upper().startswith(cid.upper())
            for other in cleaned
        )
        if not is_prefix:
            final.append(cid)

    return final


# ---------------------------------------------------------------------------
# IntelExtractor class
# ---------------------------------------------------------------------------

class IntelExtractor:

    # ── Core extraction ──────────────────────────────────────────────────────

    def extract(self, text: str) -> IntelResult:
        """Extract all 8 intel types from a single text string."""
        result = IntelResult()

        # ── Phone numbers ────────────────────────────────────────────────
        # Normalize first so +91-9876543210 and +919876543210 collapse to one entry
        phones: List[str] = []
        seen_digits: set = set()
        for m in PHONE_RE.finditer(text):
            normed = _normalise_phone(m.group())
            if normed:
                digits_key = re.sub(r'[^\d]', '', normed)
                if digits_key not in seen_digits:
                    seen_digits.add(digits_key)
                    phones.append(normed)
        result.phoneNumbers = phones

        # ── Bank account numbers ─────────────────────────────────────────
        accounts = []
        for m in BANK_CONTEXT_RE.finditer(text):
            accounts.append(m.group(1))
        # Keyword BEFORE number
        bank_keyword_re = re.compile(
            r"(?:account|bank|acc|a\/c|ifsc)[^.]{0,60}?([0-9]{11,18})",
            re.IGNORECASE,
        )
        for m in bank_keyword_re.finditer(text):
            accounts.append(m.group(1))
        # Keyword AFTER number (e.g. "deposit 1234567890123456 to bank account")
        bank_keyword_after_re = re.compile(
            r"([0-9]{11,18})[^.]{0,60}?(?:account|bank|acc|a\/c|ifsc)",
            re.IGNORECASE,
        )
        for m in bank_keyword_after_re.finditer(text):
            accounts.append(m.group(1))
        # Standalone fallback: any 11-18 digit number not already captured
        # Covers hackathon fake data like bare "1234567890123456" in messages
        _phone_digits = {re.sub(r"[^\d]", "", p) for p in result.phoneNumbers}
        for m in BANK_STANDALONE_RE.finditer(text):
            candidate = m.group()
            if candidate not in accounts and candidate not in _phone_digits:
                accounts.append(candidate)
        result.bankAccounts = _deduplicate(accounts)

        # ── UPI IDs ──────────────────────────────────────────────────────
        upi_ids: List[str] = []
        # 1. Known handles (okaxis, oksbi, ybl, etc.)
        for m in UPI_RE.finditer(text):
            upi_ids.append(m.group())
        # 2. Payment-context @handle — covers fake handles like @fakebank
        for m in UPI_PAYMENT_RE.finditer(text):
            candidate = m.group(1).rstrip(".,;:")
            if candidate and candidate not in upi_ids:
                upi_ids.append(candidate)
        # 3. Generic @handle — permissive, no email filter
        #    In honeypot context every @handle shared by scammer is intel
        for m in UPI_GENERIC_RE.finditer(text):
            candidate = m.group()
            if candidate not in upi_ids:
                upi_ids.append(candidate)
        # Remove entries that are full email addresses (have TLD: .com, .in, etc.)
        # Those belong in emailAddresses, not upiIds
        _email_tld_re = re.compile(r'@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')
        result.upiIds = _deduplicate([
            uid for uid in upi_ids if not _email_tld_re.search(uid)
        ])

        # ── Email addresses ───────────────────────────────────────────────
        emails = EMAIL_RE.findall(text)
        result.emailAddresses = _deduplicate(emails)

        # ── Phishing / suspicious links ───────────────────────────────────
        links: List[str] = []
        for m in URL_RE.finditer(text):
            links.append(m.group())
        for m in WWW_RE.finditer(text):
            url = m.group()
            if not any(url in existing for existing in links):
                links.append(url)
        for m in SHORTENER_RE.finditer(text):
            links.append(m.group())
        # Bare domains (no http/www): sbi-security.com, refund-it-dept.in, etc.
        # Exclude known-legitimate domains
        already_in_links = set(u.lower() for u in links)
        for m in BARE_DOMAIN_RE.finditer(text):
            domain = m.group(1)
            if domain.lower() not in _OFFICIAL_DOMAINS and domain.lower() not in already_in_links:
                # Only flag if it has a suspicious TLD or a hyphen (common in scam domains)
                tld = '.' + domain.rsplit('.', 1)[-1].lower()
                has_hyphen = '-' in domain.split('.')[0]
                if tld in SUSPICIOUS_TLDS or has_hyphen or domain.endswith(('.in', '.org.in')):
                    links.append(domain)
        # Only keep genuinely suspicious ones
        result.phishingLinks = _deduplicate(
            [u for u in links if _is_phishing_url(u)]
        )

        # ── Case / Reference IDs ──────────────────────────────────────────
        # Primary: hardened patterns from scam_detector (org-prefixed IDs)
        case_ids: List[str] = []
        for pat in _COMPILED_CASE_PATTERNS:
            for m in pat.finditer(text):
                # Some patterns use a capture group, others match the full span
                val = m.group(1) if m.lastindex else m.group()
                if val:
                    case_ids.append(val)
        # Multi-segment compound IDs: REF-2023-98765, AUTH-2023-45678, etc.
        for m in CASE_COMPOUND_RE.finditer(text):
            case_ids.append(m.group().upper())
        # Fallback: legacy context + standalone patterns
        for m in CASE_CONTEXT_RE.finditer(text):
            case_ids.append(m.group(1))
        for m in CASE_STANDALONE_RE.finditer(text):
            case_ids.append(m.group())
        result.caseIds = _clean_case_ids(_deduplicate(case_ids), result.phishingLinks)

        # ── Policy numbers ────────────────────────────────────────────────
        policy_nums: List[str] = []
        for m in POLICY_CONTEXT_RE.finditer(text):
            policy_nums.append(m.group(1))
        for m in POLICY_PREFIX_RE.finditer(text):
            # Store the full match (e.g. LIC-884219) so evaluator sees real value
            policy_nums.append(m.group())
        result.policyNumbers = _deduplicate(policy_nums)

        # ── Order / Transaction numbers ───────────────────────────────────
        order_nums: List[str] = []
        for m in ORDER_PREFIX_RE.finditer(text):
            order_nums.append(m.group())
        for m in ORDER_CONTEXT_RE.finditer(text):
            val = m.group(1)
            if len(val) >= 6:
                order_nums.append(val)
        # Require at least one digit — filters out word fragments like 'erence'
        result.orderNumbers = _deduplicate([
            o for o in order_nums if re.search(r'\d', o)
        ])

        return result

    # ── Conversation-history extraction ──────────────────────────────────────

    def extract_from_history(self, conversation_history: list) -> IntelResult:
        """
        Run extraction over all scammer messages in the conversation history.
        Called during finalisation for a comprehensive sweep.
        """
        scammer_text = " ".join(
            m.get("content", "")
            for m in conversation_history
            if m.get("role") == "user"
        )
        return self.extract(scammer_text)

    # ── Session merge ─────────────────────────────────────────────────────────

    def merge_into_session(self, session, new_intel: IntelResult) -> None:
        """
        Merge IntelResult into the session's intel_store.
        Session.add_intel handles deduplication.
        """
        for field_name, values in new_intel.to_dict().items():
            if values:
                session.add_intel(field_name, values)

    # ── LLM result merge ──────────────────────────────────────────────────────

    def merge_llm_result(self, session, llm_dict: dict) -> None:
        """
        Merge LLM-extracted intel (dict format) into the session store.
        Safe: handles missing keys and non-list values gracefully.
        """
        for field_name in [
            "phoneNumbers", "bankAccounts", "upiIds", "phishingLinks",
            "emailAddresses", "caseIds", "policyNumbers", "orderNumbers",
        ]:
            values = llm_dict.get(field_name, [])
            if isinstance(values, list):
                clean = [str(v).strip() for v in values if v]
                if clean:
                    session.add_intel(field_name, clean)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
intel_extractor = IntelExtractor()
