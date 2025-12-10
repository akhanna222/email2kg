# API 404 Errors - Login/Signup "Not Found"

## 🔴 Symptom

When trying to login or signup, you get "Not Found" error:

**Browser Console:**
```
api/auth/register:1  Failed to load resource: the server responded with a status of 404 ()
api/auth/login:1  Failed to load resource: the server responded with a status of 404 ()
AuthContext.tsx:64 Registration error: Error: Not Found
AuthContext.tsx:53 Login error: Error: Not Found
```

**User Experience:**
- Click "Sign Up" → shows "Not Found" error
- Click "Login" → shows "Not Found" error
- No meaningful error message

---

## 🔍 Root Causes

### 1. Backend Container Not Running

The most common cause - backend API is not accessible.

**Check:**
```bash
sudo docker ps | grep backend
```

**Should show:**
```
email2kg-backend   Up X minutes (healthy)   0.0.0.0:8000->8000/tcp
```

**If missing or unhealthy:** Backend container crashed or didn't start.

---

### 2. Nginx Not Proxying `/api/` to Backend

Nginx receives request but doesn't forward to backend.

**Check:**
```bash
# Check nginx config
sudo docker exec email2kg-frontend cat /etc/nginx/conf.d/default.conf | grep -A10 "location /api/"
```

**Should show:**
```nginx
location /api/ {
    set $backend_upstream http://backend:8000;
    proxy_pass $backend_upstream/api/;
    ...
}
```

**If missing:** Nginx config doesn't have API proxy rules.

---

### 3. Backend Routes Not Registered

Backend running but auth routes not configured.

**Check:**
```bash
# Test backend directly (inside Docker network)
sudo docker exec email2kg-backend curl -s http://localhost:8000/api/health

# Check available routes
sudo docker compose logs backend | grep -i "route"
```

**Should show:** Health check returns 200, routes are registered.

---

### 4. CORS Blocking Requests

Backend rejecting requests due to CORS policy.

**Check browser console for:**
```
Access to fetch at 'https://agenticrag360.com/api/auth/login' from origin 'https://agenticrag360.com' has been blocked by CORS policy
```

**If present:** CORS configuration issue (see [CORS_ERRORS.md](./CORS_ERRORS.md))

---

## ✅ Solutions

### Fix 1: Restart Backend Container

**Most Common Fix - Try This First**

```bash
cd ~/email2kg

# Check if backend is running
sudo docker ps | grep backend

# Restart backend
sudo docker compose restart backend

# Wait 10 seconds
sleep 10

# Check status
sudo docker ps | grep backend

# Test API
curl https://agenticrag360.com/api/health
```

**Expected:** Backend restarts and API returns `{"status":"healthy"}`

---

### Fix 2: Update .env and Restart

Your `.env` might still have `PUBLIC_PROTOCOL=http` from earlier troubleshooting.

```bash
cd ~/email2kg

# Check current protocol
grep PUBLIC_PROTOCOL .env

# If it shows http, update it
nano .env
# Change: PUBLIC_PROTOCOL=https
# Save: Ctrl+X, Y, Enter

# Restart backend to apply changes
sudo docker compose restart backend

# Test
curl https://agenticrag360.com/api/health
```

---

### Fix 3: Check Backend Logs for Errors

Backend might be crashing on startup.

```bash
# View backend logs
sudo docker compose logs backend --tail=100

# Look for errors
sudo docker compose logs backend | grep -i error

# Check if database connected
sudo docker compose logs backend | grep -i "database"
```

**Common errors and fixes:**

**"Cannot connect to database"**
```bash
# Check if postgres is running
sudo docker ps | grep postgres

# Restart postgres and backend
sudo docker compose restart postgres backend
```

**"Secret key not set"**
```bash
# Check .env has SECRET_KEY
grep SECRET_KEY .env

# If missing, add it
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)" >> .env

# Restart backend
sudo docker compose restart backend
```

**"Port 8000 already in use"**
```bash
# Find what's using port 8000
sudo lsof -i :8000

# Kill the process or change port in docker-compose.yml
```

---

### Fix 4: Rebuild Backend Container

If backend has old code or configuration issues.

```bash
cd ~/email2kg

# Stop backend
sudo docker compose stop backend

# Remove backend container and image
sudo docker rm email2kg-backend
sudo docker rmi email2kg-backend

# Rebuild and start
sudo docker compose build --no-cache backend
sudo docker compose up -d backend

# Wait for startup
sleep 15

# Test
curl https://agenticrag360.com/api/health
```

---

### Fix 5: Verify Nginx Proxy Configuration

Ensure nginx is correctly forwarding `/api/` to backend.

```bash
# Check nginx config in container
sudo docker exec email2kg-frontend cat /etc/nginx/conf.d/default.conf | grep -A15 "location /api/"

# Should show proxy_pass to backend:8000
```

**If proxy config is missing:**

```bash
# Rebuild frontend
sudo docker compose build --no-cache frontend
sudo docker compose up -d frontend
```

---

## 🧪 Testing

### Test 1: Backend Health (Direct)

```bash
# Test backend container directly
sudo docker exec email2kg-backend curl -s http://localhost:8000/api/health

# Expected: {"status":"healthy"}
```

**If this works:** Backend is running, issue is with nginx proxy.

**If this fails:** Backend has internal issues.

---

### Test 2: API Through Nginx

```bash
# Test through nginx proxy
curl https://agenticrag360.com/api/health

# Expected: {"status":"healthy"}
```

**If this works:** Nginx proxy is working.

**If this fails:** Nginx not proxying correctly.

---

### Test 3: Register New User

```bash
# Try to register via API
curl -X POST https://agenticrag360.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "full_name": "Test User"
  }'

# Expected: {"access_token":"...","token_type":"bearer"}
# Or: {"detail":"User already exists"}
```

**If 404:** Backend auth routes not working.

**If 422:** Missing required fields (check backend schema).

**If 200/201:** Success! Auth is working.

---

### Test 4: Login

```bash
# Try to login
curl -X POST https://agenticrag360.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'

# Expected: {"access_token":"...","token_type":"bearer"}
```

---

## 🔍 Debugging Steps

### Step 1: Check All Services Running

```bash
sudo docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

**Must show all 5 services:**
- ✅ email2kg-backend (healthy, port 8000)
- ✅ email2kg-frontend (healthy, ports 80, 443)
- ✅ email2kg-db (healthy)
- ✅ email2kg-redis (healthy)
- ✅ email2kg-celery-worker

---

### Step 2: Check Backend Startup Logs

```bash
sudo docker compose logs backend --tail=50
```

**Look for:**
- ✅ "Application startup complete"
- ✅ "Uvicorn running on http://0.0.0.0:8000"
- ✅ "Connected to database"
- ❌ Any ERROR or CRITICAL messages

---

### Step 3: Check Network Connectivity

```bash
# Can nginx reach backend?
sudo docker exec email2kg-frontend ping -c 3 backend

# Can backend reach database?
sudo docker exec email2kg-backend ping -c 3 postgres

# Can backend reach redis?
sudo docker exec email2kg-backend ping -c 3 redis
```

All should succeed (3 packets transmitted, 3 received).

---

### Step 4: Check Environment Variables

```bash
# In backend container
sudo docker exec email2kg-backend env | grep -E "DATABASE_URL|SECRET_KEY|ALLOWED_ORIGINS"
```

**Should show:**
- `DATABASE_URL=postgresql://...`
- `SECRET_KEY=...` (long random string)
- `ALLOWED_ORIGINS=...` (includes https://agenticrag360.com)

---

## 📋 Complete Fix Procedure

If nothing else works, do a complete reset:

```bash
cd ~/email2kg

# 1. Stop all services
sudo docker compose down

# 2. Verify .env configuration
nano .env
# Ensure:
#   PUBLIC_PROTOCOL=https
#   PUBLIC_DOMAIN=agenticrag360.com
#   SECRET_KEY=<random-value>
#   JWT_SECRET_KEY=<random-value>
#   DATABASE_URL=postgresql://postgres:...@postgres:5432/email2kg

# 3. Remove backend container and image
sudo docker rm email2kg-backend 2>/dev/null || true
sudo docker rmi email2kg-backend 2>/dev/null || true

# 4. Rebuild all services
sudo docker compose build --no-cache

# 5. Start services
sudo docker compose up -d

# 6. Wait for startup
sleep 30

# 7. Check status
sudo docker ps

# 8. Test API
curl https://agenticrag360.com/api/health

# 9. Try login in browser
```

---

## ✅ Success Checklist

After fixing, verify:

- [ ] All 5 containers running: `sudo docker ps`
- [ ] Backend healthy: `curl https://agenticrag360.com/api/health`
- [ ] Can register: Try signup in browser
- [ ] Can login: Try login in browser
- [ ] No 404 errors in browser console
- [ ] No CORS errors in browser console

---

## 🆘 Still Not Working?

If API 404 errors persist after all fixes:

1. **Capture full diagnostic output:**
   ```bash
   sudo docker ps > api_debug.txt
   sudo docker compose logs backend --tail=200 >> api_debug.txt
   sudo docker compose logs frontend --tail=50 >> api_debug.txt
   curl -v https://agenticrag360.com/api/health >> api_debug.txt 2>&1
   ```

2. **Check backend routes:**
   ```bash
   sudo docker exec email2kg-backend python -c "from app.main import app; print([r.path for r in app.routes])"
   ```

3. **Create GitHub issue** with:
   - Output from step 1
   - Output from step 2
   - Screenshots of browser console errors
   - What you've already tried

---

## 📚 Related Guides

- [CORS Errors](./CORS_ERRORS.md) - If you see CORS policy errors
- [Service Won't Start](./SERVICE_WONT_START.md) - If backend container crashes
- [Database Connection](./DATABASE_CONNECTION.md) - If database connection fails

---

**Last Updated:** December 2025
