"""
Claim processor: extract info and summarize insurance claims using Amazon Bedrock.
"""

from .processor import compare_models, process_document
from .prompts import PromptTemplateManager

__all__ = [
    "process_document",
    "compare_models",
    "PromptTemplateManager",
]
