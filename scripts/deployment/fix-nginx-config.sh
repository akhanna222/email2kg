#!/bin/bash

# Fix nginx.conf to have proper SSL configuration
# This overwrites the local nginx.conf with the correct SSL version

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Fixing nginx.conf with SSL configuration...${NC}"
echo ""

cd /home/ubuntu/email2kg || cd ~/email2kg || exit 1

# Backup existing nginx.conf
if [ -f "frontend/nginx.conf" ]; then
    cp frontend/nginx.conf frontend/nginx.conf.backup
    echo -e "${GREEN}✅ Backed up existing nginx.conf${NC}"
fi

# Write the correct SSL-enabled nginx.conf
cat > frontend/nginx.conf << 'EOF'
# HTTP server - redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name agenticrag360.com www.agenticrag360.com;

    # Redirect all HTTP traffic to HTTPS
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    http2 on;
    server_name agenticrag360.com www.agenticrag360.com;

    # SSL certificate paths (mount these via Docker volume)
    ssl_certificate /etc/nginx/ssl/certificate.crt;
    ssl_certificate_key /etc/nginx/ssl/private.key;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    root /usr/share/nginx/html;
    index index.html;

    # Enable gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/javascript application/json;

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # DNS resolver for Docker - allows dynamic backend resolution
    resolver 127.0.0.11 valid=30s;

    # Proxy API requests to backend
    location /api/ {
        set $backend_upstream http://backend:8000;
        proxy_pass $backend_upstream/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # React Router - serve index.html for all routes
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

echo -e "${GREEN}✅ nginx.conf updated with SSL configuration${NC}"
echo ""

# Verify it has SSL
if grep -q "listen 443 ssl" frontend/nginx.conf; then
    echo -e "${GREEN}✅ Verified: nginx.conf has SSL (listen 443 ssl)${NC}"
else
    echo -e "${RED}❌ Error: SSL configuration not found after update${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ nginx.conf is ready!${NC}"
echo ""
echo "Now run: sudo ./scripts/deployment/final-ssl-fix.sh"
echo ""
