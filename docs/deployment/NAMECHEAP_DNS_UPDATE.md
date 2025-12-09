# Namecheap DNS Update Guide for EC2 IP Changes

## Overview

When your EC2 IP changes (e.g., from old IP to `34.245.66.42`), you need to update **TWO places**:

1. ✅ **Email2KG Configuration** (`.env` file) - [Already done!](#1-update-email2kg-configuration)
2. ⚠️ **Namecheap DNS Settings** - [Follow steps below](#2-update-namecheap-dns)

## Complete Update Process

### 1. Update Email2KG Configuration

```bash
# Already handled by our script!
./scripts/utils/update-domain.sh
```

### 2. Update Namecheap DNS

#### Step-by-Step Instructions:

**Step 1: Login to Namecheap**
- Go to: https://www.namecheap.com/
- Click "Sign In"
- Enter your credentials

**Step 2: Access DNS Settings**
1. Click "Domain List" in the left sidebar
2. Find your domain (e.g., `agenticrag360.com`)
3. Click "Manage" button next to your domain
4. Click "Advanced DNS" tab

**Step 3: Update A Records**

You should see records like this:

| Type | Host | Value | TTL |
|------|------|-------|-----|
| A Record | @ | OLD_IP | Automatic |
| A Record | www | OLD_IP | Automatic |

**Update them to:**

| Type | Host | Value | TTL |
|------|------|-------|-----|
| A Record | @ | **34.245.66.42** | Automatic |
| A Record | www | **34.245.66.42** | Automatic |

**Step 4: Save Changes**
- Click "Save all changes"
- Wait 5-30 minutes for DNS propagation

#### What Each Record Does:

- **@ (Root domain)**: Points `agenticrag360.com` → `34.245.66.42`
- **www**: Points `www.agenticrag360.com` → `34.245.66.42`

## Quick Visual Guide

### Before (Old IP):
```
agenticrag360.com     →  52.123.45.67 (OLD IP - BROKEN)
www.agenticrag360.com →  52.123.45.67 (OLD IP - BROKEN)
```

### After (New IP):
```
agenticrag360.com     →  34.245.66.42 (NEW IP - WORKING!)
www.agenticrag360.com →  34.245.66.42 (NEW IP - WORKING!)
```

## DNS Propagation Time

After updating Namecheap:
- **Minimum**: 5 minutes
- **Average**: 15-30 minutes
- **Maximum**: 24-48 hours (rare)

### Check DNS Propagation Status:

```bash
# Check if DNS has updated
nslookup agenticrag360.com

# Should show:
# Name:    agenticrag360.com
# Address: 34.245.66.42

# Or use online tool:
# https://www.whatsmydns.net/#A/agenticrag360.com
```

## Complete Update Checklist

When your EC2 IP changes, update in this order:

- [ ] **1. Update Email2KG `.env` file**
  ```bash
  ./scripts/utils/update-domain.sh
  # Enter your domain: agenticrag360.com
  ```

- [ ] **2. Restart Docker services**
  ```bash
  docker-compose down
  docker-compose up -d
  ```

- [ ] **3. Update Namecheap DNS**
  - Login to Namecheap
  - Advanced DNS → Update A Records
  - @ → 34.245.66.42
  - www → 34.245.66.42
  - Save changes

- [ ] **4. Update Google OAuth Console**
  - Go to: https://console.cloud.google.com/apis/credentials
  - Update redirect URI: `https://agenticrag360.com/api/auth/google/callback`

- [ ] **5. Wait for DNS propagation (15-30 min)**
  ```bash
  # Check propagation
  nslookup agenticrag360.com
  ```

- [ ] **6. Test your application**
  ```bash
  curl https://agenticrag360.com/health
  # Should return: {"status":"ok"}
  ```

- [ ] **7. Regenerate SSL Certificate (if needed)**
  ```bash
  ./scripts/deployment/setup-letsencrypt.sh
  ```

## Common DNS Record Types

| Record Type | Purpose | Example |
|-------------|---------|---------|
| **A Record** | Points domain to IPv4 address | agenticrag360.com → 34.245.66.42 |
| **CNAME** | Alias to another domain | www → agenticrag360.com |
| **MX** | Email server routing | mail.agenticrag360.com |
| **TXT** | Text records (SPF, verification) | Various |

**For Email2KG, you only need to update A Records!**

## Why Use Domain Instead of IP?

### Using IP Directly (34.245.66.42):
❌ Must update Namecheap when IP changes
❌ Must update `.env` when IP changes
❌ Must update Google OAuth when IP changes
❌ Users see ugly IP in browser
❌ No SSL certificate (Let's Encrypt won't work with IP)

### Using Domain (agenticrag360.com):
✅ Update Namecheap DNS only (once)
✅ `.env` stays same (no change needed!)
✅ Google OAuth stays same (no change!)
✅ Professional URL in browser
✅ SSL certificate works perfectly
✅ Easy to remember

**Recommendation**: Use your domain in `.env`:
```bash
PUBLIC_DOMAIN=agenticrag360.com
PUBLIC_PROTOCOL=https
```

This way:
- ✅ Users access: `https://agenticrag360.com`
- ✅ `.env` never needs updating
- ✅ Only update Namecheap when IP changes
- ✅ Everything else stays the same!

## Automated DNS Update (Advanced)

### Option 1: Namecheap Dynamic DNS

Enable Dynamic DNS in Namecheap for automatic updates:

1. **Enable DDNS in Namecheap:**
   - Domain List → Manage → Advanced DNS
   - Enable "Dynamic DNS"
   - Copy the DDNS password

2. **Install ddclient on EC2:**
   ```bash
   sudo apt-get update
   sudo apt-get install ddclient
   ```

3. **Configure ddclient:**
   ```bash
   sudo nano /etc/ddclient.conf
   ```

   Add:
   ```
   protocol=namecheap
   server=dynamicdns.park-your-domain.com
   login=agenticrag360.com
   password='YOUR_DDNS_PASSWORD'
   @.agenticrag360.com,www.agenticrag360.com
   ```

4. **Start service:**
   ```bash
   sudo systemctl start ddclient
   sudo systemctl enable ddclient
   ```

Now DNS updates automatically when IP changes!

### Option 2: Use Elastic IP (Best Solution)

**Stop IP from changing completely:**

1. **Allocate Elastic IP (AWS Console):**
   - EC2 → Elastic IPs → Allocate Elastic IP address
   - Note the allocated IP

2. **Associate with your instance:**
   - Select Elastic IP
   - Actions → Associate Elastic IP address
   - Choose your EC2 instance
   - Associate

3. **Update Namecheap DNS (ONE TIME):**
   - A Record @ → Your Elastic IP
   - A Record www → Your Elastic IP
   - Save

4. **Update `.env` (ONE TIME):**
   ```bash
   PUBLIC_DOMAIN=agenticrag360.com
   PUBLIC_PROTOCOL=https
   ```

5. **DONE! IP never changes again!** 🎉

**Cost**: FREE while running (~$3.60/month if stopped)

## Troubleshooting

### Issue: DNS not propagating
**Solution:**
```bash
# Clear local DNS cache

# macOS:
sudo dscacheutil -flushcache

# Linux:
sudo systemd-resolve --flush-caches

# Windows:
ipconfig /flushdns
```

### Issue: Old IP still showing
**Solution:**
- Wait longer (up to 24 hours in rare cases)
- Check TTL settings (lower = faster updates)
- Use incognito/private browsing
- Try different device/network

### Issue: "Site can't be reached"
**Solution:**
```bash
# 1. Check if IP is correct
nslookup agenticrag360.com
# Should show: 34.245.66.42

# 2. Check if services are running
docker-compose ps

# 3. Check if port 443 is open
sudo ufw status
# Allow: 80/tcp, 443/tcp

# 4. Check nginx logs
docker-compose logs frontend
```

### Issue: SSL certificate error
**Solution:**
```bash
# Regenerate certificate for new IP
./scripts/deployment/setup-letsencrypt.sh
```

## Quick Commands Reference

```bash
# Check current DNS
nslookup agenticrag360.com
dig agenticrag360.com

# Check from different locations
curl -s https://www.whatsmydns.net/api/details?server=google&query=agenticrag360.com&type=A | jq

# Test if site is accessible
curl -I https://agenticrag360.com

# Check SSL certificate
openssl s_client -connect agenticrag360.com:443 -servername agenticrag360.com

# View current IP from EC2
curl ifconfig.me

# Update Email2KG config
./scripts/utils/update-domain.sh
```

## Best Practice Workflow

### For Production (Recommended):

1. **Get Elastic IP** ($0 while running)
2. **Configure domain once** in Namecheap
3. **Use domain in `.env`**: `PUBLIC_DOMAIN=agenticrag360.com`
4. **Never update again!** ✅

### For Development/Testing:

1. **Accept IP changes** (free)
2. **Update both** Namecheap + `.env` when IP changes
3. **Use update script**: `./scripts/utils/update-domain.sh`

## Need Help?

- **Namecheap Support**: https://www.namecheap.com/support/
- **DNS Checker**: https://www.whatsmydns.net/
- **SSL Checker**: https://www.ssllabs.com/ssltest/

## Summary

✅ **Always update BOTH places:**
1. Email2KG `.env` file (use script)
2. Namecheap DNS A records (manual)

✅ **Best solution: Use Elastic IP + Domain**
- No more updates needed
- Professional setup
- Set it and forget it!
