# Google OAuth "redirect_uri_mismatch" Error - Fix Guide

## 🔴 Error Message

```
You can't sign in because this app sent an invalid request.
Error 400: redirect_uri_mismatch
```

---

## 🔍 Root Cause

The redirect URI configured in **Google Cloud Console** doesn't match the redirect URI in your **`.env` file**.

**Your backend callback endpoint:** `/api/auth/callback`
**Expected redirect URI:** `https://agenticrag360.com/api/auth/callback`

---

## ✅ Quick Fix (3 Steps)

### **Step 1: Check Your Current `.env` Configuration**

On your server, run:

```bash
cd ~/email2kg
grep GOOGLE_REDIRECT_URI .env
```

**Expected output:**
```
GOOGLE_REDIRECT_URI=https://agenticrag360.com/api/auth/callback
```

**❌ If it shows:**
- `http://localhost:8000/api/auth/callback` → Wrong (localhost)
- `http://agenticrag360.com/api/auth/callback` → Wrong (http instead of https)
- `https://agenticrag360.com/api/auth/google/callback` → Wrong path (has /google/)
- Not set or commented out → Missing

**✅ Correct value:**
```
GOOGLE_REDIRECT_URI=https://agenticrag360.com/api/auth/callback
```

---

### **Step 2: Update Your `.env` File**

```bash
cd ~/email2kg

# Edit .env
nano .env

# Find the line with GOOGLE_REDIRECT_URI and change it to:
GOOGLE_REDIRECT_URI=https://agenticrag360.com/api/auth/callback

# Save: Ctrl+X, then Y, then Enter
```

**Also verify these are set:**
```bash
GOOGLE_CLIENT_ID=your_actual_client_id_from_google_cloud
GOOGLE_CLIENT_SECRET=your_actual_client_secret_from_google_cloud
PUBLIC_PROTOCOL=https
PUBLIC_DOMAIN=agenticrag360.com
```

---

### **Step 3: Update Google Cloud Console**

#### 3.1 Go to Google Cloud Console

1. Open: https://console.cloud.google.com/apis/credentials
2. Select your project (or create one if you haven't)

#### 3.2 Find Your OAuth 2.0 Client ID

1. Click on **"Credentials"** in the left sidebar
2. Find your OAuth 2.0 Client ID (usually named "Web client" or similar)
3. Click on it to edit

#### 3.3 Update Authorized Redirect URIs

In the **"Authorized redirect URIs"** section:

**Add this URI:**
```
https://agenticrag360.com/api/auth/callback
```

**Remove these if present:**
- ❌ `http://localhost:8000/api/auth/callback` (development only)
- ❌ `http://agenticrag360.com/api/auth/callback` (http, not https)
- ❌ `https://agenticrag360.com/api/auth/google/callback` (wrong path)

**Keep these (if you want to support development):**
- ✅ `https://agenticrag360.com/api/auth/callback` (production)
- ✅ `http://localhost:8000/api/auth/callback` (local development)

#### 3.4 Save Changes

Click **"SAVE"** at the bottom of the page.

⚠️ **Note:** Changes can take 5-10 minutes to propagate.

---

### **Step 4: Restart Backend**

```bash
cd ~/email2kg

# Restart backend to load new .env values
sudo docker compose restart backend

# Wait for it to start
sleep 10

# Verify backend is running
sudo docker ps | grep backend
```

---

### **Step 5: Test OAuth Flow**

1. Go to https://agenticrag360.com
2. Log in to your account
3. Try to connect Gmail
4. Should redirect to Google login
5. After authorizing, should redirect back successfully ✅

---

## 🔍 Detailed Troubleshooting

### Check Current Backend Configuration

```bash
# Check what redirect URI the backend is using
sudo docker exec email2kg-backend env | grep GOOGLE_REDIRECT_URI
```

**Expected:**
```
GOOGLE_REDIRECT_URI=https://agenticrag360.com/api/auth/callback
```

---

### View Backend Logs for OAuth Errors

```bash
sudo docker compose logs backend --tail=50 | grep -i "oauth\|google"
```

Look for error messages like:
- "redirect_uri_mismatch"
- "invalid_client"
- "invalid_grant"

---

### Test OAuth URL Generation

```bash
# Get the OAuth URL from the backend
curl -s https://agenticrag360.com/api/auth/google

# Should return something like:
# {"auth_url":"https://accounts.google.com/o/oauth2/auth?...redirect_uri=https://agenticrag360.com/api/auth/callback..."}
```

Check that `redirect_uri=` in the URL matches what's in Google Cloud Console.

---

## 📋 Complete Configuration Checklist

### ✅ `.env` File (on server)

```bash
cd ~/email2kg
cat .env | grep -E "GOOGLE_|PUBLIC_PROTOCOL|PUBLIC_DOMAIN"
```

**Should show:**
```
PUBLIC_PROTOCOL=https
PUBLIC_DOMAIN=agenticrag360.com
GOOGLE_CLIENT_ID=123456789-abcdefg.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abc123xyz789
GOOGLE_REDIRECT_URI=https://agenticrag360.com/api/auth/callback
```

---

### ✅ Google Cloud Console

**Project:** Your Email2KG project
**Credentials → OAuth 2.0 Client IDs → Your Client**

**Authorized JavaScript origins:**
```
https://agenticrag360.com
http://localhost:3000  (for development)
```

**Authorized redirect URIs:**
```
https://agenticrag360.com/api/auth/callback
http://localhost:8000/api/auth/callback  (for development)
```

---

### ✅ OAuth Consent Screen

Make sure you've configured the OAuth consent screen:

1. Go to: https://console.cloud.google.com/apis/credentials/consent
2. **User Type:** External (unless you have Google Workspace)
3. **App name:** Email2KG (or your app name)
4. **User support email:** Your email
5. **Developer contact:** Your email
6. **Scopes:** Add `https://www.googleapis.com/auth/gmail.readonly`
7. **Test users:** Add your Gmail accounts (if in testing mode)

---

## 🚨 Common Mistakes

### ❌ Mistake #1: Using `/api/auth/google/callback`

**Wrong:**
```
GOOGLE_REDIRECT_URI=https://agenticrag360.com/api/auth/google/callback
```

**Correct:**
```
GOOGLE_REDIRECT_URI=https://agenticrag360.com/api/auth/callback
```

The backend endpoint is `/api/auth/callback`, NOT `/api/auth/google/callback`.

---

### ❌ Mistake #2: Using HTTP instead of HTTPS

**Wrong:**
```
GOOGLE_REDIRECT_URI=http://agenticrag360.com/api/auth/callback
```

**Correct:**
```
GOOGLE_REDIRECT_URI=https://agenticrag360.com/api/auth/callback
```

Production must use HTTPS.

---

### ❌ Mistake #3: Localhost in Production

**Wrong (for production):**
```
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/callback
```

This only works locally. Production must use your domain.

---

### ❌ Mistake #4: Not Restarting Backend

After changing `.env`, you **must** restart the backend:

```bash
sudo docker compose restart backend
```

---

### ❌ Mistake #5: Google Console Not Saved

After adding the redirect URI in Google Cloud Console, you **must** click **"SAVE"**.

Changes can take 5-10 minutes to propagate.

---

## 🧪 Testing & Verification

### Test 1: Get OAuth URL

```bash
curl -s https://agenticrag360.com/api/auth/google | jq .
```

**Expected:**
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=...&redirect_uri=https%3A%2F%2Fagenticrag360.com%2Fapi%2Fauth%2Fcallback&scope=..."
}
```

Check that `redirect_uri=` is correctly URL-encoded to `https://agenticrag360.com/api/auth/callback`.

---

### Test 2: Manual OAuth Flow

1. Copy the `auth_url` from Test 1
2. Open it in a browser
3. Sign in with your Google account
4. Grant permissions
5. After redirect, you should land on `/api/auth/callback` (might show an error about needing authentication, but the redirect should work)

---

### Test 3: Full Flow in App

1. Go to https://agenticrag360.com
2. Log in with your Email2KG account
3. Navigate to Gmail connection
4. Click "Connect Gmail"
5. Authorize on Google
6. Should redirect back and show success ✅

---

## 🆘 Still Getting Errors?

### Error: "invalid_client"

**Cause:** Client ID or Client Secret is wrong.

**Fix:**
1. Go to Google Cloud Console → Credentials
2. Copy the correct Client ID and Client Secret
3. Update your `.env` file
4. Restart backend

---

### Error: "access_denied"

**Cause:** User denied permission or app not verified.

**Fix:**
1. Try again and click "Allow" when prompted
2. If app is not verified, add yourself as a test user in OAuth consent screen

---

### Error: "unauthorized_client"

**Cause:** OAuth consent screen not configured or app not enabled for Gmail API.

**Fix:**
1. Enable Gmail API: https://console.cloud.google.com/apis/library/gmail.googleapis.com
2. Configure OAuth consent screen
3. Add required scopes: `https://www.googleapis.com/auth/gmail.readonly`

---

## 📚 Additional Resources

- **Google OAuth 2.0 Guide:** https://developers.google.com/identity/protocols/oauth2
- **Gmail API Scopes:** https://developers.google.com/gmail/api/auth/scopes
- **OAuth Playground:** https://developers.google.com/oauthplayground/

---

## 🎯 Quick Reference

| Setting | Value |
|---------|-------|
| **Redirect URI** | `https://agenticrag360.com/api/auth/callback` |
| **OAuth URL Endpoint** | `GET /api/auth/google` |
| **Callback Endpoint** | `POST /api/auth/callback` |
| **Required Scope** | `https://www.googleapis.com/auth/gmail.readonly` |

---

**Last Updated:** December 2025
