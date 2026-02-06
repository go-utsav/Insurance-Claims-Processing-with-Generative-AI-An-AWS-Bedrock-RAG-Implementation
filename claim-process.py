"""
Entry point: process one claim or compare models.
Uses the claim_processor package (see claim_processor/ folder).

Run:
  python claim-process.py                    # process default claim
  python claim-process.py --compare          # compare Claude 3 Sonnet vs Haiku
  python claim-process.py --process --compare  # run both
  python run_claim_process.py --process --compare  # same, alternative script
"""
import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from claim_processor import compare_models, process_document
from claim_processor.document import extract_text_from_s3, get_bucket_name

DEFAULT_KEY = "claim-documents/2026-02-06/Claim - CL-2024-001.pdf"


def main():
    import argparse
    p = argparse.ArgumentParser(description="Process claim or compare models.")
    p.add_argument("--process", action="store_true", help="Extract + summary (default).")
    p.add_argument("--compare", action="store_true", help="Compare Claude 3 models.")
    p.add_argument("--key", default=DEFAULT_KEY, help="S3 key for claim document.")
    args = p.parse_args()
    if not args.process and not args.compare:
        args.process = True

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
