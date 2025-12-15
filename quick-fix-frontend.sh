#!/bin/bash
# Quick fix for signup error - rebuild frontend only

set -e

echo "========================================"
echo "  QUICK FIX: Rebuild Frontend"
echo "========================================"
echo ""
echo "This will rebuild the frontend with the auth endpoint fix"
echo ""

echo "=== Step 1: Pull latest changes ==="
git pull origin claude/add-ocr-email-extraction-01E2J9RkrixaT8TUTReBnHiG
echo "✅ Latest code pulled"

echo ""
echo "=== Step 2: Stop frontend container ==="
docker compose stop frontend
echo "✅ Frontend stopped"

echo ""
echo "=== Step 3: Remove frontend container ==="
docker compose rm -f frontend
echo "✅ Old frontend removed"

echo ""
echo "=== Step 4: Rebuild frontend (no cache) ==="
docker compose build --no-cache frontend
echo "✅ Frontend rebuilt with auth fix"

echo ""
echo "=== Step 5: Start frontend ==="
docker compose up -d frontend
echo "✅ Frontend started"

echo ""
echo "=== Step 6: Wait for frontend to start (5 seconds) ==="
sleep 5

echo ""
echo "=== Step 7: Verify frontend is running ==="
docker compose ps frontend

echo ""
echo "========================================"
echo "  ✅ FRONTEND FIX COMPLETE"
echo "========================================"
echo ""
echo "🔧 What was fixed:"
echo "  ✓ Frontend now calls /auth/register (not /api/auth/register)"
echo "  ✓ Separate authApi instance for auth endpoints"
echo ""
echo "📋 Test Now:"
echo "  1. Clear browser cache (Ctrl+Shift+Delete)"
echo "  2. Go to: http://localhost:3000/signup"
echo "  3. Try creating an account"
echo ""
echo "🔍 If still having issues, check browser console:"
echo "  - Press F12"
echo "  - Go to Network tab"
echo "  - Try signup"
echo "  - Look at the request URL (should be /auth/register, not /api/auth/register)"
echo ""
