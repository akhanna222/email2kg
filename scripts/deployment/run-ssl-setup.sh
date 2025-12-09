#!/bin/bash

# Quick check and fix for SSL setup
# This ensures you have the latest code before running SSL fix

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}   SSL Setup Validator${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

cd /home/ubuntu/email2kg || cd ~/email2kg || exit 1

echo -e "${YELLOW}Checking if you have the latest code...${NC}"

# Check if nginx.conf has SSL
if grep -q "listen 443 ssl" frontend/nginx.conf; then
    echo -e "${GREEN}✅ nginx.conf has SSL configuration${NC}"
else
    echo -e "${RED}❌ nginx.conf missing SSL configuration${NC}"
    echo ""
    echo "Pulling latest code from repository..."
    git pull origin claude/add-ocr-email-extraction-01E2J9RkrixaT8TUTReBnHiG

    # Check again
    if grep -q "listen 443 ssl" frontend/nginx.conf; then
        echo -e "${GREEN}✅ Updated! nginx.conf now has SSL${NC}"
    else
        echo -e "${RED}❌ Still missing SSL. This shouldn't happen.${NC}"
        echo ""
        echo "Manually check: cat frontend/nginx.conf | grep 443"
        exit 1
    fi
fi
echo ""

# Check if Dockerfile exposes 443
if grep -q "EXPOSE.*443" frontend/Dockerfile; then
    echo -e "${GREEN}✅ Dockerfile exposes port 443${NC}"
else
    echo -e "${RED}❌ Dockerfile doesn't expose port 443${NC}"
    echo ""
    echo "Pulling latest code..."
    git pull origin claude/add-ocr-email-extraction-01E2J9RkrixaT8TUTReBnHiG
fi
echo ""

# Check if SSL certificates exist in Let's Encrypt
if [ -d "/etc/letsencrypt/live/agenticrag360.com" ]; then
    echo -e "${GREEN}✅ Let's Encrypt certificates exist${NC}"
else
    echo -e "${RED}❌ Let's Encrypt certificates not found${NC}"
    echo ""
    echo "You need to obtain SSL certificates first."
    echo "Run: sudo ./scripts/deployment/enable-https.sh"
    exit 1
fi
echo ""

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}   All prerequisites met!${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

echo "Now running the SSL fix script..."
echo ""
sleep 2

# Run the fix script
if [ "$EUID" -ne 0 ]; then
    exec sudo ./scripts/deployment/final-ssl-fix.sh
else
    ./scripts/deployment/final-ssl-fix.sh
fi
