from typing import Dict, Optional, Literal
import json
from app.core.config import settings


class LLMService:
    """Service for LLM-based document classification and extraction."""

    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        if self.provider == "openai":
            import openai
            self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = "gpt-4-turbo-preview"
        elif self.provider == "anthropic":
            import anthropic
            self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            self.model = "claude-3-sonnet-20240229"
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def classify_document(
        self,
        text: str,
        email_subject: Optional[str] = None,
        email_body: Optional[str] = None
    ) -> str:
        """
        Classify document type using LLM with email context.

        Classification strategy:
        1. Check email subject for keywords (invoice, receipt, statement, etc.)
        2. Check email body for additional context
        3. Use OCR-extracted text from attachment
        4. Make final classification decision

        Args:
            text: Extracted document text from OCR
            email_subject: Email subject line for context
            email_body: Email body text for context

        Returns:
            Document type
        """
        # Build context from email metadata
        context_parts = []

        if email_subject:
            context_parts.append(f"Email Subject: {email_subject}")

        if email_body:
            # Limit email body to first 500 chars to save tokens
            body_preview = email_body[:500]
            context_parts.append(f"Email Body: {body_preview}")

        email_context = "\n\n".join(context_parts) if context_parts else "No email context available."

        prompt = f"""Classify the following document into one of these categories:
- invoice
- receipt
- bank_statement
- purchase_order
- sales_order
- delivery_note
- quote
- contract
- tax_document
- other

IMPORTANT: Use this classification strategy in order:
1. First, check the email subject for clear indicators (e.g., "Invoice", "Receipt", "Statement")
2. Then, check the email body for additional context about the document
3. Finally, use the document text extracted from the attachment via OCR
4. Make your classification based on ALL available information

Email Context:
{email_context}

Document Text (from OCR):
{text[:2000]}

Respond with ONLY the category name, nothing else."""

        response = self._call_llm(prompt)

        # Normalize response
        doc_type = response.strip().lower()
        valid_types = ["invoice", "receipt", "bank_statement", "purchase_order",
                       "sales_order", "delivery_note", "quote", "contract",
                       "tax_document", "other"]

        if doc_type not in valid_types:
            doc_type = "other"

        return doc_type

    def extract_structured_data(
        self,
        text: str,
        doc_type: str,
        email_subject: Optional[str] = None,
        email_body: Optional[str] = None
    ) -> Dict:
        """
        Extract structured data from document using LLM with email context.

        Args:
            text: Extracted document text
            doc_type: Document type (invoice, receipt, etc.)
            email_subject: Email subject line for context
            email_body: Email body text for context

        Returns:
            Dictionary with extracted fields
        """
        # Build context from email metadata
        context_parts = []

        if email_subject:
            context_parts.append(f"Email Subject: {email_subject}")

        if email_body:
            # Limit email body to first 500 chars to save tokens
            body_preview = email_body[:500]
            context_parts.append(f"Email Body: {body_preview}")

        email_context = "\n\n".join(context_parts) if context_parts else "No email context available."

        prompt = f"""Extract structured information from this {doc_type}.

Email Context (use this to fill in missing fields if document text is unclear):
{email_context}

Document Text (from OCR):
{text[:3000]}

Extract the following fields and return as JSON:
{{
    "amount": <float or null>,
    "currency": <string or "USD">,
    "date": <ISO date string or null>,
    "merchant": <string or null>,
    "vendor": <string or null>,
    "type": "{doc_type}",
    "invoice_number": <string or null>,
    "items": [list of items if applicable, or empty list]
}}

Rules:
- Extract amount as a number (e.g., 123.45)
- Date should be in ISO format (YYYY-MM-DD)
- merchant/vendor is the company or person providing goods/services
- Use email context to supplement or clarify information from document text
- Return valid JSON only, no other text

JSON:"""

        response = self._call_llm(prompt)

        try:
            # Parse JSON response
            data = json.loads(response)
            return data
        except json.JSONDecodeError:
            # Try to extract JSON from response if wrapped in markdown or text
            try:
                # Look for JSON between curly braces
                start = response.find('{')
                end = response.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = response[start:end]
                    data = json.loads(json_str)
                    return data
            except:
                pass

            # Return empty structure if parsing fails
            return {
                "amount": None,
                "currency": "USD",
                "date": None,
                "merchant": None,
                "vendor": None,
                "type": doc_type,
                "invoice_number": None,
                "items": []
            }

    def _call_llm(self, prompt: str) -> str:
        """Call the configured LLM provider."""
        if self.provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts structured data from documents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=1000
            )
            return response.choices[0].message.content

        elif self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text

        return ""

    def normalize_party_name(self, name: str) -> str:
        """
        Normalize party name for entity resolution.
        Simple approach: lowercase and remove punctuation.
        """
        if not name:
            return ""

        # Convert to lowercase
        normalized = name.lower()

        # Remove common punctuation
        import re
        normalized = re.sub(r'[^\w\s]', '', normalized)

        # Remove extra whitespace
        normalized = ' '.join(normalized.split())

        return normalized
