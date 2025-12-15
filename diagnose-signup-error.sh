#!/bin/bash
# Diagnose signup error - check which endpoint is being called

echo "========================================"
echo "  SIGNUP ERROR DIAGNOSTIC"
echo "========================================"
echo ""

echo "=== 1. Check if containers are running ==="
docker compose ps
echo ""

echo "=== 2. Test auth endpoints directly ==="
echo "Testing: POST /auth/register (correct endpoint)"
curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123","full_name":"Test"}' | head -20
echo ""

echo "Testing: POST /api/auth/register (wrong endpoint - should return 404 HTML)"
curl -s -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123","full_name":"Test"}' | head -20
echo ""

echo "=== 3. Check backend routes ==="
echo "Available auth routes:"
curl -s http://localhost:8000/docs | grep -o '/auth/[^"]*' | head -10
echo ""

echo "=== 4. Check frontend build date ==="
docker compose exec frontend ls -lh /usr/share/nginx/html/static/js/*.js 2>/dev/null | head -5 || echo "Frontend container not running"
echo ""

echo "=== 5. Recent backend logs (auth related) ==="
docker compose logs backend --tail=50 | grep -i auth
echo ""

echo "========================================"
echo "  DIAGNOSIS COMPLETE"
echo "========================================"
echo ""
echo "📋 Next Steps:"
echo ""
echo "If you see HTML response for /auth/register:"
echo "  → Backend route is missing - check backend/app/main.py"
echo ""
echo "If frontend JS files are old (before today):"
echo "  → Run: bash rebuild-containers.sh"
echo ""
echo "If /api/auth/register returns HTML:"
echo "  → This is expected (wrong endpoint)"
echo "  → Frontend needs rebuild to use /auth/register"
echo ""
