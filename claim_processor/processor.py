"""Process claim documents (extract + summary) and compare Bedrock models."""

import json
import time

from .bedrock import get_bedrock_runtime, invoke_claude3_messages
from .document import extract_text_from_s3, get_bucket_name
from .prompts import PromptTemplateManager


def process_document(
    model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0",
    key: str = "claim-documents/2026-02-06/Claim - CL-2024-001.pdf",
    prompt_manager: PromptTemplateManager | None = None,
) -> dict:
    """
    Load claim from S3, extract info with Bedrock, then generate summary.
    Returns {"extracted_info": ..., "summary": ...}.
    """
    prompt_manager = prompt_manager or PromptTemplateManager()
    bucket = get_bucket_name()
    client = get_bedrock_runtime()

    document_text = extract_text_from_s3(bucket, key)

    prompt = prompt_manager.get_prompt("extract_info", document_text=document_text)
    extracted_info = invoke_claude3_messages(
        model_id, prompt, max_tokens=1000, temperature=0.0, client=client
    )

    summary_prompt = prompt_manager.get_prompt(
        "generate_summary", extracted_info=extracted_info
    )
    summary = invoke_claude3_messages(
        model_id, summary_prompt, max_tokens=500, temperature=0.7, client=client
    )

    return {"extracted_info": extracted_info, "summary": summary}


def compare_models(
    document_text: str,
    models: list[str] | None = None,
    prompt_manager: PromptTemplateManager | None = None,
) -> dict:
    """
    Run the same extract prompt on multiple Claude 3 models.
    Returns { model_id: { "time_seconds", "output_length", "output_sample" } }.
    """
    if models is None:
        models = [
            "anthropic.claude-3-sonnet-20240229-v1:0",
            "anthropic.claude-3-haiku-20240307-v1:0",
        ]
    prompt_manager = prompt_manager or PromptTemplateManager()
    prompt = prompt_manager.get_prompt("extract_info", document_text=document_text)
    client = get_bedrock_runtime()

    results = {}
    for model_id in models:
        start_time = time.perf_counter()
        try:
            output = invoke_claude3_messages(
                model_id, prompt, max_tokens=1000, temperature=0.0, client=client
            )
            elapsed = time.perf_counter() - start_time
            results[model_id] = {
                "time_seconds": round(elapsed, 2),
                "output_length": len(output),
                "output_sample": (output[:200] + "...") if len(output) > 200 else output,
            }
        except Exception as e:
            results[model_id] = {
                "time_seconds": None,
                "output_length": None,
                "output_sample": None,
                "error": str(e),
            }
    return results
