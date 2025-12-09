# HTTPS Not Working - Quick Fix Guide

## 🔴 Symptom

```bash
# HTTP works:
curl http://agenticrag360.com/health
✅ healthy

# HTTPS doesn't work:
curl https://agenticrag360.com/health
❌ curl: (7) Failed to connect to agenticrag360.com port 443: Couldn't connect to server
```

---

## 🔍 Run Diagnostics (on your EC2 server)

```bash
cd ~/email2kg
chmod +x scripts/utils/diagnose-https.sh
sudo ./scripts/utils/diagnose-https.sh
```

This will check:
- ✅ Container status
- ✅ Port 443 listening
- ✅ SSL certificates exist
- ✅ Nginx configuration
- ✅ Security group access

---

## 🎯 Most Common Issue: EC2 Security Group

**Port 443 is likely blocked by your EC2 security group.**

### Quick Fix:

1. **Go to AWS Console**
   - Open: https://console.aws.amazon.com/ec2/
   - Region: Check you're in the correct region (top-right)

2. **Find Your Security Group**
   - Left menu → **Security Groups**
   - Find the security group attached to your EC2 instance
   - Click on it

3. **Add HTTPS Rule**
   - Click **"Edit inbound rules"** button
   - Click **"Add rule"**
   - Configure:
     ```
     Type: HTTPS
     Protocol: TCP
     Port range: 443
     Source: 0.0.0.0/0
     Description: Allow HTTPS traffic
     ```
   - Click **"Save rules"**

4. **Test After 30 Seconds**
   ```bash
   curl https://agenticrag360.com/health
   ```
   Should return: `healthy` ✅

---

## 🔧 Alternative Issues & Fixes

### Issue 1: SSL Certificates Missing

**Symptom:**
```bash
ls ssl/
# Output: No such file or directory
```

**Fix:**
```bash
# Check if Let's Encrypt certificates exist
sudo ls /etc/letsencrypt/live/agenticrag360.com/

# If they exist, copy them
sudo mkdir -p ssl
sudo cp /etc/letsencrypt/live/agenticrag360.com/fullchain.pem ssl/certificate.crt
sudo cp /etc/letsencrypt/live/agenticrag360.com/privkey.pem ssl/private.key
sudo chmod 644 ssl/certificate.crt
sudo chmod 600 ssl/private.key
sudo chown $USER:$USER ssl/*

# Restart frontend
sudo docker compose restart frontend

# Test
curl -k https://localhost/health
```

### Issue 2: Nginx Not Configured for SSL

**Symptom:**
```bash
sudo netstat -tlnp | grep :443
# Output: (nothing - port 443 not listening)
```

**Fix:**
```bash
# Check nginx config
docker exec email2kg-frontend cat /etc/nginx/conf.d/default.conf | grep "listen 443"

# If no "listen 443" line, nginx is using wrong config
# Rebuild with correct config:
sudo docker compose down
sudo docker compose up --build -d

# Verify
sudo netstat -tlnp | grep :443
```

### Issue 3: Firewall Blocking Port 443

**Symptom:**
```bash
sudo ufw status
# Output: Status: active
```

**Fix:**
```bash
# Allow port 443
sudo ufw allow 443/tcp
sudo ufw status

# Test
curl https://agenticrag360.com/health
```

### Issue 4: SSL Certificates Not Mounted in Container

**Symptom:**
```bash
docker exec email2kg-frontend ls /etc/nginx/ssl/
# Output: cannot access '/etc/nginx/ssl/': No such file or directory
```

**Fix:**
```bash
# Check docker-compose.yml has SSL volume
cat docker-compose.yml | grep -A10 "frontend:" | grep ssl

# Should show:
# - ./ssl:/etc/nginx/ssl:ro

# If missing, rebuild:
sudo docker compose down
sudo docker compose up -d
```

---

## 🧪 Testing Steps

### Step 1: Test Locally (Inside Server)
```bash
# Should work if nginx is configured correctly
curl -k https://localhost/health
```
- ✅ Works → Nginx SSL is configured correctly
- ❌ Fails → Nginx configuration issue

### Step 2: Test Port 443 Listening
```bash
sudo netstat -tlnp | grep :443
```
- ✅ Shows output → Port 443 is listening
- ❌ No output → Nginx not configured for SSL

### Step 3: Test Externally (From Your Computer)
```bash
# From your local machine (not the server)
curl https://agenticrag360.com/health
```
- ✅ Works → Everything configured correctly!
- ❌ Fails → Security group or firewall blocking

### Step 4: Test Security Group
```bash
# On EC2 server:
nc -zv localhost 443
# Should show: Connection to localhost 443 port [tcp/https] succeeded!

# From your local machine:
nc -zv agenticrag360.com 443
# Should show: Connection to agenticrag360.com 443 port [tcp/https] succeeded!
```
- ✅ Both succeed → Everything works
- ❌ Local succeeds, external fails → Security group issue

---

## ✅ Expected Working State

When everything is configured correctly:

### 1. Certificates Exist
```bash
ls -la ssl/
# -rw-r--r-- 1 ubuntu ubuntu 5582 Dec 9 certificate.crt
# -rw------- 1 ubuntu ubuntu 1704 Dec 9 private.key
```

### 2. Port 443 Listening
```bash
sudo netstat -tlnp | grep :443
# tcp6  0  0 :::443  :::*  LISTEN  1234/docker-proxy
```

### 3. Container Running with Port 443
```bash
sudo docker ps | grep frontend
# email2kg-frontend  0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
```

### 4. Nginx Configured for SSL
```bash
docker exec email2kg-frontend cat /etc/nginx/conf.d/default.conf | grep "listen 443"
# listen 443 ssl;
# listen [::]:443 ssl;
```

### 5. HTTPS Works
```bash
curl https://agenticrag360.com/health
# healthy
```

---

## 🚀 Complete Fix Procedure

If none of the above works, do a complete reset:

```bash
cd ~/email2kg

# 1. Stop all services
sudo docker compose down

# 2. Ensure certificates exist
sudo ls /etc/letsencrypt/live/agenticrag360.com/
# If not exist: run sudo ./scripts/deployment/enable-https.sh

# 3. Copy certificates to project
sudo mkdir -p ssl
sudo cp /etc/letsencrypt/live/agenticrag360.com/fullchain.pem ssl/certificate.crt
sudo cp /etc/letsencrypt/live/agenticrag360.com/privkey.pem ssl/private.key
sudo chmod 644 ssl/certificate.crt
sudo chmod 600 ssl/private.key
sudo chown $USER:$USER ssl/*

# 4. Verify certificates
ls -la ssl/
openssl x509 -in ssl/certificate.crt -noout -dates

# 5. Check docker-compose.yml has SSL volume
grep -A5 "frontend:" docker-compose.yml | grep ssl
# Should show: - ./ssl:/etc/nginx/ssl:ro

# 6. Start services
sudo docker compose up --build -d

# 7. Wait 30 seconds
sleep 30

# 8. Test locally
curl -k https://localhost/health

# 9. If local works, add security group rule for port 443
# (see EC2 Security Group section above)

# 10. Test externally
curl https://agenticrag360.com/health
```

---

## 📞 Still Not Working?

Run full diagnostics:
```bash
sudo ./scripts/utils/diagnose-https.sh > https-diagnostics.txt
cat https-diagnostics.txt
```

Check each section for ❌ marks and follow the recommendations.

---

## 🎯 Quick Reference

| Issue | Check | Fix |
|-------|-------|-----|
| Security group | AWS Console → Security Groups | Add HTTPS rule (port 443) |
| Certificates missing | `ls ssl/` | Copy from `/etc/letsencrypt/` |
| Port not listening | `netstat -tlnp \| grep 443` | Rebuild containers |
| Firewall blocking | `ufw status` | `ufw allow 443/tcp` |
| Wrong nginx config | `docker exec ... cat nginx.conf` | Rebuild with `--build` |

---

## ✨ Success Confirmation

You know HTTPS is working when:

```bash
# 1. External HTTPS works
curl https://agenticrag360.com/health
# → healthy ✅

# 2. Browser shows padlock
# Visit: https://agenticrag360.com
# → Padlock icon visible ✅

# 3. HTTP redirects to HTTPS
curl -I http://agenticrag360.com
# → 301 Moved Permanently
# → Location: https://agenticrag360.com ✅

# 4. Can login via HTTPS
# Visit: https://agenticrag360.com
# → Can signup/login without errors ✅
```

Your application is now secure with HTTPS! 🔒
