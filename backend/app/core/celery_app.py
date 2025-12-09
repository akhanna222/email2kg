"""
Celery configuration for background task processing.
"""
from celery import Celery
from app.core.config import settings
import os

# Initialize Celery
celery_app = Celery(
    "email2kg",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    include=[
        "app.workers.attachment_processor",
        "app.workers.document_processor"
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
    task_soft_time_limit=540,  # 9 minutes soft limit
    worker_prefetch_multiplier=1,  # One task at a time per worker
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks
    task_acks_late=True,  # Acknowledge tasks after completion
    task_reject_on_worker_lost=True,  # Requeue tasks if worker dies
    result_expires=3600,  # Results expire after 1 hour
    task_default_retry_delay=60,  # 1 minute retry delay
    task_max_retries=3,  # Max 3 retries
)

# Task routes - can be used to send different tasks to different queues
celery_app.conf.task_routes = {
    "app.workers.attachment_processor.*": {"queue": "attachments"},
    "app.workers.document_processor.*": {"queue": "documents"},
}

# Periodic tasks configuration (if needed in the future)
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    # Example: Auto-sync emails every hour
    # "auto-sync-gmail": {
    #     "task": "app.workers.email_sync.sync_all_users",
    #     "schedule": crontab(minute=0),  # Every hour
    # },
}

if __name__ == "__main__":
    celery_app.start()
