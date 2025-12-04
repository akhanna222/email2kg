#!/bin/bash

# Celery worker startup script for Email2KG
# This script starts Celery workers for background task processing

# Exit on error
set -e

echo "Starting Celery workers for Email2KG..."

# Set environment variables if not already set
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Check if Redis is available
echo "Checking Redis connection..."
python -c "import redis; r = redis.from_url('${CELERY_BROKER_URL:-redis://localhost:6379/0}'); r.ping(); print('✓ Redis is available')" || {
    echo "✗ Error: Cannot connect to Redis. Make sure Redis is running."
    echo "  Start Redis with: redis-server"
    echo "  Or with Docker: docker run -d -p 6379:6379 redis:alpine"
    exit 1
}

# Start Celery worker
echo "Starting Celery worker..."
celery -A app.core.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --queues=attachments,documents,default \
    --max-tasks-per-child=1000 \
    --time-limit=600 \
    --soft-time-limit=540 \
    --pool=prefork

# Alternative: Start worker with autoscaling
# celery -A app.core.celery_app worker \
#     --loglevel=info \
#     --autoscale=8,2 \
#     --queues=attachments,documents,default

# Alternative: Start multiple specialized workers
# Terminal 1: celery -A app.core.celery_app worker -Q attachments --loglevel=info --concurrency=2
# Terminal 2: celery -A app.core.celery_app worker -Q documents --loglevel=info --concurrency=2
