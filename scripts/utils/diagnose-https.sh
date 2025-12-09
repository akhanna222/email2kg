#!/bin/bash

# HTTPS Diagnostics Script
# Diagnoses why HTTPS is not working

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=================================================="
echo "HTTPS Diagnostics"
echo -e "==================================================${NC}"
echo ""

# Check 1: Is frontend container running?
echo -e "${YELLOW}📋 Check 1: Frontend Container Status${NC}"
if docker ps --format '{{.Names}}' | grep -q "email2kg-frontend"; then
    echo -e "${GREEN}✅ Frontend container is running${NC}"
    docker ps --filter name=email2kg-frontend --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
else
    echo -e "${RED}❌ Frontend container is not running${NC}"
    echo "Start it with: sudo docker compose up -d frontend"
    exit 1
fi
echo ""

# Check 2: Is port 443 listening?
echo -e "${YELLOW}📋 Check 2: Port 443 Listening${NC}"
if sudo netstat -tlnp | grep -q ":443"; then
    echo -e "${GREEN}✅ Port 443 is listening${NC}"
    sudo netstat -tlnp | grep ":443"
else
    echo -e "${RED}❌ Port 443 is NOT listening${NC}"
    echo "This means nginx inside the container is not configured for HTTPS"
fi
echo ""

# Check 3: SSL certificates exist?
echo -e "${YELLOW}📋 Check 3: SSL Certificates${NC}"
if [ -f "ssl/certificate.crt" ] && [ -f "ssl/private.key" ]; then
    echo -e "${GREEN}✅ SSL certificates exist in ssl/ directory${NC}"
    ls -lh ssl/
    echo ""
    echo "Certificate validity:"
    openssl x509 -in ssl/certificate.crt -noout -dates 2>/dev/null || echo "Could not read certificate"
else
    echo -e "${RED}❌ SSL certificates are MISSING${NC}"
    echo ""
    echo "Location checked: $(pwd)/ssl/"
    echo ""
    echo "Fix: Copy certificates from Let's Encrypt:"
    echo "  sudo mkdir -p ssl"
    echo "  sudo cp /etc/letsencrypt/live/agenticrag360.com/fullchain.pem ssl/certificate.crt"
    echo "  sudo cp /etc/letsencrypt/live/agenticrag360.com/privkey.pem ssl/private.key"
    echo "  sudo chmod 644 ssl/certificate.crt"
    echo "  sudo chmod 600 ssl/private.key"
    echo "  sudo chown \$USER:\$USER ssl/*"
    echo "  sudo docker compose restart frontend"
fi
echo ""

# Check 4: Are certificates mounted in container?
echo -e "${YELLOW}📋 Check 4: Certificates Mounted in Container${NC}"
if docker exec email2kg-frontend ls /etc/nginx/ssl/ &>/dev/null; then
    echo -e "${GREEN}✅ /etc/nginx/ssl/ directory exists in container${NC}"
    docker exec email2kg-frontend ls -la /etc/nginx/ssl/
else
    echo -e "${RED}❌ SSL directory not accessible in container${NC}"
fi
echo ""

# Check 5: Nginx configuration
echo -e "${YELLOW}📋 Check 5: Nginx Configuration${NC}"
echo "Active nginx configuration in container:"
docker exec email2kg-frontend cat /etc/nginx/conf.d/default.conf | grep -E "(listen|ssl|server_name)" | head -20
echo ""

# Check 6: EC2 Security Group (if applicable)
echo -e "${YELLOW}📋 Check 6: External Port Access${NC}"
echo "Testing if port 443 is accessible from outside..."
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s icanhazip.com 2>/dev/null)
if [ -n "$PUBLIC_IP" ]; then
    echo "Server public IP: $PUBLIC_IP"
    echo ""
    echo "Testing external access to port 443..."
    timeout 5 bash -c "echo '' | nc -w 3 $PUBLIC_IP 443" &>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Port 443 is accessible from outside${NC}"
    else
        echo -e "${RED}❌ Port 443 is NOT accessible from outside${NC}"
        echo ""
        echo "Possible issues:"
        echo "  1. EC2 Security Group doesn't allow port 443"
        echo "  2. Firewall (ufw) is blocking port 443"
        echo ""
        echo "To fix EC2 Security Group:"
        echo "  1. Go to EC2 Console → Security Groups"
        echo "  2. Find your instance's security group"
        echo "  3. Add inbound rule:"
        echo "     Type: HTTPS"
        echo "     Protocol: TCP"
        echo "     Port: 443"
        echo "     Source: 0.0.0.0/0"
    fi
else
    echo "Could not determine public IP"
fi
echo ""

# Check 7: Let's Encrypt certificates
echo -e "${YELLOW}📋 Check 7: Let's Encrypt Certificates${NC}"
if [ -d "/etc/letsencrypt/live/agenticrag360.com" ]; then
    echo -e "${GREEN}✅ Let's Encrypt certificates exist${NC}"
    sudo ls -la /etc/letsencrypt/live/agenticrag360.com/
else
    echo -e "${RED}❌ Let's Encrypt certificates not found${NC}"
    echo "Run: sudo ./scripts/deployment/enable-https.sh"
fi
echo ""

# Summary and recommendations
echo -e "${BLUE}=================================================="
echo "Summary & Recommendations"
echo -e "==================================================${NC}"
echo ""

# Determine the issue
HAS_CERTS=false
[ -f "ssl/certificate.crt" ] && HAS_CERTS=true

FRONTEND_RUNNING=false
docker ps --format '{{.Names}}' | grep -q "email2kg-frontend" && FRONTEND_RUNNING=true

PORT_443_LISTENING=false
sudo netstat -tlnp | grep -q ":443" && PORT_443_LISTENING=true

if [ "$HAS_CERTS" = false ]; then
    echo -e "${RED}🔴 ISSUE: SSL certificates are missing${NC}"
    echo ""
    echo "Solution:"
    echo "  1. Check if Let's Encrypt created certificates:"
    echo "     sudo ls /etc/letsencrypt/live/agenticrag360.com/"
    echo ""
    echo "  2. If certificates exist, copy them:"
    echo "     sudo mkdir -p ssl"
    echo "     sudo cp /etc/letsencrypt/live/agenticrag360.com/fullchain.pem ssl/certificate.crt"
    echo "     sudo cp /etc/letsencrypt/live/agenticrag360.com/privkey.pem ssl/private.key"
    echo "     sudo chmod 644 ssl/certificate.crt"
    echo "     sudo chmod 600 ssl/private.key"
    echo "     sudo chown \$USER:\$USER ssl/*"
    echo ""
    echo "  3. If certificates don't exist, run SSL setup:"
    echo "     sudo ./scripts/deployment/enable-https.sh"
    echo ""
    echo "  4. Restart frontend:"
    echo "     sudo docker compose restart frontend"

elif [ "$PORT_443_LISTENING" = false ]; then
    echo -e "${RED}🔴 ISSUE: Port 443 not listening (nginx not configured for SSL)${NC}"
    echo ""
    echo "Solution:"
    echo "  1. Check nginx config:"
    echo "     docker exec email2kg-frontend cat /etc/nginx/conf.d/default.conf | grep 443"
    echo ""
    echo "  2. Verify SSL volume is mounted:"
    echo "     cat docker-compose.yml | grep -A5 frontend | grep ssl"
    echo ""
    echo "  3. Restart with fresh build:"
    echo "     sudo docker compose down"
    echo "     sudo docker compose up --build -d"

else
    echo -e "${YELLOW}🟡 LIKELY ISSUE: EC2 Security Group blocking port 443${NC}"
    echo ""
    echo "Solution:"
    echo "  1. Go to AWS Console → EC2 → Security Groups"
    echo "  2. Select your instance's security group"
    echo "  3. Inbound rules → Edit inbound rules → Add rule:"
    echo "     - Type: HTTPS"
    echo "     - Protocol: TCP"
    echo "     - Port range: 443"
    echo "     - Source: 0.0.0.0/0"
    echo "  4. Save rules"
    echo ""
    echo "  Test after 30 seconds: curl https://agenticrag360.com/health"
fi

echo ""
echo -e "${BLUE}Quick test commands:${NC}"
echo "  # Local (should work if nginx is configured):"
echo "  curl -k https://localhost/health"
echo ""
echo "  # External (should work if security group allows):"
echo "  curl https://agenticrag360.com/health"
echo ""
