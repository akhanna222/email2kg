# 🚀 Quick IP Update Guide

Your EC2 IP changed to **34.245.66.42**? Here's how to update it in **30 seconds**:

## Method 1: Use the Update Script (Easiest)

```bash
./scripts/utils/update-domain.sh
```

Then follow the prompts:
1. Enter: `34.245.66.42`
2. Select protocol: `1` (for HTTPS) or `2` (for HTTP)
3. Type `y` to restart services

**Done!** ✅

## Method 2: Manual Update (2 steps)

### Step 1: Edit `.env` file

```bash
# Create .env if it doesn't exist
cp .env.production.example .env

# Edit these two lines:
PUBLIC_DOMAIN=34.245.66.42
PUBLIC_PROTOCOL=https
```

### Step 2: Restart services

```bash
docker-compose down
docker-compose up -d
```

**Done!** ✅

## Method 3: One-Line Update (Advanced)

```bash
# Update and restart in one command
sed -i 's/^PUBLIC_DOMAIN=.*/PUBLIC_DOMAIN=34.245.66.42/' .env && \
sed -i 's/^PUBLIC_PROTOCOL=.*/PUBLIC_PROTOCOL=https/' .env && \
docker-compose down && docker-compose up -d
```

## What Gets Updated Automatically?

When you update `PUBLIC_DOMAIN`, these are automatically configured:

✅ **CORS Origins**
```
["https://34.245.66.42","http://34.245.66.42"]
```

✅ **Google OAuth Redirect URI**
```
https://34.245.66.42/api/auth/google/callback
```

✅ **Frontend URL**
```
https://34.245.66.42
```

✅ **Backend API**
```
https://34.245.66.42/api
```

## ⚠️ Don't Forget: Update Google OAuth!

After updating your IP, you **MUST** update Google OAuth Console:

1. Go to: https://console.cloud.google.com/apis/credentials
2. Click your OAuth 2.0 Client ID
3. Add redirect URI: `https://34.245.66.42/api/auth/google/callback`
4. Click **Save**

## Current IP: 34.245.66.42

Your new URLs:
- **Frontend**: https://34.245.66.42
- **Backend API**: https://34.245.66.42/api
- **Health Check**: https://34.245.66.42/health
- **OAuth Callback**: https://34.245.66.42/api/auth/google/callback

## Pro Tip: Stop IP from Changing

**Use an Elastic IP** (stays same after stop/start):

1. AWS Console → EC2 → Elastic IPs → Allocate
2. Associate with your instance
3. Update `PUBLIC_DOMAIN` one last time
4. **Never changes again!** 🎉

**Cost**: FREE while running, ~$0.005/hour when stopped

## Need Help?

- **Full Guide**: [docs/deployment/EC2_IP_MANAGEMENT.md](docs/deployment/EC2_IP_MANAGEMENT.md)
- **Troubleshooting**: Check logs: `docker-compose logs -f`
- **Verify Config**: `grep PUBLIC_DOMAIN .env`

## Quick Tests

```bash
# Test backend is running
curl https://34.245.66.42/health

# Check environment variables
docker-compose exec backend env | grep PUBLIC

# View all logs
docker-compose logs -f
```

---

**That's it!** Your app should now work with the new IP: `34.245.66.42` 🚀
