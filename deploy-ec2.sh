#!/bin/bash

# Email2KG EC2 Deployment Script
# Run this script on your EC2 instance after SSH connection

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Email2KG EC2 Deployment Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}Please do not run this script as root${NC}"
    echo "Run as ubuntu user: ./deploy-ec2.sh"
    exit 1
fi

# Step 1: Update system
echo -e "${BLUE}Step 1: Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# Step 2: Install dependencies
echo -e "${BLUE}Step 2: Installing dependencies...${NC}"
sudo apt install -y \
    python3.10 \
    python3-pip \
    python3.10-venv \
    nodejs \
    npm \
    postgresql \
    postgresql-contrib \
    nginx \
    git \
    curl \
    poppler-utils \
    ca-certificates \
    gnupg \
    lsb-release

echo -e "${GREEN}✓ System packages installed${NC}"

# Step 3: Install Docker
echo -e "${BLUE}Step 3: Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo -e "${GREEN}✓ Docker installed${NC}"
    echo -e "${YELLOW}Note: You may need to log out and back in for docker group to take effect${NC}"
else
    echo -e "${GREEN}✓ Docker already installed${NC}"
fi

# Install Docker Compose
echo -e "${BLUE}Installing Docker Compose...${NC}"
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
echo -e "${GREEN}✓ Docker Compose installed${NC}"

# Step 4: Setup PostgreSQL
echo -e "${BLUE}Step 4: Setting up PostgreSQL database...${NC}"
read -p "Enter database password (or press Enter for auto-generated): " DB_PASSWORD
if [ -z "$DB_PASSWORD" ]; then
    DB_PASSWORD=$(openssl rand -base64 32)
    echo -e "${YELLOW}Generated database password: ${DB_PASSWORD}${NC}"
    echo -e "${YELLOW}Save this password!${NC}"
fi

sudo -u postgres psql -c "CREATE DATABASE email2kg;" 2>/dev/null || echo "Database already exists"
sudo -u postgres psql -c "CREATE USER email2kg_user WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || echo "User already exists"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE email2kg TO email2kg_user;"

echo -e "${GREEN}✓ PostgreSQL configured${NC}"

# Step 5: Clone repository (if not already in the directory)
echo -e "${BLUE}Step 5: Setting up application...${NC}"
APP_DIR="/home/ubuntu/email2kg"

if [ ! -d "$APP_DIR" ]; then
    echo "Enter your GitHub repository URL (e.g., https://github.com/user/email2kg.git):"
    read REPO_URL
    git clone $REPO_URL $APP_DIR
    cd $APP_DIR
else
    cd $APP_DIR
    echo "Already in application directory"
fi

# Step 6: Configure environment variables
echo -e "${BLUE}Step 6: Configuring environment variables...${NC}"

echo ""
echo -e "${YELLOW}Please provide the following API keys:${NC}"
read -p "OpenAI API Key: " OPENAI_KEY
read -p "Google OAuth Client ID: " GOOGLE_CLIENT_ID
read -p "Google OAuth Client Secret: " GOOGLE_CLIENT_SECRET

# Generate secure secrets
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Get EC2 public IP
EC2_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
echo -e "${GREEN}EC2 Public IP: ${EC2_IP}${NC}"

# Create .env file
cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://email2kg_user:${DB_PASSWORD}@localhost:5432/email2kg

# API Keys
OPENAI_API_KEY=${OPENAI_KEY}

# Google OAuth
GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
GOOGLE_REDIRECT_URI=http://${EC2_IP}:8000/auth/google/callback

# Security
SECRET_KEY=${SECRET_KEY}
JWT_SECRET_KEY=${JWT_SECRET_KEY}

# CORS
ALLOWED_ORIGINS=["http://${EC2_IP}","http://localhost"]

# App Settings
DEBUG=False
EOF

echo -e "${GREEN}✓ Environment configured${NC}"

# Step 7: Ask for deployment method
echo ""
echo -e "${YELLOW}Choose deployment method:${NC}"
echo "1) Docker Compose (Recommended - Easy & Isolated)"
echo "2) Manual Setup (Direct installation)"
read -p "Enter choice [1-2]: " DEPLOY_METHOD

case $DEPLOY_METHOD in
    1)
        echo -e "${BLUE}Deploying with Docker Compose...${NC}"

        # Start services
        docker-compose up --build -d

        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}Deployment Complete!${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        echo -e "${BLUE}Access your application:${NC}"
        echo "  Frontend: http://${EC2_IP}"
        echo "  Backend API: http://${EC2_IP}:8000"
        echo "  API Docs: http://${EC2_IP}:8000/docs"
        echo ""
        echo -e "${BLUE}Useful commands:${NC}"
        echo "  View logs: docker-compose logs -f"
        echo "  Restart: docker-compose restart"
        echo "  Stop: docker-compose down"
        echo "  View status: docker-compose ps"
        ;;

    2)
        echo -e "${BLUE}Setting up manual deployment...${NC}"

        # Backend setup
        cd backend
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt

        # Frontend setup
        cd ../frontend
        npm install
        npm run build

        cd ..

        echo -e "${GREEN}✓ Application installed${NC}"
        echo ""
        echo -e "${YELLOW}Next steps:${NC}"
        echo "1. Configure nginx (use provided config in nginx-ec2.conf)"
        echo "2. Setup systemd services for auto-start"
        echo "3. Start the application"
        echo ""
        echo "See DEPLOY_EC2_MANUAL.md for detailed instructions"
        ;;

    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Important: Update your Google OAuth redirect URI to:${NC}"
echo "  http://${EC2_IP}:8000/auth/google/callback"
echo ""
echo -e "${YELLOW}Security Note: For production, configure:${NC}"
echo "  - Domain name with SSL certificate"
echo "  - Firewall rules (Security Groups)"
echo "  - Backup strategy"
