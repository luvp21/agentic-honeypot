"""
Metrics Analyzer for Honeypot Testing
======================================

Analyzes test results and generates accuracy metrics for:
- Intelligence extraction success rate
- Persona consistency
- Engagement duration
- Response quality

Usage:
    python metrics_analyzer.py test_results/
"""

import json
import re
from pathlib import Path
from typing import List, Dict
from collections import defaultdict


class MetricsAnalyzer:
    def __init__(self, results_dir: str):
        self.results_dir = Path(results_dir)
        self.conversations = []
        self.load_conversations()

    def load_conversations(self):
        """Load all conversation logs (supports both internal and platform logs)"""
        # Dictionary to track sessions to avoid duplicates
        loaded_sessions = {}

        # Pattern 1: Internal test suite logs (round_*.json)
        for file in self.results_dir.glob("round_*.json"):
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    # Normalize to internal format
                    if "conversation" in data:
                        loaded_sessions[data["session_id"]] = data
            except Exception as e:
                print(f"⚠️ Error loading {file}: {e}")

        # Pattern 2: Platform test logs (*.json, excluding summary/report)
        for file in self.results_dir.glob("*.json"):
            if file.name.startswith("round_") or file.name.startswith("summary_") or file.name == "metrics_report.json":
                continue

            try:
                with open(file, 'r') as f:
                    data = json.load(f)

                    # Check if it's a platform log (has "exchanges" list)
                    if "session_id" in data and "exchanges" in data:
                        # Convert platform log format to analyzer format
                        normalized = self._normalize_platform_log(data)
                        loaded_sessions[normalized["session_id"]] = normalized
            except Exception as e:
                print(f"⚠️ Error loading {file}: {e}")

        self.conversations = list(loaded_sessions.values())
        print(f"📂 Loaded {len(self.conversations)} conversation logs")

    def _normalize_platform_log(self, platform_data: Dict) -> Dict:
        """Convert platform log format to internal analyzer format"""
        conversation = []
        for x in platform_data.get("exchanges", []):
            conversation.append({
                "turn": x["turn"],
                "scammer": x["incoming_message"]["text"] or "",
                "agent": x["agent_response"]["reply"] or "",
                "timestamp": x["timestamp"]
            })

        return {
            "session_id": platform_data["session_id"],
            "scenario_type": platform_data.get("final_callback", {}).get("scam_type", "unknown"),
            "total_turns": len(conversation),
            "conversation": conversation
        }

    def extract_intelligence_from_text(self, text: str) -> Dict:
        """Extract intelligence mentions from text"""
        intel = {
            "bank_accounts": [],
            "upi_ids": [],
            "phone_numbers": [],
            "ifsc_codes": [],
            "urls": []
        }

        # Bank accounts (9-18 digits)
        bank_pattern = r'\b(\d{9,18})\b'
        intel['bank_accounts'] = re.findall(bank_pattern, text)

        # UPI IDs
        upi_pattern = r'\b([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+)\b'
        intel['upi_ids'] = re.findall(upi_pattern, text)

        # Phone numbers
        phone_pattern = r'(?:\+91[\s-]?)?[6-9]\d{9}'
        intel['phone_numbers'] = re.findall(phone_pattern, text)

        # IFSC codes
        ifsc_pattern = r'\b([A-Z]{4}0[A-Z0-9]{6})\b'
        intel['ifsc_codes'] = re.findall(ifsc_pattern, text)

        # URLs
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        intel['urls'] = re.findall(url_pattern, text)

        return intel

    def analyze_intelligence_extraction(self) -> Dict:
        """Analyze how well the agent extracted intelligence"""
        print("\n📊 Analyzing Intelligence Extraction...")

        extraction_stats = {
            "total_conversations": len(self.conversations),
            "conversations_with_extractions": 0,
            "extraction_by_type": defaultdict(lambda: {"available": 0, "extracted": 0}),
            "detailed_results": []
        }

        for conv in self.conversations:
            # Get all scammer messages
            scammer_messages = [turn['scammer'] for turn in conv['conversation']]
            scammer_text = ' '.join(scammer_messages)

            # Get all agent messages
            agent_messages = [turn['agent'] for turn in conv['conversation']]
            agent_text = ' '.join(agent_messages)

            # Extract what was available in scammer messages
            available_intel = self.extract_intelligence_from_text(scammer_text)

            # Check what agent asked for/extracted
            agent_intel_requests = self.extract_intelligence_from_text(agent_text)

            conv_result = {
                "session_id": conv['session_id'],
                "scenario": conv['scenario_type'],
                "turns": conv['total_turns'],
                "available_intel": {},
                "extraction_attempts": {}
            }

            has_extraction = False

            for intel_type in ['bank_accounts', 'upi_ids', 'phone_numbers', 'ifsc_codes', 'urls']:
                available_count = len(available_intel[intel_type])

                # Check if agent mentioned this type or asked for it
                asked_for_it = (
                    ('account' in agent_text.lower() and intel_type == 'bank_accounts') or
                    ('upi' in agent_text.lower() and intel_type == 'upi_ids') or
                    ('phone' in agent_text.lower() or 'mobile' in agent_text.lower() and intel_type == 'phone_numbers') or
                    ('ifsc' in agent_text.lower() and intel_type == 'ifsc_codes') or
                    ('link' in agent_text.lower() and intel_type == 'urls')
                )

                if available_count > 0:
                    extraction_stats['extraction_by_type'][intel_type]['available'] += 1
                    conv_result['available_intel'][intel_type] = available_count

                    if asked_for_it:
                        extraction_stats['extraction_by_type'][intel_type]['extracted'] += 1
                        has_extraction = True
                        conv_result['extraction_attempts'][intel_type] = "asked"

            if has_extraction:
                extraction_stats['conversations_with_extractions'] += 1

            extraction_stats['detailed_results'].append(conv_result)

        return extraction_stats

    def analyze_engagement_metrics(self) -> Dict:
        """Analyze conversation engagement metrics"""
        print("\n💬 Analyzing Engagement Metrics...")

        total_turns = [conv['total_turns'] for conv in self.conversations]

        return {
            "total_conversations": len(self.conversations),
            "total_turns": sum(total_turns),
            "average_turns": round(sum(total_turns) / len(total_turns), 2) if total_turns else 0,
            "min_turns": min(total_turns) if total_turns else 0,
            "max_turns": max(total_turns) if total_turns else 0,
            "by_scenario": self._engagement_by_scenario()
        }

    def _engagement_by_scenario(self) -> Dict:
        """Break down engagement by scenario type"""
        by_scenario = defaultdict(list)

        for conv in self.conversations:
            by_scenario[conv['scenario_type']].append(conv['total_turns'])

        result = {}
        for scenario, turns in by_scenario.items():
            result[scenario] = {
                "count": len(turns),
                "avg_turns": round(sum(turns) / len(turns), 2),
                "total_turns": sum(turns)
            }

        return result

    def analyze_persona_consistency(self) -> Dict:
        """Analyze if agent maintains consistent persona"""
        print("\n🎭 Analyzing Persona Consistency...")

        persona_keywords = {
            "elderly": ["confused", "don't understand", "grandson", "help me", "please explain"],
            "cautious": ["verify", "proof", "legitimate", "how can I", "make sure"],
            "eager": ["!", "wow", "really", "exciting", "great"],
            "tech_novice": ["how do I", "confused", "technology", "step by step", "don't know"]
        }

        consistency_scores = []

        for conv in self.conversations:
            agent_messages = [turn['agent'].lower() for turn in conv['conversation']]
            agent_text = ' '.join(agent_messages)

            # Count persona markers
            persona_scores = {}
            for persona, keywords in persona_keywords.items():
                score = sum(1 for keyword in keywords if keyword in agent_text)
                persona_scores[persona] = score

            # Dominant persona
            dominant = max(persona_scores, key=persona_scores.get) if persona_scores else "unknown"
            max_score = persona_scores.get(dominant, 0)

            consistency_scores.append({
                "session_id": conv['session_id'],
                "dominant_persona": dominant,
                "persona_strength": max_score,
                "scores": persona_scores
            })

        return {
            "total_conversations": len(consistency_scores),
            "results": consistency_scores
        }

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("GENERATING COMPREHENSIVE TEST REPORT")
        print("="*60)

        # Run all analyses
        intel_stats = self.analyze_intelligence_extraction()
        engagement_stats = self.analyze_engagement_metrics()
        persona_stats = self.analyze_persona_consistency()

        # Get timestamp from summary OR first log file
        if list(self.results_dir.glob("summary_*.json")):
            ts = Path(list(self.results_dir.glob("summary_*.json"))[0]).stem.split('_')[1]
        else:
            from datetime import datetime
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")

        report = {
            "report_timestamp": ts,
            "intelligence_extraction": intel_stats,
            "engagement_metrics": engagement_stats,
            "persona_consistency": persona_stats
        }

        # Save report
        report_file = self.results_dir / "metrics_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, indent=2, fp=f)

        # Print summary
        self.print_summary(intel_stats, engagement_stats)

        print(f"\n📊 Full report saved to: {report_file}")

        return report

    def print_summary(self, intel_stats: Dict, engagement_stats: Dict):
        """Print readable summary"""
        print("\n" + "="*60)
        print("KEY METRICS SUMMARY")
        print("="*60)

        print(f"\n📈 ENGAGEMENT METRICS")
        print(f"   Total Conversations: {engagement_stats['total_conversations']}")
        print(f"   Average Turns/Conversation: {engagement_stats['average_turns']}")
        print(f"   Range: {engagement_stats['min_turns']}-{engagement_stats['max_turns']} turns")

        print(f"\n🔍 INTELLIGENCE EXTRACTION")
        total_conversations = intel_stats['total_conversations']
        with_extraction = intel_stats['conversations_with_extractions']
        extraction_rate = (with_extraction / total_conversations * 100) if total_conversations > 0 else 0
        print(f"   Conversations with Extraction Attempts: {with_extraction}/{total_conversations} ({extraction_rate:.1f}%)")

        print(f"\n   Extraction by Type:")
        for intel_type, stats in intel_stats['extraction_by_type'].items():
            available = stats['available']
            extracted = stats['extracted']
            rate = (extracted / available * 100) if available > 0 else 0
            print(f"      {intel_type}: {extracted}/{available} ({rate:.1f}%)")

        print(f"\n📊 BY SCENARIO:")
        for scenario, stats in engagement_stats['by_scenario'].items():
            print(f"   {scenario}:")
            print(f"      Conversations: {stats['count']}")
            print(f"      Avg Turns: {stats['avg_turns']}")


if __name__ == "__main__":
    import sys

    results_dir = sys.argv[1] if len(sys.argv) > 1 else "test_results"

    print("="*60)
    print("HONEYPOT METRICS ANALYZER")
    print("="*60)
    print(f"\nAnalyzing results from: {results_dir}")

    analyzer = MetricsAnalyzer(results_dir)
    analyzer.generate_report()

    print("\n✅ Analysis complete!")
