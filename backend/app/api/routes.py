from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os
import shutil

from app.db.database import get_db
from app.db.models import Document, Transaction, Email, User, ProcessingStatus, EmailDocumentLink
from app.services.gmail_service import GmailService
from app.services.processing_service import ProcessingService
from app.services.query_service import QueryService
from app.services.graph_service import GraphService
from app.services.template_service import TemplateService
from app.services.llm_service import LLMService
from app.core.config import settings
from app.core.auth import get_current_active_user
from pydantic import BaseModel

# Import workers for background processing
from app.workers.attachment_processor import (
    process_email_attachment,
    process_all_email_attachments,
    bulk_process_email_attachments
)
from app.workers.document_processor import process_uploaded_document

router = APIRouter()


# Pydantic models for request/response
class OAuthResponse(BaseModel):
    auth_url: str


class OAuthCallbackRequest(BaseModel):
    code: str


class TokenResponse(BaseModel):
    message: str
    user_id: int


class UploadResponse(BaseModel):
    document_id: int
    filename: str
    status: str


class QueryRequest(BaseModel):
    query_type: str  # total_spend, top_vendors, invoices_above
    params: dict


# ========== Authentication Routes ==========

@router.get("/auth/google", response_model=OAuthResponse)
async def google_auth(current_user: User = Depends(get_current_active_user)):
    """Initiate Google OAuth flow with user context."""
    # Pass user ID in state parameter to identify user after OAuth redirect
    auth_url = GmailService.get_auth_url(user_id=current_user.id)
    return {"auth_url": auth_url}


@router.get("/auth/callback")
async def oauth_callback(
    code: str,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Handle OAuth callback from Google.

    Google redirects here after user authorizes with query parameters:
    - code: Authorization code to exchange for tokens
    - state: User ID passed during OAuth initiation
    - error: Error message if user denied access
    """
    from fastapi.responses import RedirectResponse

    # Check if user denied access
    if error:
        return RedirectResponse(
            url=f"https://agenticrag360.com/dashboard?gmail_error=access_denied",
            status_code=302
        )

    if not code:
        return RedirectResponse(
            url=f"https://agenticrag360.com/dashboard?gmail_error=no_code",
            status_code=302
        )

    if not state:
        return RedirectResponse(
            url=f"https://agenticrag360.com/dashboard?gmail_error=no_user_id",
            status_code=302
        )

    try:
        # Extract user ID from state
        user_id = int(state)

        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return RedirectResponse(
                url=f"https://agenticrag360.com/dashboard?gmail_error=user_not_found",
                status_code=302
            )

        # Exchange code for tokens
        tokens = GmailService.exchange_code_for_tokens(code)

        # Update user's Gmail tokens
        user.gmail_access_token = tokens["access_token"]
        user.gmail_refresh_token = tokens["refresh_token"]
        user.gmail_token_expiry = tokens["token_expiry"]
        user.gmail_connected = True

        db.commit()

        # Redirect back to frontend with success
        return RedirectResponse(
            url="https://agenticrag360.com/dashboard?gmail_connected=true",
            status_code=302
        )

    except ValueError:
        return RedirectResponse(
            url=f"https://agenticrag360.com/dashboard?gmail_error=invalid_state",
            status_code=302
        )
    except Exception as e:
        return RedirectResponse(
            url=f"https://agenticrag360.com/dashboard?gmail_error={str(e)}",
            status_code=302
        )


# ========== Email Sync Routes ==========

@router.post("/sync/gmail")
async def sync_gmail(
    process_attachments: bool = Query(True, description="Automatically process attachments"),
    months: int = Query(None, description="Number of months to fetch (default: 3, max: 12)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Sync emails from Gmail for the authenticated user.
    Uses LLM to qualify emails before processing.
    """
    if not current_user.gmail_access_token:
        raise HTTPException(status_code=401, detail="Gmail not connected")

    try:
        # Get email sync limit from user preferences (default: None = unlimited)
        email_limit = current_user.preferences.get('email_sync_limit') if current_user.preferences else None

        # Determine how many months to fetch
        fetch_months = months if months else settings.EMAIL_FETCH_MONTHS
        fetch_months = min(fetch_months, 12)  # Cap at 12 months

        # Fetch ALL emails (no filtering at Gmail level - we'll use LLM to qualify)
        emails = GmailService.fetch_emails(
            access_token=current_user.gmail_access_token,
            refresh_token=current_user.gmail_refresh_token,
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            months=fetch_months,  # Use user-selected months, not settings default
            max_emails=email_limit
        )

        llm_service = LLMService()
        new_count = 0
        qualified_count = 0
        new_email_ids = []

        for email_data in emails:
            # Check if email already exists
            existing = db.query(Email).filter(
                Email.gmail_id == email_data["gmail_id"]
            ).first()

            if not existing:
                # Qualify email using LLM
                qualification = llm_service.qualify_email(
                    email_subject=email_data["subject"],
                    email_body=email_data["body_text"]
                )

                email = Email(
                    gmail_id=email_data["gmail_id"],
                    subject=email_data["subject"],
                    sender=email_data["sender"],
                    receiver=email_data["receiver"],
                    timestamp=email_data["timestamp"],
                    body_text=email_data["body_text"],
                    # Store qualification results
                    is_qualified=qualification["qualified"],
                    qualification_stage=qualification["stage"],
                    qualification_confidence=qualification["confidence"],
                    qualification_reason=qualification["reason"],
                    qualified_at=datetime.utcnow()
                )
                db.add(email)
                db.flush()  # Get ID without full commit

                new_count += 1
                if qualification["qualified"]:
                    new_email_ids.append(email.id)
                    qualified_count += 1

        db.commit()
        current_user.last_sync = datetime.utcnow()
        db.commit()

        # Process attachments for qualified emails only
        attachments_queued = 0
        if process_attachments and new_email_ids:
            try:
                # Queue bulk attachment processing for qualified emails
                result = bulk_process_email_attachments.apply_async(
                    args=[new_email_ids, current_user.id],
                    queue="attachments"
                )
                attachments_queued = len(new_email_ids)
            except Exception as e:
                # Log but don't fail the sync if background processing fails
                print(f"Warning: Failed to queue attachment processing: {e}")

        return {
            "message": f"Synced {new_count} new emails ({qualified_count} qualified)",
            "total_fetched": len(emails),
            "new_emails": new_count,
            "qualified_emails": qualified_count,
            "attachments_processing": process_attachments,
            "emails_queued_for_attachment_processing": attachments_queued
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.post("/emails/{email_id}/process-attachments")
async def process_email_attachments_endpoint(
    email_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Manually trigger attachment processing for a specific email.
    Useful for reprocessing or processing emails synced without auto-processing.
    """
    # Verify email exists
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    try:
        # Queue attachment processing
        result = process_all_email_attachments.apply_async(
            args=[email_id, current_user.id],
            queue="attachments"
        )

        return {
            "message": "Attachment processing queued",
            "email_id": email_id,
            "task_id": result.id,
            "status": "queued"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue processing: {str(e)}")


@router.get("/emails")
async def get_emails(
    limit: int = Query(50, le=500),
    offset: int = Query(0),
    has_attachments: Optional[bool] = Query(None, description="Filter emails with/without attachments"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get emails for the authenticated user with optional filters."""
    query = db.query(Email)

    # Apply filters
    if has_attachments is not None:
        if has_attachments:
            # Emails that have linked documents
            query = query.join(EmailDocumentLink).distinct()
        # Note: filtering for emails WITHOUT attachments is harder, skip for now

    total = query.count()

    emails = query.order_by(Email.timestamp.desc()).offset(offset).limit(limit).all()

    results = []
    for email in emails:
        # Count linked documents
        doc_count = db.query(EmailDocumentLink).filter(
            EmailDocumentLink.email_id == email.id
        ).count()

        results.append({
            "id": email.id,
            "gmail_id": email.gmail_id,
            "subject": email.subject,
            "sender": email.sender,
            "receiver": email.receiver,
            "timestamp": email.timestamp.isoformat() if email.timestamp else None,
            "body_preview": email.body_text[:200] if email.body_text else "",
            "attached_documents": doc_count,
            "created_at": email.created_at.isoformat()
        })

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "emails": results
    }


@router.get("/emails/{email_id}")
async def get_email_detail(
    email_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed information about a specific email."""
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    # Get linked documents
    links = db.query(EmailDocumentLink).filter(
        EmailDocumentLink.email_id == email_id
    ).all()

    documents = []
    for link in links:
        doc = db.query(Document).filter(Document.id == link.document_id).first()
        if doc:
            documents.append({
                "id": doc.id,
                "filename": doc.filename,
                "processing_status": doc.processing_status.value,
                "document_type": doc.document_type.value if doc.document_type else None,
                "file_size": doc.file_size,
                "processed_at": doc.processed_at.isoformat() if doc.processed_at else None
            })

    return {
        "id": email.id,
        "gmail_id": email.gmail_id,
        "subject": email.subject,
        "sender": email.sender,
        "receiver": email.receiver,
        "timestamp": email.timestamp.isoformat() if email.timestamp else None,
        "body_text": email.body_text,
        "attached_documents": documents,
        "created_at": email.created_at.isoformat()
    }


@router.get("/emails/recent/activity")
async def get_recent_email_activity(
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get recent emails with qualification activity for sync feed display.
    Shows which emails were qualified/rejected and why.
    """
    emails = db.query(Email).order_by(Email.created_at.desc()).limit(limit).all()

    results = []
    for email in emails:
        # Count linked documents
        doc_count = db.query(EmailDocumentLink).filter(
            EmailDocumentLink.email_id == email.id
        ).count()

        results.append({
            "id": email.id,
            "subject": email.subject,
            "sender": email.sender,
            "timestamp": email.timestamp.isoformat() if email.timestamp else None,
            "created_at": email.created_at.isoformat(),
            "is_qualified": email.is_qualified,
            "qualification_stage": email.qualification_stage,
            "qualification_confidence": email.qualification_confidence,
            "qualification_reason": email.qualification_reason,
            "qualified_at": email.qualified_at.isoformat() if email.qualified_at else None,
            "attached_documents": doc_count
        })

    return {
        "total": len(results),
        "emails": results
    }


# ========== Document Upload Routes ==========

@router.post("/upload/pdf", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload a PDF document for the authenticated user."""
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Validate file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset

    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {settings.MAX_FILE_SIZE} bytes"
        )

    try:
        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(settings.UPLOAD_DIR, filename)

        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Create document record
        document = Document(
            user_id=current_user.id,
            filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            mime_type="application/pdf",
            processing_status=ProcessingStatus.PENDING
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        # Process document in background (for MVP, do it synchronously)
        processor = ProcessingService(db)
        processor.process_document(document.id)

        return {
            "document_id": document.id,
            "filename": file.filename,
            "status": "uploaded"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# ========== Transaction Routes ==========

@router.get("/transactions")
async def get_transactions(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    vendor: Optional[str] = Query(None),
    doc_type: Optional[str] = Query(None),
    currency: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get transactions for the authenticated user with optional filters."""
    # Only get transactions from user's documents
    query = db.query(Transaction).join(Document).filter(Document.user_id == current_user.id)

    # Apply filters
    if date_from:
        try:
            date_from_dt = datetime.fromisoformat(date_from)
            query = query.filter(Transaction.transaction_date >= date_from_dt)
        except:
            pass

    if date_to:
        try:
            date_to_dt = datetime.fromisoformat(date_to)
            query = query.filter(Transaction.transaction_date <= date_to_dt)
        except:
            pass

    if vendor:
        from app.db.models import Party
        query = query.join(Party).filter(Party.name.ilike(f"%{vendor}%"))

    if doc_type:
        query = query.filter(Transaction.transaction_type == doc_type)

    if currency:
        query = query.filter(Transaction.currency == currency)

    # Get total count
    total = query.count()

    # Apply pagination
    transactions = query.order_by(
        Transaction.transaction_date.desc()
    ).offset(offset).limit(limit).all()

    # Format response
    results = []
    for txn in transactions:
        party_name = None
        if txn.party:
            party_name = txn.party.name

        # Get email_id through EmailDocumentLink
        email_id = None
        if txn.document_id:
            from app.db.models import EmailDocumentLink
            email_link = db.query(EmailDocumentLink).filter(
                EmailDocumentLink.document_id == txn.document_id
            ).first()
            if email_link:
                email_id = email_link.email_id

        results.append({
            "id": txn.id,
            "amount": txn.amount,
            "currency": txn.currency,
            "date": txn.transaction_date.isoformat() if txn.transaction_date else None,
            "type": txn.transaction_type,
            "vendor": party_name,
            "document_id": txn.document_id,
            "email_id": email_id,
            "description": txn.description
        })

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "transactions": results
    }


# ========== Document Routes ==========

@router.get("/documents/{document_id}")
async def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get document details for the authenticated user."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "id": document.id,
        "filename": document.filename,
        "file_path": document.file_path,
        "file_size": document.file_size,
        "processing_status": document.processing_status.value,
        "document_type": document.document_type.value if document.document_type else None,
        "extracted_text": document.extracted_text,
        "extracted_data": document.extracted_data,
        "uploaded_at": document.uploaded_at.isoformat(),
        "processed_at": document.processed_at.isoformat() if document.processed_at else None
    }


# ========== Query Routes ==========

@router.post("/query")
async def query(
    request: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Answer predefined queries for the authenticated user."""
    query_service = QueryService(db, user_id=current_user.id)

    try:
        result = query_service.answer_query(request.query_type, request.params)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Query failed: {str(e)}")


@router.get("/filters")
async def get_filters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get available filter values for the authenticated user."""
    query_service = QueryService(db, user_id=current_user.id)
    return query_service.get_transaction_filters()


# ========== Stats Routes ==========

@router.get("/stats")
async def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get statistics for the authenticated user."""
    # Count user's documents
    total_documents = db.query(Document).filter(Document.user_id == current_user.id).count()

    # Count user's transactions (through documents)
    total_transactions = db.query(Transaction).join(Document).filter(
        Document.user_id == current_user.id
    ).count()

    # Count emails (all emails for now - can be user-specific later)
    total_emails = db.query(Email).count()

    # Calculate total amount from user's transactions
    from sqlalchemy import func
    total_amount = db.query(func.sum(Transaction.amount)).join(Document).filter(
        Document.user_id == current_user.id
    ).scalar() or 0.0

    return {
        "total_transactions": total_transactions,
        "total_documents": total_documents,
        "total_emails": total_emails,
        "total_amount": round(total_amount, 2),
        "currency": "USD"
    }


# ========== Knowledge Graph Routes ==========

@router.get("/graph")
async def get_knowledge_graph(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get knowledge graph for the authenticated user."""
    graph_service = GraphService(db, user_id=current_user.id)
    return graph_service.build_knowledge_graph()


@router.get("/graph/document/{document_id}")
async def get_document_graph(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get knowledge graph for a specific document."""
    graph_service = GraphService(db, user_id=current_user.id)
    return graph_service.get_document_graph(document_id)


@router.get("/graph/party/{party_id}")
async def get_party_graph(
    party_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get knowledge graph for a specific party (vendor)."""
    graph_service = GraphService(db, user_id=current_user.id)
    return graph_service.get_party_graph(party_id)


# ========== Template Management Routes ==========

@router.get("/templates")
async def get_templates(
    document_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all document templates, optionally filtered by document type."""
    template_service = TemplateService(db)

    from app.db.models import DocumentType as DocType
    doc_type_enum = None

    if document_type:
        try:
            doc_type_enum = DocType(document_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid document type: {document_type}")

    templates = template_service.get_all_templates(doc_type_enum)

    return {
        "templates": [
            {
                "id": t.id,
                "name": t.name,
                "document_type": t.document_type.value,
                "usage_count": t.usage_count,
                "success_count": t.success_count,
                "confidence_score": round(t.confidence_score, 2),
                "is_active": t.is_active,
                "created_at": t.created_at.isoformat(),
                "last_updated": t.last_updated.isoformat() if t.last_updated else None
            }
            for t in templates
        ]
    }


@router.get("/templates/{template_id}")
async def get_template(template_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific template."""
    template_service = TemplateService(db)
    template = template_service.get_template(template_id)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return {
        "id": template.id,
        "name": template.name,
        "document_type": template.document_type.value,
        "template_schema": template.template_schema,
        "keywords": template.keywords,
        "vendor_pattern": template.vendor_pattern,
        "usage_count": template.usage_count,
        "success_count": template.success_count,
        "confidence_score": round(template.confidence_score, 2),
        "sample_documents": template.sample_documents,
        "is_active": template.is_active,
        "created_at": template.created_at.isoformat(),
        "last_updated": template.last_updated.isoformat() if template.last_updated else None
    }


@router.delete("/templates/{template_id}")
async def delete_template(template_id: int, db: Session = Depends(get_db)):
    """Delete a template."""
    template_service = TemplateService(db)
    success = template_service.delete_template(template_id)

    if not success:
        raise HTTPException(status_code=404, detail="Template not found")

    return {"message": "Template deleted successfully"}


@router.get("/extraction-logs")
async def get_extraction_logs(
    document_id: Optional[int] = Query(None),
    template_id: Optional[int] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """Get extraction logs for analysis and improvement."""
    from app.db.models import ExtractionLog

    query = db.query(ExtractionLog)

    if document_id:
        query = query.filter(ExtractionLog.document_id == document_id)
    if template_id:
        query = query.filter(ExtractionLog.template_id == template_id)

    total = query.count()
    logs = query.order_by(ExtractionLog.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "logs": [
            {
                "id": log.id,
                "document_id": log.document_id,
                "template_id": log.template_id,
                "extraction_method": log.extraction_method,
                "fields_extracted": log.fields_extracted,
                "confidence_scores": log.confidence_scores,
                "extraction_time": round(log.extraction_time, 3) if log.extraction_time else None,
                "success": log.success,
                "error_message": log.error_message,
                "manually_verified": log.manually_verified,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ]
    }


# ========== Metrics Routes ==========

@router.get("/metrics/processing")
async def get_processing_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get processing metrics including:
    - Total emails processed
    - Total pages processed
    - Pages per email
    - Total characters processed
    - Characters per email
    - Email qualification statistics
    """
    from sqlalchemy import func

    # Get all emails with their linked documents
    email_metrics = []

    emails = db.query(Email).all()

    total_emails = len(emails)
    total_pages = 0
    total_characters = 0
    emails_with_documents = 0

    # Qualification statistics
    emails_qualified = 0
    emails_not_qualified = 0
    emails_pending_qualification = 0
    qualified_by_subject = 0
    qualified_by_body = 0

    for email in emails:
        # Track qualification stats
        if email.is_qualified is None:
            emails_pending_qualification += 1
        elif email.is_qualified:
            emails_qualified += 1
            if email.qualification_stage == "subject":
                qualified_by_subject += 1
            elif email.qualification_stage == "body":
                qualified_by_body += 1
        else:
            emails_not_qualified += 1
        # Get linked documents for this email
        links = db.query(EmailDocumentLink).filter(
            EmailDocumentLink.email_id == email.id
        ).all()

        if links:
            email_pages = 0
            email_chars = 0

            for link in links:
                doc = db.query(Document).filter(Document.id == link.document_id).first()
                if doc:
                    email_pages += doc.page_count or 0
                    email_chars += doc.character_count or 0

            if email_pages > 0 or email_chars > 0:
                emails_with_documents += 1
                total_pages += email_pages
                total_characters += email_chars

                email_metrics.append({
                    "email_id": email.id,
                    "subject": email.subject,
                    "pages": email_pages,
                    "characters": email_chars,
                    "timestamp": email.timestamp.isoformat() if email.timestamp else None
                })

    # Get document-level aggregated metrics
    doc_stats = db.query(
        func.count(Document.id).label('total_documents'),
        func.sum(Document.page_count).label('sum_pages'),
        func.sum(Document.character_count).label('sum_characters'),
        func.avg(Document.page_count).label('avg_pages'),
        func.avg(Document.character_count).label('avg_characters')
    ).filter(
        Document.user_id == current_user.id
    ).first()

    return {
        "summary": {
            "total_emails": total_emails,
            "emails_with_documents": emails_with_documents,
            "total_documents": doc_stats.total_documents or 0,
            "total_pages_processed": int(doc_stats.sum_pages or 0),
            "total_characters_processed": int(doc_stats.sum_characters or 0),
            "avg_pages_per_document": round(float(doc_stats.avg_pages or 0), 2),
            "avg_characters_per_document": round(float(doc_stats.avg_characters or 0), 2),
            # Qualification statistics
            "emails_qualified": emails_qualified,
            "emails_not_qualified": emails_not_qualified,
            "emails_pending_qualification": emails_pending_qualification,
            "qualified_by_subject": qualified_by_subject,
            "qualified_by_body": qualified_by_body,
            "qualification_rate": round(emails_qualified / total_emails * 100, 1) if total_emails > 0 else 0
        },
        "per_email_metrics": email_metrics[:50]  # Limit to 50 most recent for performance
    }
