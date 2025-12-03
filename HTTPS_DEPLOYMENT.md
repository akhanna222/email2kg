# HTTPS Deployment Guide for Email2KG

This guide walks you through deploying Email2KG with HTTPS using your Namecheap SSL certificate on AWS EC2.

## Overview

The application has been configured to:
- ✅ Serve frontend via HTTPS on port 443
- ✅ Proxy API requests through nginx (no port 8000 in URLs)
- ✅ Automatically redirect HTTP to HTTPS
- ✅ Use clean URLs: `https://agenticrag360.com`

## Prerequisites

- ✅ SSL certificate purchased from Namecheap for `agenticrag360.com`
- ✅ AWS EC2 instance running
- ✅ Domain pointing to EC2 IP address
- ✅ Latest code pulled from GitHub

## Step-by-Step Deployment

### 1. Download SSL Certificate from Namecheap

1. Log in to Namecheap account
2. Go to **SSL Certificates** section
3. Find your certificate for `agenticrag360.com`
4. Download the certificate files (you'll get a ZIP file)
5. Extract the ZIP - you should have:
   - `agenticrag360_com.crt` (your certificate)
   - `agenticrag360_com.ca-bundle` (CA bundle)
   - `private.key` (your private key)

### 2. Prepare Certificate Files

On your local machine, combine the certificate with the CA bundle:

```bash
cat agenticrag360_com.crt agenticrag360_com.ca-bundle > certificate.crt
```

You should now have:
- `certificate.crt` (combined certificate)
- `private.key` (private key)

### 3. Upload SSL Files to EC2

From your local machine, upload the SSL files to EC2:

```bash
# Create ssl directory on EC2
ssh ubuntu@34.245.37.71 "mkdir -p ~/email2kg/ssl"

# Upload certificate
scp certificate.crt ubuntu@34.245.37.71:~/email2kg/ssl/

# Upload private key
scp private.key ubuntu@34.245.37.71:~/email2kg/ssl/
```

### 4. Update Security Group (AWS Console)

1. Go to AWS Console → EC2 → Security Groups
2. Select your instance's security group
3. Click **Edit inbound rules**
4. Click **Add rule**
5. Configure:
   - **Type:** HTTPS
   - **Protocol:** TCP
   - **Port:** 443
   - **Source:** 0.0.0.0/0
   - **Description:** HTTPS access
6. Click **Save rules**

### 5. Update Configuration on EC2

SSH into your EC2 instance:

```bash
ssh ubuntu@34.245.37.71
cd ~/email2kg
```

Pull latest code:

```bash
git pull origin claude/knowledge-graph-platform-01ESPh8siCG8bo3JMuK4wLiv
```

Update your `.env` file:

```bash
nano .env
```

Update these values:

```bash
# CORS - Add HTTPS origin
ALLOWED_ORIGINS=["http://localhost","http://localhost:3000","https://agenticrag360.com"]

# Google OAuth - Use HTTPS without port
GOOGLE_REDIRECT_URI=https://agenticrag360.com/api/auth/google/callback

# Keep your existing values for:
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-secret
DB_PASSWORD=postgres
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
OPENAI_API_KEY=your-openai-key
```

Save and exit (Ctrl+X, Y, Enter)

### 6. Run the HTTPS Setup Script

```bash
cd ~/email2kg
./setup-https.sh
```

The script will:
- Verify SSL files exist
- Set correct permissions
- Rebuild containers with HTTPS configuration
- Start all services

**OR manually deploy:**

```bash
# Set SSL file permissions
chmod 644 ssl/certificate.crt
chmod 600 ssl/private.key

# Rebuild and restart containers
sudo docker-compose down
sudo docker-compose up --build -d

# Wait for services to start
sleep 30

# Check status
sudo docker ps
```

### 7. Update Google OAuth Settings

1. Go to https://console.cloud.google.com/apis/credentials
2. Click on your OAuth 2.0 Client ID
3. Under **Authorized redirect URIs**, **remove old URIs** and **add**:
   ```
   https://agenticrag360.com/api/auth/google/callback
   ```
   (Note: HTTPS, no port number)
4. Click **SAVE**

### 8. Test Your Deployment

#### Test HTTPS Access:
```bash
# From your laptop
curl -I https://agenticrag360.com

# Should return: HTTP/2 200
```

#### Test in Browser:
1. Open https://agenticrag360.com
2. Check for padlock icon in browser
3. Click padlock → View certificate details
4. Verify certificate is valid and matches your domain

#### Test HTTP Redirect:
```bash
# Should automatically redirect to HTTPS
curl -I http://agenticrag360.com

# Should return: HTTP/1.1 301 Moved Permanently
# Location: https://agenticrag360.com
```

#### Test Gmail OAuth:
1. Go to https://agenticrag360.com
2. Click "Sign in with Google"
3. Should successfully authenticate (no "Authorization Error")

## Troubleshooting

### Issue: "Certificate not found" error

**Solution:** Verify SSL files are in the correct location:
```bash
ls -la ~/email2kg/ssl/
# Should show:
# certificate.crt
# private.key
```

### Issue: "ERR_SSL_PROTOCOL_ERROR" in browser

**Possible causes:**
1. Port 443 not open in security group
2. SSL certificate files not mounted correctly
3. Nginx not started

**Check:**
```bash
# Check if frontend container is running
sudo docker ps | grep frontend

# Check nginx logs
sudo docker logs email2kg-frontend

# Verify port 443 is listening
sudo netstat -tlnp | grep :443
```

### Issue: Google OAuth still showing error

**Solution:**
1. Verify redirect URI in Google Console is exactly:
   `https://agenticrag360.com/api/auth/google/callback`
2. Make sure OAuth consent screen is set to "Testing" mode
3. Check that your email is in the test users list

### Issue: API calls failing (CORS errors)

**Solution:** Check backend ALLOWED_ORIGINS includes HTTPS:
```bash
sudo docker exec email2kg-backend env | grep ALLOWED_ORIGINS

# Should include: "https://agenticrag360.com"
```

If not, update .env and restart:
```bash
nano .env  # Add https://agenticrag360.com to ALLOWED_ORIGINS
sudo docker-compose restart backend
```

## Architecture Changes

### Before (HTTP):
- Frontend: http://agenticrag360.com:3000
- Backend: http://agenticrag360.com:8000/api

### After (HTTPS):
- Frontend: https://agenticrag360.com (port 443, default)
- Backend: https://agenticrag360.com/api (proxied by nginx)

Benefits:
- 🔒 Encrypted traffic (HTTPS)
- 🎯 Clean URLs (no ports)
- 🚀 Single entry point (nginx handles routing)
- ✅ Google OAuth compatible
- 🔐 Browser auto-redirect to HTTPS

## Files Modified

1. **docker-compose.yml**
   - Added port 443 mapping
   - Added SSL volume mount
   - Updated CORS origins
   - Changed Google redirect URI to HTTPS

2. **frontend/nginx.conf**
   - Added HTTPS server block
   - Added SSL certificate configuration
   - Added HTTP→HTTPS redirect
   - Added API proxy to backend

3. **frontend/Dockerfile**
   - Changed API URL to https://agenticrag360.com/api

4. **.env.example**
   - Updated examples for HTTPS configuration

## SSL Certificate Renewal

Your Namecheap SSL certificate will expire after 1-2 years. To renew:

1. Renew certificate through Namecheap before expiration
2. Download new certificate files
3. Replace files in `~/email2kg/ssl/`
4. Restart containers:
   ```bash
   cd ~/email2kg
   sudo docker-compose restart frontend
   ```

## Security Notes

- ✅ SSL private key has 600 permissions (owner read/write only)
- ✅ Certificate has 644 permissions (readable by nginx)
- ✅ Using TLS 1.2 and 1.3 (secure protocols)
- ✅ HSTS headers configured
- ✅ Security headers enabled (X-Frame-Options, etc.)

## Support

If you encounter issues:
1. Check container logs: `sudo docker logs email2kg-frontend`
2. Verify SSL files: `ls -la ~/email2kg/ssl/`
3. Test backend directly: `curl http://localhost:8000/health`
4. Check nginx config: `sudo docker exec email2kg-frontend nginx -t`

---

**Deployment Date:** $(date)
**Domain:** agenticrag360.com
**SSL Provider:** Namecheap
**Deployment Type:** AWS EC2 with Docker Compose
