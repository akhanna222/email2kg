from sqlalchemy.orm import Session
from app.db.models import Document, Transaction, Party, ProcessingStatus, DocumentType
from app.services.pdf_service import PDFService
from app.services.llm_service import LLMService
from app.services.template_service import TemplateService
from app.services.vision_ocr_service import VisionOCRService
from app.core.config import settings
from datetime import datetime
from typing import Optional
import time
import os


class ProcessingService:
    """Service for processing documents and creating knowledge graph entities."""

    def __init__(self, db: Session):
        self.db = db
        self.pdf_service = PDFService()
        self.llm_service = LLMService()
        self.template_service = TemplateService(db)
        self.vision_ocr = VisionOCRService(api_key=settings.OPENAI_API_KEY)

    def process_document(
        self,
        document_id: int,
        email_subject: Optional[str] = None,
        email_body: Optional[str] = None
    ) -> bool:
        """
        Process a document: extract text, classify, extract structured data,
        create entities and relationships.

        Args:
            document_id: ID of document to process
            email_subject: Optional email subject for context-aware classification
            email_body: Optional email body for context-aware classification

        Returns:
            True if successful, False otherwise
        """
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return False

        try:
            # Update status to processing
            document.processing_status = ProcessingStatus.PROCESSING
            self.db.commit()

            # Step 1: Extract text based on file type
            file_ext = os.path.splitext(document.file_path.lower())[1]

            if file_ext == '.pdf':
                # PDF extraction
                extracted_text = self.pdf_service.extract_text(document.file_path)
            elif file_ext in {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.webp', '.bmp'}:
                # Image extraction using Vision OCR
                ocr_result = self.vision_ocr.extract_text_from_image_file(
                    document.file_path,
                    extract_structure=False,
                    detail_level="high"
                )
                extracted_text = ocr_result.get('text', '')
            else:
                # Unsupported file type
                document.processing_status = ProcessingStatus.FAILED
                self.db.commit()
                return False

            document.extracted_text = extracted_text

            if not extracted_text or len(extracted_text.strip()) < 20:
                # Not enough text to process
                document.processing_status = ProcessingStatus.FAILED
                self.db.commit()
                return False

            # Step 2: Classify document using email context + OCR text
            start_time = time.time()
            doc_type = self.llm_service.classify_document(
                extracted_text,
                email_subject=email_subject,
                email_body=email_body
            )
            document.document_type = DocumentType(doc_type)

            # Skip "other" documents in MVP1
            if doc_type == "other":
                document.processing_status = ProcessingStatus.COMPLETED
                document.processed_at = datetime.utcnow()
                self.db.commit()
                return True

            # Step 3: Try template-based extraction first
            template = self.template_service.find_matching_template(
                extracted_text,
                DocumentType(doc_type)
            )

            structured_data = None
            extraction_method = "llm"  # Default to LLM
            template_id = None

            if template:
                # Try template-based extraction
                print(f"Found matching template: {template.name}")
                template_result = self.template_service.extract_with_template(
                    extracted_text,
                    template
                )

                if template_result.get('data'):
                    structured_data = template_result['data']
                    extraction_method = "template"
                    template_id = template.id

                    # Update template stats
                    self.template_service.update_template_stats(template.id, success=True)

            # Fall back to LLM if template extraction failed or no template found
            if not structured_data:
                print("Using LLM extraction (no template or template failed)")
                structured_data = self.llm_service.extract_structured_data(
                    extracted_text,
                    doc_type,
                    email_subject=email_subject,
                    email_body=email_body
                )

                # If LLM extraction was successful, create a new template
                if structured_data.get('amount'):
                    print("Creating new template from LLM extraction")
                    self.template_service.create_template_from_extraction(
                        document.id,
                        DocumentType(doc_type),
                        structured_data,
                        extracted_text
                    )

            # Log the extraction
            extraction_time = time.time() - start_time
            self.template_service.log_extraction(
                document_id=document.id,
                template_id=template_id,
                extraction_method=extraction_method,
                fields_extracted=structured_data or {},
                confidence_scores={},
                success=bool(structured_data),
                extraction_time=extraction_time
            )

            document.extracted_data = structured_data

            # Step 4: Create or find party (vendor/merchant)
            party = None
            party_name = structured_data.get('merchant') or structured_data.get('vendor')

            if party_name:
                party = self._find_or_create_party(party_name)

            # Step 5: Create transaction
            if structured_data.get('amount'):
                transaction = Transaction(
                    document_id=document.id,
                    party_id=party.id if party else None,
                    amount=float(structured_data['amount']),
                    currency=structured_data.get('currency', 'USD'),
                    transaction_date=self._parse_date(structured_data.get('date')),
                    transaction_type=doc_type,
                    description=f"{doc_type.title()} from {party_name}" if party_name else doc_type.title(),
                    transaction_metadata=structured_data
                )
                self.db.add(transaction)

            # Step 6: Mark as completed
            document.processing_status = ProcessingStatus.COMPLETED
            document.processed_at = datetime.utcnow()

            self.db.commit()
            return True

        except Exception as e:
            print(f"Error processing document {document_id}: {e}")
            document.processing_status = ProcessingStatus.FAILED
            self.db.commit()
            return False

    def _find_or_create_party(self, name: str) -> Party:
        """Find existing party or create new one with entity resolution."""
        normalized_name = self.llm_service.normalize_party_name(name)

        # Try to find existing party by normalized name
        party = self.db.query(Party).filter(
            Party.normalized_name == normalized_name
        ).first()

        if party:
            return party

        # Create new party
        party = Party(
            name=name,
            normalized_name=normalized_name,
            party_type="vendor"
        )
        self.db.add(party)
        self.db.flush()  # Get ID without committing

        return party

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime."""
        if not date_str:
            return None

        try:
            # Try ISO format first
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            pass

        # Try other common formats
        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%B %d, %Y',
            '%b %d, %Y'
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue

        return None
