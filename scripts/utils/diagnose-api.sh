#!/bin/bash

# Quick API Diagnostic - Check why login/signup returns 404

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}   API 404 Diagnostic${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

cd /home/ubuntu/email2kg || cd ~/email2kg || exit 1

echo -e "${YELLOW}1. Checking if all services are running...${NC}"
echo ""
if docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep email2kg; then
    echo ""
    BACKEND_RUNNING=$(docker ps | grep email2kg-backend | grep "Up" || echo "")
    if [ -n "$BACKEND_RUNNING" ]; then
        echo -e "${GREEN}✅ Backend is running${NC}"
    else
        echo -e "${RED}❌ Backend is NOT running${NC}"
        echo ""
        echo "Fix: sudo docker compose up -d backend"
        exit 1
    fi
else
    echo -e "${RED}❌ No services running${NC}"
    echo "Fix: sudo docker compose up -d"
    exit 1
fi
echo ""

echo -e "${YELLOW}2. Testing backend health (direct)...${NC}"
HEALTH=$(docker exec email2kg-backend curl -s http://localhost:8000/api/health 2>/dev/null || echo "FAILED")
if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Backend API is healthy${NC}"
    echo "Response: $HEALTH"
else
    echo -e "${RED}❌ Backend API not responding${NC}"
    echo "Response: $HEALTH"
    echo ""
    echo "Checking backend logs for errors..."
    docker compose logs backend --tail=20 | grep -i error || echo "(no recent errors)"
fi
echo ""

echo -e "${YELLOW}3. Testing API through HTTPS...${NC}"
HTTPS_HEALTH=$(curl -s https://agenticrag360.com/api/health 2>&1 || echo "FAILED")
if echo "$HTTPS_HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✅ API accessible through HTTPS${NC}"
    echo "Response: $HTTPS_HEALTH"
else
    echo -e "${RED}❌ API not accessible through HTTPS${NC}"
    echo "Response: $HTTPS_HEALTH"
    echo ""
    echo "This means nginx is not proxying /api/ to backend correctly."
fi
echo ""

echo -e "${YELLOW}4. Checking nginx proxy configuration...${NC}"
if docker exec email2kg-frontend cat /etc/nginx/conf.d/default.conf 2>/dev/null | grep -q "location /api/"; then
    echo -e "${GREEN}✅ Nginx has /api/ location block${NC}"
    echo ""
    echo "Proxy configuration:"
    docker exec email2kg-frontend cat /etc/nginx/conf.d/default.conf | grep -A5 "location /api/" | head -6
else
    echo -e "${RED}❌ Nginx missing /api/ proxy configuration${NC}"
    echo ""
    echo "Fix: Rebuild frontend container"
fi
echo ""

echo -e "${YELLOW}5. Checking ALLOWED_ORIGINS configuration...${NC}"
ORIGINS=$(docker exec email2kg-backend env | grep ALLOWED_ORIGINS || echo "NOT_SET")
if echo "$ORIGINS" | grep -q "agenticrag360.com"; then
    echo -e "${GREEN}✅ ALLOWED_ORIGINS includes agenticrag360.com${NC}"
    echo "$ORIGINS"
else
    echo -e "${YELLOW}⚠️  ALLOWED_ORIGINS may not include domain${NC}"
    echo "$ORIGINS"
    echo ""
    echo "This could cause CORS errors."
fi
echo ""

echo -e "${YELLOW}6. Checking PUBLIC_PROTOCOL setting...${NC}"
PROTOCOL=$(grep PUBLIC_PROTOCOL .env 2>/dev/null || echo "NOT_SET")
if echo "$PROTOCOL" | grep -q "https"; then
    echo -e "${GREEN}✅ PUBLIC_PROTOCOL=https${NC}"
else
    echo -e "${RED}❌ PUBLIC_PROTOCOL not set to https${NC}"
    echo "Current: $PROTOCOL"
    echo ""
    echo "Fix:"
    echo "  nano .env"
    echo "  Change: PUBLIC_PROTOCOL=https"
    echo "  Then: sudo docker compose restart backend"
fi
echo ""

echo -e "${YELLOW}7. Testing auth endpoints...${NC}"
echo ""

echo "Testing /api/auth/register..."
REGISTER_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST https://agenticrag360.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test"}' 2>&1)

if [ "$REGISTER_RESPONSE" = "404" ]; then
    echo -e "${RED}❌ Register endpoint returns 404${NC}"
elif [ "$REGISTER_RESPONSE" = "422" ]; then
    echo -e "${GREEN}✅ Register endpoint exists (422 = validation error)${NC}"
elif [ "$REGISTER_RESPONSE" = "201" ] || [ "$REGISTER_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✅ Register endpoint works (HTTP $REGISTER_RESPONSE)${NC}"
else
    echo -e "${YELLOW}⚠️  Register endpoint returned: HTTP $REGISTER_RESPONSE${NC}"
fi

echo ""
echo "Testing /api/auth/login..."
LOGIN_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST https://agenticrag360.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test"}' 2>&1)

if [ "$LOGIN_RESPONSE" = "404" ]; then
    echo -e "${RED}❌ Login endpoint returns 404${NC}"
elif [ "$LOGIN_RESPONSE" = "401" ]; then
    echo -e "${GREEN}✅ Login endpoint exists (401 = unauthorized)${NC}"
elif [ "$LOGIN_RESPONSE" = "422" ]; then
    echo -e "${GREEN}✅ Login endpoint exists (422 = validation error)${NC}"
elif [ "$LOGIN_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✅ Login endpoint works${NC}"
else
    echo -e "${YELLOW}⚠️  Login endpoint returned: HTTP $LOGIN_RESPONSE${NC}"
fi
echo ""

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}   Diagnosis Summary${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

if [ "$REGISTER_RESPONSE" = "404" ] || [ "$LOGIN_RESPONSE" = "404" ]; then
    echo -e "${RED}🔴 ISSUE: Auth endpoints return 404${NC}"
    echo ""
    echo "Most likely causes:"
    echo "  1. Backend not restarted after .env changes"
    echo "  2. Backend routes not registered properly"
    echo "  3. Nginx not proxying /api/ to backend"
    echo ""
    echo "Recommended fix:"
    echo "  1. Check .env has PUBLIC_PROTOCOL=https"
    echo "  2. Restart backend: sudo docker compose restart backend"
    echo "  3. Wait 10 seconds: sleep 10"
    echo "  4. Test again: curl https://agenticrag360.com/api/health"
    echo ""
    echo "If still failing:"
    echo "  See docs/troubleshooting/API_404_ERRORS.md"
else
    echo -e "${GREEN}✅ Auth endpoints are working!${NC}"
    echo ""
    echo "Try login/signup in the browser now."
fi
echo ""
