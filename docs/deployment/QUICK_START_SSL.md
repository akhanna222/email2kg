# Quick Start: Enable HTTPS on Your Email2KG Server

**Time Required:** 10 minutes
**Current IP:** 34.245.66.42
**Domain:** agenticrag360.com

## ⚡ One-Command Setup

SSH into your EC2 server and run:

```bash
cd ~/email2kg
sudo ./scripts/deployment/enable-https.sh
```

That's it! The script will:
- ✅ Check prerequisites
- ✅ Obtain free SSL certificate
- ✅ Configure HTTPS
- ✅ Set up auto-renewal
- ✅ Restart services

## 📋 Prerequisites (Must Complete First)

### 1. DNS Configuration
Your domain must point to your EC2 server:

```bash
# Check DNS (should show 34.245.66.42)
nslookup agenticrag360.com
```

**If DNS is wrong:**
1. Go to Namecheap.com → Domain List → Manage
2. Advanced DNS → Add Record:
   - Type: `A Record`
   - Host: `@`
   - Value: `34.245.66.42`
   - TTL: `Automatic`
3. Add another record:
   - Type: `A Record`
   - Host: `www`
   - Value: `34.245.66.42`
   - TTL: `Automatic`
4. Wait 5-10 minutes for propagation

### 2. Security Group Configuration
Port 80 and 443 must be open:

1. EC2 Console → Security Groups → Your security group
2. Inbound rules must include:
   ```
   HTTP  | TCP | 80  | 0.0.0.0/0
   HTTPS | TCP | 443 | 0.0.0.0/0
   ```

### 3. Services Running
Check services are running with HTTP:

```bash
cd ~/email2kg
sudo docker ps

# Should show 5 containers:
# - email2kg-db
# - email2kg-redis
# - email2kg-backend
# - email2kg-celery-worker
# - email2kg-frontend
```

## 🚀 SSL Setup Steps

### Step 1: SSH into Server

```bash
ssh -i "your-key.pem" ubuntu@34.245.66.42
```

### Step 2: Navigate to Project

```bash
cd ~/email2kg
```

### Step 3: Pull Latest Code (if needed)

```bash
git pull origin $(git branch --show-current)
```

### Step 4: Run SSL Setup

```bash
sudo ./scripts/deployment/enable-https.sh
```

**Follow the prompts:**
- ✅ Verify prerequisites
- ✅ Confirm domain
- ✅ Press 'y' to continue
- ⏳ Wait 2-3 minutes for setup

### Step 5: Update .env for HTTPS

```bash
nano .env
```

Update these two lines:
```bash
PUBLIC_PROTOCOL=https
GOOGLE_REDIRECT_URI=https://agenticrag360.com/api/auth/google/callback
```

Save and exit: `Ctrl+X`, then `Y`, then `Enter`

### Step 6: Restart Backend

```bash
sudo docker compose restart backend
```

### Step 7: Update Google OAuth

1. Go to: https://console.cloud.google.com/apis/credentials
2. Click your OAuth 2.0 Client ID
3. Under "Authorized redirect URIs":
   - Remove: `http://agenticrag360.com/api/auth/google/callback`
   - Add: `https://agenticrag360.com/api/auth/google/callback`
4. Click "Save"

## ✅ Verify HTTPS is Working

### Test 1: HTTPS Endpoint
```bash
curl https://agenticrag360.com/health
```
Expected: `healthy`

### Test 2: HTTP Redirect
```bash
curl -I http://agenticrag360.com
```
Expected: `301 Moved Permanently` → `Location: https://...`

### Test 3: Browser
1. Open: https://agenticrag360.com
2. Check for 🔒 padlock icon
3. Click padlock → Should show "Let's Encrypt" certificate
4. Try to login/signup → Should work

### Test 4: Service Status
```bash
sudo docker ps
```
All 5 services should show "Up" status

## 🔧 Troubleshooting

### Issue: "DNS not resolving"

**Check DNS:**
```bash
nslookup agenticrag360.com
```

**If wrong IP:** Update Namecheap A records (see Prerequisites above)

**If timeout:** Wait for DNS propagation (up to 48 hours, usually 5-10 min)

### Issue: "Port 80 not accessible"

**Check security group:**
```bash
# From your local machine:
telnet 34.245.66.42 80
```

**If connection refused:** Add port 80 to EC2 security group (see Prerequisites above)

### Issue: "Certificate already exists"

**If you've run setup before:**
```bash
# Delete old certificates
sudo rm -rf /etc/letsencrypt/live/agenticrag360.com/
sudo rm -rf /etc/letsencrypt/archive/agenticrag360.com/
sudo rm -rf /etc/letsencrypt/renewal/agenticrag360.com.conf

# Run setup again
sudo ./scripts/deployment/enable-https.sh
```

### Issue: "HTTPS returns 503"

**Check SSL certificates exist:**
```bash
ls -la ~/email2kg/ssl/
```

Should show:
- `certificate.crt`
- `private.key`

**If missing:** Run setup script again

**Check frontend logs:**
```bash
sudo docker compose logs frontend --tail=100
```

### Issue: "Login still doesn't work"

**Check .env has HTTPS:**
```bash
grep PUBLIC_PROTOCOL .env
```
Should show: `PUBLIC_PROTOCOL=https`

**Check CORS in logs:**
```bash
sudo docker compose logs backend --tail=50 | grep CORS
```

**Restart backend:**
```bash
sudo docker compose restart backend
```

**Verify Google OAuth redirect URI is HTTPS:**
- Go to: https://console.cloud.google.com/apis/credentials
- Check redirect URI is: `https://agenticrag360.com/api/auth/google/callback`

## 📊 Monitoring

### Check Certificate Expiration
```bash
sudo certbot certificates
```

Shows expiration date (90 days from issue)

### Check Auto-Renewal
```bash
sudo certbot renew --dry-run
```

Should show: "Congratulations, all simulated renewals succeeded"

### View Logs
```bash
# All services
sudo docker compose logs -f

# Specific service
sudo docker compose logs -f backend
sudo docker compose logs -f frontend
sudo docker compose logs -f celery_worker
```

## 🎯 Success Checklist

After completing setup:

- [ ] HTTPS endpoint returns `healthy`: `curl https://agenticrag360.com/health`
- [ ] HTTP redirects to HTTPS: `curl -I http://agenticrag360.com`
- [ ] Browser shows padlock icon at: https://agenticrag360.com
- [ ] Can login/signup without errors
- [ ] All 5 services running: `sudo docker ps`
- [ ] .env has `PUBLIC_PROTOCOL=https`
- [ ] Google OAuth uses HTTPS redirect URI
- [ ] Certificate auto-renewal configured: `sudo certbot renew --dry-run`

## 🔄 Certificate Renewal

Certificates auto-renew every 90 days. No action needed!

**Manual renewal (if needed):**
```bash
sudo certbot renew
cd ~/email2kg
sudo cp /etc/letsencrypt/live/agenticrag360.com/fullchain.pem ssl/certificate.crt
sudo cp /etc/letsencrypt/live/agenticrag360.com/privkey.pem ssl/private.key
sudo docker compose restart frontend
```

## 📚 More Information

For detailed troubleshooting and advanced configuration, see:
- [Complete SSL Setup Guide](./SSL_SETUP_GUIDE.md)
- [EC2 Deployment Guide](./EC2_DEPLOYMENT.md)

## 🆘 Need Help?

**Common fixes:**

1. **Services not starting:**
   ```bash
   sudo docker compose down
   sudo docker compose up -d
   ```

2. **Certificate issues:**
   ```bash
   sudo certbot certificates
   sudo certbot renew --force-renewal
   ```

3. **Reset to HTTP (temporary):**
   ```bash
   nano .env
   # Change: PUBLIC_PROTOCOL=http
   sudo docker compose restart backend
   ```

Your Email2KG application should now be running securely with HTTPS! 🔒
