#!/bin/bash

# Let's Encrypt SSL Setup Script for Email2KG
# This script automates the complete HTTPS setup with free SSL certificates

set -e

echo "=================================================="
echo "Let's Encrypt SSL Setup for Email2KG"
echo "=================================================="
echo ""

# Check if running from correct directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: Please run this script from the email2kg directory"
    exit 1
fi

# Check if running as root or with sudo
if [ "$EUID" -eq 0 ]; then
    SUDO=""
else
    SUDO="sudo"
fi

echo "📋 Step 1: Temporarily switching to HTTP-only mode"
echo "This allows Let's Encrypt to verify your domain..."
echo ""

# Backup current nginx config
if [ -f "frontend/nginx.conf" ]; then
    cp frontend/nginx.conf frontend/nginx.conf.backup
    echo "✅ Backed up nginx.conf"
fi

# Use HTTP-only config temporarily
cp frontend/nginx-http-only.conf frontend/nginx.conf
echo "✅ Switched to HTTP-only configuration"
echo ""

echo "📋 Step 2: Removing SSL volume mount temporarily"
# Remove SSL volume line from docker-compose.yml temporarily
if grep -q "./ssl:/etc/nginx/ssl:ro" docker-compose.yml; then
    cp docker-compose.yml docker-compose.yml.bak
    sed -i '/\.\/ssl:\/etc\/nginx\/ssl:ro/d' docker-compose.yml
    # Also remove the volumes: line if it's now empty
    sed -i '/volumes:$/N;s/volumes:\n    depends_on:/depends_on:/' docker-compose.yml
    echo "✅ Disabled SSL volume mount"
fi
echo ""

echo "📋 Step 3: Restarting containers with HTTP-only"
$SUDO docker-compose down
$SUDO docker-compose up --build -d
echo "⏳ Waiting for services to start..."
sleep 15
echo "✅ Services started"
echo ""

echo "📋 Step 4: Installing Certbot"
$SUDO apt-get update -qq
$SUDO apt-get install -y certbot python3-certbot-nginx
echo "✅ Certbot installed"
echo ""

echo "📋 Step 5: Stopping nginx to free port 80"
$SUDO systemctl stop nginx 2>/dev/null || true
echo ""

echo "=================================================="
echo "📋 Step 6: Obtaining SSL Certificate"
echo "=================================================="
echo ""
echo "⚠️  Let's Encrypt will now verify your domain ownership."
echo "This requires:"
echo "  - Port 80 accessible from internet"
echo "  - Domain pointing to this server"
echo ""
echo "Press ENTER to continue..."
read -r

# Get certificate
$SUDO certbot certonly --standalone \
    --preferred-challenges http \
    --agree-tos \
    --non-interactive \
    --register-unsafely-without-email \
    -d agenticrag360.com \
    -d www.agenticrag360.com

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Failed to obtain certificate!"
    echo ""
    echo "Common issues:"
    echo "  1. Port 80 not accessible from internet (check security group)"
    echo "  2. Domain not pointing to this server"
    echo "  3. Rate limit reached (try again later)"
    echo ""
    echo "Restoring original configuration..."
    mv docker-compose.yml.bak docker-compose.yml
    mv frontend/nginx.conf.backup frontend/nginx.conf
    exit 1
fi

echo "✅ Certificate obtained successfully!"
echo ""

echo "📋 Step 7: Setting up SSL directory"
mkdir -p ssl
$SUDO chmod 755 ssl

# Copy Let's Encrypt certificates to our ssl directory
$SUDO cp /etc/letsencrypt/live/agenticrag360.com/fullchain.pem ssl/certificate.crt
$SUDO cp /etc/letsencrypt/live/agenticrag360.com/privkey.pem ssl/private.key
$SUDO chmod 644 ssl/certificate.crt
$SUDO chmod 600 ssl/private.key
$SUDO chown $USER:$USER ssl/*

echo "✅ Certificates copied to ssl/ directory"
echo ""

echo "📋 Step 8: Restoring HTTPS nginx configuration"
if [ -f "frontend/nginx.conf.backup" ]; then
    mv frontend/nginx.conf.backup frontend/nginx.conf
    echo "✅ Restored HTTPS nginx config"
fi

# Restore SSL volume mount
if [ -f "docker-compose.yml.bak" ]; then
    mv docker-compose.yml.bak docker-compose.yml
    echo "✅ Restored docker-compose.yml"
fi
echo ""

echo "📋 Step 9: Deploying with HTTPS"
$SUDO docker-compose down
$SUDO docker-compose up --build -d
echo "⏳ Waiting for services to start..."
sleep 20
echo ""

echo "📊 Step 10: Checking container status"
$SUDO docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "📋 Step 11: Setting up auto-renewal"
# Create renewal hook
$SUDO tee /etc/letsencrypt/renewal-hooks/post/email2kg-renew.sh > /dev/null <<'HOOK_SCRIPT'
#!/bin/bash
# Copy renewed certificates to email2kg ssl directory
cd /home/ubuntu/email2kg
cp /etc/letsencrypt/live/agenticrag360.com/fullchain.pem ssl/certificate.crt
cp /etc/letsencrypt/live/agenticrag360.com/privkey.pem ssl/private.key
chmod 644 ssl/certificate.crt
chmod 600 ssl/private.key
chown ubuntu:ubuntu ssl/*
# Restart frontend container
docker-compose restart frontend
HOOK_SCRIPT

$SUDO chmod +x /etc/letsencrypt/renewal-hooks/post/email2kg-renew.sh
echo "✅ Auto-renewal hook configured"
echo ""

# Test renewal (dry run)
echo "Testing auto-renewal..."
$SUDO certbot renew --dry-run
echo "✅ Auto-renewal test passed"
echo ""

echo "=================================================="
echo "✅ HTTPS Setup Complete!"
echo "=================================================="
echo ""
echo "🌐 Your application is now available at:"
echo "   https://agenticrag360.com"
echo ""
echo "🔒 SSL Certificate Details:"
echo "   - Provider: Let's Encrypt"
echo "   - Valid for: 90 days"
echo "   - Auto-renewal: Enabled (runs automatically)"
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Test your site:"
echo "   Open https://agenticrag360.com in browser"
echo "   Check for padlock icon"
echo ""
echo "2. Update Google OAuth:"
echo "   Go to: https://console.cloud.google.com/apis/credentials"
echo "   Update redirect URI to:"
echo "   https://agenticrag360.com/api/auth/google/callback"
echo ""
echo "3. Update .env file:"
echo "   nano .env"
echo "   Set: GOOGLE_REDIRECT_URI=https://agenticrag360.com/api/auth/google/callback"
echo "   Then: sudo docker-compose restart backend"
echo ""
echo "=================================================="
echo ""
echo "Certificate will auto-renew every 90 days."
echo "No manual intervention needed!"
echo ""
