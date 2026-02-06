"""
Local backend for FNOL PoC: compare claim text vs policy using Bedrock.
Run from project root: python -m backend.app
Then open frontend at http://localhost:3000 and use API at http://localhost:5000.
"""
import json
import os
import re
import sys

# Project root on path so claim_processor and data/ are findable
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from flask import Flask, jsonify, request
from flask_cors import CORS

from backend.prompts import CLAIMS_ADJUSTER_SYSTEM
from backend.verification import verify_document_legitimacy

# Load .env from project root
from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"))

DATA_DIR = os.path.join(ROOT, "data")
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
BUCKET_NAME = os.getenv("BUCKET_NAME")

app = Flask(__name__)
# CORS: allow React dev server for local PoC
CORS(
    app,
    origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.after_request
def add_cors_headers(response):
    """Ensure CORS headers are on every response (e.g. errors)."""
    origin = request.origin if request.origin else "http://localhost:3000"
    if origin in ("http://localhost:3000", "http://127.0.0.1:3000"):
        response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


def _load_policy() -> str:
    path = os.path.join(DATA_DIR, "policy_document.txt")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Policy file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _load_sample(name: str) -> str:
    allowed = ("claim_valid", "claim_invalid", "claim_invalid_no_police")
    if name not in allowed:
        raise ValueError(f"Sample must be one of {allowed}")
    path = os.path.join(DATA_DIR, f"{name}.txt")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Sample file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _invoke_bedrock(policy_text: str, claim_text: str) -> str:
    from claim_processor.bedrock import get_bedrock_runtime, invoke_claude3_messages
    user_content = f"""{CLAIMS_ADJUSTER_SYSTEM}

[Policy]
{policy_text}

[Claim]
{claim_text}
"""
    client = get_bedrock_runtime()
    return invoke_claude3_messages(
        MODEL_ID, user_content, max_tokens=1500, temperature=0.0, client=client
    )


def _parse_json_from_model(reply: str) -> dict:
    reply = reply.strip()
    # Strip markdown code block if present
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", reply)
    if m:
        reply = m.group(1).strip()
    return json.loads(reply)


def _extract_claim_metadata(claim_text: str) -> dict:
    """Extract claim_id, dates, cost, police_report_filed from claim text for verification."""
    metadata = {
        "claim_id": None,
        "incident_date": None,
        "filing_date": None,
        "estimated_cost": None,
        "police_report_filed": False,
    }
    # Extract claim ID (e.g. "Claim ID: CL-2024-001")
    m = re.search(r"Claim ID:\s*([A-Z0-9-]+)", claim_text, re.IGNORECASE)
    if m:
        metadata["claim_id"] = m.group(1).strip()
    # Extract incident date
    m = re.search(r"Date of Incident:\s*(\d{4}-\d{2}-\d{2})", claim_text, re.IGNORECASE)
    if m:
        metadata["incident_date"] = m.group(1)
    # Extract filing date
    m = re.search(r"Date of Filing:\s*(\d{4}-\d{2}-\d{2})", claim_text, re.IGNORECASE)
    if m:
        metadata["filing_date"] = m.group(1)
    # Extract estimated cost (e.g. "$1,800" or "$3,500")
    m = re.search(r"Estimated (?:Repair )?Cost:\s*\$?([\d,]+)", claim_text, re.IGNORECASE)
    if m:
        cost_str = m.group(1).replace(",", "")
        try:
            metadata["estimated_cost"] = float(cost_str)
        except ValueError:
            pass
    # Check if police report filed
    police_match = re.search(r"Police Report Filed:\s*(Yes|No)", claim_text, re.IGNORECASE)
    if police_match:
        metadata["police_report_filed"] = police_match.group(1).lower() == "yes"
    return metadata


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/upload-url", methods=["GET"])
def get_upload_url():
    """Return a presigned PUT URL for uploading a file to S3. Used by form + upload flow."""
    if not BUCKET_NAME:
        return jsonify({"error": "S3 bucket not configured (BUCKET_NAME not set)"}), 503
    claim_id = request.args.get("claim_id", "unknown").strip() or "unknown"
    filename = request.args.get("filename", "").strip()
    if not filename:
        return jsonify({"error": "filename is required"}), 400
    # Sanitise: only allow safe chars in key
    safe_name = os.path.basename(filename).replace(" ", "-")
    key = f"claims/{claim_id}/{safe_name}"
    try:
        import boto3
        s3 = boto3.client("s3")
        url = s3.generate_presigned_url(
            "put_object",
            Params={"Bucket": BUCKET_NAME, "Key": key},
            ExpiresIn=900,
        )
        return jsonify({"upload_url": url, "key": key})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/upload-claim-file", methods=["POST"])
def upload_claim_file():
    """
    Proxy upload: accept file via multipart/form-data and upload to S3 server-side.
    Avoids S3 CORS (browser only talks to this API). Requires claim_id and file.
    """
    if not BUCKET_NAME:
        return jsonify({"error": "S3 bucket not configured (BUCKET_NAME not set)"}), 503
    claim_id = request.form.get("claim_id", "unknown").strip() or "unknown"
    file = request.files.get("file")
    if not file or file.filename == "":
        return jsonify({"error": "file is required"}), 400
    safe_name = os.path.basename(file.filename).replace(" ", "-")
    key = f"claims/{claim_id}/{safe_name}"
    try:
        import boto3
        s3 = boto3.client("s3")
        s3.upload_fileobj(
            file.stream,
            BUCKET_NAME,
            key,
            ExtraArgs={"ContentType": file.content_type or "application/octet-stream"},
        )
        return jsonify({"ok": True, "key": key})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/samples/<name>", methods=["GET"])
def get_sample(name: str):
    try:
        text = _load_sample(name)
        return jsonify({"claim_text": text})
    except (ValueError, FileNotFoundError) as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/process-claim", methods=["POST"])
def process_claim():
    body = request.get_json() or {}
    claim_text = body.get("claim_text", "").strip()
    police_report_text = body.get("police_report_text", "").strip() or None
    if not claim_text:
        return jsonify({"error": "claim_text is required"}), 400
    try:
        policy_text = _load_policy()
        reply = _invoke_bedrock(policy_text, claim_text)
        result = _parse_json_from_model(reply)
        
        # Run document verification
        metadata = _extract_claim_metadata(claim_text)
        if metadata["claim_id"] and metadata["incident_date"] and metadata["filing_date"]:
            verification = verify_document_legitimacy(
                claim_id=metadata["claim_id"],
                incident_date=metadata["incident_date"],
                filing_date=metadata["filing_date"],
                estimated_cost=metadata["estimated_cost"],
                police_report_filed=metadata["police_report_filed"],
                claim_type="collision",  # Could detect from claim text
                claim_text=claim_text,
                police_report_text=police_report_text,
            )
            # Flatten nested checks (date_logic has nested checks array)
            flat_checks = []
            for check in verification.get("checks", []):
                if "checks" in check:  # Nested checks (e.g. date_logic)
                    flat_checks.extend(check["checks"])
                else:
                    flat_checks.append(check)
            verification["checks"] = flat_checks
            result["verification"] = verification
        
        return jsonify(result)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 500
    except json.JSONDecodeError as e:
        return jsonify({"error": f"Model did not return valid JSON: {e}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Use 5001 if 5000 is taken (e.g. macOS AirPlay Receiver)
    port = int(os.getenv("FLASK_PORT", "5001"))
    app.run(host="0.0.0.0", port=port, debug=True)
