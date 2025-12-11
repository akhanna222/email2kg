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

IMPORTANT Classification Rules:
1. ALWAYS check email subject first for keywords (e.g., "Invoice", "Receipt", "Statement")
2. Then check email body for additional context
3. Analyze the document text from OCR extraction
4. If document contains:
   - Itemized lists/tables with prices → likely invoice, receipt, or quote
   - Payment amounts and vendor info → invoice or receipt
   - Bank transactions or account info → bank_statement
   - Order numbers and product lists → purchase_order or sales_order
5. ONLY use "other" if document truly doesn't fit any financial/business category
6. When in doubt between similar categories, prefer the more specific one

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

    def qualify_email(
        self,
        email_subject: Optional[str] = None,
        email_body: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Qualify an email to determine if it should be processed for extraction.
        Uses LLM to intelligently detect financial/business documents.

        Two-stage process:
        1. Check subject first (fast, low-cost)
        2. If subject fails, check body (more thorough)
        3. If both fail, bypass the email

        Args:
            email_subject: Email subject line
            email_body: Email body text

        Returns:
            Dict with:
            - qualified: bool - Whether email should be processed
            - stage: str - Which stage qualified it ("subject", "body", or "none")
            - confidence: float - Confidence score (0-1)
            - reason: str - Explanation for the decision
        """
        # Stage 1: Check subject line
        if email_subject:
            subject_result = self._qualify_text(
                text=email_subject,
                stage="subject"
            )

            if subject_result["qualified"]:
                return {
                    "qualified": True,
                    "stage": "subject",
                    "confidence": subject_result["confidence"],
                    "reason": subject_result["reason"]
                }

        # Stage 2: Check body if subject didn't qualify
        if email_body:
            # Limit body to first 1000 chars to save tokens
            body_preview = email_body[:1000]

            body_result = self._qualify_text(
                text=body_preview,
                stage="body"
            )

            if body_result["qualified"]:
                return {
                    "qualified": True,
                    "stage": "body",
                    "confidence": body_result["confidence"],
                    "reason": body_result["reason"]
                }

        # Both stages failed - bypass email
        return {
            "qualified": False,
            "stage": "none",
            "confidence": 0.0,
            "reason": "No financial or business document indicators found in subject or body"
        }

    def _qualify_text(self, text: str, stage: str) -> Dict[str, any]:
        """
        Use LLM to qualify a piece of text (subject or body).

        Args:
            text: Text to qualify
            stage: "subject" or "body"

        Returns:
            Dict with qualified, confidence, and reason
        """
        prompt = f"""Analyze this email {stage} and determine if it contains a financial or business document that should be processed.

Email {stage.title()}:
{text}

Documents to INCLUDE (qualify as YES):
- Invoices, receipts, bills, payment confirmations
- Bank statements, transaction records, account summaries
- Purchase orders, sales orders, quotes, delivery notes
- Contracts, agreements, tax documents
- Expense reports, reimbursements
- Shipping notifications with itemized costs
- Subscription renewals with pricing
- Any email mentioning monetary transactions, amounts, or financial documents

Documents to EXCLUDE (qualify as NO):
- Marketing emails, newsletters, promotions
- Social media notifications
- Personal correspondence without financial content
- Spam, unsubscribe confirmations
- Event invitations (unless they're paid events with invoices)
- General updates or announcements without financial data

Respond in this EXACT JSON format:
{{
    "qualified": true or false,
    "confidence": 0.0 to 1.0,
    "reason": "Brief explanation (one sentence)"
}}

JSON:"""

        response = self._call_llm(prompt)

        try:
            # Parse JSON response
            result = json.loads(response)
            return {
                "qualified": result.get("qualified", False),
                "confidence": result.get("confidence", 0.0),
                "reason": result.get("reason", "No reason provided")
            }
        except json.JSONDecodeError:
            # Try to extract JSON from response
            try:
                start = response.find('{')
                end = response.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = response[start:end]
                    result = json.loads(json_str)
                    return {
                        "qualified": result.get("qualified", False),
                        "confidence": result.get("confidence", 0.0),
                        "reason": result.get("reason", "No reason provided")
                    }
            except:
                pass

            # Default to not qualified if parsing fails
            return {
                "qualified": False,
                "confidence": 0.0,
                "reason": "Failed to parse LLM response"
            }
