"""
Background worker for processing email attachments.
Handles PDF and image attachments with OCR extraction.
"""
import os
import time
from datetime import datetime
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from celery import Task
from celery.utils.log import get_task_logger

from app.core.celery_app import celery_app
from app.db.database import SessionLocal
from app.db.models import Email, Document, EmailDocumentLink, ProcessingStatus, User
from app.services.gmail_service import GmailService
from app.services.processing_service import ProcessingService
from app.core.config import settings

logger = get_task_logger(__name__)

# Supported file types
SUPPORTED_IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".webp", ".bmp"}
SUPPORTED_DOC_TYPES = {".pdf"}
ALL_SUPPORTED_TYPES = SUPPORTED_IMAGE_TYPES | SUPPORTED_DOC_TYPES


class DatabaseTask(Task):
    """Base task class that provides database session management."""

    _db: Optional[Session] = None

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        """Clean up database session after task completion."""
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(bind=True, base=DatabaseTask, max_retries=3)
def process_email_attachment(
    self,
    email_id: int,
    attachment_info: Dict,
    user_id: int
) -> Dict:
    """
    Process a single email attachment: download, save, extract data.

    Args:
        email_id: Database ID of the email
        attachment_info: Dict with filename, mime_type, size, attachment_id, gmail_id
        user_id: ID of the user who owns the email

    Returns:
        Dict with status and document_id if successful
    """
    logger.info(f"Processing attachment: {attachment_info['filename']} from email {email_id}")

    try:
        # Get email from database
        email = self.db.query(Email).filter(Email.id == email_id).first()
        if not email:
            logger.error(f"Email {email_id} not found")
            return {"status": "error", "message": "Email not found"}

        # Get user to access Gmail token
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.gmail_access_token:
            logger.error(f"User {user_id} not found or Gmail not connected")
            return {"status": "error", "message": "User not found or Gmail not connected"}

        # Validate file type
        filename = attachment_info["filename"]
        file_ext = os.path.splitext(filename.lower())[1]

        if file_ext not in ALL_SUPPORTED_TYPES:
            logger.warning(f"Unsupported file type: {file_ext}")
            return {"status": "skipped", "message": f"Unsupported file type: {file_ext}"}

        # Download attachment from Gmail
        logger.info(f"Downloading attachment {filename}...")
        try:
            attachment_data = GmailService.download_attachment(
                access_token=user.gmail_access_token,
                message_id=attachment_info["gmail_id"],
                attachment_id=attachment_info["attachment_id"]
            )
        except Exception as e:
            logger.error(f"Failed to download attachment: {e}")
            # Retry with exponential backoff
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        # Generate unique filename and save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_email_{email_id}_{filename}"
        file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

        # Ensure upload directory exists
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

        # Save file to disk
        logger.info(f"Saving file to: {file_path}")
        with open(file_path, "wb") as f:
            f.write(attachment_data)

        file_size = len(attachment_data)

        # Create document record
        document = Document(
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=attachment_info["mime_type"],
            processing_status=ProcessingStatus.PENDING
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)

        logger.info(f"Created document record with ID: {document.id}")

        # Link document to email
        link = EmailDocumentLink(
            email_id=email_id,
            document_id=document.id
        )
        self.db.add(link)
        self.db.commit()

        logger.info(f"Linked document {document.id} to email {email_id}")

        # Process the document (extract text, classify, extract structured data)
        logger.info(f"Starting document processing for document {document.id}")
        processor = ProcessingService(self.db)
        success = processor.process_document(document.id)

        if success:
            logger.info(f"Successfully processed document {document.id}")
            return {
                "status": "success",
                "document_id": document.id,
                "filename": filename,
                "email_id": email_id
            }
        else:
            logger.error(f"Failed to process document {document.id}")
            return {
                "status": "failed",
                "document_id": document.id,
                "message": "Document processing failed"
            }

    except Exception as e:
        logger.error(f"Error processing attachment: {e}", exc_info=True)
        # Mark as failed but don't retry forever
        if self.request.retries >= self.max_retries:
            return {
                "status": "error",
                "message": str(e),
                "retries_exhausted": True
            }
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@celery_app.task(bind=True, base=DatabaseTask)
def process_all_email_attachments(
    self,
    email_id: int,
    user_id: int
) -> Dict:
    """
    Process all attachments for a given email.

    Args:
        email_id: Database ID of the email
        user_id: ID of the user who owns the email

    Returns:
        Dict with summary of processed attachments
    """
    logger.info(f"Processing all attachments for email {email_id}")

    try:
        # Get email from database
        email = self.db.query(Email).filter(Email.id == email_id).first()
        if not email:
            logger.error(f"Email {email_id} not found")
            return {"status": "error", "message": "Email not found"}

        # Get user
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.gmail_access_token:
            logger.error(f"User {user_id} not found or Gmail not connected")
            return {"status": "error", "message": "User not found or Gmail not connected"}

        # Fetch fresh email data to get attachments
        gmail_service = GmailService()
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials

        credentials = Credentials(token=user.gmail_access_token)
        service = build('gmail', 'v1', credentials=credentials)

        # Get full message details
        msg = service.users().messages().get(
            userId='me',
            id=email.gmail_id,
            format='full'
        ).execute()

        # Extract attachments info
        attachments = GmailService._get_attachments_info(msg['payload'])

        # Also check for image attachments (not just PDFs)
        attachments.extend(_extract_image_attachments(msg['payload']))

        if not attachments:
            logger.info(f"No attachments found in email {email_id}")
            return {"status": "success", "message": "No attachments found", "processed": 0}

        logger.info(f"Found {len(attachments)} attachments in email {email_id}")

        # Queue each attachment for processing
        results = []
        for attachment in attachments:
            # Add gmail_id to attachment info for downloading
            attachment["gmail_id"] = email.gmail_id

            # Process synchronously for now (can be made async with .delay())
            result = process_email_attachment.apply_async(
                args=[email_id, attachment, user_id],
                queue="attachments"
            )
            results.append({
                "filename": attachment["filename"],
                "task_id": result.id
            })

        return {
            "status": "success",
            "email_id": email_id,
            "attachments_queued": len(results),
            "tasks": results
        }

    except Exception as e:
        logger.error(f"Error processing email attachments: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


def _extract_image_attachments(payload: Dict) -> List[Dict]:
    """
    Extract image attachments from email payload.
    Gmail API returns images as parts with Content-Disposition: attachment.
    """
    attachments = []

    def _extract_from_part(part: Dict):
        """Recursively extract attachments from email parts."""
        if isinstance(part, dict):
            # Check if this part is an attachment
            filename = part.get('filename', '')
            if filename:
                file_ext = os.path.splitext(filename.lower())[1]
                # Check if it's an image type we support
                if file_ext in SUPPORTED_IMAGE_TYPES:
                    attachment_id = part.get('body', {}).get('attachmentId')
                    if attachment_id:
                        attachments.append({
                            "filename": filename,
                            "mime_type": part.get('mimeType', 'image/jpeg'),
                            "size": part.get('body', {}).get('size', 0),
                            "attachment_id": attachment_id
                        })

            # Check nested parts
            if 'parts' in part:
                for subpart in part['parts']:
                    _extract_from_part(subpart)

    _extract_from_part(payload)
    return attachments


@celery_app.task(bind=True, base=DatabaseTask)
def bulk_process_email_attachments(
    self,
    email_ids: List[int],
    user_id: int
) -> Dict:
    """
    Bulk process attachments for multiple emails.

    Args:
        email_ids: List of email database IDs
        user_id: ID of the user who owns the emails

    Returns:
        Dict with summary of bulk processing
    """
    logger.info(f"Bulk processing attachments for {len(email_ids)} emails")

    results = []
    for email_id in email_ids:
        result = process_all_email_attachments.apply_async(
            args=[email_id, user_id],
            queue="attachments"
        )
        results.append({
            "email_id": email_id,
            "task_id": result.id
        })

    return {
        "status": "success",
        "emails_queued": len(results),
        "tasks": results
    }
