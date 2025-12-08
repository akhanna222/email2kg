#!/bin/bash

# ============================================
# Update Public Domain/IP Script
# ============================================
# Easily update your public domain or IP when it changes
# Usage: ./scripts/utils/update-domain.sh

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        Email2KG - Update Public Domain/IP Tool            ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠ .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file${NC}"
fi

# Get current values
CURRENT_DOMAIN=$(grep "^PUBLIC_DOMAIN=" .env | cut -d '=' -f2 || echo "not set")
CURRENT_PROTOCOL=$(grep "^PUBLIC_PROTOCOL=" .env | cut -d '=' -f2 || echo "not set")

echo -e "${BLUE}Current Configuration:${NC}"
echo -e "  Domain/IP: ${YELLOW}${CURRENT_DOMAIN}${NC}"
echo -e "  Protocol:  ${YELLOW}${CURRENT_PROTOCOL}${NC}"
echo ""

# Prompt for new domain/IP
echo -e "${BLUE}Enter your new domain or IP address:${NC}"
echo -e "${YELLOW}  Examples:${NC}"
echo -e "    - Domain: ${GREEN}yourdomain.com${NC}"
echo -e "    - IP:     ${GREEN}34.245.66.42${NC}"
echo -e "    - Local:  ${GREEN}localhost${NC}"
echo ""
read -p "Domain/IP: " NEW_DOMAIN

if [ -z "$NEW_DOMAIN" ]; then
    echo -e "${RED}✗ Error: Domain/IP cannot be empty${NC}"
    exit 1
fi

# Prompt for protocol
echo ""
echo -e "${BLUE}Select protocol:${NC}"
echo -e "  ${GREEN}1${NC}) HTTPS (recommended for production)"
echo -e "  ${GREEN}2${NC}) HTTP (development only)"
echo ""
read -p "Choice (1 or 2): " PROTOCOL_CHOICE

case $PROTOCOL_CHOICE in
    1)
        NEW_PROTOCOL="https"
        ;;
    2)
        NEW_PROTOCOL="http"
        ;;
    *)
        echo -e "${RED}✗ Invalid choice. Defaulting to https${NC}"
        NEW_PROTOCOL="https"
        ;;
esac

# Update .env file
echo ""
echo -e "${BLUE}Updating .env file...${NC}"

# Check if variables exist and update them, or add them
if grep -q "^PUBLIC_DOMAIN=" .env; then
    sed -i "s|^PUBLIC_DOMAIN=.*|PUBLIC_DOMAIN=$NEW_DOMAIN|" .env
else
    echo "" >> .env
    echo "# Public Domain/IP Configuration" >> .env
    echo "PUBLIC_DOMAIN=$NEW_DOMAIN" >> .env
fi

if grep -q "^PUBLIC_PROTOCOL=" .env; then
    sed -i "s|^PUBLIC_PROTOCOL=.*|PUBLIC_PROTOCOL=$NEW_PROTOCOL|" .env
else
    echo "PUBLIC_PROTOCOL=$NEW_PROTOCOL" >> .env
fi

echo -e "${GREEN}✓ Updated .env file${NC}"

# Show new configuration
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                  Configuration Updated!                    ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}New Configuration:${NC}"
echo -e "  Domain/IP: ${GREEN}${NEW_DOMAIN}${NC}"
echo -e "  Protocol:  ${GREEN}${NEW_PROTOCOL}${NC}"
echo ""
echo -e "${BLUE}URLs:${NC}"
echo -e "  Frontend:      ${GREEN}${NEW_PROTOCOL}://${NEW_DOMAIN}${NC}"
echo -e "  Backend API:   ${GREEN}${NEW_PROTOCOL}://${NEW_DOMAIN}/api${NC}"
echo -e "  OAuth Callback: ${GREEN}${NEW_PROTOCOL}://${NEW_DOMAIN}/api/auth/google/callback${NC}"
echo ""

# Update Google OAuth redirect URI
echo -e "${YELLOW}⚠ Important: Update Google OAuth Redirect URI${NC}"
echo -e "  Go to: ${BLUE}https://console.cloud.google.com/apis/credentials${NC}"
echo -e "  Add this redirect URI: ${GREEN}${NEW_PROTOCOL}://${NEW_DOMAIN}/api/auth/google/callback${NC}"
echo ""

# Restart services
echo -e "${BLUE}Next Steps:${NC}"
echo -e "  1. Restart Docker services:"
echo -e "     ${GREEN}docker-compose down && docker-compose up -d${NC}"
echo ""
echo -e "  2. Or restart backend only:"
echo -e "     ${GREEN}docker-compose restart backend celery_worker${NC}"
echo ""

# Offer to restart now
read -p "$(echo -e ${BLUE}Restart Docker services now? [y/N]:${NC} )" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Restarting services...${NC}"
    docker-compose down
    docker-compose up -d
    echo -e "${GREEN}✓ Services restarted${NC}"
    echo ""
    echo -e "${GREEN}Your application is now running at:${NC}"
    echo -e "  ${GREEN}${NEW_PROTOCOL}://${NEW_DOMAIN}${NC}"
else
    echo -e "${YELLOW}⚠ Remember to restart services manually!${NC}"
fi

echo ""
echo -e "${GREEN}✓ All done!${NC}"
