#!/bin/bash

# SSL Certificate Installation and HTTPS Deployment Script
# This script helps you deploy HTTPS configuration with your Namecheap SSL certificate

echo "=================================================="
echo "Email2KG HTTPS Deployment Setup"
echo "=================================================="
echo ""

# Check if running from correct directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: Please run this script from the email2kg directory"
    exit 1
fi

echo "📋 Step 1: Create SSL directory"
mkdir -p ssl
echo "✅ Created ./ssl directory"
echo ""

echo "=================================================="
echo "⚠️  MANUAL STEP REQUIRED:"
echo "=================================================="
echo ""
echo "You need to download your SSL certificate files from Namecheap"
echo "and place them in the ./ssl directory with these exact names:"
echo ""
echo "  1. certificate.crt  - Your SSL certificate"
echo "  2. private.key      - Your private key"
echo ""
echo "If you have a certificate bundle (CA bundle), you may need to"
echo "combine your certificate with the CA bundle:"
echo ""
echo "  cat your_domain.crt ca_bundle.crt > certificate.crt"
echo ""
echo "After placing the files, they should be at:"
echo "  - $(pwd)/ssl/certificate.crt"
echo "  - $(pwd)/ssl/private.key"
echo ""
echo "Press ENTER when you have placed the SSL files in ./ssl/"
read -r

# Verify SSL files exist
if [ ! -f "ssl/certificate.crt" ]; then
    echo "❌ Error: ssl/certificate.crt not found"
    exit 1
fi

if [ ! -f "ssl/private.key" ]; then
    echo "❌ Error: ssl/private.key not found"
    exit 1
fi

echo "✅ SSL certificate files found"
echo ""

echo "📋 Step 2: Setting correct permissions for SSL files"
chmod 644 ssl/certificate.crt
chmod 600 ssl/private.key
echo "✅ SSL file permissions set"
echo ""

echo "📋 Step 3: Updating .env file for HTTPS"
echo ""
echo "Please update your .env file with these values:"
echo ""
echo "ALLOWED_ORIGINS=[\"http://localhost\",\"http://localhost:3000\",\"https://agenticrag360.com\"]"
echo "GOOGLE_REDIRECT_URI=https://agenticrag360.com/api/auth/google/callback"
echo ""
echo "Press ENTER when you have updated .env"
read -r

echo "📋 Step 4: Pulling latest code"
git pull origin claude/knowledge-graph-platform-01ESPh8siCG8bo3JMuK4wLiv
echo ""

echo "📋 Step 5: Rebuilding containers with HTTPS configuration"
sudo docker-compose down
sudo docker-compose up --build -d
echo ""

echo "⏳ Waiting for services to start (30 seconds)..."
sleep 30
echo ""

echo "📊 Step 6: Checking container status"
sudo docker ps
echo ""

echo "=================================================="
echo "✅ HTTPS Deployment Complete!"
echo "=================================================="
echo ""
echo "🌐 Your application should now be accessible at:"
echo "   https://agenticrag360.com"
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Open AWS Console → EC2 → Security Groups"
echo "   Add inbound rule: Port 443, Source: 0.0.0.0/0 (HTTPS)"
echo ""
echo "2. Go to Google Cloud Console:"
echo "   https://console.cloud.google.com/apis/credentials"
echo "   Update OAuth redirect URI to:"
echo "   https://agenticrag360.com/api/auth/google/callback"
echo ""
echo "3. Test your application:"
echo "   - Open https://agenticrag360.com in browser"
echo "   - Try Gmail OAuth login"
echo ""
echo "4. Verify HTTPS is working:"
echo "   - Browser should show padlock icon"
echo "   - Check SSL certificate details in browser"
echo ""
echo "=================================================="
