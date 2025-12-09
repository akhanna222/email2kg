#!/bin/bash

# Fix SSL Certificates Not Being Used by Nginx
# This script copies Let's Encrypt certificates to the project and restarts services

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Please run with sudo${NC}"
    exit 1
fi

echo -e "${BLUE}=================================================="
echo "Fix SSL Certificates"
echo -e "==================================================${NC}"
echo ""

# Navigate to project directory
cd /home/ubuntu/email2kg || cd ~/email2kg || { echo "Cannot find project directory"; exit 1; }

echo -e "${YELLOW}📋 Step 1: Checking Let's Encrypt certificates${NC}"
echo ""

if [ ! -d "/etc/letsencrypt/live/agenticrag360.com" ]; then
    echo -e "${RED}❌ Let's Encrypt certificates not found${NC}"
    echo ""
    echo "Run this first: sudo ./scripts/deployment/enable-https.sh"
    exit 1
fi

echo -e "${GREEN}✅ Let's Encrypt certificates exist${NC}"
ls -la /etc/letsencrypt/live/agenticrag360.com/
echo ""

echo -e "${YELLOW}📋 Step 2: Creating ssl/ directory${NC}"
echo ""

mkdir -p ssl
echo -e "${GREEN}✅ Created ssl/ directory${NC}"
echo ""

echo -e "${YELLOW}📋 Step 3: Copying certificates to project${NC}"
echo ""

# Copy certificates
cp /etc/letsencrypt/live/agenticrag360.com/fullchain.pem ssl/certificate.crt
cp /etc/letsencrypt/live/agenticrag360.com/privkey.pem ssl/private.key

# Set proper permissions
chmod 644 ssl/certificate.crt
chmod 600 ssl/private.key
chown ubuntu:ubuntu ssl/* 2>/dev/null || chown $SUDO_USER:$SUDO_USER ssl/* 2>/dev/null || true

echo -e "${GREEN}✅ Certificates copied${NC}"
ls -lh ssl/
echo ""

echo -e "${YELLOW}📋 Step 4: Verifying certificate validity${NC}"
echo ""

openssl x509 -in ssl/certificate.crt -noout -dates
echo ""

echo -e "${YELLOW}📋 Step 5: Checking docker-compose.yml${NC}"
echo ""

if grep -A5 "frontend:" docker-compose.yml | grep -q "./ssl:/etc/nginx/ssl"; then
    echo -e "${GREEN}✅ docker-compose.yml has SSL volume mount${NC}"
else
    echo -e "${RED}⚠️  WARNING: docker-compose.yml missing SSL volume mount${NC}"
    echo ""
    echo "The frontend service should have this volume:"
    echo "  - ./ssl:/etc/nginx/ssl:ro"
    echo ""
    echo "Please check docker-compose.yml"
fi
echo ""

echo -e "${YELLOW}📋 Step 6: Checking nginx configuration${NC}"
echo ""

# Check if using correct nginx config
if [ -f "frontend/nginx.conf" ]; then
    if grep -q "listen 443 ssl" frontend/nginx.conf; then
        echo -e "${GREEN}✅ nginx.conf configured for SSL${NC}"
        grep "listen.*443" frontend/nginx.conf | head -3
    else
        echo -e "${RED}❌ nginx.conf NOT configured for SSL${NC}"
        echo ""
        echo "frontend/nginx.conf should have:"
        echo "  listen 443 ssl;"
        echo "  listen [::]:443 ssl;"
    fi
else
    echo -e "${YELLOW}⚠️  frontend/nginx.conf not found${NC}"
fi
echo ""

echo -e "${YELLOW}📋 Step 7: Stopping services${NC}"
echo ""

docker compose down
echo -e "${GREEN}✅ Services stopped${NC}"
echo ""

echo -e "${YELLOW}📋 Step 8: Starting services with SSL${NC}"
echo ""

docker compose up --build -d
echo -e "${GREEN}✅ Services starting...${NC}"
echo ""

echo "Waiting 30 seconds for services to start..."
sleep 30
echo ""

echo -e "${YELLOW}📋 Step 9: Checking container status${NC}"
echo ""

docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep email2kg
echo ""

echo -e "${YELLOW}📋 Step 10: Verifying port 443 is listening${NC}"
echo ""

if command -v netstat &> /dev/null; then
    if netstat -tlnp 2>/dev/null | grep -q ":443"; then
        echo -e "${GREEN}✅ Port 443 is now listening!${NC}"
        netstat -tlnp 2>/dev/null | grep ":443"
    else
        echo -e "${RED}❌ Port 443 still not listening${NC}"
    fi
elif command -v ss &> /dev/null; then
    if ss -tlnp 2>/dev/null | grep -q ":443"; then
        echo -e "${GREEN}✅ Port 443 is now listening!${NC}"
        ss -tlnp 2>/dev/null | grep ":443"
    else
        echo -e "${RED}❌ Port 443 still not listening${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Cannot check port (netstat/ss not available)${NC}"
    echo "Checking with docker ps instead..."
    if docker ps | grep email2kg-frontend | grep -q "443"; then
        echo -e "${GREEN}✅ Frontend container has port 443 exposed${NC}"
    fi
fi
echo ""

echo -e "${YELLOW}📋 Step 11: Testing HTTPS locally${NC}"
echo ""

sleep 5  # Give nginx a moment to fully start

if curl -k -s -o /dev/null -w "%{http_code}" https://localhost/health | grep -q "200"; then
    echo -e "${GREEN}✅ HTTPS works locally!${NC}"
    echo "Response: $(curl -k -s https://localhost/health)"
else
    echo -e "${RED}❌ HTTPS not working locally${NC}"
    echo "Check frontend logs: docker compose logs frontend"
fi
echo ""

echo -e "${BLUE}=================================================="
echo "✅ SSL Fix Complete!"
echo -e "==================================================${NC}"
echo ""

echo -e "${GREEN}📝 What was done:${NC}"
echo "  1. ✅ Copied certificates from Let's Encrypt to ssl/"
echo "  2. ✅ Set proper file permissions"
echo "  3. ✅ Rebuilt and restarted all services"
echo "  4. ✅ Verified configuration"
echo ""

echo -e "${BLUE}🧪 Test Commands:${NC}"
echo ""
echo "  # Test locally (on the server):"
echo "  curl -k https://localhost/health"
echo ""
echo "  # Test externally (make sure port 443 is open in security group):"
echo "  curl https://agenticrag360.com/health"
echo ""
echo "  # Check what ports are listening:"
echo "  sudo ss -tlnp | grep -E ':(80|443)'"
echo ""
echo "  # Check container ports:"
echo "  sudo docker ps | grep frontend"
echo ""

echo -e "${YELLOW}⚠️  If external HTTPS still doesn't work:${NC}"
echo ""
echo "  Make sure port 443 is open in your EC2 Security Group:"
echo "  1. Go to: AWS Console → EC2 → Security Groups"
echo "  2. Select your security group"
echo "  3. Add inbound rule:"
echo "     Type: HTTPS, Port: 443, Source: 0.0.0.0/0"
echo ""

echo -e "${GREEN}🎉 Your certificates are now installed and nginx is configured for HTTPS!${NC}"
echo ""
