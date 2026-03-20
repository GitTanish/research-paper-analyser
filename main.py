#!/usr/bin/env python3
"""
CLI entry point for the Research Paper Analyzer.
Usage:
  python main.py --pdf path/to/paper.pdf
  python main.py --url https://arxiv.org/abs/2303.08774
  python main.py --text path/to/paper.txt
"""
import argparse
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="AI Research Paper Analyzer")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pdf", type=str, help="Path to PDF file")
    group.add_argument("--url", type=str, help="URL to PDF (arXiv supported)")
    group.add_argument("--text", type=str, help="Path to plain text file")

    parser.add_argument("--output", type=str, default="research_brief.md",
                        help="Output file for the research brief (default: research_brief.md)")
    parser.add_argument("--json-output", type=str, default=None,
                        help="Optional: also save full JSON results")

    args = parser.parse_args()

    # Check API key
    if not os.environ.get("GROQ_API_KEY"):
        print("[ERROR] GROQ_API_KEY environment variable not set.")
        print("        Export it: export GROQ_API_KEY=gsk_...")
        sys.exit(1)

    # Load paper text
    from pdf_utils import extract_text_from_pdf, fetch_pdf_from_url, truncate_for_context

    print("📥 Loading paper...")
    if args.pdf:
        paper_text = extract_text_from_pdf(args.pdf)
        print(f"✅ Extracted {len(paper_text):,} chars from {args.pdf}")
    elif args.url:
        paper_text = fetch_pdf_from_url(args.url)
        print(f"✅ Fetched {len(paper_text):,} chars from {args.url}")
    else:
        paper_text = Path(args.text).read_text(encoding="utf-8")
        print(f"✅ Loaded {len(paper_text):,} chars from {args.text}")

    # Truncate for context window
    trimmed = truncate_for_context(paper_text, max_chars=12000)
    if len(trimmed) < len(paper_text):
        print(f"[WARN] Paper truncated to {len(trimmed):,} chars for context window")

    # Run pipeline
    print("\n[START] Starting multi-agent pipeline...\n")
    from crew import run_full_pipeline

    def cli_status(msg):
        print(f"  {msg}")

    results = run_full_pipeline(trimmed, status_callback=cli_status)

    # Save outputs
    brief = results.get("final_brief", "")
    Path(args.output).write_text(brief, encoding="utf-8")
    print(f"\n[OK] Research brief saved to: {args.output}")

    if args.json_output:
        Path(args.json_output).write_text(
            json.dumps(results, indent=2, default=str), encoding="utf-8"
        )
        print(f"[OK] Full JSON results saved to: {args.json_output}")

    # Print brief to stdout
    print("\n" + "="*60)
    print(brief)


if __name__ == "__main__":
    main()
