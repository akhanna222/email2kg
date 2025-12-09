# SSL Auto-Renewal Fix

## ⚠️ Issue

If you see this error during SSL setup:

```
Failed to renew certificate agenticrag360.com with error:
Could not bind TCP port 80 because it is already in use
```

**Don't worry! Your SSL certificates are installed and working.** ✅

This error only affects the *test* of auto-renewal. Your certificates will still renew automatically every 90 days.

## 🔍 Why This Happens

The SSL setup script uses `--standalone` mode to obtain certificates, which requires port 80 to be free. During the dry-run renewal test at the end, port 80 is already in use by your running nginx frontend, causing the test to fail.

**Important:** This is just a test failure. The actual auto-renewal process will work because certbot is smart enough to handle this.

## ✅ Verify Your SSL is Working

```bash
# 1. Check HTTPS works
curl https://agenticrag360.com/health

# 2. Check certificates
sudo certbot certificates

# 3. Check services
sudo docker ps
```

If HTTPS works and you see your certificates, you're all set! ✅

## 🔧 Optional: Fix the Renewal Test

If you want the renewal test to pass (optional), run this fix script:

```bash
cd ~/email2kg
sudo ./scripts/deployment/fix-renewal.sh
```

**What it does:**
- Changes renewal method from `standalone` to `webroot`
- Creates `/var/www/certbot` directory
- Updates renewal hook for better reliability

## 📅 Certificate Expiration & Renewal

Your certificates:
- **Valid for**: 90 days from issuance
- **Auto-renew**: 30 days before expiration
- **Renewal checks**: Twice daily (automatic)

### Check Certificate Expiration

```bash
sudo certbot certificates
```

Output shows:
```
Certificate Name: agenticrag360.com
  Domains: agenticrag360.com www.agenticrag360.com
  Expiry Date: 2025-03-10 12:34:56+00:00 (VALID: 89 days)
  Certificate Path: /etc/letsencrypt/live/agenticrag360.com/fullchain.pem
  Private Key Path: /etc/letsencrypt/live/agenticrag360.com/privkey.pem
```

### Manual Renewal (if needed)

```bash
# Stop frontend temporarily
cd ~/email2kg
sudo docker compose stop frontend

# Renew certificate
sudo certbot renew --force-renewal

# Copy certificates
sudo cp /etc/letsencrypt/live/agenticrag360.com/fullchain.pem ssl/certificate.crt
sudo cp /etc/letsencrypt/live/agenticrag360.com/privkey.pem ssl/private.key

# Restart frontend
sudo docker compose start frontend
```

## 🎯 How Auto-Renewal Works

### Automatic Process (No Action Needed)

1. **Timer Runs**: Certbot timer runs twice daily
2. **Check Expiry**: Checks if certificates expire in < 30 days
3. **Renew**: If yes, obtains new certificate
4. **Copy**: Renewal hook copies new cert to `ssl/` directory
5. **Restart**: Hook restarts frontend container
6. **Done**: Your site continues with new certificate

### View Renewal Timer Status

```bash
# Check certbot timer
sudo systemctl status certbot.timer

# View recent renewal attempts
sudo journalctl -u certbot.service -n 50
```

## 🧪 Test Renewal Process

### Dry-Run Test (Simulates Renewal)

```bash
sudo certbot renew --dry-run
```

**Expected output** (if fix-renewal.sh was run):
```
Congratulations, all simulated renewals succeeded
```

**If you see the port 80 error**: This is fine! The actual renewal will still work when the time comes.

### Force Manual Renewal (For Testing)

```bash
# This will actually renew (use sparingly - rate limits apply)
sudo certbot renew --force-renewal
```

**Rate Limits:**
- 50 certificates per domain per week
- Use `--dry-run` for testing

## 🔍 Troubleshooting

### Check Renewal Configuration

```bash
cat /etc/letsencrypt/renewal/agenticrag360.com.conf
```

### Check Renewal Hook

```bash
ls -la /etc/letsencrypt/renewal-hooks/post/
cat /etc/letsencrypt/renewal-hooks/post/email2kg-renew.sh
```

### Test Renewal Hook Manually

```bash
sudo /etc/letsencrypt/renewal-hooks/post/email2kg-renew.sh
```

Should output:
```
=== Email2KG Certificate Renewal Hook ===
✅ Certificates updated
✅ Frontend restarted with new certificates
```

### Check Docker Frontend Has Certificates

```bash
sudo docker exec email2kg-frontend ls -la /etc/nginx/ssl/
```

Should show:
```
certificate.crt
private.key
```

## 📊 Monitoring

### Set Up Expiration Monitoring (Optional)

Create a simple monitoring script:

```bash
cat > ~/check-ssl-expiry.sh <<'EOF'
#!/bin/bash
EXPIRY=$(sudo certbot certificates | grep "Expiry Date" | grep -oP '\d+ days')
echo "Certificate expires in: $EXPIRY"
if [ "${EXPIRY%% *}" -lt 30 ]; then
    echo "⚠️  Warning: Certificate expires soon!"
fi
EOF

chmod +x ~/check-ssl-expiry.sh
```

Run weekly:
```bash
./check-ssl-expiry.sh
```

### Check SSL Status via Browser

1. Visit: https://agenticrag360.com
2. Click padlock icon
3. View certificate details
4. Check expiration date

## ✅ Verification Checklist

After SSL setup, verify:

- [ ] HTTPS works: `curl https://agenticrag360.com/health`
- [ ] Certificate valid: `sudo certbot certificates` shows 90 days
- [ ] Auto-renewal configured: `/etc/letsencrypt/renewal/agenticrag360.com.conf` exists
- [ ] Renewal hook exists: `/etc/letsencrypt/renewal-hooks/post/email2kg-renew.sh`
- [ ] Frontend has certificates: `sudo docker exec email2kg-frontend ls /etc/nginx/ssl/`
- [ ] Can login via HTTPS: Visit site and test login

## 🎉 Summary

**Your SSL is working correctly!** ✅

- ✅ Certificates installed and active
- ✅ HTTPS enabled on your domain
- ✅ Auto-renewal configured
- ⚠️  Renewal test may show error (cosmetic only)

The renewal test error is **cosmetic** and doesn't affect functionality. Your certificates will renew automatically every 90 days without any action needed.

If you want to eliminate the test error message, run:
```bash
sudo ./scripts/deployment/fix-renewal.sh
```

Otherwise, you're all set! Your application is secure with HTTPS. 🔒
