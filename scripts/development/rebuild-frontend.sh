#!/bin/bash

# Script to rebuild the frontend with new domain configuration
# This ensures REACT_APP_API_URL is properly baked into the JavaScript bundle

set -e

echo "=================================================="
echo "Rebuilding Frontend with Domain Configuration"
echo "=================================================="
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found. Please run this script from the email2kg directory."
    exit 1
fi

echo "📋 Step 1: Checking current API URL in frontend bundle..."
CURRENT_URL=$(sudo docker exec email2kg-frontend cat /usr/share/nginx/html/static/js/main.*.js 2>/dev/null | grep -o 'http://[^"]*8000' | head -1 || echo "Container not running")
echo "Current API URL: $CURRENT_URL"
echo ""

echo "🔄 Step 2: Rebuilding frontend container..."
echo "This will take 2-3 minutes as it installs dependencies and builds the React app..."
sudo docker-compose up --build -d frontend
echo ""

echo "⏳ Step 3: Waiting for frontend to be ready..."
sleep 5
echo ""

echo "✅ Step 4: Verifying new API URL in frontend bundle..."
NEW_URL=$(sudo docker exec email2kg-frontend cat /usr/share/nginx/html/static/js/main.*.js | grep -o 'http://[^"]*8000' | head -1)
echo "New API URL: $NEW_URL"
echo ""

echo "📊 Step 5: Checking container status..."
sudo docker ps --filter "name=email2kg-frontend" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

if [[ "$NEW_URL" == *"agenticrag360.com"* ]]; then
    echo "=================================================="
    echo "✅ SUCCESS! Frontend rebuilt with correct domain"
    echo "=================================================="
    echo ""
    echo "🌐 You can now access the application from your laptop:"
    echo "   http://agenticrag360.com:3000"
    echo ""
    echo "💡 Remember to hard refresh your browser (Ctrl+Shift+R)"
    echo "   to clear any cached JavaScript files"
    echo ""
else
    echo "⚠️  Warning: API URL might not be correct. Expected agenticrag360.com but got: $NEW_URL"
fi
