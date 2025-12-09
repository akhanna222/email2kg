#!/bin/bash

# Quick SSL Diagnostics - Find why SSL_ERROR_SYSCALL occurs
# This checks the actual container configuration

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔍 SSL Error Diagnostics"
echo "========================"
echo ""

echo "1️⃣ Checking if frontend container is running..."
if docker ps --format '{{.Names}}' | grep -q "email2kg-frontend"; then
    echo -e "${GREEN}✅ Frontend container is running${NC}"
else
    echo -e "${RED}❌ Frontend container is NOT running${NC}"
    echo "Start it: sudo docker compose up -d frontend"
    exit 1
fi
echo ""

echo "2️⃣ Checking SSL certificates in HOST (project directory)..."
if [ -f "ssl/certificate.crt" ] && [ -f "ssl/private.key" ]; then
    echo -e "${GREEN}✅ Certificates exist on host${NC}"
    ls -lh ssl/
else
    echo -e "${RED}❌ Certificates missing on host${NC}"
    echo "Copy them: sudo ./scripts/deployment/fix-ssl-missing.sh"
    exit 1
fi
echo ""

echo "3️⃣ Checking if SSL certificates are mounted in CONTAINER..."
if docker exec email2kg-frontend test -f /etc/nginx/ssl/certificate.crt 2>/dev/null; then
    echo -e "${GREEN}✅ certificate.crt exists in container${NC}"
    docker exec email2kg-frontend ls -lh /etc/nginx/ssl/
else
    echo -e "${RED}❌ SSL certificates NOT mounted in container${NC}"
    echo ""
    echo "This means docker-compose.yml volume mount is not working."
    echo "Need to restart containers with proper mount."
fi
echo ""

echo "4️⃣ Checking nginx configuration in CONTAINER..."
if docker exec email2kg-frontend cat /etc/nginx/conf.d/default.conf 2>/dev/null | grep -q "listen 443 ssl"; then
    echo -e "${GREEN}✅ Nginx configured for SSL (listen 443 ssl)${NC}"
    docker exec email2kg-frontend cat /etc/nginx/conf.d/default.conf | grep -E "listen.*443"
else
    echo -e "${RED}❌ Nginx NOT configured for SSL in container${NC}"
    echo ""
    echo "Container has wrong nginx config. Need to rebuild."
fi
echo ""

echo "5️⃣ Checking if port 443 is listening..."
if docker exec email2kg-frontend sh -c "command -v netstat && netstat -tlnp | grep :443" 2>/dev/null; then
    echo -e "${GREEN}✅ Port 443 is listening inside container${NC}"
elif docker exec email2kg-frontend sh -c "command -v ss && ss -tlnp | grep :443" 2>/dev/null; then
    echo -e "${GREEN}✅ Port 443 is listening inside container${NC}"
else
    echo -e "${RED}❌ Port 443 is NOT listening inside container${NC}"
    echo "This means nginx is not configured for SSL or has errors."
fi
echo ""

echo "6️⃣ Checking nginx error logs..."
echo "Recent nginx errors:"
docker exec email2kg-frontend cat /var/log/nginx/error.log 2>/dev/null | tail -10 || echo "(No error log or errors found)"
echo ""

echo "7️⃣ Testing nginx configuration syntax..."
if docker exec email2kg-frontend nginx -t 2>&1 | grep -q "successful"; then
    echo -e "${GREEN}✅ Nginx config syntax is valid${NC}"
else
    echo -e "${RED}❌ Nginx config has syntax errors${NC}"
    docker exec email2kg-frontend nginx -t 2>&1
fi
echo ""

echo "=================================================="
echo "Summary & Fix"
echo "=================================================="
echo ""

# Determine the issue
HAS_HOST_CERTS=false
[ -f "ssl/certificate.crt" ] && HAS_HOST_CERTS=true

HAS_CONTAINER_CERTS=false
docker exec email2kg-frontend test -f /etc/nginx/ssl/certificate.crt 2>/dev/null && HAS_CONTAINER_CERTS=true

HAS_SSL_CONFIG=false
docker exec email2kg-frontend cat /etc/nginx/conf.d/default.conf 2>/dev/null | grep -q "listen 443 ssl" && HAS_SSL_CONFIG=true

if [ "$HAS_HOST_CERTS" = false ]; then
    echo -e "${RED}🔴 ISSUE: SSL certificates missing from host${NC}"
    echo ""
    echo "FIX:"
    echo "  sudo ./scripts/deployment/fix-ssl-missing.sh"

elif [ "$HAS_CONTAINER_CERTS" = false ]; then
    echo -e "${RED}🔴 ISSUE: SSL certificates not mounted in container${NC}"
    echo ""
    echo "The ssl/ directory exists on host but isn't mounted in the container."
    echo ""
    echo "FIX:"
    echo "  # Stop containers"
    echo "  sudo docker compose down"
    echo ""
    echo "  # Verify docker-compose.yml has this under frontend:"
    echo "  #   volumes:"
    echo "  #     - ./ssl:/etc/nginx/ssl:ro"
    echo ""
    echo "  # Start containers"
    echo "  sudo docker compose up -d"

elif [ "$HAS_SSL_CONFIG" = false ]; then
    echo -e "${RED}🔴 ISSUE: Nginx config in container doesn't have SSL${NC}"
    echo ""
    echo "The container was built before nginx.conf had SSL configuration."
    echo ""
    echo "FIX:"
    echo "  # Rebuild frontend with correct nginx.conf"
    echo "  sudo docker compose down"
    echo "  sudo docker compose build --no-cache frontend"
    echo "  sudo docker compose up -d"

else
    echo -e "${YELLOW}🟡 Configuration looks correct, but SSL not working${NC}"
    echo ""
    echo "Try restarting nginx inside the container:"
    echo "  sudo docker compose restart frontend"
    echo ""
    echo "Or check the detailed error logs above."
fi

echo ""
