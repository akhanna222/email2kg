from sqlalchemy.orm import Session
from app.db.models import DocumentTemplate, Document, DocumentType, ExtractionLog
from typing import Dict, List, Optional, Any
from datetime import datetime
import re
import hashlib
import json


class TemplateService:
    """Service for managing document templates and template-based extraction."""

    def __init__(self, db: Session):
        self.db = db

    def find_matching_template(
        self,
        document_text: str,
        document_type: DocumentType
    ) -> Optional[DocumentTemplate]:
        """
        Find the best matching template for a document.

        Args:
            document_text: Extracted text from document
            document_type: Classified document type

        Returns:
            Best matching template or None
        """
        # Get all active templates for this document type
        templates = self.db.query(DocumentTemplate).filter(
            DocumentTemplate.document_type == document_type,
            DocumentTemplate.is_active == True
        ).order_by(DocumentTemplate.confidence_score.desc()).all()

        if not templates:
            return None

        # Calculate match scores for each template
        best_template = None
        best_score = 0.0

        for template in templates:
            score = self._calculate_template_match_score(document_text, template)
            if score > best_score:
                best_score = score
                best_template = template

        # Only return template if match score is above threshold
        if best_score > 0.6:  # 60% confidence threshold
            return best_template

        return None

    def _calculate_template_match_score(
        self,
        document_text: str,
        template: DocumentTemplate
    ) -> float:
        """
        Calculate how well a document matches a template.

        Returns:
            Match score between 0.0 and 1.0
        """
        scores = []

        # Check keyword matching
        if template.keywords:
            keyword_score = self._match_keywords(document_text, template.keywords)
            scores.append(keyword_score * 0.4)  # 40% weight

        # Check vendor pattern if exists
        if template.vendor_pattern:
            vendor_score = 1.0 if re.search(template.vendor_pattern, document_text, re.IGNORECASE) else 0.0
            scores.append(vendor_score * 0.3)  # 30% weight

        # Check layout signature similarity
        if template.layout_signature:
            layout_score = self._match_layout(document_text, template.layout_signature)
            scores.append(layout_score * 0.3)  # 30% weight

        return sum(scores) / len(scores) if scores else 0.0

    def _match_keywords(self, text: str, keywords: List[str]) -> float:
        """Calculate keyword match score."""
        text_lower = text.lower()
        matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
        return matches / len(keywords) if keywords else 0.0

    def _match_layout(self, text: str, layout_signature: str) -> float:
        """Calculate layout similarity score."""
        # Simple implementation: compare text structure hash
        current_signature = self._generate_layout_signature(text)
        return 1.0 if current_signature == layout_signature else 0.5

    def _generate_layout_signature(self, text: str) -> str:
        """Generate a signature representing document layout."""
        # Simple hash based on line structure and formatting patterns
        lines = text.split('\n')
        structure = {
            'total_lines': len(lines),
            'avg_line_length': sum(len(line) for line in lines) / len(lines) if lines else 0,
            'has_tables': bool(re.search(r'\|.*\|', text)),
            'has_amounts': bool(re.search(r'\$[\d,]+\.?\d*', text)),
            'has_dates': bool(re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', text))
        }
        return hashlib.md5(json.dumps(structure, sort_keys=True).encode()).hexdigest()

    def extract_with_template(
        self,
        document_text: str,
        template: DocumentTemplate
    ) -> Dict[str, Any]:
        """
        Extract structured data using a template.

        Args:
            document_text: Extracted text from document
            template: Template to use for extraction

        Returns:
            Extracted data dictionary
        """
        extracted_data = {}
        confidence_scores = {}

        if not template.template_schema or 'fields' not in template.template_schema:
            return extracted_data

        fields = template.template_schema['fields']

        for field in fields:
            field_name = field['name']
            patterns = field.get('patterns', [])
            field_type = field.get('type', 'string')

            # Try to extract field using patterns
            value, confidence = self._extract_field(
                document_text,
                patterns,
                field_type
            )

            if value is not None:
                extracted_data[field_name] = value
                confidence_scores[field_name] = confidence

        return {
            'data': extracted_data,
            'confidence_scores': confidence_scores,
            'template_id': template.id
        }

    def _extract_field(
        self,
        text: str,
        patterns: List[str],
        field_type: str
    ) -> tuple[Any, float]:
        """
        Extract a specific field from text using patterns.

        Returns:
            (value, confidence) tuple
        """
        for pattern in patterns:
            # Build regex to find value after pattern
            if field_type == 'float':
                regex = rf'{re.escape(pattern)}\s*[:]*\s*\$?\s*([\d,]+\.?\d*)'
            elif field_type == 'date':
                regex = rf'{re.escape(pattern)}\s*[:]*\s*(\d{{1,2}}[/-]\d{{1,2}}[/-]\d{{2,4}})'
            else:  # string
                regex = rf'{re.escape(pattern)}\s*[:]*\s*([^\n]+)'

            match = re.search(regex, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()

                # Convert based on type
                if field_type == 'float':
                    try:
                        value = float(value.replace(',', ''))
                        return value, 0.9  # High confidence for pattern match
                    except:
                        continue
                elif field_type == 'date':
                    return value, 0.9
                else:
                    return value, 0.8

        return None, 0.0

    def create_template_from_extraction(
        self,
        document_id: int,
        document_type: DocumentType,
        extracted_data: Dict[str, Any],
        document_text: str
    ) -> DocumentTemplate:
        """
        Create a new template based on successful extraction.

        Args:
            document_id: Source document ID
            document_type: Document type
            extracted_data: Successfully extracted data
            document_text: Original document text

        Returns:
            Created template
        """
        # Generate template name
        template_name = f"{document_type.value.title()} Template #{self._get_template_count(document_type) + 1}"

        # Extract keywords from document
        keywords = self._extract_keywords(document_text, document_type)

        # Generate template schema
        template_schema = self._generate_template_schema(extracted_data, document_text)

        # Create template
        template = DocumentTemplate(
            name=template_name,
            document_type=document_type,
            template_schema=template_schema,
            keywords=keywords,
            layout_signature=self._generate_layout_signature(document_text),
            sample_documents=[document_id],
            usage_count=1,
            success_count=1,
            confidence_score=1.0,
            created_from_document_id=document_id
        )

        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)

        return template

    def _get_template_count(self, document_type: DocumentType) -> int:
        """Get count of existing templates for a document type."""
        return self.db.query(DocumentTemplate).filter(
            DocumentTemplate.document_type == document_type
        ).count()

    def _extract_keywords(self, text: str, document_type: DocumentType) -> List[str]:
        """Extract relevant keywords from document text."""
        # Common keywords by document type
        type_keywords = {
            DocumentType.INVOICE: ['invoice', 'bill', 'due', 'payment', 'subtotal'],
            DocumentType.RECEIPT: ['receipt', 'paid', 'purchased', 'transaction'],
            DocumentType.PURCHASE_ORDER: ['purchase order', 'PO', 'quantity', 'unit price'],
            DocumentType.SALES_ORDER: ['sales order', 'SO', 'order date', 'ship to'],
            DocumentType.QUOTE: ['quote', 'quotation', 'estimate', 'valid until'],
        }

        keywords = []
        text_lower = text.lower()

        # Add type-specific keywords that appear in document
        if document_type in type_keywords:
            for keyword in type_keywords[document_type]:
                if keyword in text_lower:
                    keywords.append(keyword)

        # Extract company/vendor names (simple heuristic)
        # Look for capitalized words at the beginning
        lines = text.split('\n')[:10]  # First 10 lines
        for line in lines:
            words = line.split()
            if words and words[0][0].isupper():
                keywords.append(line.strip()[:50])  # Limit length

        return list(set(keywords))[:10]  # Return up to 10 unique keywords

    def _generate_template_schema(
        self,
        extracted_data: Dict[str, Any],
        document_text: str
    ) -> Dict[str, Any]:
        """Generate template schema from extracted data."""
        fields = []

        for field_name, value in extracted_data.items():
            # Determine field type
            if isinstance(value, (int, float)):
                field_type = 'float'
            elif field_name in ['date', 'transaction_date', 'invoice_date']:
                field_type = 'date'
            else:
                field_type = 'string'

            # Find patterns in text that precede this value
            patterns = self._find_value_patterns(document_text, str(value))

            fields.append({
                'name': field_name,
                'type': field_type,
                'required': field_name in ['amount', 'date', 'vendor'],
                'patterns': patterns[:3]  # Keep top 3 patterns
            })

        return {
            'fields': fields,
            'layout_hints': {
                'header_section': [0, 0.25],
                'footer_section': [0.75, 1.0]
            }
        }

    def _find_value_patterns(self, text: str, value: str) -> List[str]:
        """Find patterns that precede a value in text."""
        patterns = []

        # Look for label before value
        regex = r'([A-Za-z\s#]+)[:]*\s*' + re.escape(value)
        matches = re.finditer(regex, text, re.IGNORECASE)

        for match in matches:
            label = match.group(1).strip()
            if len(label) > 2 and len(label) < 30:
                patterns.append(label)

        return list(set(patterns))

    def update_template_stats(
        self,
        template_id: int,
        success: bool
    ):
        """Update template usage statistics."""
        template = self.db.query(DocumentTemplate).filter(
            DocumentTemplate.id == template_id
        ).first()

        if template:
            template.usage_count += 1
            if success:
                template.success_count += 1

            # Recalculate confidence score
            template.confidence_score = template.success_count / template.usage_count if template.usage_count > 0 else 0.0
            template.last_updated = datetime.utcnow()

            self.db.commit()

    def log_extraction(
        self,
        document_id: int,
        template_id: Optional[int],
        extraction_method: str,
        fields_extracted: Dict[str, Any],
        confidence_scores: Dict[str, float],
        success: bool,
        extraction_time: float,
        error_message: Optional[str] = None
    ) -> ExtractionLog:
        """Log extraction attempt for learning and improvement."""
        log = ExtractionLog(
            document_id=document_id,
            template_id=template_id,
            extraction_method=extraction_method,
            fields_extracted=fields_extracted,
            confidence_scores=confidence_scores,
            extraction_time=extraction_time,
            success=success,
            error_message=error_message
        )

        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)

        return log

    def get_all_templates(self, document_type: Optional[DocumentType] = None) -> List[DocumentTemplate]:
        """Get all templates, optionally filtered by document type."""
        query = self.db.query(DocumentTemplate)

        if document_type:
            query = query.filter(DocumentTemplate.document_type == document_type)

        return query.order_by(DocumentTemplate.confidence_score.desc()).all()

    def get_template(self, template_id: int) -> Optional[DocumentTemplate]:
        """Get a specific template by ID."""
        return self.db.query(DocumentTemplate).filter(
            DocumentTemplate.id == template_id
        ).first()

    def delete_template(self, template_id: int) -> bool:
        """Delete a template."""
        template = self.get_template(template_id)
        if template:
            self.db.delete(template)
            self.db.commit()
            return True
        return False
