#!/bin/bash
# Check celery worker logs
echo "=== CELERY WORKER LOGS ==="
docker compose logs celery_worker --tail=50

echo ""
echo "=== BACKEND LOGS ==="
docker compose logs backend --tail=50

echo ""
echo "=== CONTAINER STATUS ==="
docker compose ps
