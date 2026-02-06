"""Prompt templates for claim extraction and summary."""


class PromptTemplateManager:
    """Stores and fills prompt templates (e.g. extract_info, generate_summary)."""

    def __init__(self):
        self.templates = {
            "extract_info": """
                Extract the following information from this insurance claim document:
                - Claimant Name
                - Policy Number
                - Incident Date
                - Claim Amount
                - Incident Description

                Document:
                {document_text}

                Return the information in JSON format.
                """,
             "generate_summary": """
                Based on this extracted information:
                {extracted_info}

                Generate a concise summary of the claim.
                """,
        }

    def get_prompt(self, template_name: str, **kwargs) -> str:
        template = self.templates.get(template_name)
        if not template:
            raise ValueError(f"Template {template_name} not found")
        return template.format(**kwargs)
