#!/bin/bash
# Fix frontend API URL for local testing

set -e

echo "========================================"
echo "  FIX FRONTEND API URL"
echo "========================================"
echo ""
echo "This script fixes the frontend to use localhost:8000 instead of the domain"
echo ""

echo "=== Step 1: Create .env file (if not exists) ==="
if [ ! -f .env ]; then
    echo "Creating .env file..."
    echo "# Frontend API URL Configuration" > .env
    echo "# For local testing: http://localhost:8000/api" >> .env
    echo "# For production: https://agenticrag360.com/api" >> .env
    echo "FRONTEND_API_URL=http://localhost:8000/api" >> .env
    echo "✅ .env file created with local API URL"
else
    if grep -q "FRONTEND_API_URL" .env; then
        echo "✅ FRONTEND_API_URL already exists in .env"
    else
        echo "FRONTEND_API_URL=http://localhost:8000/api" >> .env
        echo "✅ Added FRONTEND_API_URL to .env"
    fi
fi

echo ""
echo "=== Step 2: Show current .env configuration ==="
grep "FRONTEND_API_URL" .env || echo "FRONTEND_API_URL not set"

echo ""
echo "=== Step 3: Pull latest code ==="
git pull origin claude/add-ocr-email-extraction-01E2J9RkrixaT8TUTReBnHiG
echo "✅ Code updated"

echo ""
echo "=== Step 4: Stop frontend ==="
docker compose stop frontend
echo "✅ Frontend stopped"

echo ""
echo "=== Step 5: Remove old frontend container ==="
docker compose rm -f frontend
echo "✅ Old container removed"

echo ""
echo "=== Step 6: Rebuild frontend with local API URL ==="
docker compose build --no-cache frontend
echo "✅ Frontend rebuilt"

echo ""
echo "=== Step 7: Start frontend ==="
docker compose up -d frontend
echo "✅ Frontend started"

echo ""
echo "=== Step 8: Wait for frontend (5 seconds) ==="
sleep 5

echo ""
echo "=== Step 9: Verify frontend ==="
docker compose ps frontend

echo ""
echo "========================================"
echo "  ✅ FIX COMPLETE"
echo "========================================"
echo ""
echo "Frontend is now configured to use: http://localhost:8000/api"
echo ""
echo "📋 Test Now:"
echo "  1. Clear browser cache (Ctrl+Shift+Delete)"
echo "  2. Refresh page: http://localhost:3000"
echo "  3. Try signup: http://localhost:3000/signup"
echo ""
echo "🔍 Check browser console (F12) to verify:"
echo "  - Requests should go to http://localhost:8000/auth/..."
echo "  - Not to https://agenticrag360.com/auth/..."
echo ""
