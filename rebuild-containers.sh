#!/bin/bash
# Rebuild and restart containers after bug fixes

echo "=== Pulling latest changes ==="
git pull origin claude/add-ocr-email-extraction-01E2J9RkrixaT8TUTReBnHiG

echo ""
echo "=== Stopping containers ==="
docker compose down

echo ""
echo "=== Rebuilding backend (with bug fixes) ==="
docker compose build --no-cache backend

echo ""
echo "=== Rebuilding celery worker (with bug fixes) ==="
docker compose build --no-cache celery_worker

echo ""
echo "=== Rebuilding frontend (with auth fix) ==="
docker compose build --no-cache frontend

echo ""
echo "=== Starting all containers ==="
docker compose up -d

echo ""
echo "=== Waiting 10 seconds for startup ==="
sleep 10

echo ""
echo "=== Container Status ==="
docker compose ps

echo ""
echo "=== Backend Health Check ==="
curl -s http://localhost:8000/health | jq '.' || echo "Backend not ready yet"

echo ""
echo "=== Recent Backend Logs ==="
docker compose logs backend --tail=20

echo ""
echo "=== Recent Celery Worker Logs ==="
docker compose logs celery_worker --tail=20

echo ""
echo "✅ Rebuild complete! Check logs above for any errors."
echo ""
echo "Next steps:"
echo "1. Try signup at http://localhost:3000/signup"
echo "2. If auth works, try syncing emails"
echo "3. Check activity feed to see LLM qualification working"
