#!/usr/bin/env python3
"""
AI Skills Rank - Report Generator
通用报告生成器，可根据参数调用不同的采集脚本。
"""
import argparse
import subprocess
import sys
import os
from datetime import datetime

COLLECTORS = {
    "star": "collect_star.py",
    "activity": "collect_activity.py",
    "security": "collect_security.py",
    "cn-friendly": "collect_cn_friendly.py",
    "cn-made": "collect_cn_made.py",
}

OUTPUT_MAP = {
    "star": "top50-ai-skills-{month}.html",
    "activity": "active-ai-skills-{month}.html",
    "security": "secure-ai-skills-{month}.html",
    "cn-friendly": "cn-friendly-skills-{month}.html",
    "cn-made": "cn-made-skills-{month}.html",
}


def main():
    parser = argparse.ArgumentParser(description="AI Skills Rank Report Generator")
    parser.add_argument("--type", "-t", required=True, choices=COLLECTORS.keys(), help="Report type")
    parser.add_argument("--month", "-m", default=None, help="Report month (YYYY-MM)")
    args = parser.parse_args()

    if not args.month:
        args.month = datetime.now().strftime("%Y-%m")

    output_file = OUTPUT_MAP[args.type].format(month=args.month)
    output_path = os.path.join("reports", args.month, output_file)

    script = os.path.join("scripts", COLLECTORS[args.type])
    
    print(f"[Generator] Running {COLLECTORS[args.type]} for {args.month}...")
    print(f"[Generator] Output: {output_path}")

    result = subprocess.run(
        [sys.executable, script, "--output", output_path, "--month", args.month],
        capture_output=False
    )

    if result.returncode != 0:
        print(f"[Generator] ERROR: Collector exited with code {result.returncode}")
        sys.exit(result.returncode)

    print(f"[Generator] Report generated successfully: {output_path}")


if __name__ == "__main__":
    main()
