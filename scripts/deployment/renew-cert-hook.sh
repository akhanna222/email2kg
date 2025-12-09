#!/bin/bash

# Fixed Auto-Renewal Hook for Email2KG
# This script runs after Let's Encrypt certificate renewal
# It properly handles the running Docker containers

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="/home/ubuntu/email2kg"

echo "=== Email2KG Certificate Renewal Hook ==="
echo "Time: $(date)"
echo ""

# Navigate to project directory
cd "$PROJECT_DIR" || exit 1

# Copy renewed certificates to project ssl directory
echo "Copying renewed certificates..."
cp /etc/letsencrypt/live/agenticrag360.com/fullchain.pem ssl/certificate.crt
cp /etc/letsencrypt/live/agenticrag360.com/privkey.pem ssl/private.key

# Set proper permissions
chmod 644 ssl/certificate.crt
chmod 600 ssl/private.key
chown ubuntu:ubuntu ssl/*

echo "✅ Certificates updated"

# Restart frontend container to load new certificates
echo "Restarting frontend container..."
docker compose restart frontend

echo "✅ Frontend restarted with new certificates"
echo ""
echo "Certificate renewal completed successfully!"
