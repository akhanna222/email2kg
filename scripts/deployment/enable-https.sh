#!/bin/bash

# Enable HTTPS for Email2KG - Quick Setup Script
# This script provides a simplified interface for SSL setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Detect if running as root
if [ "$EUID" -eq 0 ]; then
    SUDO=""
else
    SUDO="sudo"
fi

echo "=================================================="
echo -e "${BLUE}📦 Email2KG HTTPS Quick Setup${NC}"
echo "=================================================="
echo ""
echo "This script will:"
echo "  1. Verify prerequisites"
echo "  2. Obtain free SSL certificate from Let's Encrypt"
echo "  3. Configure HTTPS"
echo "  4. Set up auto-renewal"
echo ""

# ============================================
# PREREQUISITE CHECKS
# ============================================

echo -e "${YELLOW}📋 Step 1: Checking Prerequisites${NC}"
echo ""

# Check if in correct directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Error: Please run this script from the email2kg directory${NC}"
    echo ""
    echo "Run: cd ~/email2kg && sudo ./scripts/deployment/enable-https.sh"
    exit 1
fi
echo -e "${GREEN}✅${NC} Running from correct directory"

# Check if Docker is running
if ! $SUDO docker ps &> /dev/null; then
    echo -e "${RED}❌ Error: Docker is not running${NC}"
    echo ""
    echo "Start Docker:"
    echo "  sudo systemctl start docker"
    exit 1
fi
echo -e "${GREEN}✅${NC} Docker is running"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Warning: .env file not found${NC}"
    echo ""
    echo "Please create .env file first:"
    echo "  cp .env.production.example .env"
    echo "  nano .env  # Update with your credentials"
    exit 1
fi
echo -e "${GREEN}✅${NC} .env file exists"

# Extract domain from .env
if grep -q "PUBLIC_DOMAIN" .env; then
    DOMAIN=$(grep "PUBLIC_DOMAIN" .env | cut -d'=' -f2 | tr -d ' "')
    echo -e "${GREEN}✅${NC} Domain configured: $DOMAIN"
else
    echo -e "${RED}❌ Error: PUBLIC_DOMAIN not set in .env${NC}"
    echo ""
    echo "Add to .env:"
    echo "  PUBLIC_DOMAIN=agenticrag360.com"
    exit 1
fi

# Check DNS resolution
echo ""
echo -e "${YELLOW}📋 Step 2: Verifying DNS Configuration${NC}"
echo ""

DNS_IP=$(nslookup $DOMAIN 8.8.8.8 | awk '/^Address: / { if (NR>1) print $2 }' | head -1)
if [ -z "$DNS_IP" ]; then
    echo -e "${RED}❌ Error: Cannot resolve domain $DOMAIN${NC}"
    echo ""
    echo "Please ensure:"
    echo "  1. Domain is registered"
    echo "  2. DNS A record points to this server's IP"
    echo "  3. DNS has propagated (can take up to 48 hours)"
    echo ""
    echo "Check DNS: nslookup $DOMAIN"
    exit 1
fi

echo -e "${GREEN}✅${NC} DNS resolves to: $DNS_IP"

# Get server's public IP
SERVER_IP=$(curl -s ifconfig.me || curl -s icanhazip.com || echo "unknown")
echo "   Server IP: $SERVER_IP"

if [ "$DNS_IP" != "$SERVER_IP" ]; then
    echo -e "${YELLOW}⚠️  Warning: DNS IP ($DNS_IP) doesn't match server IP ($SERVER_IP)${NC}"
    echo ""
    echo "This might cause issues. Continue anyway? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Exiting. Please update your DNS records first."
        exit 1
    fi
fi

# Check if port 80 is accessible
echo ""
echo -e "${YELLOW}📋 Step 3: Checking Port Accessibility${NC}"
echo ""

# Check if services are running
if $SUDO docker ps | grep -q "email2kg-frontend"; then
    echo -e "${GREEN}✅${NC} Services are running"

    # Test if port 80 is accessible
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
        echo -e "${GREEN}✅${NC} Port 80 is accessible (HTTP code: $HTTP_CODE)"
    else
        echo -e "${RED}❌ Error: Port 80 not accessible (HTTP code: $HTTP_CODE)${NC}"
        echo ""
        echo "Check EC2 security group allows port 80 from 0.0.0.0/0"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  Services not running - will start them for verification${NC}"
fi

# ============================================
# SSL CERTIFICATE SETUP
# ============================================

echo ""
echo "=================================================="
echo -e "${YELLOW}📋 Step 4: SSL Certificate Setup${NC}"
echo "=================================================="
echo ""
echo "This will:"
echo "  - Stop current services"
echo "  - Obtain SSL certificate from Let's Encrypt (free)"
echo "  - Configure HTTPS"
echo "  - Restart services with SSL enabled"
echo ""
echo -e "${YELLOW}⚠️  Services will be down for ~2-3 minutes${NC}"
echo ""
echo "Domain: $DOMAIN"
echo "Provider: Let's Encrypt"
echo "Cost: Free"
echo "Validity: 90 days (auto-renews)"
echo ""
echo "Continue? (y/n)"
read -r response

if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "Setup cancelled."
    exit 0
fi

echo ""
echo -e "${BLUE}🚀 Starting SSL setup...${NC}"
echo ""

# Call the main setup script
if [ -f "scripts/deployment/setup-letsencrypt.sh" ]; then
    chmod +x scripts/deployment/setup-letsencrypt.sh
    $SUDO ./scripts/deployment/setup-letsencrypt.sh
else
    echo -e "${RED}❌ Error: setup-letsencrypt.sh not found${NC}"
    echo ""
    echo "Please ensure you have the latest code:"
    echo "  git pull origin $(git branch --show-current)"
    exit 1
fi

# ============================================
# POST-SETUP VERIFICATION
# ============================================

echo ""
echo "=================================================="
echo -e "${YELLOW}📋 Step 5: Verifying HTTPS Setup${NC}"
echo "=================================================="
echo ""

# Wait for services to start
echo "Waiting for services to start..."
sleep 15

# Test HTTPS
echo ""
echo "Testing HTTPS endpoint..."
HTTPS_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN/health 2>/dev/null || echo "000")

if [ "$HTTPS_CODE" = "200" ]; then
    echo -e "${GREEN}✅ HTTPS is working! (HTTP code: 200)${NC}"
else
    echo -e "${RED}⚠️  HTTPS returned code: $HTTPS_CODE${NC}"
    echo ""
    echo "Checking SSL certificate..."
    if [ -f "ssl/certificate.crt" ]; then
        echo -e "${GREEN}✅${NC} Certificate file exists"
    else
        echo -e "${RED}❌${NC} Certificate file missing"
    fi
fi

# Test HTTP redirect
echo ""
echo "Testing HTTP to HTTPS redirect..."
HTTP_REDIRECT=$(curl -s -I http://$DOMAIN/ | grep -i "location:" | head -1)
if echo "$HTTP_REDIRECT" | grep -q "https://"; then
    echo -e "${GREEN}✅ HTTP redirects to HTTPS${NC}"
else
    echo -e "${YELLOW}⚠️  HTTP redirect: $HTTP_REDIRECT${NC}"
fi

# Check services
echo ""
echo "Checking service status..."
$SUDO docker ps --format "table {{.Names}}\t{{.Status}}" | grep email2kg || true

# ============================================
# FINAL INSTRUCTIONS
# ============================================

echo ""
echo "=================================================="
echo -e "${GREEN}✅ HTTPS Setup Complete!${NC}"
echo "=================================================="
echo ""
echo -e "${BLUE}🌐 Your application is now available at:${NC}"
echo "   https://$DOMAIN"
echo ""
echo -e "${BLUE}📝 Important Next Steps:${NC}"
echo ""
echo "1. Update Google OAuth Redirect URI:"
echo "   a. Go to: https://console.cloud.google.com/apis/credentials"
echo "   b. Click your OAuth 2.0 Client ID"
echo "   c. Update 'Authorized redirect URIs' to:"
echo "      https://$DOMAIN/api/auth/google/callback"
echo "   d. Remove any HTTP redirect URIs"
echo "   e. Click 'Save'"
echo ""
echo "2. Update .env file:"
echo "   nano .env"
echo ""
echo "   Update these lines:"
echo "   PUBLIC_PROTOCOL=https"
echo "   GOOGLE_REDIRECT_URI=https://$DOMAIN/api/auth/google/callback"
echo ""
echo "   Save and exit (Ctrl+X, Y, Enter)"
echo ""
echo "3. Restart backend to apply changes:"
echo "   sudo docker compose restart backend"
echo ""
echo "4. Test your application:"
echo "   - Open: https://$DOMAIN"
echo "   - Check for padlock icon in browser"
echo "   - Try to login/signup"
echo ""
echo -e "${BLUE}🔒 SSL Certificate Info:${NC}"
echo "   - Provider: Let's Encrypt"
echo "   - Valid for: 90 days"
echo "   - Auto-renewal: Enabled"
echo "   - Location: ~/email2kg/ssl/"
echo ""
echo -e "${BLUE}📊 Verification Commands:${NC}"
echo "   # Test HTTPS"
echo "   curl https://$DOMAIN/health"
echo ""
echo "   # Check certificate expiration"
echo "   sudo certbot certificates"
echo ""
echo "   # View service logs"
echo "   sudo docker compose logs -f"
echo ""
echo "=================================================="
echo ""
echo -e "${GREEN}🎉 Setup complete! Your site is now secure with HTTPS.${NC}"
echo ""
