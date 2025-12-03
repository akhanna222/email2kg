#!/bin/bash

# Script to debug frontend container issues

echo "=========================================="
echo "Frontend Container Debugging"
echo "=========================================="
echo ""

echo "📊 Container Status:"
sudo docker ps --filter "name=email2kg-frontend" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "📋 Last 30 lines of container logs:"
echo "=========================================="
sudo docker logs --tail 30 email2kg-frontend
echo ""

echo "🔍 Checking if nginx is running inside container:"
sudo docker exec email2kg-frontend ps aux | grep nginx || echo "nginx process not found"
echo ""

echo "📁 Checking if build files exist:"
sudo docker exec email2kg-frontend ls -la /usr/share/nginx/html/
echo ""

echo "🌐 Testing health check manually:"
sudo docker exec email2kg-frontend wget --quiet --tries=1 --spider http://localhost/ && echo "✅ Health check passed!" || echo "❌ Health check failed!"
echo ""

echo "📝 Nginx error logs:"
echo "=========================================="
sudo docker exec email2kg-frontend cat /var/log/nginx/error.log 2>/dev/null || echo "No error log found"
echo ""

echo "🔧 Testing if nginx config is valid:"
sudo docker exec email2kg-frontend nginx -t
echo ""

echo "📂 Checking nginx config:"
echo "=========================================="
sudo docker exec email2kg-frontend cat /etc/nginx/conf.d/default.conf
echo ""
