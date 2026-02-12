"""
Cloud Log Extractor for Honeypot
================================

Extracts structured test data from raw Hugging Face Space logs.

Usage:
1. Go to your HF Space -> Logs
2. Copy all text
3. Paste into a file named 'raw_logs.txt'
4. Run: python extract_cloud_logs.py raw_logs.txt
5. Run analyzer: python metrics_analyzer.py platform_test_logs/
"""

import sys
import json
import re
from pathlib import Path

def extract_logs(log_file: str, output_dir: str = "platform_test_logs"):
    """Parse raw log file and save JSON sessions"""

    # Create output directory
    out_path = Path(output_dir)
    out_path.mkdir(exist_ok=True)

    print(f"📂 Reading logs from: {log_file}")

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return

    # Regex to find JSON blocks between delimiters
    # Pattern: @@@TEST_LOG_START@@@\n{JSON}\n@@@TEST_LOG_END@@@
    pattern = r"@@@TEST_LOG_START@@@\s*(\{.*?\})\s*@@@TEST_LOG_END@@@"

    matches = re.finditer(pattern, content, re.DOTALL)

    count = 0
    for match in matches:
        json_str = match.group(1)
        try:
            data = json.loads(json_str)
            session_id = data.get("session_id", f"unknown_session_{count}")

            # Save to file
            out_file = out_path / f"{session_id}.json"
            with open(out_file, 'w') as f:
                json.dump(data, indent=2, fp=f)

            print(f"✅ Extracted session: {session_id}")
            count += 1

        except json.JSONDecodeError:
            print(f"⚠️ Failed to parse JSON block at index {match.start()}")
            continue

    print(f"\n🎉 Extraction complete! Found {count} valid sessions.")
    print(f"Files saved to: {output_dir}/")
    print(f"Now run: python metrics_analyzer.py {output_dir}/")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_cloud_logs.py <raw_log_file>")
        sys.exit(1)

    extract_logs(sys.argv[1])
