# Complete IP Change Checklist

When your EC2 IP changes, follow this checklist to ensure everything works.

## Your New IP: 34.245.66.42

## ✅ Step-by-Step Checklist

### Phase 1: Update Email2KG Configuration (5 minutes)

- [ ] **1.1 Run update script**
  ```bash
  cd /path/to/email2kg
  ./scripts/utils/update-domain.sh
  ```
  - Enter new IP or domain
  - Select protocol (HTTPS recommended)

- [ ] **1.2 Verify .env file**
  ```bash
  grep -E "PUBLIC_DOMAIN|PUBLIC_PROTOCOL" .env
  ```
  Should show:
  ```
  PUBLIC_DOMAIN=34.245.66.42  (or agenticrag360.com)
  PUBLIC_PROTOCOL=https
  ```

- [ ] **1.3 Restart Docker services**
  ```bash
  docker-compose down
  docker-compose up -d
  ```

- [ ] **1.4 Verify services are running**
  ```bash
  docker-compose ps
  ```
  All services should show "Up" or "healthy"

---

### Phase 2: Update Namecheap DNS (15-30 minutes)

**Only if using a domain (e.g., agenticrag360.com)**

- [ ] **2.1 Login to Namecheap**
  - URL: https://www.namecheap.com/
  - Sign in to your account

- [ ] **2.2 Access Advanced DNS**
  - Click "Domain List"
  - Find your domain: `agenticrag360.com`
  - Click "Manage"
  - Click "Advanced DNS" tab

- [ ] **2.3 Update A Records**
  Update these records:

  | Type | Host | Value | TTL |
  |------|------|-------|-----|
  | A Record | @ | **34.245.66.42** | Automatic |
  | A Record | www | **34.245.66.42** | Automatic |

- [ ] **2.4 Save changes**
  - Click "Save all changes" button
  - Note the time (for propagation tracking)

- [ ] **2.5 Wait for DNS propagation (15-30 min)**
  Check status:
  ```bash
  # Local check
  nslookup agenticrag360.com

  # Global check
  # Visit: https://www.whatsmydns.net/#A/agenticrag360.com
  ```

---

### Phase 3: Update OAuth Providers (5 minutes)

- [ ] **3.1 Update Google OAuth Console**
  1. Go to: https://console.cloud.google.com/apis/credentials
  2. Select your OAuth 2.0 Client ID
  3. Under "Authorized redirect URIs", add:
     - If using IP: `https://34.245.66.42/api/auth/google/callback`
     - If using domain: `https://agenticrag360.com/api/auth/google/callback`
  4. Click "Save"
  5. Wait 5 minutes for changes to propagate

- [ ] **3.2 Remove old redirect URI (optional)**
  - Remove the old IP's redirect URI to keep things clean

---

### Phase 4: SSL Certificate Update (10 minutes)

**Only if using HTTPS**

- [ ] **4.1 Stop Docker services**
  ```bash
  docker-compose down
  ```

- [ ] **4.2 Remove old certificates**
  ```bash
  sudo rm -rf ssl/
  ```

- [ ] **4.3 Generate new SSL certificate**
  ```bash
  ./scripts/deployment/setup-letsencrypt.sh
  ```

- [ ] **4.4 Restart services**
  ```bash
  docker-compose up -d
  ```

**Note:** If you're using a domain (not IP), SSL should work automatically. IPs may have issues with Let's Encrypt.

---

### Phase 5: Verification & Testing (5 minutes)

- [ ] **5.1 Test backend health**
  ```bash
  # If using IP:
  curl https://34.245.66.42/health

  # If using domain:
  curl https://agenticrag360.com/health
  ```
  Expected: `{"status":"ok"}` or similar

- [ ] **5.2 Test frontend**
  Open in browser:
  - https://34.245.66.42 (or https://agenticrag360.com)
  - Should load the application

- [ ] **5.3 Test OAuth login**
  - Click "Login with Google"
  - Should redirect to Google
  - Should redirect back successfully
  - Should not show redirect URI mismatch error

- [ ] **5.4 Test email sync**
  - After logging in, try syncing emails
  - Should not show CORS errors
  - Check browser console (F12) for errors

- [ ] **5.5 Check Docker logs**
  ```bash
  # Check all services
  docker-compose logs --tail=50

  # Check specific service
  docker-compose logs backend --tail=50
  docker-compose logs frontend --tail=50
  docker-compose logs celery_worker --tail=50
  ```
  Look for any errors

- [ ] **5.6 Test from different network**
  - Try accessing from your phone (not on same WiFi)
  - Try from a different computer
  - Ensures it works externally, not just locally

---

## Quick Reference

### Current Configuration

```bash
# Check current settings
grep PUBLIC_DOMAIN .env
grep PUBLIC_PROTOCOL .env

# Check DNS
nslookup agenticrag360.com

# Check if services are up
docker-compose ps

# View logs
docker-compose logs -f
```

### URLs to Update

When IP changes, update these:

| Service | URL to Update | New Value |
|---------|---------------|-----------|
| Email2KG .env | `PUBLIC_DOMAIN` | `34.245.66.42` or `agenticrag360.com` |
| Namecheap DNS | A Record @ | `34.245.66.42` |
| Namecheap DNS | A Record www | `34.245.66.42` |
| Google OAuth | Redirect URI | `https://agenticrag360.com/api/auth/google/callback` |

### Troubleshooting Commands

```bash
# Test if port is open
nc -zv 34.245.66.42 443

# Check SSL certificate
openssl s_client -connect agenticrag360.com:443 -servername agenticrag360.com

# Check current public IP
curl ifconfig.me

# Flush DNS cache (if old IP still shows)
# macOS: sudo dscacheutil -flushcache
# Linux: sudo systemd-resolve --flush-caches
# Windows: ipconfig /flushdns

# Restart single service
docker-compose restart backend
docker-compose restart celery_worker
docker-compose restart frontend
```

---

## Common Issues

### Issue: "Site can't be reached"
**Cause:** DNS not updated or not propagated yet
**Solution:**
1. Check DNS: `nslookup agenticrag360.com`
2. Wait 30 minutes for propagation
3. Flush DNS cache
4. Try different browser/device

### Issue: CORS errors in browser console
**Cause:** `.env` not updated or services not restarted
**Solution:**
1. Verify: `grep PUBLIC_DOMAIN .env`
2. Restart: `docker-compose restart backend celery_worker`
3. Clear browser cache and reload

### Issue: "Redirect URI mismatch" OAuth error
**Cause:** Google OAuth not updated
**Solution:**
1. Go to Google Cloud Console
2. Update redirect URI to match new IP/domain
3. Wait 5 minutes
4. Try again

### Issue: SSL certificate error
**Cause:** Certificate for old IP
**Solution:**
```bash
docker-compose down
sudo rm -rf ssl/
./scripts/deployment/setup-letsencrypt.sh
docker-compose up -d
```

### Issue: Services not starting
**Cause:** Configuration error
**Solution:**
```bash
# Check logs
docker-compose logs

# Verify .env syntax (no quotes needed)
cat .env | grep PUBLIC

# Restart fresh
docker-compose down -v
docker-compose up -d
```

---

## Time Estimates

| Phase | Estimated Time | Can Work in Parallel? |
|-------|----------------|----------------------|
| Phase 1: Email2KG Config | 5 minutes | No |
| Phase 2: Namecheap DNS | 15-30 minutes | Yes (waiting) |
| Phase 3: OAuth Update | 5 minutes | Yes (while DNS propagates) |
| Phase 4: SSL Certificate | 10 minutes | No (after DNS) |
| Phase 5: Testing | 5 minutes | No |
| **Total** | **40-55 minutes** | |

**Tip:** While waiting for DNS propagation (Phase 2), you can do Phase 3 (OAuth update).

---

## Best Practice: Avoid This Entirely

### Use Elastic IP (Recommended)

**One-time setup, never update again:**

1. **Allocate Elastic IP:**
   ```bash
   # AWS Console: EC2 → Elastic IPs → Allocate
   # Cost: FREE while running
   ```

2. **Associate with instance:**
   ```bash
   # AWS Console: Actions → Associate → Select instance
   ```

3. **Update everything ONE LAST TIME:**
   - Update Namecheap DNS A records
   - Update `.env` with domain
   - Update Google OAuth
   - Generate SSL certificate

4. **Done forever!** IP never changes on stop/start 🎉

**Cost:** FREE while instance runs, ~$3.60/month if stopped

---

## Completed? Print This!

```
✅ Updated Email2KG .env file
✅ Restarted Docker services
✅ Updated Namecheap DNS (if using domain)
✅ Waited for DNS propagation
✅ Updated Google OAuth redirect URI
✅ Regenerated SSL certificate (if needed)
✅ Tested backend health endpoint
✅ Tested frontend in browser
✅ Tested OAuth login
✅ Tested email sync
✅ No errors in logs

New IP/Domain: 34.245.66.42 / agenticrag360.com
Date Completed: _______________
Notes: ____________________________________
```

---

## Quick Links

- **Namecheap Login**: https://www.namecheap.com/
- **Google OAuth Console**: https://console.cloud.google.com/apis/credentials
- **DNS Checker**: https://www.whatsmydns.net/
- **SSL Checker**: https://www.ssllabs.com/ssltest/

**Full Guides:**
- [Namecheap DNS Update Guide](NAMECHEAP_DNS_UPDATE.md)
- [EC2 IP Management](EC2_IP_MANAGEMENT.md)
- [Quick Update Guide](../../QUICK_IP_UPDATE.md)
