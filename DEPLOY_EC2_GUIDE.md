# 🚀 EC2 Deployment Guide - Email2KG

Complete step-by-step guide to deploy Email2KG on AWS EC2.

---

## 📋 Prerequisites

Before you start, make sure you have:

- ✅ AWS Account
- ✅ AWS CLI installed and configured
- ✅ OpenAI API Key
- ✅ Google OAuth credentials (Client ID & Secret)
- ✅ SSH key pair for EC2 access

---

## 🎯 Quick Start (5 Minutes)

### Step 1: Launch EC2 Instance

**Option A: Using AWS Console**

1. Go to AWS EC2 Console
2. Click "Launch Instance"
3. Configure:
   - **Name:** `email2kg-server`
   - **AMI:** Ubuntu Server 22.04 LTS
   - **Instance Type:** `t3.medium` (2 vCPU, 4GB RAM)
   - **Key Pair:** Select or create new
   - **Security Group:** Create with these rules:
     - SSH (22) - Your IP only
     - HTTP (80) - Anywhere
     - HTTPS (443) - Anywhere (for future SSL)
     - Custom TCP (8000) - Anywhere (API access)
   - **Storage:** 20GB gp3

4. Click "Launch Instance"

**Option B: Using AWS CLI**

```bash
# First, create a security group
aws ec2 create-security-group \
  --group-name email2kg-sg \
  --description "Email2KG Security Group"

# Get the security group ID
SG_ID=$(aws ec2 describe-security-groups \
  --group-names email2kg-sg \
  --query 'SecurityGroups[0].GroupId' \
  --output text)

# Add inbound rules
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --ip-permissions \
    IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges='[{CidrIp=0.0.0.0/0}]' \
    IpProtocol=tcp,FromPort=80,ToPort=80,IpRanges='[{CidrIp=0.0.0.0/0}]' \
    IpProtocol=tcp,FromPort=443,ToPort=443,IpRanges='[{CidrIp=0.0.0.0/0}]' \
    IpProtocol=tcp,FromPort=8000,ToPort=8000,IpRanges='[{CidrIp=0.0.0.0/0}]'

# Launch instance
aws ec2 run-instances \
  --image-id ami-0c7217cdde317cfec \
  --instance-type t3.medium \
  --key-name YOUR_KEY_PAIR_NAME \
  --security-group-ids $SG_ID \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":20,"VolumeType":"gp3"}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=email2kg-server}]'
```

### Step 2: Get EC2 Public IP

```bash
# Using AWS Console: EC2 Dashboard → Instances → Select instance → Copy Public IPv4 address

# Or using CLI:
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=email2kg-server" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text
```

Save this IP address - you'll need it!

### Step 3: Connect to EC2 Instance

```bash
# SSH to your instance
ssh -i /path/to/your-key.pem ubuntu@YOUR_EC2_IP

# Example:
# ssh -i ~/.ssh/email2kg-key.pem ubuntu@54.123.45.67
```

### Step 4: Upload Deployment Files

**From your local machine** (in a new terminal):

```bash
# Navigate to your email2kg project
cd /home/user/email2kg

# Copy deployment script to EC2
scp -i /path/to/your-key.pem deploy-ec2.sh ubuntu@YOUR_EC2_IP:~/

# Make it executable on EC2
ssh -i /path/to/your-key.pem ubuntu@YOUR_EC2_IP 'chmod +x deploy-ec2.sh'
```

**Or clone from GitHub:**

```bash
# On EC2 instance:
git clone https://github.com/YOUR_USERNAME/email2kg.git
cd email2kg
chmod +x deploy-ec2.sh
```

### Step 5: Run Automated Deployment

**On your EC2 instance:**

```bash
./deploy-ec2.sh
```

**The script will:**
1. ✅ Update system packages
2. ✅ Install Python, Node.js, PostgreSQL, Docker
3. ✅ Setup PostgreSQL database
4. ✅ Configure environment variables (you'll be prompted)
5. ✅ Deploy with Docker Compose or Manual setup

**When prompted, provide:**
- OpenAI API Key
- Google OAuth Client ID
- Google OAuth Client Secret

### Step 6: Access Your Application

After deployment completes:

```
✅ Frontend: http://YOUR_EC2_IP
✅ Backend API: http://YOUR_EC2_IP:8000
✅ API Docs: http://YOUR_EC2_IP:8000/docs
```

### Step 7: Update Google OAuth Settings

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to: APIs & Services → Credentials
3. Edit your OAuth 2.0 Client
4. Add to **Authorized redirect URIs**:
   ```
   http://YOUR_EC2_IP:8000/auth/google/callback
   ```
5. Save

---

## 🛠️ Manual Deployment (Alternative)

If you prefer manual setup without the automated script:

### 1. Update System & Install Dependencies

```bash
sudo apt update && sudo apt upgrade -y

sudo apt install -y \
    python3.10 \
    python3-pip \
    python3.10-venv \
    nodejs \
    npm \
    postgresql \
    postgresql-contrib \
    nginx \
    git \
    curl \
    poppler-utils
```

### 2. Setup PostgreSQL

```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL shell:
CREATE DATABASE email2kg;
CREATE USER email2kg_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE email2kg TO email2kg_user;
\q
```

### 3. Clone Repository

```bash
cd ~
git clone https://github.com/YOUR_USERNAME/email2kg.git
cd email2kg
```

### 4. Configure Environment

```bash
# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://email2kg_user:your_secure_password@localhost:5432/email2kg
OPENAI_API_KEY=your_openai_key_here
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://YOUR_EC2_IP:8000/auth/google/callback
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
ALLOWED_ORIGINS=["http://YOUR_EC2_IP"]
EOF
```

### 5. Setup Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 6. Setup Frontend

```bash
cd ../frontend
npm install

# Update API endpoint in .env or config
echo "REACT_APP_API_URL=http://YOUR_EC2_IP:8000" > .env
```

### 7. Setup Systemd Services (Auto-start on boot)

```bash
# Copy service files
sudo cp systemd/email2kg-backend.service /etc/systemd/system/
sudo cp systemd/email2kg-frontend.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable email2kg-backend
sudo systemctl enable email2kg-frontend

# Start services
sudo systemctl start email2kg-backend
sudo systemctl start email2kg-frontend

# Check status
sudo systemctl status email2kg-backend
sudo systemctl status email2kg-frontend
```

### 8. Configure Nginx (Optional - for production)

```bash
# Copy nginx config
sudo cp nginx-ec2.conf /etc/nginx/sites-available/email2kg

# Create symlink
sudo ln -s /etc/nginx/sites-available/email2kg /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

---

## 🐳 Docker Compose Method (Recommended)

If you chose Docker Compose during automated deployment:

### Start Services

```bash
docker-compose up -d
```

### View Logs

```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f frontend
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Stop Services

```bash
docker-compose down
```

### Rebuild After Code Changes

```bash
docker-compose down
docker-compose up --build -d
```

---

## 📊 Monitoring & Management

### Check Service Status

```bash
# Docker Compose
docker-compose ps

# Systemd
sudo systemctl status email2kg-backend
sudo systemctl status email2kg-frontend
```

### View Logs

```bash
# Docker Compose
docker-compose logs -f

# Systemd
sudo journalctl -u email2kg-backend -f
sudo journalctl -u email2kg-frontend -f
```

### Database Access

```bash
# Connect to PostgreSQL
sudo -u postgres psql -d email2kg

# Backup database
pg_dump -U email2kg_user email2kg > backup.sql

# Restore database
psql -U email2kg_user email2kg < backup.sql
```

---

## 🔒 Security Hardening

### 1. Configure Firewall

```bash
# Enable UFW
sudo ufw enable

# Allow necessary ports
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw allow 8000/tcp # API (optional - can route through nginx)

# Check status
sudo ufw status
```

### 2. Setup SSL Certificate (Free with Let's Encrypt)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate (requires domain name)
sudo certbot --nginx -d yourdomain.com

# Auto-renewal is setup automatically
```

### 3. Restrict PostgreSQL Access

```bash
# Edit PostgreSQL config
sudo nano /etc/postgresql/*/main/pg_hba.conf

# Ensure local connections only
# local   all   all   peer
# host    all   all   127.0.0.1/32   md5
```

---

## 💰 Cost Estimation

**Monthly costs for EC2 deployment:**

| Resource | Type | Cost/Month |
|----------|------|------------|
| EC2 Instance | t3.medium | ~$30 |
| Storage | 20GB gp3 | ~$2 |
| Data Transfer | 10GB out | ~$1 |
| **Total** | | **~$33/month** |

**Additional costs:**
- OpenAI API (Vision): ~$10-20/month (varies by usage)
- Domain name: ~$12/year (optional)

---

## 🔧 Troubleshooting

### Backend won't start

```bash
# Check logs
sudo journalctl -u email2kg-backend -n 50

# Common issues:
# 1. Database connection - verify DATABASE_URL in .env
# 2. Missing OPENAI_API_KEY
# 3. Port 8000 already in use
sudo lsof -i :8000
```

### Frontend not accessible

```bash
# Check if service is running
sudo systemctl status email2kg-frontend

# Check nginx
sudo nginx -t
sudo systemctl status nginx

# View nginx logs
sudo tail -f /var/log/nginx/error.log
```

### Database connection errors

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -U email2kg_user -d email2kg -h localhost
```

### Gmail OAuth not working

1. Verify redirect URI in Google Console matches:
   ```
   http://YOUR_EC2_IP:8000/auth/google/callback
   ```
2. Check GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env
3. Ensure port 8000 is accessible from internet

### "Failed to fetch" error on registration

**Issue:** Frontend can't connect to backend API, browser shows CORS errors or "Failed to fetch".

**Cause:** Frontend is trying to call `localhost:8000` instead of the EC2 IP address.

**Solution:**
```bash
# 1. Verify frontend was rebuilt with correct API URL
sudo docker exec email2kg-frontend cat /usr/share/nginx/html/static/js/main.*.js | grep -o 'http://[^"]*:8000' | head -1
# Should show: http://YOUR_EC2_IP:8000/api

# 2. If it shows localhost, rebuild frontend:
cd ~/email2kg
git pull
sudo docker-compose up --build -d frontend

# 3. Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)
```

### SQLAlchemy "metadata" reserved keyword error

**Issue:** Backend crashes with:
```
sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved
```

**Cause:** Older versions of the code used `metadata` as a column name, which conflicts with SQLAlchemy.

**Solution:**
```bash
# Pull latest code with fixed field names (party_metadata, transaction_metadata)
cd ~/email2kg
git pull
sudo docker-compose up --build -d backend
```

### PostgreSQL ENUM type already exists error

**Issue:** Backend startup shows:
```
duplicate key value violates unique constraint "pg_type_typname_nsp_index"
Key (typname, typnamespace)=(processingstatus, 2200) already exists
```

**Cause:** PostgreSQL ENUM types persist from previous deployments.

**Solution:** Latest code handles this gracefully. Update to latest version:
```bash
cd ~/email2kg
git pull
sudo docker-compose up --build -d backend
```

### 404 error with double /api/api/ in URL

**Issue:** Browser console shows requests to `/api/api/auth/register` (double /api).

**Cause:** Mismatch between REACT_APP_API_URL configuration and code expectations.

**Solution:** Latest code is fixed. Update and rebuild:
```bash
cd ~/email2kg
git pull
sudo docker-compose up --build -d
# Hard refresh browser after rebuild
```

---

## 🔄 Updating the Application

### Pull latest changes

```bash
cd ~/email2kg
git pull origin main

# If using Docker Compose:
docker-compose down
docker-compose up --build -d

# If using Systemd:
source backend/venv/bin/activate
pip install -r backend/requirements.txt
cd frontend && npm install
sudo systemctl restart email2kg-backend
sudo systemctl restart email2kg-frontend
```

---

## 📞 Support

If you encounter issues:

1. Check logs: `docker-compose logs` or `journalctl -u email2kg-*`
2. Verify all environment variables are set correctly
3. Ensure Security Group allows inbound traffic on required ports
4. Check GitHub issues or create a new one

---

## ✅ Post-Deployment Checklist

- [ ] Application accessible at `http://YOUR_EC2_IP`
- [ ] API docs available at `http://YOUR_EC2_IP:8000/docs`
- [ ] Can register new user
- [ ] Can login successfully
- [ ] Gmail OAuth working
- [ ] Can upload PDF and extract text
- [ ] Knowledge graph displays correctly
- [ ] Google OAuth redirect URI updated
- [ ] Firewall configured (UFW)
- [ ] Services auto-start on reboot
- [ ] Database backups scheduled

---

**Congratulations! Your Email2KG platform is now running on AWS EC2! 🎉**
