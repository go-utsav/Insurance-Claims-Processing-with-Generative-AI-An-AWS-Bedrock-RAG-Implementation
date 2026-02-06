"""Call Amazon Bedrock (Claude 3) using the Messages API."""

import json

import boto3


def get_bedrock_runtime():
    """Bedrock runtime client (uses default region / env)."""
    return boto3.client("bedrock-runtime")


def invoke_claude3_messages(
    model_id: str,
    user_content: str,
    max_tokens: int = 1000,
    temperature: float = 0.0,
    client=None,
) -> str:
    """
    Call Claude 3 on Bedrock using the Messages API.
    Returns the assistant text reply.
    """
    if client is None:
        client = get_bedrock_runtime()
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": user_content}],
        "temperature": temperature,
    }
    response = client.invoke_model(modelId=model_id, body=json.dumps(body))
    response_body = json.loads(response["body"].read())
    for block in response_body.get("content", []):
        if block.get("type") == "text":
            return block["text"]
    raise ValueError("No text in Bedrock response")
