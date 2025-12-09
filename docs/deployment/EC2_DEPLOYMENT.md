# Email2KG - EC2 Deployment Guide

Complete guide to deploy Email2KG on your EC2 server with OCR email extraction.

## Prerequisites

- EC2 instance running (Ubuntu 20.04+ or Amazon Linux 2)
- Security groups configured (ports 80, 443, 8000 open)
- SSH access to your EC2 instance
- Your EC2 public IP: **34.245.66.42**

---

## Step 1: Connect to EC2

```bash
# SSH into your EC2 instance
ssh -i /path/to/your-key.pem ubuntu@34.245.66.42

# Or if using Amazon Linux:
# ssh -i /path/to/your-key.pem ec2-user@34.245.66.42
```

---

## Step 2: Install Docker & Docker Compose

### If Docker is NOT installed:

```bash
# Update package manager
sudo apt-get update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group (no sudo needed)
sudo usermod -aG docker $USER

# Log out and back in for group changes to take effect
exit
# Then SSH back in
ssh -i /path/to/your-key.pem ubuntu@34.245.66.42

# Verify Docker installation
docker --version
```

### Install Docker Compose:

```bash
# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make it executable
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

---

## Step 3: Clone Repository

### Option A: First Time Setup

```bash
# Clone the repository
git clone https://github.com/akhanna222/email2kg.git
cd email2kg

# Switch to the feature branch with OCR
git checkout claude/add-ocr-email-extraction-01E2J9RkrixaT8TUTReBnHiG
```

### Option B: Update Existing Installation

```bash
# Navigate to existing directory
cd email2kg

# Fetch latest changes
git fetch origin

# Switch to the OCR feature branch
git checkout claude/add-ocr-email-extraction-01E2J9RkrixaT8TUTReBnHiG

# Pull latest changes
git pull origin claude/add-ocr-email-extraction-01E2J9RkrixaT8TUTReBnHiG
```

---

## Step 4: Configure Environment Variables

### Create .env file from template:

```bash
# Copy production template
cp .env.production.example .env

# Edit the file
nano .env
```

### Critical Configuration:

Update these values in `.env`:

```bash
# ============================================
# PUBLIC DOMAIN/IP (REQUIRED!)
# ============================================
PUBLIC_DOMAIN=34.245.66.42
PUBLIC_PROTOCOL=https

# Or if using your domain:
# PUBLIC_DOMAIN=agenticrag360.com
# PUBLIC_PROTOCOL=https

# ============================================
# SECURITY (REQUIRED!)
# ============================================
# Generate secure keys:
SECRET_KEY=YOUR_SECURE_RANDOM_KEY_HERE
JWT_SECRET_KEY=YOUR_SECURE_RANDOM_KEY_HERE

# ============================================
# DATABASE (REQUIRED!)
# ============================================
DB_PASSWORD=YOUR_SECURE_DATABASE_PASSWORD

# ============================================
# OPENAI API KEY (REQUIRED!)
# ============================================
OPENAI_API_KEY=sk-your-openai-api-key-here

# ============================================
# GMAIL OAUTH (REQUIRED for email sync!)
# ============================================
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
# Auto-configured: GOOGLE_REDIRECT_URI will be https://34.245.66.42/api/auth/google/callback
```

### Generate Secure Keys:

```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate JWT_SECRET_KEY
openssl rand -hex 32

# Copy these values into your .env file
```

### Quick Configuration Script:

```bash
# Use the built-in update script
./scripts/utils/update-domain.sh

# Follow prompts:
# 1. Enter: 34.245.66.42 (or agenticrag360.com)
# 2. Select: 1 (HTTPS) or 2 (HTTP)
```

---

## Step 5: Configure Security Groups

Ensure your EC2 security group allows these ports:

```bash
# Check current firewall rules
sudo ufw status

# Allow necessary ports
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8000/tcp  # Backend API (optional, for direct access)
sudo ufw allow 22/tcp    # SSH

# Enable firewall
sudo ufw enable
```

**Or configure in AWS Console:**
- EC2 → Security Groups → Your instance's security group
- Add Inbound Rules:
  - HTTP (80) - Source: 0.0.0.0/0
  - HTTPS (443) - Source: 0.0.0.0/0
  - Custom TCP (8000) - Source: 0.0.0.0/0 (optional)

---

## Step 6: Build and Start Services

### First-time setup:

```bash
# Build all Docker images (may take 5-10 minutes)
docker-compose build

# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

### Services that should be running:

```
NAME                     STATUS
email2kg-backend         Up (healthy)
email2kg-celery-worker   Up
email2kg-db              Up (healthy)
email2kg-frontend        Up (healthy)
email2kg-redis           Up (healthy)
```

---

## Step 7: Update Namecheap DNS (If using domain)

**If using `agenticrag360.com`:**

1. Login to Namecheap: https://www.namecheap.com/
2. Domain List → Manage → **Advanced DNS**
3. Update A Records:
   - **@** → `34.245.66.42`
   - **www** → `34.245.66.42`
4. Click **Save all changes**
5. Wait 15-30 minutes for DNS propagation

### Check DNS propagation:

```bash
nslookup agenticrag360.com
# Should show: 34.245.66.42
```

---

## Step 8: Update Google OAuth

1. Go to: https://console.cloud.google.com/apis/credentials
2. Click your OAuth 2.0 Client ID
3. Under "Authorized redirect URIs", add:
   - If using IP: `https://34.245.66.42/api/auth/google/callback`
   - If using domain: `https://agenticrag360.com/api/auth/google/callback`
4. Click **Save**
5. Wait 5 minutes for changes to propagate

---

## Step 9: Setup SSL Certificate (HTTPS)

### Option A: Using Domain (Recommended)

```bash
# Stop services temporarily
docker-compose down

# Run Let's Encrypt setup
./scripts/deployment/setup-letsencrypt.sh

# Follow prompts and enter your domain
# Certificate will be auto-generated and configured

# Start services
docker-compose up -d
```

### Option B: Using IP (Development Only)

For IP addresses, use self-signed certificate or HTTP:

```bash
# Edit .env to use HTTP
nano .env

# Change to:
PUBLIC_PROTOCOL=http

# Restart services
docker-compose down
docker-compose up -d
```

**Note**: HTTPS with Let's Encrypt requires a domain name, not an IP address.

---

## Step 10: Verify Deployment

### Check services are running:

```bash
# View all services
docker-compose ps

# Check logs
docker-compose logs -f

# Check specific service
docker-compose logs backend --tail=50
docker-compose logs celery_worker --tail=50
```

### Test endpoints:

```bash
# Test backend health
curl https://34.245.66.42/health
# Expected: {"status":"ok"} or similar

# Test frontend (in browser)
# Visit: https://34.245.66.42

# Check if Celery worker is running
docker-compose logs celery_worker | grep "ready"
# Should see: "celery@... ready"

# Check Redis
docker exec email2kg-redis redis-cli ping
# Should return: PONG
```

### Test from your local machine:

```bash
# From your laptop/desktop
curl https://34.245.66.42/health

# Or open in browser:
# https://34.245.66.42
```

---

## Step 11: Test Email OCR Feature

1. **Open application**: https://34.245.66.42
2. **Login/Register** an account
3. **Connect Gmail**:
   - Click "Connect Gmail"
   - Authorize with Google
4. **Sync Emails**:
   - Click "Sync Emails"
   - Wait for sync to complete
5. **Check Processing**:
   - View Celery logs: `docker-compose logs celery_worker -f`
   - Should see attachment processing messages
6. **View Results**:
   - Go to Documents page
   - See extracted data from email attachments

---

## Common Commands

### Service Management:

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart backend
docker-compose restart celery_worker

# View logs (follow mode)
docker-compose logs -f

# View logs for specific service
docker-compose logs backend -f
docker-compose logs celery_worker -f

# Check service status
docker-compose ps

# View resource usage
docker stats
```

### Update Application:

```bash
# Pull latest code
git pull origin claude/add-ocr-email-extraction-01E2J9RkrixaT8TUTReBnHiG

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

### Database Management:

```bash
# Access PostgreSQL
docker exec -it email2kg-db psql -U postgres -d email2kg

# Backup database
docker exec email2kg-db pg_dump -U postgres email2kg > backup.sql

# View database size
docker exec email2kg-db psql -U postgres -c "SELECT pg_size_pretty(pg_database_size('email2kg'));"
```

### Cleanup:

```bash
# Remove stopped containers
docker-compose down

# Remove all (including volumes - DANGEROUS!)
docker-compose down -v

# Clean up Docker system
docker system prune -a
```

---

## Troubleshooting

### Issue: Services won't start

```bash
# Check logs
docker-compose logs

# Check if ports are already in use
sudo lsof -i :80
sudo lsof -i :443
sudo lsof -i :8000

# Stop conflicting services
sudo systemctl stop nginx  # If you have nginx installed
sudo systemctl stop apache2  # If you have apache installed
```

### Issue: "Cannot connect to the Docker daemon"

```bash
# Start Docker service
sudo systemctl start docker

# Enable Docker to start on boot
sudo systemctl enable docker

# Check Docker status
sudo systemctl status docker
```

### Issue: Permission denied

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in
exit
# SSH back in
```

### Issue: Out of disk space

```bash
# Check disk usage
df -h

# Clean up Docker
docker system prune -a --volumes

# Clean up old images
docker image prune -a
```

### Issue: CORS errors

```bash
# Verify PUBLIC_DOMAIN in .env
grep PUBLIC_DOMAIN .env

# Should match your actual IP/domain
# Restart backend
docker-compose restart backend celery_worker
```

### Issue: OAuth redirect error

```bash
# Check redirect URI in .env
grep GOOGLE_REDIRECT .env

# Ensure it matches what's in Google Console
# https://console.cloud.google.com/apis/credentials

# Should be: https://34.245.66.42/api/auth/google/callback
```

### Issue: Celery worker not processing

```bash
# Check worker logs
docker-compose logs celery_worker -f

# Check Redis is running
docker exec email2kg-redis redis-cli ping

# Restart worker
docker-compose restart celery_worker
```

---

## Monitoring

### View Application Logs:

```bash
# All services (live)
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Specific service
docker-compose logs backend -f
docker-compose logs celery_worker -f
docker-compose logs frontend -f
```

### Check Resource Usage:

```bash
# Real-time stats
docker stats

# Disk usage
df -h
docker system df
```

### Check Celery Task Queue:

```bash
# Connect to Redis
docker exec -it email2kg-redis redis-cli

# Check queue length
LLEN celery
LLEN attachments
LLEN documents

# Exit Redis
exit
```

---

## Performance Tuning

### For Low-Memory Instances (< 2GB RAM):

Edit `docker-compose.yml`:

```yaml
celery_worker:
  command: celery -A app.core.celery_app worker --loglevel=info --concurrency=2  # Reduce from 4
  deploy:
    resources:
      limits:
        memory: 512M  # Reduce from 1G
```

### For High-Traffic Sites:

```yaml
celery_worker:
  command: celery -A app.core.celery_app worker --loglevel=info --concurrency=8  # Increase from 4
```

---

## Security Best Practices

1. **Change default passwords**:
   - Database password
   - Secret keys
   - JWT secret

2. **Enable firewall**:
   ```bash
   sudo ufw enable
   ```

3. **Keep Docker updated**:
   ```bash
   sudo apt-get update
   sudo apt-get upgrade docker-ce docker-ce-cli containerd.io
   ```

4. **Regular backups**:
   ```bash
   # Backup script (save as backup.sh)
   docker exec email2kg-db pg_dump -U postgres email2kg > backup_$(date +%Y%m%d).sql
   ```

5. **Monitor logs** for suspicious activity:
   ```bash
   docker-compose logs backend | grep "401\|403\|500"
   ```

---

## Auto-Start on Reboot

```bash
# Create systemd service
sudo nano /etc/systemd/system/email2kg.service
```

Add:
```ini
[Unit]
Description=Email2KG Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/email2kg
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable email2kg
sudo systemctl start email2kg
```

---

## Update Checklist

When your EC2 IP changes:

- [ ] Update `.env`: `PUBLIC_DOMAIN=new-ip`
- [ ] Update Namecheap DNS (if using domain)
- [ ] Update Google OAuth redirect URI
- [ ] Restart services: `docker-compose restart backend celery_worker`
- [ ] Test: `curl https://new-ip/health`

**Use the script:**
```bash
./scripts/utils/update-domain.sh
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Start services | `docker-compose up -d` |
| Stop services | `docker-compose down` |
| View logs | `docker-compose logs -f` |
| Restart backend | `docker-compose restart backend` |
| Check status | `docker-compose ps` |
| Update code | `git pull && docker-compose build && docker-compose up -d` |
| Test health | `curl https://34.245.66.42/health` |

---

## Next Steps

1. **Test the application**: https://34.245.66.42
2. **Connect Gmail** and sync emails
3. **Test OCR extraction** on email attachments
4. **Monitor Celery logs** to see processing
5. **Set up monitoring** with your preferred tools
6. **Configure backups** for database
7. **Consider Elastic IP** to avoid IP changes

---

## Support

- **Documentation**: Check `/docs` folder in repository
- **OCR Feature**: `OCR_EMAIL_EXTRACTION.md`
- **IP Management**: `docs/deployment/EC2_IP_MANAGEMENT.md`
- **Namecheap DNS**: `docs/deployment/NAMECHEAP_DNS_UPDATE.md`
- **Quick Updates**: `QUICK_IP_UPDATE.md`

---

## Success Criteria

✅ All services showing "Up (healthy)" in `docker-compose ps`
✅ Backend responds: `curl https://34.245.66.42/health` returns 200
✅ Frontend loads in browser: https://34.245.66.42
✅ Can login and register users
✅ Gmail OAuth works (no redirect errors)
✅ Email sync completes successfully
✅ Celery worker processes attachments
✅ Documents appear with extracted data

**You're all set!** 🚀
