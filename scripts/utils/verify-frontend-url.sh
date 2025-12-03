#!/bin/bash

# Script to verify the API URL in the frontend bundle

set -e

echo "Waiting for frontend container to be fully healthy..."
echo ""

# Wait for container to be healthy (max 60 seconds)
COUNTER=0
MAX_WAIT=60
while [ $COUNTER -lt $MAX_WAIT ]; do
    HEALTH=$(sudo docker inspect --format='{{.State.Health.Status}}' email2kg-frontend 2>/dev/null || echo "starting")
    if [ "$HEALTH" = "healthy" ]; then
        echo "✅ Container is healthy!"
        break
    fi
    echo "⏳ Waiting... ($COUNTER/$MAX_WAIT seconds) - Status: $HEALTH"
    sleep 2
    COUNTER=$((COUNTER + 2))
done

echo ""
echo "📁 Checking frontend file structure..."
sudo docker exec email2kg-frontend ls -la /usr/share/nginx/html/
echo ""

echo "📁 Checking static directory..."
sudo docker exec email2kg-frontend find /usr/share/nginx/html -name "*.js" -type f | head -5
echo ""

echo "🔍 Searching for API URL in JavaScript files..."
API_URL=$(sudo docker exec email2kg-frontend sh -c "find /usr/share/nginx/html -name '*.js' -type f -exec grep -h 'REACT_APP_API_URL\|http://.*:8000' {} \; 2>/dev/null | grep -o 'http://[^\",:]*:8000' | head -1" || echo "Not found")

if [ -z "$API_URL" ] || [ "$API_URL" = "Not found" ]; then
    echo "⚠️  Could not find API URL in standard location. Trying alternative search..."
    API_URL=$(sudo docker exec email2kg-frontend sh -c "grep -r 'api/auth/login' /usr/share/nginx/html 2>/dev/null | head -1" || echo "Files not ready")
    echo "Sample API call found: $API_URL"
else
    echo "Found API URL: $API_URL"
fi

echo ""
echo "=================================="

if [[ "$API_URL" == *"agenticrag360.com"* ]]; then
    echo "✅ SUCCESS! Frontend is configured with agenticrag360.com"
    echo ""
    echo "🌐 Access your application at:"
    echo "   http://agenticrag360.com:3000"
    echo ""
    echo "💡 Remember to hard refresh (Ctrl+Shift+R) in your browser"
elif [[ "$API_URL" == *"localhost"* ]]; then
    echo "❌ ERROR: Frontend is still using localhost"
    echo "The build might not have picked up the environment variable."
    echo "Try rebuilding again with: ./rebuild-frontend.sh"
else
    echo "⚠️  Could not determine API URL. Container might still be initializing."
    echo "Wait 10-20 seconds and run this script again: ./verify-frontend-url.sh"
fi

echo "=================================="
