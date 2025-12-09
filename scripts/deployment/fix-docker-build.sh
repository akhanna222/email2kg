#!/bin/bash

# Fix Docker Build Cache Corruption
# Clears cache and rebuilds all containers from scratch

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
echo "Fix Docker Build Issues"
echo -e "==================================================${NC}"
echo ""

# Navigate to project directory
cd /home/ubuntu/email2kg || cd ~/email2kg || { echo "Cannot find project directory"; exit 1; }

echo -e "${YELLOW}📋 Step 1: Stopping all containers${NC}"
echo ""

docker compose down -v 2>/dev/null || docker-compose down -v 2>/dev/null || true
echo -e "${GREEN}✅ Containers stopped${NC}"
echo ""

echo -e "${YELLOW}📋 Step 2: Removing old images${NC}"
echo ""

# Remove project images
docker rmi email2kg-backend email2kg-frontend email2kg-celery_worker 2>/dev/null || true
echo -e "${GREEN}✅ Old images removed${NC}"
echo ""

echo -e "${YELLOW}📋 Step 3: Clearing Docker build cache${NC}"
echo ""

docker builder prune -af
echo -e "${GREEN}✅ Build cache cleared${NC}"
echo ""

echo -e "${YELLOW}📋 Step 4: Pruning dangling images${NC}"
echo ""

docker image prune -f
echo -e "${GREEN}✅ Dangling images pruned${NC}"
echo ""

echo -e "${YELLOW}📋 Step 5: Verifying SSL certificates exist${NC}"
echo ""

if [ -f "ssl/certificate.crt" ] && [ -f "ssl/private.key" ]; then
    echo -e "${GREEN}✅ SSL certificates exist${NC}"
    ls -lh ssl/
else
    echo -e "${RED}❌ SSL certificates missing${NC}"
    echo ""
    echo "Copying certificates from Let's Encrypt..."
    mkdir -p ssl
    cp /etc/letsencrypt/live/agenticrag360.com/fullchain.pem ssl/certificate.crt
    cp /etc/letsencrypt/live/agenticrag360.com/privkey.pem ssl/private.key
    chmod 644 ssl/certificate.crt
    chmod 600 ssl/private.key
    chown ubuntu:ubuntu ssl/* 2>/dev/null || chown $SUDO_USER:$SUDO_USER ssl/* 2>/dev/null || true
    echo -e "${GREEN}✅ Certificates copied${NC}"
fi
echo ""

echo -e "${YELLOW}📋 Step 6: Building containers from scratch (no cache)${NC}"
echo ""
echo "This may take 2-3 minutes..."
echo ""

docker compose build --no-cache --progress=plain
echo -e "${GREEN}✅ Containers built successfully${NC}"
echo ""

echo -e "${YELLOW}📋 Step 7: Starting services${NC}"
echo ""

docker compose up -d
echo -e "${GREEN}✅ Services started${NC}"
echo ""

echo "Waiting 30 seconds for services to initialize..."
sleep 30
echo ""

echo -e "${YELLOW}📋 Step 8: Checking container status${NC}"
echo ""

docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep email2kg
echo ""

echo -e "${YELLOW}📋 Step 9: Testing HTTPS${NC}"
echo ""

# Test locally
if curl -k -s -o /dev/null -w "%{http_code}" https://localhost/health | grep -q "200"; then
    echo -e "${GREEN}✅ HTTPS works locally!${NC}"
    echo "Response: $(curl -k -s https://localhost/health)"
else
    echo -e "${RED}⚠️  HTTPS test failed${NC}"
    echo "Checking frontend logs..."
    docker compose logs frontend --tail=20
fi
echo ""

echo -e "${BLUE}=================================================="
echo "✅ Docker Build Fixed!"
echo -e "==================================================${NC}"
echo ""

echo -e "${GREEN}📝 Services Status:${NC}"
docker compose ps
echo ""

echo -e "${BLUE}🧪 Test Commands:${NC}"
echo ""
echo "  # Test locally:"
echo "  curl -k https://localhost/health"
echo ""
echo "  # Test externally (requires port 443 open in security group):"
echo "  curl https://agenticrag360.com/health"
echo ""
echo "  # View logs:"
echo "  sudo docker compose logs -f"
echo ""

echo -e "${YELLOW}⚠️  If external HTTPS still doesn't work:${NC}"
echo "  Make sure port 443 is open in AWS Security Group"
echo ""
