from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, Enum, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .database import Base


class DocumentType(str, enum.Enum):
    INVOICE = "invoice"
    RECEIPT = "receipt"
    BANK_STATEMENT = "bank_statement"
    PURCHASE_ORDER = "purchase_order"
    SALES_ORDER = "sales_order"
    DELIVERY_NOTE = "delivery_note"
    QUOTE = "quote"
    CONTRACT = "contract"
    TAX_DOCUMENT = "tax_document"
    OTHER = "other"


class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    gmail_id = Column(String, unique=True, index=True)
    subject = Column(String)
    sender = Column(String, index=True)
    receiver = Column(String)
    timestamp = Column(DateTime, index=True)
    body_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    documents = relationship("Document", secondary="email_document_links", back_populates="emails")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)  # Multi-user support
    filename = Column(String)
    file_path = Column(String)
    file_size = Column(Integer)
    mime_type = Column(String)

    # Processing
    processing_status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING, index=True)
    document_type = Column(Enum(DocumentType), nullable=True, index=True)

    # Extracted data
    extracted_text = Column(Text)
    extracted_data = Column(JSON)  # Store the full JSON extraction

    # User feedback
    needs_review = Column(Boolean, default=False)  # Flag for user review
    user_verified = Column(Boolean, default=False)  # User has verified extraction
    user_corrections = Column(JSON, nullable=True)  # User corrections to extraction

    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    # Relationships
    emails = relationship("Email", secondary="email_document_links", back_populates="documents")
    transactions = relationship("Transaction", back_populates="document")
    user = relationship("User", back_populates="documents")


class Party(Base):
    __tablename__ = "parties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    normalized_name = Column(String, index=True)  # For entity resolution
    party_type = Column(String)  # company, person, vendor, etc.

    # Additional info
    email = Column(String, nullable=True)
    metadata = Column(JSON)  # Store additional party information

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    transactions = relationship("Transaction", back_populates="party")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    party_id = Column(Integer, ForeignKey("parties.id"), nullable=True)

    # Transaction details
    amount = Column(Float, index=True)
    currency = Column(String, default="USD")
    transaction_date = Column(DateTime, index=True)
    transaction_type = Column(String)  # invoice, receipt, payment, etc.

    # Additional details
    description = Column(Text, nullable=True)
    metadata = Column(JSON)  # Store additional transaction information

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="transactions")
    party = relationship("Party", back_populates="transactions")


class EmailDocumentLink(Base):
    __tablename__ = "email_document_links"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"))
    document_id = Column(Integer, ForeignKey("documents.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Google OAuth (optional)
    google_id = Column(String, unique=True, index=True, nullable=True)

    # OAuth tokens
    gmail_access_token = Column(Text, nullable=True)
    gmail_refresh_token = Column(Text, nullable=True)
    gmail_token_expiry = Column(DateTime, nullable=True)
    gmail_connected = Column(Boolean, default=False)

    # User preferences
    preferences = Column(JSON, default={})

    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    last_sync = Column(DateTime, nullable=True)

    # Relationships
    documents = relationship("Document", back_populates="user")


class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    document_id = Column(Integer, ForeignKey("documents.id"))
    extraction_log_id = Column(Integer, ForeignKey("extraction_logs.id"), nullable=True)

    # Feedback type
    feedback_type = Column(String)  # "correction", "verification", "flag_error"

    # Original vs corrected data
    original_data = Column(JSON)
    corrected_data = Column(JSON)

    # Feedback details
    field_name = Column(String, nullable=True)  # Which field was corrected
    comments = Column(Text, nullable=True)
    confidence_before = Column(Float, nullable=True)
    confidence_after = Column(Float, default=1.0)  # User correction assumed 100% confident

    # Status
    status = Column(String, default="pending")  # pending, applied, dismissed
    applied_to_template = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    applied_at = Column(DateTime, nullable=True)


class DocumentTemplate(Base):
    __tablename__ = "document_templates"

    id = Column(Integer, primary_key=True, index=True)

    # Template identification
    name = Column(String, index=True)  # e.g., "Standard Invoice Template"
    document_type = Column(Enum(DocumentType), index=True)

    # Template definition
    template_schema = Column(JSON)  # Field definitions and extraction rules
    """
    Example schema:
    {
        "fields": [
            {
                "name": "invoice_number",
                "type": "string",
                "required": true,
                "patterns": ["Invoice #", "Invoice No:", "INV-"],
                "location": "top_right"  # Optional: where typically found
            },
            {
                "name": "total_amount",
                "type": "float",
                "required": true,
                "patterns": ["Total:", "Amount Due:", "Grand Total:"],
                "location": "bottom_right"
            },
            {
                "name": "date",
                "type": "date",
                "required": true,
                "patterns": ["Date:", "Invoice Date:", "Issued:"],
                "location": "top_right"
            },
            {
                "name": "vendor",
                "type": "string",
                "required": true,
                "patterns": ["From:", "Vendor:", "Supplier:"],
                "location": "top_left"
            }
        ],
        "layout_hints": {
            "header_section": [0, 0.25],  # Top 25% of document
            "footer_section": [0.75, 1.0],  # Bottom 25%
            "left_section": [0, 0.5],
            "right_section": [0.5, 1.0]
        }
    }
    """

    # Template statistics and confidence
    usage_count = Column(Integer, default=0)  # How many times used
    success_count = Column(Integer, default=0)  # Successful extractions
    confidence_score = Column(Float, default=0.0)  # success_count / usage_count

    # Template characteristics for matching
    keywords = Column(JSON)  # Common keywords found in this document type
    vendor_pattern = Column(String, nullable=True)  # Regex pattern for vendor identification
    layout_signature = Column(String, nullable=True)  # Hash of document layout characteristics

    # Learning data
    sample_documents = Column(JSON)  # Store references to sample documents
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_from_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)


class ExtractionLog(Base):
    __tablename__ = "extraction_logs"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    template_id = Column(Integer, ForeignKey("document_templates.id"), nullable=True)

    # Extraction details
    extraction_method = Column(String)  # "template", "llm", "hybrid"
    fields_extracted = Column(JSON)  # What was extracted
    confidence_scores = Column(JSON)  # Confidence per field

    # Quality metrics
    extraction_time = Column(Float)  # Time taken in seconds
    success = Column(Boolean)
    error_message = Column(Text, nullable=True)

    # Validation
    manually_verified = Column(Boolean, default=False)
    corrections = Column(JSON, nullable=True)  # User corrections

    created_at = Column(DateTime, default=datetime.utcnow)
