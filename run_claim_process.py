#!/usr/bin/env python3
"""
Run claim processing: process a single document or compare models.

Examples:
  # Process one claim (extract + summary)
  python run_claim_process.py --process

  # Compare Claude 3 Sonnet vs Haiku on the same document
  python run_claim_process.py --compare

  # Run both: process, then model comparison
  python run_claim_process.py --process --compare

  # Use a different S3 key
  python run_claim_process.py --process --key claim-documents/2026-02-06/Claim - CL-2024-002.pdf
  python run_claim_process.py --compare --key claim-documents/2026-02-06/Claim - CL-2024-002.pdf
"""
import argparse
import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()

# Add project root so claim_processor can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from claim_processor import compare_models, process_document
from claim_processor.document import extract_text_from_s3, get_bucket_name


DEFAULT_KEY = "claim-documents/2026-02-06/Claim - CL-2024-001.pdf"


def main():
    parser = argparse.ArgumentParser(
        description="Process insurance claims with Bedrock or compare models."
    )
    parser.add_argument(
        "--process",
        action="store_true",
        help="Run process_document: extract info + generate summary.",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Run compare_models: same extract on multiple Claude 3 models.",
    )
    parser.add_argument(
        "--key",
        default=DEFAULT_KEY,
        help=f"S3 object key for the claim document (default: {DEFAULT_KEY}).",
    )
    args = parser.parse_args()

    if not args.process and not args.compare:
        args.process = True  # default: process

    if args.process:
        print("Running process_document...")
        result = process_document(key=args.key)
        print(json.dumps(result, indent=2))

    if args.compare:
        print("\nRunning compare_models...")
        bucket = get_bucket_name()
        document_text = extract_text_from_s3(bucket, args.key)
        results = compare_models(document_text)
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
