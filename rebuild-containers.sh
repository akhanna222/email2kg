#!/bin/bash
# Complete rebuild from scratch - pull latest changes and rebuild all containers

set -e  # Exit on any error

echo "========================================"
echo "  COMPLETE REBUILD FROM SCRATCH"
echo "========================================"
echo ""

echo "=== Step 1: Pull latest changes from git ==="
git pull origin claude/add-ocr-email-extraction-01E2J9RkrixaT8TUTReBnHiG
echo "✅ Git pull complete"

echo ""
echo "=== Step 2: Stop all running containers ==="
docker compose down
echo "✅ Containers stopped"

echo ""
echo "=== Step 3: Remove old containers completely ==="
docker compose rm -f -s -v
echo "✅ Old containers removed"

echo ""
echo "=== Step 4: Prune dangling images (free up space) ==="
docker image prune -f
echo "✅ Dangling images pruned"

echo ""
echo "=== Step 5: Remove old volumes (fresh database) ==="
read -p "⚠️  Remove database volumes? This will DELETE all data. (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker compose down -v
    echo "✅ Volumes removed - fresh database will be created"
else
    echo "⏭️  Skipping volume removal - keeping existing data"
fi

echo ""
echo "=== Step 6: Build backend from scratch (no cache) ==="
docker compose build --no-cache backend
echo "✅ Backend built"

echo ""
echo "=== Step 7: Build celery worker from scratch (no cache) ==="
docker compose build --no-cache celery_worker
echo "✅ Celery worker built"

echo ""
echo "=== Step 8: Build frontend from scratch (no cache) ==="
docker compose build --no-cache frontend
echo "✅ Frontend built"

echo ""
echo "=== Step 9: Build remaining services ==="
docker compose build postgres redis
echo "✅ All services built"

echo ""
echo "=== Step 10: Start all containers ==="
docker compose up -d
echo "✅ Containers starting..."

echo ""
echo "=== Step 11: Wait for services to start (15 seconds) ==="
for i in {15..1}; do
    echo -n "$i... "
    sleep 1
done
echo ""

echo ""
echo "=== Step 12: Container Status ==="
docker compose ps

echo ""
echo "=== Step 13: Backend Health Check ==="
for i in {1..5}; do
    echo "Attempt $i/5..."
    if curl -s http://localhost:8000/health | jq '.' 2>/dev/null; then
        echo "✅ Backend is healthy!"
        break
    else
        echo "⏳ Backend not ready yet, waiting 3 seconds..."
        sleep 3
    fi
done

echo ""
echo "=== Step 14: Recent Backend Logs ==="
docker compose logs backend --tail=30

echo ""
echo "=== Step 15: Recent Celery Worker Logs ==="
docker compose logs celery_worker --tail=30

echo ""
echo "=== Step 16: Recent Frontend Logs ==="
docker compose logs frontend --tail=15

echo ""
echo "========================================"
echo "  ✅ REBUILD COMPLETE!"
echo "========================================"
echo ""
echo "🔧 Bug Fixes Applied:"
echo "  ✓ Celery worker duplicate refresh_token parameter fixed"
echo "  ✓ Month selection variable bug fixed (routes.py)"
echo "  ✓ Auth endpoint routing fixed (separate authApi instance)"
echo "  ✓ OpenAI cost optimizations (keyword filtering, skip Vision OCR)"
echo ""
echo "📋 Next Steps:"
echo "  1. Frontend: http://localhost:3000"
echo "  2. Try signup/login: http://localhost:3000/signup"
echo "  3. Connect Gmail and sync emails"
echo "  4. Check activity feed for LLM qualification results"
echo "  5. API docs: http://localhost:8000/docs"
echo ""
echo "🔍 Monitor Logs:"
echo "  docker compose logs -f backend"
echo "  docker compose logs -f celery_worker"
echo "  docker compose logs -f frontend"
echo ""
