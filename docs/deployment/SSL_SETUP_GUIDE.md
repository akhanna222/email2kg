# SSL/HTTPS Setup Guide for Email2KG

This guide will help you set up free SSL certificates using Let's Encrypt and enable HTTPS for your Email2KG application.

## 🎯 Overview

- **Time Required**: 10-15 minutes
- **Cost**: Free (Let's Encrypt)
- **Auto-Renewal**: Yes (certificates renew automatically every 90 days)
- **Prerequisites**:
  - Domain pointing to your EC2 server
  - Port 80 and 443 open in security group
  - Services currently running on HTTP

## 📋 Current Status Check

Before starting, verify your current setup:

```bash
# 1. Check domain DNS
nslookup agenticrag360.com

# 2. Check HTTP is working
curl http://agenticrag360.com/health

# 3. Check services are running
sudo docker ps
```

Expected results:
- ✅ DNS shows your EC2 IP (34.245.66.42)
- ✅ HTTP returns "healthy"
- ✅ All 5 services running (postgres, redis, backend, celery_worker, frontend)

## 🚀 Quick SSL Setup (Automated)

The fastest way to set up SSL is using our automated script:

```bash
cd ~/email2kg

# Make sure script is executable
chmod +x scripts/deployment/setup-letsencrypt.sh

# Run the SSL setup script (will prompt for confirmation)
sudo ./scripts/deployment/setup-letsencrypt.sh
```

**What the script does:**
1. Temporarily switches to HTTP-only mode
2. Installs certbot
3. Obtains SSL certificate from Let's Encrypt
4. Copies certificates to `ssl/` directory
5. Switches back to HTTPS mode
6. Restarts services with SSL enabled
7. Sets up auto-renewal

**Expected output:**
```
✅ Certificate obtained successfully!
✅ Certificates copied to ssl/ directory
✅ Restored HTTPS nginx config
✅ HTTPS Setup Complete!
```

## 📝 Manual SSL Setup (Step by Step)

If you prefer to understand each step or if the automated script fails, follow this manual process:

### Step 1: Ensure Port 80 is Open

Let's Encrypt needs port 80 to verify domain ownership.

**Check EC2 Security Group:**
1. Go to EC2 Console → Security Groups
2. Find your instance's security group
3. Verify inbound rules include:
   ```
   Type: HTTP
   Protocol: TCP
   Port: 80
   Source: 0.0.0.0/0
   ```

### Step 2: Stop Services Temporarily

```bash
cd ~/email2kg
sudo docker compose down
```

### Step 3: Install Certbot

```bash
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx
```

### Step 4: Obtain SSL Certificate

```bash
sudo certbot certonly --standalone \
  --preferred-challenges http \
  --agree-tos \
  --non-interactive \
  --register-unsafely-without-email \
  -d agenticrag360.com \
  -d www.agenticrag360.com
```

**Troubleshooting common errors:**

**Error: "Port 80 already in use"**
```bash
# Stop any service using port 80
sudo systemctl stop nginx
sudo docker compose down
# Try certbot again
```

**Error: "Connection refused"**
```bash
# Check security group allows port 80
# Check if firewall is blocking:
sudo ufw status
# If active, allow port 80:
sudo ufw allow 80/tcp
```

**Error: "DNS problem: NXDOMAIN"**
```bash
# Wait for DNS propagation (can take up to 48 hours)
# Check DNS:
nslookup agenticrag360.com
# Try again later
```

### Step 5: Create SSL Directory and Copy Certificates

```bash
cd ~/email2kg

# Create ssl directory
mkdir -p ssl

# Copy certificates
sudo cp /etc/letsencrypt/live/agenticrag360.com/fullchain.pem ssl/certificate.crt
sudo cp /etc/letsencrypt/live/agenticrag360.com/privkey.pem ssl/private.key

# Set permissions
sudo chmod 644 ssl/certificate.crt
sudo chmod 600 ssl/private.key
sudo chown $USER:$USER ssl/*
```

Verify certificates were copied:
```bash
ls -la ssl/
# Should show:
# certificate.crt
# private.key
```

### Step 6: Update Environment Variables

```bash
nano .env
```

Update these values:
```bash
PUBLIC_PROTOCOL=https
GOOGLE_REDIRECT_URI=https://agenticrag360.com/api/auth/google/callback
```

Save and exit (Ctrl+X, Y, Enter)

### Step 7: Start Services with HTTPS

```bash
sudo docker compose down
sudo docker compose up --build -d
```

Wait 30 seconds for services to start, then check:
```bash
sudo docker ps
```

### Step 8: Verify HTTPS is Working

```bash
# Test HTTPS endpoint
curl https://agenticrag360.com/health

# Test HTTP redirect (should redirect to HTTPS)
curl -I http://agenticrag360.com/health
```

Expected results:
- HTTPS should return: `healthy`
- HTTP should return: `301 Moved Permanently` with `Location: https://...`

### Step 9: Set Up Auto-Renewal

Create renewal hook:
```bash
sudo tee /etc/letsencrypt/renewal-hooks/post/email2kg-renew.sh > /dev/null <<'EOF'
#!/bin/bash
# Copy renewed certificates to email2kg ssl directory
cd /home/ubuntu/email2kg
cp /etc/letsencrypt/live/agenticrag360.com/fullchain.pem ssl/certificate.crt
cp /etc/letsencrypt/live/agenticrag360.com/privkey.pem ssl/private.key
chmod 644 ssl/certificate.crt
chmod 600 ssl/private.key
chown ubuntu:ubuntu ssl/*
# Restart frontend container to load new certificates
docker compose restart frontend
EOF

sudo chmod +x /etc/letsencrypt/renewal-hooks/post/email2kg-renew.sh
```

Test auto-renewal (dry run):
```bash
sudo certbot renew --dry-run
```

Expected output: `Congratulations, all simulated renewals succeeded`

## 🔐 Update Google OAuth for HTTPS

After SSL is working, update your Google OAuth configuration:

1. Go to: https://console.cloud.google.com/apis/credentials
2. Click on your OAuth 2.0 Client ID
3. Under "Authorized redirect URIs", update to:
   ```
   https://agenticrag360.com/api/auth/google/callback
   ```
4. Remove the HTTP redirect URI
5. Click "Save"

Then restart the backend:
```bash
cd ~/email2kg
sudo docker compose restart backend
```

## ✅ Final Verification

### Test 1: HTTPS Access
```bash
curl https://agenticrag360.com/health
# Should return: healthy
```

### Test 2: HTTP Redirect
```bash
curl -I http://agenticrag360.com
# Should return: 301 and Location: https://agenticrag360.com
```

### Test 3: Browser Access
1. Open browser
2. Go to: https://agenticrag360.com
3. Check for padlock icon in address bar
4. Click padlock → Certificate should show "Let's Encrypt Authority X3"

### Test 4: SSL Grade
Check your SSL configuration quality:
```bash
# In browser, visit:
https://www.ssllabs.com/ssltest/analyze.html?d=agenticrag360.com
```
Should get an A or A+ grade.

### Test 5: Login/Signup
1. Go to https://agenticrag360.com
2. Try to sign up or log in
3. Should work without CORS errors

## 🔧 Troubleshooting

### Issue: "HTTPS not working after setup"

**Check nginx is using SSL config:**
```bash
sudo docker exec email2kg-frontend cat /etc/nginx/conf.d/default.conf | grep ssl
```
Should show SSL configuration lines.

**Check SSL certificates are mounted:**
```bash
sudo docker exec email2kg-frontend ls -la /etc/nginx/ssl/
```
Should show:
- certificate.crt
- private.key

**Check logs:**
```bash
sudo docker compose logs frontend --tail=100
```

### Issue: "Mixed content warnings in browser"

This means some resources are loading over HTTP instead of HTTPS.

**Fix:**
1. Open browser console (F12)
2. Look for mixed content warnings
3. Update any hardcoded HTTP URLs in frontend code to use HTTPS

### Issue: "Can't login after enabling HTTPS"

**Check CORS configuration:**
```bash
sudo docker compose logs backend --tail=50 | grep CORS
```

**Update .env:**
```bash
nano .env
```
Make sure ALLOWED_ORIGINS includes HTTPS:
```bash
ALLOWED_ORIGINS=["https://agenticrag360.com","http://agenticrag360.com"]
```

Then restart:
```bash
sudo docker compose restart backend
```

### Issue: "Certificate renewal fails"

**Check renewal configuration:**
```bash
sudo cat /etc/letsencrypt/renewal/agenticrag360.com.conf
```

**Test renewal manually:**
```bash
sudo certbot renew --force-renewal
```

**Check certbot timer is running:**
```bash
sudo systemctl status certbot.timer
```

## 📅 Certificate Management

### Check Certificate Expiration
```bash
sudo certbot certificates
```

Shows:
- Certificate name
- Domains
- Expiry date
- Certificate path

### Manual Renewal (if needed)
```bash
sudo certbot renew
# Then copy certificates
cd ~/email2kg
sudo cp /etc/letsencrypt/live/agenticrag360.com/fullchain.pem ssl/certificate.crt
sudo cp /etc/letsencrypt/live/agenticrag360.com/privkey.pem ssl/private.key
sudo docker compose restart frontend
```

### View Certificate Details
```bash
openssl x509 -in ssl/certificate.crt -text -noout | grep -A2 "Validity"
```

Shows certificate valid from/to dates.

## 🎓 Understanding the Setup

### Why Port 80?
Let's Encrypt uses HTTP-01 challenge to verify you control the domain. It makes a request to `http://yourdomain.com/.well-known/acme-challenge/` on port 80.

### Certificate Locations
- **Let's Encrypt originals**: `/etc/letsencrypt/live/agenticrag360.com/`
- **Docker copies**: `~/email2kg/ssl/`

We copy certificates because Docker containers need access to them, and it's safer than mounting the entire `/etc/letsencrypt` directory.

### Auto-Renewal Process
1. Certbot timer runs twice daily
2. Checks if certificates expire in < 30 days
3. If yes, obtains new certificate
4. Runs renewal hook (copies to ssl/ and restarts frontend)
5. Application continues without downtime

### HTTPS Architecture
```
Client Browser (HTTPS)
    ↓
Nginx Frontend Container (port 443, SSL termination)
    ↓
Backend API Container (port 8000, HTTP internal)
    ↓
Database/Redis (internal network)
```

SSL termination happens at nginx, internal traffic uses HTTP (which is fine since it's within Docker network).

## 🚨 Security Notes

1. **Never commit certificates to Git**
   - The `ssl/` directory is in `.gitignore`
   - Certificates are server-specific

2. **Keep certificates secure**
   - `private.key` should have 600 permissions (owner read/write only)
   - `certificate.crt` can have 644 permissions (world-readable)

3. **Monitor expiration**
   - Certificates expire every 90 days
   - Auto-renewal should handle this
   - Set up monitoring to alert if renewal fails

4. **Backup strategy**
   - Let's Encrypt certificates can be re-issued anytime
   - No need to backup - just run certbot again if needed

## 📚 Additional Resources

- **Let's Encrypt Documentation**: https://letsencrypt.org/docs/
- **Certbot Documentation**: https://certbot.eff.org/
- **SSL Labs Test**: https://www.ssllabs.com/ssltest/
- **MDN HTTPS Guide**: https://developer.mozilla.org/en-US/docs/Web/Security/Transport_Layer_Security

## ✨ Success Checklist

After completing setup, you should have:

- [ ] SSL certificates in `ssl/` directory
- [ ] HTTPS working (https://agenticrag360.com)
- [ ] HTTP redirecting to HTTPS
- [ ] Padlock icon showing in browser
- [ ] Auto-renewal configured and tested
- [ ] Google OAuth updated to use HTTPS redirect URI
- [ ] Login/signup working without errors
- [ ] All services running (`sudo docker ps` shows 5 services)

## 🎉 Next Steps

1. **Test the application**
   - Sign up/login
   - Sync Gmail emails
   - Upload documents
   - Verify OCR processing

2. **Monitor logs**
   ```bash
   # Watch all logs
   sudo docker compose logs -f

   # Watch specific service
   sudo docker compose logs -f backend
   ```

3. **Set up monitoring**
   - Consider setting up SSL monitoring (e.g., SSL Labs API)
   - Monitor certificate expiration
   - Set up alerts for service downtime

Your Email2KG application is now production-ready with HTTPS! 🔒
