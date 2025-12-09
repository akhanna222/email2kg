# EC2 IP Management for Email2KG

## Problem: EC2 Public IP Changes After Stop/Start

AWS EC2 instances get a **new public IP** every time you stop and restart them (unless you're using an Elastic IP). This breaks your configuration because:

- CORS origins become invalid
- Google OAuth redirect URI stops working
- Frontend can't connect to backend
- SSL certificates may need regeneration

## Solutions

### Option 1: Quick Update Script (Recommended for Development)

**When your IP changes to a new one (e.g., `34.245.66.42`):**

```bash
# Run the update script
./scripts/utils/update-domain.sh

# Follow the prompts:
# 1. Enter your new IP: 34.245.66.42
# 2. Select protocol: 1 (HTTPS) or 2 (HTTP)
# 3. Script will update .env and offer to restart services
```

The script automatically:
- ✅ Updates `PUBLIC_DOMAIN` in `.env`
- ✅ Updates `PUBLIC_PROTOCOL` in `.env`
- ✅ Shows new OAuth callback URL
- ✅ Offers to restart Docker services
- ✅ Displays all new URLs

### Option 2: Manual Update

Edit your `.env` file:

```bash
# Update these two lines
PUBLIC_DOMAIN=34.245.66.42
PUBLIC_PROTOCOL=https
```

Then restart:
```bash
docker-compose down
docker-compose up -d
```

### Option 3: Use Elastic IP (Recommended for Production)

**Elastic IPs don't change** when you stop/start your instance.

#### Setup Elastic IP:

1. **Allocate Elastic IP:**
   ```bash
   # AWS Console: EC2 → Elastic IPs → Allocate Elastic IP address
   # Or via CLI:
   aws ec2 allocate-address --domain vpc
   ```

2. **Associate with your EC2 instance:**
   ```bash
   # AWS Console: Actions → Associate Elastic IP address → Select your instance
   # Or via CLI:
   aws ec2 associate-address \
     --instance-id i-your-instance-id \
     --allocation-id eipalloc-your-allocation-id
   ```

3. **Update your configuration once:**
   ```bash
   PUBLIC_DOMAIN=your-elastic-ip
   PUBLIC_PROTOCOL=https
   ```

4. **Your IP never changes again!** 🎉

**Cost:** FREE while instance is running, ~$0.005/hour when stopped

### Option 4: Use a Domain Name (Best for Production)

**Domain names never change**, even if your IP changes.

#### Setup with Domain:

1. **Register a domain** (e.g., GoDaddy, Namecheap, Route 53)

2. **Point domain to your Elastic IP:**
   - Create an A record: `yourdomain.com` → `your-elastic-ip`
   - Create an A record: `www.yourdomain.com` → `your-elastic-ip`

3. **Update configuration:**
   ```bash
   PUBLIC_DOMAIN=yourdomain.com
   PUBLIC_PROTOCOL=https
   ```

4. **Setup SSL (Let's Encrypt):**
   ```bash
   ./scripts/deployment/setup-letsencrypt.sh
   ```

## Automatic Configuration Updates

When you update `PUBLIC_DOMAIN` and `PUBLIC_PROTOCOL`, the following are automatically updated:

### 1. CORS Origins
```
Before: ["https://agenticrag360.com","http://agenticrag360.com"]
After:  ["https://34.245.66.42","http://34.245.66.42"]
```

### 2. Google OAuth Redirect URI
```
Before: https://agenticrag360.com/api/auth/google/callback
After:  https://34.245.66.42/api/auth/google/callback
```

### 3. Frontend URLs
```
Before: https://agenticrag360.com
After:  https://34.245.66.42
```

## After Updating IP/Domain

### 1. Update Google OAuth Console

**CRITICAL:** Update your OAuth redirect URI in Google Cloud Console:

1. Go to: https://console.cloud.google.com/apis/credentials
2. Click on your OAuth 2.0 Client ID
3. Under "Authorized redirect URIs", add:
   ```
   https://34.245.66.42/api/auth/google/callback
   ```
4. Click **Save**

### 2. Regenerate SSL Certificate (if using HTTPS)

If your IP changed and you're using Let's Encrypt:

```bash
# Stop services
docker-compose down

# Remove old certificates
sudo rm -rf ssl/

# Generate new certificates for new IP
./scripts/deployment/setup-letsencrypt.sh

# Restart services
docker-compose up -d
```

**Note:** Let's Encrypt has rate limits. Use HTTP temporarily if you change IPs frequently.

### 3. Test Your Configuration

```bash
# Check if services are running
docker-compose ps

# Test backend API
curl https://34.245.66.42/health

# Test frontend
curl https://34.245.66.42/

# Check logs
docker-compose logs -f backend
```

## Environment Variables Reference

### Current Implementation

```bash
# In docker-compose.yml, these are auto-configured:
ALLOWED_ORIGINS: ${ALLOWED_ORIGINS:-["${PUBLIC_PROTOCOL}://${PUBLIC_DOMAIN}","http://${PUBLIC_DOMAIN}"]}
GOOGLE_REDIRECT_URI: ${GOOGLE_REDIRECT_URI:-${PUBLIC_PROTOCOL}://${PUBLIC_DOMAIN}/api/auth/google/callback}
```

### Manual Override (if needed)

You can still manually override in `.env`:

```bash
# Override auto-configuration
ALLOWED_ORIGINS=["https://custom-domain.com","http://another-domain.com"]
GOOGLE_REDIRECT_URI=https://custom-domain.com/api/auth/google/callback
```

## Common Issues & Solutions

### Issue: CORS Error in Browser
**Symptom:** `Access-Control-Allow-Origin` error in console

**Solution:**
```bash
# 1. Verify PUBLIC_DOMAIN matches your actual IP
grep PUBLIC_DOMAIN .env

# 2. Restart backend
docker-compose restart backend celery_worker

# 3. Check logs
docker-compose logs backend | grep CORS
```

### Issue: OAuth Redirect Error
**Symptom:** "Redirect URI mismatch" from Google

**Solution:**
1. Check current redirect URI:
   ```bash
   grep GOOGLE_REDIRECT_URI .env
   ```
2. Update Google Console to match exactly
3. Wait 5 minutes for Google to propagate changes

### Issue: SSL Certificate Invalid
**Symptom:** Browser shows "Your connection is not private"

**Solution:**
```bash
# If using IP address, SSL may not work properly
# Use HTTP temporarily:
PUBLIC_PROTOCOL=http

# Or get an Elastic IP + domain name and use Let's Encrypt
```

### Issue: Services Won't Start
**Symptom:** `docker-compose up` fails

**Solution:**
```bash
# Check .env syntax
cat .env | grep -E "PUBLIC_DOMAIN|PUBLIC_PROTOCOL"

# Ensure no quotes around values
# ✓ Correct: PUBLIC_DOMAIN=34.245.66.42
# ✗ Wrong:   PUBLIC_DOMAIN="34.245.66.42"

# Check Docker logs
docker-compose logs
```

## Best Practices

### Development
- ✅ Use dynamic IP with update script
- ✅ Use HTTP (faster, no SSL hassle)
- ✅ Update on every EC2 restart

### Staging
- ✅ Use Elastic IP (stable, still costs same)
- ✅ Use HTTP or self-signed SSL
- ✅ Set up once, no more updates

### Production
- ✅ Use Elastic IP + Domain Name
- ✅ Use HTTPS with Let's Encrypt
- ✅ Set up once, never change
- ✅ Enable auto-renewal for SSL

## Quick Reference Commands

```bash
# Update IP/Domain
./scripts/utils/update-domain.sh

# Check current configuration
grep -E "PUBLIC_DOMAIN|PUBLIC_PROTOCOL" .env

# Restart services
docker-compose restart backend celery_worker

# Full restart
docker-compose down && docker-compose up -d

# View current IP from inside EC2
curl ifconfig.me

# Check which IP Docker is using
docker-compose exec backend env | grep PUBLIC

# Regenerate SSL
./scripts/deployment/setup-letsencrypt.sh
```

## Cost Comparison

| Solution | Cost | Stability | Best For |
|----------|------|-----------|----------|
| Dynamic IP | FREE | Changes on stop | Development |
| Elastic IP | ~$3.60/month* | Stable | Staging/Production |
| Domain + Elastic IP | ~$15/year + $3.60/month | Very stable | Production |

*Elastic IP is FREE while instance is running, only charged when instance is stopped

## Getting Help

If you encounter issues:

1. Check logs:
   ```bash
   docker-compose logs -f
   ```

2. Verify environment:
   ```bash
   docker-compose exec backend env | grep -E "PUBLIC|GOOGLE|ALLOWED"
   ```

3. Test connectivity:
   ```bash
   curl -v http://$(grep PUBLIC_DOMAIN .env | cut -d= -f2)/health
   ```

4. Review this guide for common issues above
