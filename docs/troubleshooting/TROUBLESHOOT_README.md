# Troubleshooting Guide - Email2KG

This directory contains detailed troubleshooting guides for common issues encountered during deployment and operation of Email2KG.

---

## 📚 Troubleshooting Guides

### Authentication & API Issues
- **[API 404 Errors](./API_404_ERRORS.md)** - Login/signup returns "Not Found"
- **[CORS Errors](./CORS_ERRORS.md)** - Cross-origin request blocked
- **[OAuth Issues](./OAUTH_ISSUES.md)** - Gmail/Outlook login not working

### SSL/HTTPS Issues
- **[HTTPS Not Working](../deployment/HTTPS_NOT_WORKING.md)** - Can't connect to port 443
- **[SSL Certificate Errors](./SSL_CERTIFICATE_ERRORS.md)** - Certificate invalid or expired
- **[Mixed Content](./MIXED_CONTENT.md)** - HTTP resources on HTTPS page

### Deployment Issues
- **[Docker Build Failures](./DOCKER_BUILD_FAILURES.md)** - Container build errors
- **[Service Won't Start](./SERVICE_WONT_START.md)** - Container crashes or won't run
- **[Database Connection](./DATABASE_CONNECTION.md)** - Can't connect to PostgreSQL

### Performance Issues
- **[Slow OCR Processing](./SLOW_OCR.md)** - Document processing takes too long
- **[High Memory Usage](./HIGH_MEMORY.md)** - Services consuming too much RAM
- **[Celery Worker Issues](./CELERY_ISSUES.md)** - Background tasks not processing

### Email Integration
- **[Gmail Sync Failing](./GMAIL_SYNC_FAILING.md)** - Can't sync emails from Gmail
- **[Attachment Processing](./ATTACHMENT_PROCESSING.md)** - Attachments not being processed
- **[Email Categorization](./EMAIL_CATEGORIZATION.md)** - Emails not categorized correctly

---

## 🎯 Quick Diagnostic Commands

### Check Service Status
```bash
# All containers
sudo docker ps

# Specific service logs
sudo docker compose logs backend --tail=50
sudo docker compose logs frontend --tail=50
sudo docker compose logs celery_worker --tail=50
```

### Test API Endpoints
```bash
# Health check
curl https://agenticrag360.com/health

# Backend health
curl https://agenticrag360.com/api/health

# Test auth endpoint
curl -X POST https://agenticrag360.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

### Check Configuration
```bash
# Environment variables
cat .env | grep -v PASSWORD | grep -v SECRET

# Nginx config in container
sudo docker exec email2kg-frontend cat /etc/nginx/conf.d/default.conf

# Backend logs for startup errors
sudo docker compose logs backend --tail=100 | grep -i error
```

---

## 🔍 Common Issues by Symptom

### "Not Found" / 404 Errors on API Calls

**Symptoms:**
- Login/signup returns "Not Found"
- API calls to `/api/*` return 404
- Developer console shows `Failed to load resource: 404`

**Likely Causes:**
1. Backend container not running
2. Nginx not proxying `/api/` to backend
3. Backend routes not registered
4. CORS blocking requests

**Fix:** See [API 404 Errors](./API_404_ERRORS.md)

---

### "Access Blocked by CORS Policy"

**Symptoms:**
- Browser console shows CORS error
- API calls fail with CORS message
- `Access-Control-Allow-Origin` missing

**Likely Causes:**
1. `ALLOWED_ORIGINS` not configured correctly in `.env`
2. Frontend URL not in `ALLOWED_ORIGINS`
3. Backend not sending CORS headers

**Fix:** See [CORS Errors](./CORS_ERRORS.md)

---

### SSL/HTTPS Connection Failed

**Symptoms:**
- `curl: (7) Failed to connect to port 443`
- `SSL_ERROR_SYSCALL`
- Browser shows "Connection refused"

**Likely Causes:**
1. Port 443 not open in security group
2. Nginx not configured for SSL
3. SSL certificates not mounted
4. Nginx not listening on port 443

**Fix:** See [HTTPS Not Working](../deployment/HTTPS_NOT_WORKING.md)

---

### Container Keeps Restarting

**Symptoms:**
- `docker ps` shows container constantly restarting
- Service unhealthy in `docker compose ps`
- Application not accessible

**Likely Causes:**
1. Missing environment variables
2. Database connection failed
3. Port already in use
4. Application crash on startup

**Fix:** See [Service Won't Start](./SERVICE_WONT_START.md)

---

### Celery Worker Not Processing Tasks

**Symptoms:**
- Emails synced but attachments not processed
- Background tasks stuck in queue
- `docker logs celery_worker` shows no activity

**Likely Causes:**
1. Redis connection failed
2. Worker not connected to queue
3. Tasks not being queued
4. Worker crashed

**Fix:** See [Celery Worker Issues](./CELERY_ISSUES.md)

---

## 🆘 Getting Help

### Before Asking for Help

Gather this information:

```bash
# 1. Service status
sudo docker ps > debug_info.txt

# 2. Container logs
sudo docker compose logs --tail=100 >> debug_info.txt

# 3. Environment config (sanitized)
cat .env | grep -v PASSWORD | grep -v SECRET >> debug_info.txt

# 4. Recent errors
sudo docker compose logs backend --tail=50 | grep -i error >> debug_info.txt
sudo docker compose logs frontend --tail=50 | grep -i error >> debug_info.txt

# 5. Network connectivity
curl -v https://agenticrag360.com/health >> debug_info.txt 2>&1
curl -v https://agenticrag360.com/api/health >> debug_info.txt 2>&1
```

### Where to Get Help

- **GitHub Issues:** https://github.com/akhanna222/email2kg/issues
- **Documentation:** Check this troubleshooting directory first
- **Email Support:** support@email2kg.com
- **Community:** [Discussion Forum]

### What to Include

1. Detailed description of the issue
2. Steps to reproduce
3. Expected vs actual behavior
4. Output from diagnostic commands above
5. Screenshots of errors (if applicable)
6. What you've already tried

---

## 📊 Diagnostic Scripts

Located in `scripts/utils/`:

- **`diagnose-https.sh`** - Complete HTTPS diagnostics
- **`quick-ssl-check.sh`** - Fast SSL validation
- More scripts available in repository

---

## 🔄 Common Fixes Summary

| Issue | Quick Fix | Detailed Guide |
|-------|-----------|----------------|
| API 404 | Restart backend: `sudo docker compose restart backend` | [API 404 Errors](./API_404_ERRORS.md) |
| CORS | Update `.env` ALLOWED_ORIGINS | [CORS Errors](./CORS_ERRORS.md) |
| HTTPS | Run `./scripts/deployment/final-ssl-fix.sh` | [HTTPS Not Working](../deployment/HTTPS_NOT_WORKING.md) |
| Login fails | Check backend logs, verify .env | [API 404 Errors](./API_404_ERRORS.md) |
| Slow performance | Scale workers, check resources | [Performance Issues](./SLOW_OCR.md) |

---

**Last Updated:** December 2025
**Version:** 2.0.0
