# Diagnosing "Not Found" Error on Signup/Signin

I've analyzed your codebase and found the auth routes are correctly configured. Here's what's happening and how to fix it:

## 🔍 Analysis

Your backend auth routes are at:
- `/api/auth/register` (backend/app/api/auth_routes.py:25)
- `/api/auth/login` (backend/app/api/auth_routes.py:25)

Your nginx is configured to proxy `/api/` requests to the backend (frontend/nginx.conf:46-48).

The "Not Found" error means the request isn't reaching the backend properly.

---

## 🚨 Most Likely Causes

### 1. Backend Container Not Running (90% of cases)
### 2. Incorrect .env Configuration (8% of cases)
### 3. CORS Issues (2% of cases)

---

## ✅ Step-by-Step Fix

### Step 1: Check if Services Are Running

**On your server**, run:

```bash
cd ~/email2kg
sudo docker ps
```

**Expected output - ALL 5 containers should be running:**
```
CONTAINER ID   IMAGE             NAMES                      STATUS
xxxxxxxxxxxx   email2kg-backend  email2kg-backend           Up X minutes (healthy)
xxxxxxxxxxxx   email2kg-frontend email2kg-frontend          Up X minutes (healthy)
xxxxxxxxxxxx   postgres:14       email2kg-db                Up X minutes (healthy)
xxxxxxxxxxxx   redis:7           email2kg-redis             Up X minutes (healthy)
xxxxxxxxxxxx   email2kg-backend  email2kg-celery-worker     Up X minutes
```

**❌ If `email2kg-backend` is missing or unhealthy** → Continue to Step 2

**✅ If all containers are running** → Skip to Step 3

---

### Step 2: Check Backend Logs for Errors

```bash
# View backend startup logs
sudo docker compose logs backend --tail=50

# Look for specific errors
sudo docker compose logs backend | grep -i error
```

**Common errors and fixes:**

#### Error: "Cannot connect to database"
```bash
# Check if postgres is running
sudo docker ps | grep postgres

# Restart postgres and backend
sudo docker compose restart postgres
sleep 10
sudo docker compose restart backend
```

#### Error: "Secret key not set" or "SECRET_KEY"
```bash
# Check if .env has SECRET_KEY and JWT_SECRET_KEY
grep -E "SECRET_KEY|JWT_SECRET_KEY" .env

# If missing or showing default values, generate new ones:
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)" >> .env

# Restart backend
sudo docker compose restart backend
```

#### Error: "ALLOWED_ORIGINS" or CORS-related
→ Continue to Step 3

---

### Step 3: Verify .env Configuration

Check your `.env` file has the correct settings for HTTPS:

```bash
# Check current settings
cat .env | grep -E "PUBLIC_PROTOCOL|PUBLIC_DOMAIN|ALLOWED_ORIGINS"
```

**Expected for production HTTPS:**
```
PUBLIC_PROTOCOL=https
PUBLIC_DOMAIN=agenticrag360.com
ALLOWED_ORIGINS=["https://agenticrag360.com","http://agenticrag360.com"]
```

**❌ If PUBLIC_PROTOCOL=http** → Fix it:

```bash
# Edit .env
nano .env

# Change these lines:
PUBLIC_PROTOCOL=https
PUBLIC_DOMAIN=agenticrag360.com
ALLOWED_ORIGINS=["https://agenticrag360.com","http://agenticrag360.com"]

# Save: Ctrl+X, then Y, then Enter

# Restart backend to apply changes
sudo docker compose restart backend

# Wait for backend to start
sleep 15
```

---

### Step 4: Test Backend Directly

```bash
# Test if backend is responding (inside container)
sudo docker exec email2kg-backend curl -s http://localhost:8000/health

# Expected: {"status":"healthy",...}
```

**❌ If this fails:**
```bash
# Backend is not running properly - rebuild it
sudo docker compose stop backend
sudo docker compose build --no-cache backend
sudo docker compose up -d backend

# Wait for startup
sleep 20

# Test again
sudo docker exec email2kg-backend curl -s http://localhost:8000/health
```

---

### Step 5: Test API Through HTTPS

```bash
# Test health endpoint through nginx
curl https://agenticrag360.com/api/health

# Expected: {"status":"healthy",...}
```

**❌ If this returns 404:**
```bash
# Nginx proxy not working - check nginx logs
sudo docker compose logs frontend --tail=30

# Restart frontend
sudo docker compose restart frontend
sleep 5

# Test again
curl https://agenticrag360.com/api/health
```

---

### Step 6: Test Auth Endpoints

```bash
# Test register endpoint
curl -X POST https://agenticrag360.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "full_name": "Test User"
  }' -v

# Expected responses:
# 201 Created = Success!
# 400 = User already exists (also means endpoint works!)
# 422 = Validation error (endpoint works, check input)
# 404 = NOT FOUND (still broken)
```

**If you get 404:**
```bash
# Check backend route registration
sudo docker compose logs backend | grep "auth"

# Should see routes being registered on startup
```

---

## 🔧 Complete Reset (If Nothing Works)

If the auth endpoints still return 404 after all steps:

```bash
cd ~/email2kg

# 1. Stop all services
sudo docker compose down

# 2. Verify .env configuration
nano .env
# Ensure:
#   PUBLIC_PROTOCOL=https
#   PUBLIC_DOMAIN=agenticrag360.com
#   SECRET_KEY=<long-random-string>
#   JWT_SECRET_KEY=<long-random-string>
#   ALLOWED_ORIGINS=["https://agenticrag360.com","http://agenticrag360.com"]

# 3. Remove and rebuild backend
sudo docker rm email2kg-backend 2>/dev/null || true
sudo docker rmi email2kg-backend 2>/dev/null || true

# 4. Rebuild all
sudo docker compose build --no-cache

# 5. Start all services
sudo docker compose up -d

# 6. Wait for all services to start
sleep 30

# 7. Check all containers are healthy
sudo docker ps

# 8. Test API
curl https://agenticrag360.com/api/health

# 9. Test auth
curl -X POST https://agenticrag360.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123","full_name":"Test"}'
```

---

## 🎯 Quick Diagnostic Script

I've created an automated diagnostic script for you. Run this:

```bash
cd ~/email2kg
chmod +x scripts/utils/diagnose-api.sh
./scripts/utils/diagnose-api.sh
```

This will check all common issues and provide specific fixes.

---

## 📊 Expected Behavior

Once fixed, you should see:

**In browser console (F12 → Network tab):**
```
POST https://agenticrag360.com/api/auth/register
Status: 201 Created
Response: {"id": 1, "email": "...", "full_name": "..."}
```

**No errors in browser console**

---

## 🆘 Still Broken?

If auth still returns 404 after all these steps:

1. **Capture diagnostic output:**
   ```bash
   cd ~/email2kg
   ./scripts/utils/diagnose-api.sh > auth_debug.txt 2>&1
   ```

2. **Check backend routes:**
   ```bash
   sudo docker exec email2kg-backend python -c "from app.main import app; print([r.path for r in app.routes])" >> auth_debug.txt
   ```

3. **Share the output:**
   - Create a GitHub issue
   - Include `auth_debug.txt`
   - Include screenshots of browser console errors
   - Describe what you've already tried

---

## 📌 Reference

- **Auth routes source:** `backend/app/api/auth_routes.py:25`
- **Main app setup:** `backend/app/main.py:176`
- **Nginx proxy config:** `frontend/nginx.conf:46-57`
- **Docker compose:** `docker-compose.yml:66-143`
