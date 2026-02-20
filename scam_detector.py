"""
scam_detector.py — Hardened hybrid scam detection.

Scoring tiers:
  >=7.0  = HIGH  -> rule-based result trusted, skip LLM classification
  3.0-6.9 = GREY -> ambiguous, trigger gemini_client.classify_scam() fallback
  <3.0   = LOW   -> probably not scam (unless red flags found)

All 15 scam types covered with integer-weighted keywords.
Rule-based fires first; LLM only for grey-zone messages.

Scoring impact:
  - scamDetected: true  -> 20 pts
  - red_flags count     -> up to 8 pts (conversation quality section)
"""

import re
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class DetectionResult:
    is_scam:            bool
    scam_type:          Optional[str]
    confidence_score:   float
    red_flags_detected: List[str] = field(default_factory=list)
    detection_tier:     str       = "LOW"   # HIGH / GREY / LOW -> controls LLM fallback
    type_scores:        Dict[str, float] = field(default_factory=dict)


# ==========================================================================
# UNIVERSAL RED FLAGS
# Add to score of whichever scam type scores highest.
# ==========================================================================

UNIVERSAL_FLAGS: Dict[str, int] = {
    # Urgency triggers
    "immediately": 2, "urgent": 3, "act now": 3, "right now": 2,
    "within 30 minutes": 4, "within 2 hours": 4, "within 24 hours": 3,
    "expires in 10 minutes": 4, "limited time": 2, "time is running out": 3,
    "last chance": 3, "final warning": 4, "final notice": 3,
    "do not delay": 2, "respond immediately": 3,
    # Fear / threat triggers
    "avoid arrest": 5, "avoid legal action": 4, "legal action": 3,
    "will be arrested": 5, "case registered": 4, "fir registered": 4,
    "warrant issued": 5, "cybercrime case": 4, "police case": 4,
    "permanent suspension": 4, "permanent freeze": 4, "permanently blocked": 4,
    "account will be blocked": 4, "services will be suspended": 4,
    "deactivated": 3, "terminated": 3,
    # Money extraction triggers
    "processing fee": 4, "clearance charge": 5, "registration fee": 5,
    "documentation charge": 4, "activation fee": 5, "verification fee": 4,
    "security deposit": 4, "small fee": 3, "pay now": 3,
    "transfer amount": 3, "send money": 3, "release funds": 3,
    # Credential harvesting
    "share otp": 5, "enter otp": 5, "otp": 3, "share your otp": 5,
    "share pin": 5, "upi pin": 5, "confirm pin": 5,
    "share account number": 4, "provide account details": 4,
    "share aadhaar": 4, "share pan": 4,
    "don't tell anyone": 5, "keep this confidential": 4, "do not share": 3,
    # False legitimacy
    "case id": 3, "case ref": 3, "reference number": 2,
    "officer assigned": 4, "fraud department": 3, "security team": 2,
    "compliance team": 2, "government approved": 3, "rbi approved": 4,
    "sebi approved": 4, "verified": 1,
}


# ==========================================================================
# PER-TYPE KEYWORD DICTIONARIES (integer weights)
# ==========================================================================

SCAM_KEYWORDS: Dict[str, Dict[str, int]] = {

    "bank_fraud": {
        "account compromised": 5, "account suspended": 5, "account blocked": 5,
        "account will be frozen": 5, "account freeze": 4,
        "unauthorized transaction": 4, "unauthorized debit": 4,
        "suspicious transaction": 3, "suspicious login": 4,
        "unrecognized device": 4, "new device detected": 4,
        "verify your account": 3, "verify immediately": 3,
        "fraud department": 3, "fraud desk": 4, "fraud team": 3,
        "reverse the transaction": 4, "block the transaction": 3,
        "beneficiary added": 4, "new beneficiary": 4,
        "sbi": 2, "hdfc": 2, "icici": 2, "axis bank": 2, "pnb": 2,
        "kotak": 2, "yes bank": 2, "bank of baroda": 2,
        "trai": 3, "sim blocked": 5, "sim card blocked": 5, "sim will be blocked": 5,
        "sim services suspended": 5, "mobile number blocked": 4,
        "cybercrime officer": 4, "press 1": 3, "press 9": 3,
        "net banking suspended": 5, "net banking blocked": 5,
        "login attempt": 3, "multiple failed login": 4,
        "atm blocked": 4, "atm suspended": 4, "debit card blocked": 4,
        "rbi monitoring": 4, "rbi compliance": 3, "rbi circular": 3,
        "rbi directive": 3, "reserve bank": 2,
        "salary account blocked": 5, "salary account suspended": 5,
    },

    "upi_fraud": {
        "collect request": 6, "approve collect": 6, "approve request": 5,
        "pending collect": 5, "accept request": 4,
        "upi pin": 6, "enter pin": 5, "confirm pin": 5, "share pin": 6,
        "enter your pin": 6, "confirm your pin": 6,
        "cashback pending": 4, "cashback waiting": 4, "cashback credit": 3,
        "cashback reward": 3, "cashback transfer": 4,
        "double debit": 5, "duplicate debit": 5, "duplicate charge": 4,
        "refund failed": 3, "reversal request": 5, "failed transaction": 3,
        "upi suspended": 5, "upi blocked": 5, "upi id suspended": 5,
        "upi services blocked": 5, "upi account frozen": 5,
        "upi id": 4,
        "phonepe": 2, "gpay": 2, "google pay": 2, "paytm": 2,
        "npci": 5, "npci alert": 5, "bhim": 2,
        "government subsidy": 3, "subsidy credit": 3, "subsidy transfer": 3,
        "subsidy failed": 4,
    },

    "phishing_link": {
        "click here": 3, "visit the link": 3, "open the link": 3,
        "secure link": 3, "verification link": 3, "claim link": 3,
        "http://": 3, "https://": 1,
        "delivery failed": 4, "parcel not delivered": 4,
        "redelivery charge": 5, "rs.49": 4,
        "update delivery address": 4, "incomplete address": 4,
        "secure portal": 3, "official portal": 2, "verify at": 3,
        "update at": 3, "login at": 3,
        "mega sale": 3, "early access": 3, "exclusive offer": 2,
        "claim your benefit": 3, "claim now": 3,
        "fastag blocked": 5, "fastag recharge": 3, "fastag account": 3,
        "aadhaar update": 3, "aadhaar verification": 3, "uidai link": 5,
        "refund approved": 3, "confirm bank details": 4, "confirm account": 4,
        "amaz0n": 6, "amaz-on": 6, "flipkart-": 5, "sbi-secure": 5,
        "sbi-help": 5, "hdfc-alert": 5, "refund-it-dept": 6,
        "india-post-track": 6, "irctc-verify": 5,
    },

    "kyc_fraud": {
        "kyc expired": 6, "kyc incomplete": 5, "kyc pending": 5,
        "kyc verification": 4, "kyc update": 4, "kyc required": 4,
        "kyc validity expired": 6, "kyc period expired": 6,
        "complete kyc": 4, "submit kyc": 4, "update kyc": 4,
        "video kyc": 5, "video kyc incomplete": 6,
        "upload aadhaar": 4, "upload pan": 4, "submit documents": 3,
        "identity proof": 3, "address proof": 3, "document submission": 3,
        "rbi/kyc": 6, "rbi compliance": 4, "rbi banking compliance": 5,
        "rbi circular": 4, "rbi kyc circular": 5,
        "sebi compliance": 3, "sebi kyc": 4,
        "pan aadhaar mismatch": 6, "aadhaar pan link": 4,
        "pan not linked": 5, "aadhaar mismatch": 5,
        "demographic mismatch": 6,
        "atm upi suspended": 5, "upi will be blocked": 5,
        "banking services suspended": 5, "investment services restricted": 4,
        "demat account freeze": 5, "demat restricted": 4,
        "trading account": 3, "sip suspended": 5, "sip paused": 5,
        "wallet blocked": 4, "wallet verification": 3,
    },

    "job_scam": {
        "registration fee": 6, "joining fee": 6, "activation charge": 6,
        "security deposit": 5, "refundable deposit": 5, "refundable security": 5,
        "documentation charges": 5, "documentation fee": 5,
        "training kit charges": 5, "training fee": 4,
        "appointment letter fee": 5,
        "work from home": 2, "work from anywhere": 2, "remote job": 2,
        "no experience required": 3, "no experience needed": 3,
        "monthly income": 2, "limited seats": 3, "urgent hiring": 2,
        "immediate joining": 3, "joining immediately": 3,
        "airport authority": 3, "railway recruitment": 3, "rrb": 3,
        "amazon hiring": 3, "amazon data entry": 4,
        "flipkart warehouse": 3, "government contract": 3,
        "police recruitment": 3, "constable recruitment": 3,
        "dubai job": 4, "overseas job": 3, "foreign job": 3,
        "visa processing": 3, "visa charges": 4,
        "naukri premium": 4, "naukri activation": 5,
        "shortlisted": 2, "profile selected": 2,
    },

    "lottery_scam": {
        "you have won": 5, "you won": 4, "selected as winner": 5,
        "lucky winner": 5, "lucky draw": 5, "prize winner": 5,
        "congratulations you have won": 6,
        "claim your prize": 4, "claim your reward": 4, "claim reward": 4,
        "claim your cashback": 4,
        "clearance charge": 6, "gst clearance": 6, "processing charge": 4,
        "documentation fee": 4, "release prize": 4, "prize officer": 5,
        "tax clearance": 5, "prize clearance": 5,
        "kbc": 5, "kaun banega crorepati": 5, "kbc lucky draw": 6,
        "google 25th anniversary": 5, "airtel lucky": 4, "jio reward": 4,
        "whatsapp lottery": 5,
        "ipl jackpot": 4, "ipl fantasy": 3,
        "sbi lucky": 4, "lucky account": 4,
        "mobile number selected": 5, "your number selected": 5,
        "your number won": 5, "number chosen": 4,
        "cashback reward": 3, "festive reward": 3,
        "approve the collect request": 6,
    },

    "electricity_bill": {
        "electricity connection": 4, "power connection": 3,
        "will be disconnected": 5, "disconnection today": 6,
        "disconnected at 9 pm": 6, "disconnected tonight": 5,
        "power cut": 5, "power will be cut": 5,
        "power termination": 5, "connection terminated": 5,
        "permanent disconnection": 5,
        "unpaid bill": 4, "outstanding bill": 4, "pending dues": 3,
        "overdue payment": 4, "outstanding amount": 3,
        "consumer id": 4, "meter id": 4, "consumer number": 4,
        "smart meter": 3, "meter reading": 2,
        "mseb": 5, "msedcl": 5, "bescom": 5, "tneb": 5,
        "adani electricity": 4, "tata power": 3, "bses": 4,
        "state electricity board": 4, "electricity board": 3,
        "eb office": 3, "eb helpline": 3,
        "billing irregularity": 4, "billing error": 3,
        "penalty": 3, "legal action": 3, "penalty charge": 4,
        "electricity subsidy": 4, "subsidy expired": 5,
        "pay immediately": 3, "clear dues": 3, "pay now to avoid": 4,
    },

    "govt_scheme": {
        "pm awas yojana": 6, "pmay": 5, "pm awas": 5,
        "pm kisan": 6, "kisan installment": 6, "kisan benefit": 5,
        "ayushman bharat": 5, "ayushman card": 5,
        "mudra loan": 4, "pm mudra": 5,
        "pm suraksha bima": 5, "pm jeevan jyoti": 5,
        "digital india": 3, "startup india": 3,
        "lpg subsidy": 5, "lpg benefit": 4, "lpg kyc": 5,
        "crop insurance": 4, "farmer insurance": 4,
        "covid relief": 5, "covid grant": 5,
        "subsidy approved": 5, "subsidy released": 4, "subsidy pending": 4,
        "installment blocked": 6, "benefit blocked": 5,
        "grant approved": 4, "scholarship approved": 4,
        "aadhaar deactivation": 6, "aadhaar flagged": 5, "aadhaar has been flagged": 5,
        "aadhaar unauthorized usage": 6, "unauthorized usage": 3,
        "government scheme benefits": 5, "scheme benefits": 4,
        "linked government benefits": 5, "scheme benefits deactivated": 5,
        "processing charge": 4, "registration charge": 4,
        "verification amount": 4, "submit verification": 4,
        "bank verification mismatch": 5, "aadhaar bank mismatch": 5,
        "update linked bank": 4, "update aadhaar linked": 4,
    },

    "crypto_investment": {
        "guaranteed returns": 6, "guaranteed profit": 6, "guaranteed income": 6,
        "double your money": 6, "2x returns": 5, "5x returns": 6,
        "daily profit": 5, "daily returns": 5, "daily payout": 5,
        "weekly profit": 4, "monthly returns": 4,
        "zero risk": 5, "no risk": 4, "100% safe": 5,
        "high returns": 4, "passive income": 3,
        "bitcoin": 3, "crypto": 2, "cryptocurrency": 2,
        "ethereum": 3, "usdt": 4, "binance": 3, "tether": 3,
        "crypto wallet": 4, "wallet address": 4, "send crypto": 4,
        "mining pool": 4, "ethereum mining": 5,
        "sebi-approved crypto": 6, "rbi digital currency": 6,
        "government crypto": 5, "rbi backed": 5,
        "sebi registered": 4,
        "elon musk": 5, "mukesh ambani": 4, "warren buffett": 4,
        "ai trading bot": 5, "automated trading": 4,
        "trading bot": 4, "trading signals": 3,
        "invest now": 3, "limited slots": 4,
        "join now": 2, "register now": 2,
        "selected participants only": 4,
        "forex": 3, "forex trading": 3, "forex profit": 4,
    },

    "customs_parcel": {
        "parcel held": 6, "shipment on hold": 6, "shipment held": 6,
        "parcel seized": 6, "package detained": 5,
        "held at customs": 6, "held at delhi customs": 6,
        "customs clearance": 6, "clearance required": 5,
        "customs duty": 5, "import duty": 5, "import tax": 5,
        "customs charge": 5, "clearance charge": 5,
        "dhl": 3, "fedex": 3, "india post customs": 4,
        "ups": 2, "aramex": 3, "blue dart customs": 3,
        "seizure": 5, "confiscation": 5, "will be seized": 6,
        "will be auctioned": 5, "returned to sender": 3,
        "avoid confiscation": 5,
        "cbi-ed": 6, "cbi ed notice": 6, "ed notice": 5,
        "money laundering": 5, "anti-money laundering": 5,
        "suspected money laundering": 6, "aml verification": 5,
        "illegal contents": 5, "restricted items": 4,
        "smuggling review": 5,
        "in-cust-": 5, "customs case": 4,
        "gold jewelry": 4, "gold shipment": 4,
        "from london": 2, "from dubai": 2, "from usa": 2, "from uk": 2,
    },

    "tech_support": {
        "trojan": 6, "trojan malware": 6, "trojan virus": 6,
        "malware": 5, "virus detected": 5, "ransomware": 6,
        "spyware": 5, "system infected": 5, "infected with": 4,
        "data theft": 4, "hacking attempt": 4,
        "remote access": 6, "remote assistance": 6, "remote support": 5,
        "anydesk": 6, "teamviewer": 6, "quicksupport": 6,
        "install software": 4, "download tool": 4,
        "remote desktop": 5, "screen sharing": 4,
        "windows license": 5, "license expired": 5, "license key expired": 5,
        "windows defender": 3, "antivirus expired": 4,
        "subscription expired": 3,
        "apple id": 4, "apple support": 3, "icloud": 3,
        "macbook security": 4, "apple security": 4,
        "microsoft security": 4, "microsoft support": 3,
        "windows security": 4, "system registry": 4,
        "ip address flagged": 6, "your ip": 4, "ip blocked": 5,
        "illegal downloads": 5, "illegal activity": 4,
        "illegal access": 4, "cybercrime": 4,
        "firewall breach": 5, "network intrusion": 4,
        "immediate remote": 5, "call immediately": 3, "call now": 2,
    },

    "loan_scam": {
        "processing fee": 6, "activation fee": 6, "file charge": 5,
        "documentation charge": 5, "security deposit": 5,
        "loan processing fee": 6, "before disbursement": 5,
        "without cibil": 6, "no cibil": 6, "regardless of cibil": 6,
        "low cibil": 4, "bad cibil": 4, "cibil not required": 6,
        "pre-approved loan": 5, "pre approved": 4,
        "loan approved": 4, "loan sanctioned": 4,
        "instant loan": 4, "instant disbursal": 4,
        "funds in 10 minutes": 5, "credited within 10 minutes": 5,
        "no collateral": 4, "no documents": 4,
        "rbi loan scheme": 5, "rbi special loan": 5, "rbi directive loan": 5,
        "mudra loan scheme": 4,
        "zero interest": 5, "zero percent": 4,
        "credit card upgrade": 3, "limit increase": 3,
        "emergency loan": 4, "medical loan": 4,
        "salary advance": 4, "advance salary": 4,
    },

    "income_tax": {
        "refund approved": 5, "tax refund approved": 5,
        "income tax refund": 5, "income tax dept": 6, "income tax": 3,
        "refund for ay": 5,
        "ay 2023-24": 4, "ay 2024-25": 4, "assessment year": 3,
        "confirm bank details": 5, "confirm your account": 4,
        "confirm your bank account": 5, "confirm bank account": 4,
        "cbdt": 5, "income tax department": 4, "it department": 3,
        "income tax notice": 4, "income tax portal": 3,
        "pan verification": 5, "pan verification incomplete": 6,
        "refund on hold": 5, "refund blocked": 5, "refund cancelled": 4,
        "gst refund": 4, "business gst refund": 4,
        "arrest warrant": 6, "warrant issued": 6, "arrest in your name": 6,
        "cbi-tax": 6, "cbi tax": 6, "cbi warrant": 6,
        "non-filing": 5, "outstanding tax": 5, "tax arrears": 4,
        "tax evasion": 4, "tax fraud case": 5,
        "refund-it-dept": 6, "incometax-": 5, "efiling-": 4,
        "tds adjustment": 4, "excess tds": 4, "tds refund": 4,
        "multiple login attempts": 4, "portal security": 3,
    },

    "refund_scam": {
        "refund initiated": 5, "refund has been initiated": 5,
        "refund for cancelled": 5,
        "refund for your order": 5,
        "confirm bank details": 5, "confirm your upi": 5,
        "receive refund": 4, "process refund": 4,
        "cancelled order": 5, "order cancelled": 4,
        "order id": 3, "order amz-": 4, "order od-": 4,
        "duplicate payment": 6, "duplicate charge": 5,
        "double charged": 5, "charged twice": 5,
        "product recall": 5, "defective batch": 5, "defective product": 4,
        "recall notice": 5, "compensation approved": 5,
        "amazon refund": 4, "flipkart refund": 4,
        "amazon support": 3, "flipkart support": 3,
        "meesho refund": 4, "myntra refund": 3,
        "cashback reversal": 4, "incorrect cashback": 4,
        "warranty refund": 4, "subscription refund": 4,
        "delivery failure refund": 4,
        "refund to upi": 4, "refund to account": 4,
    },

    "insurance": {
        "policy maturity": 6, "policy has matured": 6, "policy matured": 6,
        "maturity amount": 5, "maturity benefit": 5, "bonus amount": 4,
        "maturity payout": 5,
        "clearance charges": 6, "processing fee": 4,
        "claim settlement fee": 5, "claim processing": 4,
        "settlement charge": 5, "release funds": 4,
        "irdai": 5, "irdai compliance": 5, "irdai notice": 5,
        "irdai verification": 5,
        "lic-": 5, "lic policy": 5, "lic maturity": 6,
        "lic bonus": 5, "lic claim": 4,
        "policy lapse": 5, "lapse notice": 5, "policy will lapse": 6,
        "forfeiture": 5, "benefits forfeited": 5,
        "policy expired": 4, "policy cancelled": 4,
        "accident benefit": 4, "accident claim": 4,
        "claim approved": 4, "claim settled": 4, "claim amount": 3,
        "claim settlement": 4,
        "nominee verification": 5, "nominee details": 4,
        "nominee update": 4,
        "renewal discount": 3, "renewal offer": 3,
        "premium due": 3, "premium pending": 4,
    },
}


# ==========================================================================
# PHISHING URL PATTERNS  (+6 per match, auto-boost phishing_link score)
# ==========================================================================

PHISHING_URL_PATTERNS: List[str] = [
    r"https?://[^\s]*(amaz0n|amaz-on)[^\s]*",
    r"https?://[^\s]*(flipkart-)[^\s]*",
    r"https?://[^\s]*(sbi-secure|sbi-help|sbi-verify)[^\s]*",
    r"https?://[^\s]*(hdfc-alert|hdfc-verify)[^\s]*",
    r"https?://[^\s]*(refund-it-dept)[^\s]*",
    r"https?://[^\s]*(india-post-track)[^\s]*",
    r"https?://[^\s]*(irctc-verify)[^\s]*",
    r"https?://[^\s]*(uidai-link|uidai-update)[^\s]*",
    r"http://[^\s]+\.(xyz|tk|cf|ml|in)[^\s]*",
    r"https?://[^\s]+-(secure|verify|help|login|portal|update)\.[^\s]*",
    r"bit\.ly/[^\s]+",
    r"tinyurl\.com/[^\s]+",
    r"rb\.gy/[^\s]+",
]


# ==========================================================================
# CASE ID PATTERNS — exported for intel_extractor.py
# ==========================================================================

CASE_ID_PATTERNS: List[str] = [
    # Org-prefixed IDs must have at least one digit (excludes domain names like sbi-security.com)
    r"\b(?:HDFC|SBI|ICICI|AXIS|RBI|TRAI|CBI|ED|IRDAI|NPCI|CBDT|LIC)-(?=[A-Z0-9\-]*[0-9])[A-Z0-9\-]{4,20}(?!\.[a-z]{2,4})\b",
    r"\b(?:IN-CUST|CBI-TAX|CBI-ED|TRAI-CYBER)-\d{4,10}\b",
    r"\b[A-Z]{2,5}[-/](?:SEC|FRAUD|CASE|REF|COMP)-\d{4,10}\b",
    r"\bCase\s+(?:ID|Ref|Number)[:\s]+([A-Z0-9\-]{6,20})\b",
    r"\bReference\s+(?:ID|Number)[:\s]+([A-Z0-9\-]{6,20})\b",
]


# ==========================================================================
# RED-FLAG PATTERN DEFINITIONS  (regex-based, feeds finalOutput.redFlags)
# Independent of keyword scoring — both signals are counted separately.
# ==========================================================================

RED_FLAG_PATTERNS: Dict[str, List[str]] = {
    "URGENCY": [
        r"\burgent\b", r"\bimmediately\b", r"\bact now\b", r"\blimited time\b",
        r"\bwithin \d+ hours?\b", r"\bwithin \d+ minutes?\b", r"\basap\b",
        r"\bno delay\b", r"\btoday only\b", r"\bexpires? (?:today|now|soon)\b",
        r"\blast chance\b", r"\bfinal warning\b", r"\bdeadline\b",
    ],
    "OTP_REQUEST": [
        r"\botp\b", r"\bone.?time password\b", r"\bverification code\b",
        r"\bshare.*otp\b", r"\benter.*otp\b", r"\bsend.*otp\b",
        r"\bconfirmation code\b", r"\bsecurity code\b",
    ],
    "FEE_REQUEST": [
        r"\bsmall fee\b", r"\bprocessing fee\b", r"\bregistration fee\b",
        r"\bpay.*fee\b", r"\badvance payment\b", r"\btoken amount\b",
        r"\bsecurity deposit\b", r"\bactivation fee\b", r"\bjoining fee\b",
        r"\bhandling fee\b", r"\bclearance charge\b", r"\bdocumentation charge\b",
        r"\bverification fee\b", r"\bclearance charges\b",
    ],
    "THREAT": [
        r"\blegal action\b", r"\barrested?\b", r"\bsuspended?\b",
        r"\bblocked?\b", r"\bpenalty\b", r"\bcourt\b",
        r"\bjail\b", r"\bwarrant\b", r"\bfir\b", r"\bpolice\b",
        r"\bcriminal case\b", r"\bprosecuted?\b", r"\bdisconnected?\b",
        r"\bseized?\b", r"\bfreeze\b",
    ],
    "PRIZE": [
        r"\bwon\b", r"\bwinner\b", r"\blucky draw\b", r"\blucky winner\b",
        r"\bclaim prize\b", r"\baward\b", r"\bcongratulations\b",
        r"\blottery\b", r"\bbumper prize\b",
        r"\bprize money\b", r"\bwinning amount\b", r"\bselected as winner\b",
    ],
    "IMPERSONATION": [
        r"\brbi\b", r"\bsbi\b", r"\bpolice\b", r"\bgovernment\b",
        r"\btrai\b", r"\bicici\b", r"\bhdfc\b", r"\bcbi\b",
        r"\bincome tax\b", r"\bcustoms\b", r"\bnarcotics?\b",
        r"\bcyber cell\b", r"\bprime minister\b", r"\bnarcotics bureau\b",
        r"\bcid\b", r"\birdai\b", r"\bcbdt\b", r"\buidai\b",
        r"\bmicrosoft\b", r"\bapple support\b",
    ],
    "PERSONAL_DATA_REQUEST": [
        r"\baccount number\b", r"\baadhaar\b", r"\bpan\b",
        r"\bpassword\b", r"\bcvv\b", r"\bcard number\b",
        r"\bbank details\b", r"\bpersonal details\b",
        r"\bdate of birth\b", r"\bdob\b", r"\bmother.?s name\b",
        r"\bconfirm.*bank\b", r"\bverify.*account\b",
    ],
    "SUSPICIOUS_LINK": [
        r"https?://[^\s]*\.(?:xyz|tk|ml|cf|ga|pw|gq|men|loan|top|click|download)[^\s]*",
        r"https?://[^\s]*(?:bit\.ly|tinyurl|goo\.gl|t\.co|rb\.gy|ow\.ly)[^\s]*",
        r"https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",
        r"http://[^\s]+",
        r"https?://[^\s]*(amaz0n|amaz-on|sbi-secure|hdfc-alert|refund-it-dept|india-post-track)[^\s]*",
    ],
    "PRESSURE": [
        r"don.t tell anyone", r"\bkeep.*secret\b", r"\btime running out\b",
        r"\bdon.t share\b", r"\bconfidential\b", r"\bprivate matter\b",
        r"\bonly for you\b", r"\bbetween us\b", r"\bno one should know\b",
        r"\bdo not share this\b",
    ],
    "ADVANCE_FEE": [
        r"\bsend money first\b", r"\bdeposit required\b",
        r"\badvance.*required\b", r"\bpay first\b", r"\bprepayment\b",
        r"\bupfront payment\b", r"\bpay before\b", r"\brelease.*funds\b",
        r"\bpay.*to receive\b",
    ],
}


# ==========================================================================
# Core scoring function (module-level, also used standalone for testing)
# ==========================================================================

# Pre-compile URL patterns at module load time
_COMPILED_URL_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in PHISHING_URL_PATTERNS
]


def calculate_score(message: str) -> Dict[str, Any]:
    """
    Score a message against all 15 scam types.

    Returns:
        score           : float  -- total score (type + 0.5 * universal)
        scam_type       : str
        indicators      : list   -- top 10 matched keywords
        universal_flags : list
        confidence      : float  -- 0.0-0.95 normalised
        tier            : str    -- HIGH / GREY / LOW
        type_scores     : dict
    """
    text_lower = message.lower()

    type_scores: Dict[str, float] = {}
    all_indicators: List[str] = []
    universal_score = 0.0
    universal_found: List[str] = []

    # 1. Universal flags
    for kw, weight in UNIVERSAL_FLAGS.items():
        if kw in text_lower:
            universal_score += weight
            universal_found.append(kw)

    # 2. Per-type keywords
    for scam_type, keywords in SCAM_KEYWORDS.items():
        type_score = 0.0
        for kw, weight in keywords.items():
            if kw in text_lower:
                type_score += weight
                all_indicators.append(f"{scam_type}:{kw}({weight})")
        if type_score > 0:
            type_scores[scam_type] = type_score

    # 3. Phishing URL regex (+6 per unique URL matched — not per pattern)
    #    Prevents double-counting when one URL matches multiple patterns.
    matched_urls: set = set()
    for pattern in _COMPILED_URL_PATTERNS:
        for m in pattern.finditer(message):
            url_str = m.group()
            if url_str not in matched_urls:
                matched_urls.add(url_str)
                type_scores["phishing_link"] = type_scores.get("phishing_link", 0.0) + 6
                all_indicators.append("phishing_url_match(6)")

    # 4. Best matching type
    best_type = max(type_scores, key=type_scores.get) if type_scores else "unknown"
    best_type_score = type_scores.get(best_type, 0.0)

    # 5. Total score = type score + half of universal score
    total_score = best_type_score + (universal_score * 0.5)

    # 6. Tier
    if total_score >= 7.0:
        tier = "HIGH"
    elif total_score >= 3.0:
        tier = "GREY"
    else:
        tier = "LOW"

    confidence = min(0.95, total_score / 15.0)

    return {
        "score":           total_score,
        "scam_type":       best_type,
        "indicators":      all_indicators[:10],
        "universal_flags": universal_found,
        "confidence":      confidence,
        "tier":            tier,
        "type_scores":     type_scores,
    }


# ==========================================================================
# ScamDetector class
# ==========================================================================

class ScamDetector:

    def __init__(self) -> None:
        self._compiled_red_flags: Dict[str, List[re.Pattern]] = {
            flag: [re.compile(p, re.IGNORECASE) for p in patterns]
            for flag, patterns in RED_FLAG_PATTERNS.items()
        }

    # -- Public API ---------------------------------------------------------

    def detect(
        self,
        text: str,
        conversation_history: Optional[list] = None,
    ) -> DetectionResult:
        """
        Run hybrid detection on the latest message plus conversation history.

        Tier logic:
          HIGH (>=7.0) -> is_scam=True, skip LLM, high confidence
          GREY (3-7)   -> is_scam=True, LLM fallback refines type in main.py
          LOW (<3.0)   -> only scam if red flags found
        """
        # Score the incoming message (primary)
        result = calculate_score(text)

        # Context blend with conversation history (30% weight)
        if conversation_history:
            history_text = " ".join(
                m.get("content", "") for m in conversation_history[-6:]
            )
            hist_result = calculate_score(history_text)
            for stype, hscore in hist_result["type_scores"].items():
                current = result["type_scores"].get(stype, 0.0)
                result["type_scores"][stype] = current + (hscore * 0.3)
            if result["type_scores"]:
                result["scam_type"] = max(
                    result["type_scores"], key=result["type_scores"].get
                )

        # Red-flag detection (independent signal)
        red_flags = self._detect_red_flags(text.lower())

        # Determine is_scam and final tier
        tier = result["tier"]
        if tier in ("HIGH", "GREY"):
            is_scam = True
        elif red_flags:
            is_scam = True
            if tier == "LOW":
                tier = "GREY"   # promote so LLM can refine type
        else:
            is_scam = False

        logger.debug(
            "ScamDetector: tier=%s score=%.1f type=%s flags=%s conf=%.0f%%",
            tier, result["score"], result["scam_type"],
            red_flags, result["confidence"] * 100,
        )

        return DetectionResult(
            is_scam=is_scam,
            scam_type=result["scam_type"] if is_scam else None,
            confidence_score=round(result["confidence"], 2),
            red_flags_detected=red_flags,
            detection_tier=tier,
            type_scores=result["type_scores"],
        )

    def detect_red_flags_in_text(self, text: str) -> List[str]:
        """Scan arbitrary text for red flags (used by quality_tracker)."""
        return self._detect_red_flags(text.lower())

    # -- Internal -----------------------------------------------------------

    def _detect_red_flags(self, text_lower: str) -> List[str]:
        detected: List[str] = []
        for flag_name, patterns in self._compiled_red_flags.items():
            for pattern in patterns:
                if pattern.search(text_lower):
                    detected.append(flag_name)
                    break
        return detected


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
scam_detector = ScamDetector()
