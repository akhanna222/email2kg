"""
Background worker for processing uploaded documents.
Moves synchronous document processing to background tasks.
"""
from celery.utils.log import get_task_logger
from app.core.celery_app import celery_app
from app.workers.attachment_processor import DatabaseTask
from app.services.processing_service import ProcessingService

logger = get_task_logger(__name__)


@celery_app.task(bind=True, base=DatabaseTask, max_retries=3)
def process_uploaded_document(self, document_id: int) -> dict:
    """
    Process an uploaded document in the background.

    Args:
        document_id: ID of the document to process

    Returns:
        Dict with processing result
    """
    logger.info(f"Processing uploaded document {document_id}")

    try:
        processor = ProcessingService(self.db)
        success = processor.process_document(document_id)

        if success:
            logger.info(f"Successfully processed document {document_id}")
            return {
                "status": "success",
                "document_id": document_id
            }
        else:
            logger.error(f"Failed to process document {document_id}")
            return {
                "status": "failed",
                "document_id": document_id
            }

    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}", exc_info=True)
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        return {
            "status": "error",
            "document_id": document_id,
            "message": str(e)
        }
