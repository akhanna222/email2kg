from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os
import shutil

from app.db.database import get_db
from app.db.models import Document, Transaction, Email, User, ProcessingStatus
from app.services.gmail_service import GmailService
from app.services.processing_service import ProcessingService
from app.services.query_service import QueryService
from app.core.config import settings
from pydantic import BaseModel

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
async def google_auth():
    """Initiate Google OAuth flow."""
    auth_url = GmailService.get_auth_url()
    return {"auth_url": auth_url}


@router.post("/auth/callback", response_model=TokenResponse)
async def oauth_callback(request: OAuthCallbackRequest, db: Session = Depends(get_db)):
    """Handle OAuth callback and store tokens."""
    try:
        tokens = GmailService.exchange_code_for_tokens(request.code)

        # For MVP, we have a single user. Find or create user.
        user = db.query(User).first()
        if not user:
            user = User(email="default@example.com")
            db.add(user)

        user.gmail_access_token = tokens["access_token"]
        user.gmail_refresh_token = tokens["refresh_token"]
        user.gmail_token_expiry = tokens["token_expiry"]

        db.commit()

        return {"message": "Successfully connected Gmail", "user_id": user.id}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth failed: {str(e)}")


# ========== Email Sync Routes ==========

@router.post("/sync/gmail")
async def sync_gmail(db: Session = Depends(get_db)):
    """Sync emails from Gmail."""
    # Get user (single user for MVP)
    user = db.query(User).first()
    if not user or not user.gmail_access_token:
        raise HTTPException(status_code=401, detail="Gmail not connected")

    try:
        # Fetch emails
        emails = GmailService.fetch_emails(
            user.gmail_access_token,
            months=settings.EMAIL_FETCH_MONTHS
        )

        new_count = 0
        for email_data in emails:
            # Check if email already exists
            existing = db.query(Email).filter(
                Email.gmail_id == email_data["gmail_id"]
            ).first()

            if not existing:
                email = Email(
                    gmail_id=email_data["gmail_id"],
                    subject=email_data["subject"],
                    sender=email_data["sender"],
                    receiver=email_data["receiver"],
                    timestamp=email_data["timestamp"],
                    body_text=email_data["body_text"]
                )
                db.add(email)
                new_count += 1

                # TODO: Process attachments in background job

        db.commit()
        user.last_sync = datetime.utcnow()
        db.commit()

        return {
            "message": f"Synced {new_count} new emails",
            "total_fetched": len(emails),
            "new_emails": new_count
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


# ========== Document Upload Routes ==========

@router.post("/upload/pdf", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a PDF document."""
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
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(settings.UPLOAD_DIR, filename)

        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Create document record
        document = Document(
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
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """Get transactions with optional filters."""
    query = db.query(Transaction)

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

        results.append({
            "id": txn.id,
            "amount": txn.amount,
            "currency": txn.currency,
            "date": txn.transaction_date.isoformat() if txn.transaction_date else None,
            "type": txn.transaction_type,
            "vendor": party_name,
            "document_id": txn.document_id,
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
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get document details."""
    document = db.query(Document).filter(Document.id == document_id).first()
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
async def query(request: QueryRequest, db: Session = Depends(get_db)):
    """Answer predefined queries."""
    query_service = QueryService(db)

    try:
        result = query_service.answer_query(request.query_type, request.params)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Query failed: {str(e)}")


@router.get("/filters")
async def get_filters(db: Session = Depends(get_db)):
    """Get available filter values."""
    query_service = QueryService(db)
    return query_service.get_transaction_filters()


# ========== Stats Routes ==========

@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get overall statistics."""
    total_transactions = db.query(Transaction).count()
    total_documents = db.query(Document).count()
    total_emails = db.query(Email).count()

    from sqlalchemy import func
    total_amount = db.query(func.sum(Transaction.amount)).scalar() or 0.0

    return {
        "total_transactions": total_transactions,
        "total_documents": total_documents,
        "total_emails": total_emails,
        "total_amount": round(total_amount, 2),
        "currency": "USD"
    }
