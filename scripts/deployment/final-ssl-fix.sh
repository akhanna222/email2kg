#!/bin/bash

# Final SSL Fix - Rebuilds frontend with correct Dockerfile
# This fixes the "Nginx NOT configured for SSL" issue

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Run with sudo${NC}"
    exit 1
fi

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}   Final SSL Fix for Email2KG${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

cd /home/ubuntu/email2kg || cd ~/email2kg || exit 1

echo -e "${YELLOW}1/7: Copying SSL certificates...${NC}"
mkdir -p ssl
if [ -d "/etc/letsencrypt/live/agenticrag360.com" ]; then
    cp /etc/letsencrypt/live/agenticrag360.com/fullchain.pem ssl/certificate.crt
    cp /etc/letsencrypt/live/agenticrag360.com/privkey.pem ssl/private.key
    chmod 644 ssl/certificate.crt
    chmod 600 ssl/private.key
    chown ubuntu:ubuntu ssl/* 2>/dev/null || true
    echo -e "${GREEN}✅ Certificates ready${NC}"
else
    echo -e "${RED}❌ Let's Encrypt certs not found. Run enable-https.sh first${NC}"
    exit 1
fi
echo ""

echo -e "${YELLOW}2/7: Verifying nginx.conf has SSL...${NC}"
if grep -q "listen 443 ssl" frontend/nginx.conf; then
    echo -e "${GREEN}✅ nginx.conf has SSL config${NC}"
else
    echo -e "${RED}❌ nginx.conf missing SSL. Check frontend/nginx.conf${NC}"
    exit 1
fi
echo ""

echo -e "${YELLOW}3/7: Verifying Dockerfile exposes port 443...${NC}"
if grep -q "EXPOSE.*443" frontend/Dockerfile; then
    echo -e "${GREEN}✅ Dockerfile exposes port 443${NC}"
else
    echo -e "${RED}❌ Dockerfile doesn't expose 443. Pull latest code.${NC}"
    exit 1
fi
echo ""

echo -e "${YELLOW}4/7: Stopping containers...${NC}"
docker compose down
echo -e "${GREEN}✅ Stopped${NC}"
echo ""

echo -e "${YELLOW}5/7: Removing old frontend image...${NC}"
docker rmi email2kg-frontend 2>/dev/null || true
echo -e "${GREEN}✅ Old image removed${NC}"
echo ""

echo -e "${YELLOW}6/7: Rebuilding frontend (no cache)...${NC}"
echo "This will take 1-2 minutes..."
docker compose build --no-cache frontend
echo -e "${GREEN}✅ Frontend rebuilt with SSL${NC}"
echo ""

echo -e "${YELLOW}7/7: Starting all services...${NC}"
docker compose up -d
echo ""
echo "Waiting 30 seconds for nginx to start..."
sleep 30
echo -e "${GREEN}✅ Services started${NC}"
echo ""

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}   Testing SSL Configuration${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

echo "Container status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep email2kg
echo ""

echo "Checking nginx config inside container..."
if docker exec email2kg-frontend cat /etc/nginx/conf.d/default.conf 2>/dev/null | grep -q "listen 443 ssl"; then
    echo -e "${GREEN}✅ Nginx HAS SSL config (listen 443 ssl)${NC}"
else
    echo -e "${RED}❌ Nginx still missing SSL config${NC}"
    echo "This shouldn't happen. Check the build logs above."
    exit 1
fi
echo ""

echo "Checking if SSL certificates are mounted..."
if docker exec email2kg-frontend test -f /etc/nginx/ssl/certificate.crt 2>/dev/null; then
    echo -e "${GREEN}✅ SSL certificates are mounted${NC}"
    docker exec email2kg-frontend ls -lh /etc/nginx/ssl/
else
    echo -e "${RED}❌ SSL certificates not mounted${NC}"
    echo "Check docker-compose.yml has: - ./ssl:/etc/nginx/ssl:ro"
    exit 1
fi
echo ""

echo "Testing HTTPS locally..."
sleep 5
RESPONSE=$(curl -k -s https://localhost/health 2>&1 || echo "FAILED")
if echo "$RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✅ HTTPS WORKS!${NC}"
    echo "Response: $RESPONSE"
else
    echo -e "${RED}❌ HTTPS test failed${NC}"
    echo "Response: $RESPONSE"
    echo ""
    echo "Checking nginx error logs..."
    docker exec email2kg-frontend cat /var/log/nginx/error.log 2>/dev/null | tail -20 || true
    exit 1
fi
echo ""

echo -e "${BLUE}======================================${NC}"
echo -e "${GREEN}   ✅ SSL IS NOW WORKING!${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

echo "Test commands:"
echo ""
echo "  Local test:"
echo "  curl -k https://localhost/health"
echo ""
echo "  External test:"
echo "  curl https://agenticrag360.com/health"
echo ""
echo "  Browser:"
echo "  https://agenticrag360.com"
echo ""

# Test external
echo "Testing external HTTPS..."
EXT_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://agenticrag360.com/health 2>&1 || echo "000")
if [ "$EXT_CODE" = "200" ]; then
    echo -e "${GREEN}✅ External HTTPS works! (HTTP $EXT_CODE)${NC}"
    echo ""
    echo -e "${GREEN}🎉 ALL DONE! Your site is live at: https://agenticrag360.com${NC}"
else
    echo -e "${YELLOW}⚠️  External test: HTTP $EXT_CODE${NC}"
    if [ "$EXT_CODE" = "000" ]; then
        echo "   Connection failed. Check:"
        echo "   - Port 443 open in security group (you said it is ✅)"
        echo "   - Domain DNS pointing to this server"
    fi
fi
echo ""
