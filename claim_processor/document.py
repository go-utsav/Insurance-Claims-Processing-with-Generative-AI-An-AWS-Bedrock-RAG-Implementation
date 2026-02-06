"""Read claim documents from S3 (PDF or plain text)."""

import io
import os

import boto3
from pypdf import PdfReader


def get_bucket_name() -> str:
    """Bucket name from env (used by extract_text_from_s3)."""
    name = os.getenv("BUCKET_NAME")
    if not name:
        raise ValueError("BUCKET_NAME must be set in .env")
    return name


def extract_text_from_s3(bucket: str, key: str) -> str:
    """
    Get object from S3 and return text.
    Handles PDF (extract text via pypdf) or plain text (UTF-8).
    """
    s3 = boto3.client("s3")
    response = s3.get_object(Bucket=bucket, Key=key)
    raw_bytes = response["Body"].read()
    if key.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(raw_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return raw_bytes.decode("utf-8")
