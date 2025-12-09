#!/bin/bash

# Enable SSL Now - One command to fix all SSL issues
# Copies certificates, verifies config, rebuilds if needed

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Please run with sudo${NC}"
    exit 1
fi

echo -e "${BLUE}=================================================="
echo "Enable SSL Now - Quick Fix"
echo -e "==================================================${NC}"
echo ""

cd /home/ubuntu/email2kg || cd ~/email2kg || exit 1

echo -e "${YELLOW}Step 1/6: Copying SSL certificates${NC}"
mkdir -p ssl
if [ -f "/etc/letsencrypt/live/agenticrag360.com/fullchain.pem" ]; then
    cp /etc/letsencrypt/live/agenticrag360.com/fullchain.pem ssl/certificate.crt
    cp /etc/letsencrypt/live/agenticrag360.com/privkey.pem ssl/private.key
    chmod 644 ssl/certificate.crt
    chmod 600 ssl/private.key
    chown ubuntu:ubuntu ssl/* 2>/dev/null || chown $SUDO_USER:$SUDO_USER ssl/* 2>/dev/null || true
    echo -e "${GREEN}✅ Certificates copied${NC}"
else
    echo -e "${RED}❌ Let's Encrypt certificates not found${NC}"
    echo "Run: sudo ./scripts/deployment/enable-https.sh first"
    exit 1
fi
echo ""

echo -e "${YELLOW}Step 2/6: Verifying certificates${NC}"
if [ -f "ssl/certificate.crt" ] && [ -f "ssl/private.key" ]; then
    echo -e "${GREEN}✅ Certificates exist${NC}"
    openssl x509 -in ssl/certificate.crt -noout -dates
else
    echo -e "${RED}❌ Certificates missing${NC}"
    exit 1
fi
echo ""

echo -e "${YELLOW}Step 3/6: Stopping containers${NC}"
docker compose down
echo -e "${GREEN}✅ Containers stopped${NC}"
echo ""

echo -e "${YELLOW}Step 4/6: Rebuilding frontend (no cache)${NC}"
echo "This ensures the container has the correct SSL configuration..."
docker compose build --no-cache frontend
echo -e "${GREEN}✅ Frontend rebuilt${NC}"
echo ""

echo -e "${YELLOW}Step 5/6: Starting all services${NC}"
docker compose up -d
echo ""
echo "Waiting 30 seconds for services to start..."
sleep 30
echo -e "${GREEN}✅ Services started${NC}"
echo ""

echo -e "${YELLOW}Step 6/6: Verifying SSL works${NC}"
echo ""

# Check containers
echo "Container status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep email2kg
echo ""

# Check if certs are mounted
echo "Checking if SSL certs are in container..."
if docker exec email2kg-frontend test -f /etc/nginx/ssl/certificate.crt; then
    echo -e "${GREEN}✅ SSL certificates mounted in container${NC}"
else
    echo -e "${RED}❌ SSL certificates NOT in container${NC}"
    exit 1
fi
echo ""

# Check nginx config
echo "Checking nginx SSL config..."
if docker exec email2kg-frontend cat /etc/nginx/conf.d/default.conf | grep -q "listen 443 ssl"; then
    echo -e "${GREEN}✅ Nginx configured for SSL${NC}"
else
    echo -e "${RED}❌ Nginx NOT configured for SSL${NC}"
    exit 1
fi
echo ""

# Test HTTPS locally
echo "Testing HTTPS locally..."
sleep 5
HTTP_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" https://localhost/health 2>&1 || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ HTTPS works! (HTTP code: 200)${NC}"
    echo "Response: $(curl -k -s https://localhost/health)"
else
    echo -e "${RED}❌ HTTPS not working (HTTP code: $HTTP_CODE)${NC}"
    echo ""
    echo "Checking logs..."
    docker compose logs frontend --tail=20
    exit 1
fi
echo ""

echo -e "${BLUE}=================================================="
echo "✅ SSL Enabled Successfully!"
echo -e "==================================================${NC}"
echo ""

echo -e "${GREEN}🎉 HTTPS is now working!${NC}"
echo ""
echo "Test commands:"
echo "  # Test locally:"
echo "  curl -k https://localhost/health"
echo ""
echo "  # Test externally:"
echo "  curl https://agenticrag360.com/health"
echo ""
echo "  # View in browser:"
echo "  https://agenticrag360.com"
echo ""

if ! curl -s -o /dev/null -w "%{http_code}" https://agenticrag360.com/health 2>&1 | grep -q "200"; then
    echo -e "${YELLOW}⚠️  External HTTPS test:${NC}"
    echo "External test failed. This is usually because:"
    echo "  - Port 443 not open in EC2 Security Group (you said you added it ✅)"
    echo "  - DNS not propagated yet (wait 5 minutes)"
    echo ""
    echo "Wait a moment and test again:"
    echo "  curl https://agenticrag360.com/health"
fi

echo ""
echo -e "${GREEN}All done! 🔒${NC}"
echo ""
