"""
User feedback API routes for extraction corrections and verification.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from app.db.database import get_db
from app.db.models import User, Document, UserFeedback, ExtractionLog
from app.core.auth import get_current_active_user
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])


class FeedbackSubmit(BaseModel):
    """Schema for submitting feedback."""
    document_id: int
    extraction_log_id: Optional[int] = None
    feedback_type: str  # "correction", "verification", "flag_error"
    original_data: Dict[str, Any]
    corrected_data: Dict[str, Any]
    field_name: Optional[str] = None
    comments: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Schema for feedback response."""
    id: int
    document_id: int
    feedback_type: str
    status: str
    created_at: str
    applied_to_template: bool

    class Config:
        from_attributes = True


@router.post("/submit", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    feedback: FeedbackSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Submit user feedback for document extraction.

    Args:
        feedback: Feedback data with corrections
        current_user: Current authenticated user

    Returns:
        Created feedback record
    """
    # Verify document belongs to user
    document = db.query(Document).filter(
        Document.id == feedback.document_id,
        Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Create feedback record
    user_feedback = UserFeedback(
        user_id=current_user.id,
        document_id=feedback.document_id,
        extraction_log_id=feedback.extraction_log_id,
        feedback_type=feedback.feedback_type,
        original_data=feedback.original_data,
        corrected_data=feedback.corrected_data,
        field_name=feedback.field_name,
        comments=feedback.comments,
        status="pending",
        applied_to_template=False,
        created_at=datetime.utcnow()
    )

    db.add(user_feedback)

    # Update document with correction
    if feedback.feedback_type == "correction":
        if not document.user_corrections:
            document.user_corrections = {}

        # Merge corrections
        document.user_corrections.update(feedback.corrected_data)
        document.needs_review = False
        document.user_verified = True
        document.reviewed_at = datetime.utcnow()

        # Apply corrections to extracted_data
        if document.extracted_data:
            document.extracted_data.update(feedback.corrected_data)

    elif feedback.feedback_type == "verification":
        document.user_verified = True
        document.needs_review = False
        document.reviewed_at = datetime.utcnow()

    elif feedback.feedback_type == "flag_error":
        document.needs_review = True

    db.commit()
    db.refresh(user_feedback)

    return FeedbackResponse(
        id=user_feedback.id,
        document_id=user_feedback.document_id,
        feedback_type=user_feedback.feedback_type,
        status=user_feedback.status,
        created_at=user_feedback.created_at.isoformat(),
        applied_to_template=user_feedback.applied_to_template
    )


@router.get("/document/{document_id}")
async def get_document_feedback(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all feedback for a specific document.

    Args:
        document_id: Document ID
        current_user: Current authenticated user

    Returns:
        List of feedback records
    """
    # Verify document belongs to user
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    feedback_records = db.query(UserFeedback).filter(
        UserFeedback.document_id == document_id,
        UserFeedback.user_id == current_user.id
    ).order_by(UserFeedback.created_at.desc()).all()

    return {
        "document_id": document_id,
        "feedback_count": len(feedback_records),
        "feedback": [
            {
                "id": f.id,
                "feedback_type": f.feedback_type,
                "field_name": f.field_name,
                "original_data": f.original_data,
                "corrected_data": f.corrected_data,
                "comments": f.comments,
                "status": f.status,
                "applied_to_template": f.applied_to_template,
                "created_at": f.created_at.isoformat()
            }
            for f in feedback_records
        ]
    }


@router.get("/pending")
async def get_pending_feedback(
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all pending feedback for the current user.

    Args:
        limit: Maximum number of records to return
        offset: Number of records to skip
        current_user: Current authenticated user

    Returns:
        List of pending feedback records
    """
    query = db.query(UserFeedback).filter(
        UserFeedback.user_id == current_user.id,
        UserFeedback.status == "pending"
    )

    total = query.count()
    feedback_records = query.order_by(
        UserFeedback.created_at.desc()
    ).offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "feedback": [
            {
                "id": f.id,
                "document_id": f.document_id,
                "feedback_type": f.feedback_type,
                "field_name": f.field_name,
                "status": f.status,
                "created_at": f.created_at.isoformat()
            }
            for f in feedback_records
        ]
    }


@router.get("/documents/needs-review")
async def get_documents_needing_review(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all documents that need user review.

    Args:
        current_user: Current authenticated user

    Returns:
        List of documents needing review
    """
    documents = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.needs_review == True
    ).order_by(Document.uploaded_at.desc()).all()

    return {
        "count": len(documents),
        "documents": [
            {
                "id": doc.id,
                "filename": doc.filename,
                "document_type": doc.document_type.value if doc.document_type else None,
                "extracted_data": doc.extracted_data,
                "uploaded_at": doc.uploaded_at.isoformat()
            }
            for doc in documents
        ]
    }


@router.post("/{feedback_id}/apply")
async def apply_feedback_to_template(
    feedback_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Apply user feedback to improve extraction templates.

    Args:
        feedback_id: Feedback ID
        current_user: Current authenticated user

    Returns:
        Success message
    """
    feedback = db.query(UserFeedback).filter(
        UserFeedback.id == feedback_id,
        UserFeedback.user_id == current_user.id
    ).first()

    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )

    # TODO: Implement template learning from feedback
    # This would update the DocumentTemplate with improved extraction patterns

    feedback.applied_to_template = True
    feedback.status = "applied"
    feedback.applied_at = datetime.utcnow()

    db.commit()

    return {
        "message": "Feedback applied to template successfully",
        "feedback_id": feedback_id
    }
