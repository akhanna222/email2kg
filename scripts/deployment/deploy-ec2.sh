#!/bin/bash

# ============================================
# Email2KG - EC2 Quick Deploy Script
# ============================================
# Automates deployment on EC2 instance

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        Email2KG - EC2 Quick Deploy Script                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Get EC2 public IP
echo -e "${BLUE}[1/6] Detecting EC2 public IP...${NC}"
EC2_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || curl -s ifconfig.me)
echo -e "${GREEN}✓ Detected IP: ${EC2_IP}${NC}"

# Check for .env file
echo -e "${BLUE}[2/6] Checking environment configuration...${NC}"
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠ .env file not found. Creating from template...${NC}"
    if [ -f .env.production.example ]; then
        cp .env.production.example .env
    else
        cp .env.example .env
    fi
    sed -i "s/^PUBLIC_DOMAIN=.*/PUBLIC_DOMAIN=${EC2_IP}/" .env
    sed -i "s/^PUBLIC_PROTOCOL=.*/PUBLIC_PROTOCOL=https/" .env
    echo -e "${GREEN}✓ Created .env file${NC}"
    echo ""
    echo -e "${YELLOW}⚠ Please configure these in .env:${NC}"
    echo -e "  - SECRET_KEY (generate: openssl rand -hex 32)"
    echo -e "  - JWT_SECRET_KEY (generate: openssl rand -hex 32)"
    echo -e "  - DB_PASSWORD"
    echo -e "  - OPENAI_API_KEY"
    echo -e "  - GOOGLE_CLIENT_ID"
    echo -e "  - GOOGLE_CLIENT_SECRET"
    echo ""
    echo -e "Edit with: ${BLUE}nano .env${NC}"
    exit 0
fi

# Build services
echo -e "${BLUE}[3/6] Building Docker images...${NC}"
docker-compose build

# Start services
echo -e "${BLUE}[4/6] Starting services...${NC}"
docker-compose up -d

# Wait for health
echo -e "${BLUE}[5/6] Waiting for services...${NC}"
sleep 15

# Display results
echo -e "${BLUE}[6/6] Checking status...${NC}"
docker-compose ps

DOMAIN=$(grep "^PUBLIC_DOMAIN=" .env | cut -d '=' -f2)
PROTOCOL=$(grep "^PUBLIC_PROTOCOL=" .env | cut -d '=' -f2)

echo ""
echo -e "${GREEN}✓ Deployment Complete!${NC}"
echo ""
echo -e "Application URL: ${GREEN}${PROTOCOL}://${DOMAIN}${NC}"
echo -e "OAuth Callback:  ${GREEN}${PROTOCOL}://${DOMAIN}/api/auth/google/callback${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "1. Update Google OAuth: ${BLUE}https://console.cloud.google.com/apis/credentials${NC}"
if [[ ! "$DOMAIN" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "2. Update Namecheap DNS: @ and www → ${EC2_IP}"
fi
echo -e ""
echo -e "View logs: ${GREEN}docker-compose logs -f${NC}"
