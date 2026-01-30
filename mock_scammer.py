"""
Mock Scammer API
Simulates different types of scam conversations for testing and demo purposes
"""

import random
from typing import Dict, List


class MockScammer:
    def __init__(self):
        self.scenarios = {
            "phishing": {
                "name": "Bank Account Phishing",
                "description": "Scammer impersonates bank and requests account verification",
                "messages": [
                    "URGENT: Your bank account has been temporarily suspended due to suspicious activity. Please verify your account immediately by clicking here: http://bit.ly/verify-bank-now",
                    "This is a security measure to protect your account. We need you to confirm your account number and last 4 digits of your card.",
                    "Please provide your account number so we can verify your identity and restore your access.",
                    "Time is running out! Your account will be permanently closed if not verified within 24 hours. Please send details now.",
                    "For verification, transfer Rs 1 to this account: 9876543210987654 IFSC: HDFC0001234. This amount will be refunded immediately.",
                    "You can also send to our UPI: bankverify@paytm for instant verification. Please hurry!"
                ],
                "expected_intel": ["bank_accounts", "upi_ids", "phishing_links", "ifsc_codes"]
            },
            
            "lottery": {
                "name": "Lottery Prize Scam",
                "description": "Fake lottery winning notification",
                "messages": [
                    "🎉 CONGRATULATIONS! You have won $1,000,000 in the International Lottery Draw! Your lucky number 7234 was selected!",
                    "To claim your prize, we need to verify your identity. This is a mandatory government requirement.",
                    "Please provide your bank account details where we can transfer your winning amount.",
                    "There is a small processing fee of Rs 5,000 that needs to be paid first. Send to account: 1122334455667788",
                    "Or you can pay via UPI to: lotterywinner@phonepe. This fee will be deducted from your prize money.",
                    "Call our claims department at +91-9123456789 for immediate processing. Offer valid for 48 hours only!"
                ],
                "expected_intel": ["bank_accounts", "upi_ids", "phone_numbers"]
            },
            
            "tech_support": {
                "name": "Tech Support Scam",
                "description": "Fake tech support claiming virus infection",
                "messages": [
                    "⚠️ WARNING: Your computer is infected with a critical virus! Microsoft Security has detected malicious software on your device.",
                    "Do not shut down your computer. Call our support line immediately: 1-800-TECH-911 or +91-9988776655",
                    "Our technicians need remote access to clean your system. Please visit: https://remote-fix.tk/support to download our tool.",
                    "The virus is stealing your bank information right now! We need to act fast.",
                    "For immediate fix, we offer premium service for just $299. Pay via our secure link or send to: techsupport@okaxis",
                    "Email us at urgent.support@techfix.com with your contact details and we'll call you back in 5 minutes."
                ],
                "expected_intel": ["phone_numbers", "phishing_links", "upi_ids", "email_addresses"]
            },
            
            "investment": {
                "name": "Cryptocurrency Investment Scam",
                "description": "Fake investment opportunity promising high returns",
                "messages": [
                    "💰 Limited Time Investment Opportunity! Invest in Bitcoin and earn 500% returns in just 30 days!",
                    "Our AI trading system guarantees profits. Minimum investment: Rs 10,000. Join 50,000+ successful investors!",
                    "To start investing, transfer funds to our secure Bitcoin wallet: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
                    "Or send via UPI to: cryptoinvest@paytm for instant account activation.",
                    "For bank transfer: Account 5544332211009988, IFSC: ICIC0001234, Name: Crypto Ventures Ltd",
                    "WhatsApp me at +91-9876543210 for VIP investment packages with even higher returns!"
                ],
                "expected_intel": ["cryptocurrency", "upi_ids", "bank_accounts", "ifsc_codes", "phone_numbers"]
            },
            
            "romance": {
                "name": "Romance Scam",
                "description": "Fake romantic interest asking for money",
                "messages": [
                    "Hi dear, I hope this message finds you well. I've been admiring your profile and would love to get to know you better ❤️",
                    "I'm currently stuck in a difficult situation. I'm traveling for work but my wallet was stolen. Can you help me?",
                    "I promise to pay you back as soon as I return. I just need Rs 20,000 for hotel and flight ticket.",
                    "Please send to my friend's account: 7788990011223344. He will give me cash here.",
                    "Or if easier, send via UPI: helpme@ybl. I will never forget your kindness!",
                    "You can reach me at +91-9001122334 if you have any questions. Please hurry, I'm desperate! 🙏"
                ],
                "expected_intel": ["bank_accounts", "upi_ids", "phone_numbers"]
            },
            
            "job_offer": {
                "name": "Fake Job Offer Scam",
                "description": "Scam offering work-from-home job requiring payment",
                "messages": [
                    "Congratulations! Your profile has been selected for a Work From Home opportunity. Earn Rs 50,000/month!",
                    "This is a legitimate position with Amazon/Flipkart for product review. No experience needed!",
                    "To activate your account and receive tasks, there is a one-time registration fee of Rs 2,999.",
                    "Send payment to: Account 6655443322110099, IFSC: SBIN0009876, Name: HR Solutions Pvt Ltd",
                    "Or quick payment via UPI: jobregistration@paytm. You'll start earning within 24 hours!",
                    "Contact our HR manager at +91-9112233445 or email: hr.careers@job-offer.com for more details."
                ],
                "expected_intel": ["bank_accounts", "ifsc_codes", "upi_ids", "phone_numbers", "email_addresses"]
            },
            
            "impersonation": {
                "name": "Government Official Impersonation",
                "description": "Scammer pretending to be government official",
                "messages": [
                    "This is Officer Sharma from Income Tax Department. Your PAN card has been used for suspicious transactions.",
                    "An arrest warrant has been issued in your name for tax evasion. You owe Rs 2,50,000 in unpaid taxes.",
                    "To avoid legal action and arrest, you must pay the penalty immediately.",
                    "Make payment to government account: 4433221100998877, IFSC: PUNB0012345",
                    "Or use government UPI portal: govtpayment@sbi for instant processing.",
                    "Call me directly at +91-9876501234 to confirm payment. This is time-sensitive! Do not ignore this notice."
                ],
                "expected_intel": ["bank_accounts", "ifsc_codes", "upi_ids", "phone_numbers"]
            }
        }
    
    def get_scenario(self, scam_type: str) -> Dict:
        """Get a complete scam scenario"""
        return self.scenarios.get(scam_type, self.scenarios["phishing"])
    
    def get_random_scenario(self) -> Dict:
        """Get a random scam scenario"""
        scam_type = random.choice(list(self.scenarios.keys()))
        return {
            "type": scam_type,
            **self.scenarios[scam_type]
        }
    
    def list_scenarios(self) -> List[str]:
        """List all available scam scenarios"""
        return list(self.scenarios.keys())
    
    def get_scenario_description(self, scam_type: str) -> str:
        """Get description of a scam scenario"""
        scenario = self.scenarios.get(scam_type)
        if scenario:
            return f"{scenario['name']}: {scenario['description']}"
        return "Unknown scenario"
    
    def generate_dynamic_message(self, scam_type: str, turn: int) -> str:
        """
        Generate a dynamic scammer message based on turn number
        Simulates escalation and urgency
        """
        scenario = self.scenarios.get(scam_type, self.scenarios["phishing"])
        
        if turn < len(scenario["messages"]):
            return scenario["messages"][turn]
        
        # If conversation goes beyond scripted messages, generate urgency
        urgency_messages = [
            "Why are you not responding? Time is running out!",
            "I need your decision NOW! This offer expires in 1 hour!",
            "Are you still there? Please confirm your payment immediately.",
            "This is your last chance. Act now or lose everything!",
            "I'm waiting for your response. Please hurry!"
        ]
        
        return random.choice(urgency_messages)
    
    def get_all_scenarios_summary(self) -> Dict:
        """Get summary of all available scenarios"""
        summary = {}
        for scam_type, scenario in self.scenarios.items():
            summary[scam_type] = {
                "name": scenario["name"],
                "description": scenario["description"],
                "message_count": len(scenario["messages"]),
                "expected_intel_types": scenario["expected_intel"]
            }
        return summary


# Test the mock scammer
if __name__ == "__main__":
    mock_scammer = MockScammer()
    
    print("🎭 Mock Scammer API Test\n")
    print("=" * 80)
    
    # List all scenarios
    print("\nAvailable Scam Scenarios:")
    print("-" * 80)
    for scam_type in mock_scammer.list_scenarios():
        description = mock_scammer.get_scenario_description(scam_type)
        print(f"• {scam_type.upper()}: {description}")
    
    # Show example of phishing scenario
    print("\n" + "=" * 80)
    print("\nExample: PHISHING SCENARIO")
    print("-" * 80)
    
    phishing = mock_scammer.get_scenario("phishing")
    print(f"Name: {phishing['name']}")
    print(f"Description: {phishing['description']}")
    print(f"Expected Intel: {', '.join(phishing['expected_intel'])}")
    print("\nConversation Flow:")
    
    for i, msg in enumerate(phishing['messages'], 1):
        print(f"\nTurn {i}:")
        print(f"Scammer: {msg[:100]}{'...' if len(msg) > 100 else ''}")
    
    # Test random scenario
    print("\n" + "=" * 80)
    print("\nRandom Scenario Test:")
    print("-" * 80)
    random_scenario = mock_scammer.get_random_scenario()
    print(f"Type: {random_scenario['type']}")
    print(f"Name: {random_scenario['name']}")
    print(f"First Message: {random_scenario['messages'][0][:100]}...")
    
    # Test summary
    print("\n" + "=" * 80)
    print("\nAll Scenarios Summary:")
    print("-" * 80)
    summary = mock_scammer.get_all_scenarios_summary()
    for scam_type, info in summary.items():
        print(f"\n{scam_type.upper()}:")
        print(f"  Messages: {info['message_count']}")
        print(f"  Intel Types: {', '.join(info['expected_intel_types'])}")
