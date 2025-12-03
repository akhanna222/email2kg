# Deployment Scripts

This directory contains automated scripts for deploying Email2KG to various environments.

## 📜 Available Scripts

### 🚀 **setup-letsencrypt.sh** (Recommended)
**Purpose:** Automated HTTPS setup with free Let's Encrypt SSL certificates

**Use this when:**
- ✅ Deploying to production with a custom domain
- ✅ You want automatic SSL certificate management
- ✅ You need free, auto-renewing certificates

**Requirements:**
- Domain name pointing to your server
- Ports 80 and 443 accessible from internet
- Root or sudo access

**Usage:**
```bash
cd ~/email2kg
sudo ./scripts/deployment/setup-letsencrypt.sh
```

**What it does:**
1. Installs Certbot (Let's Encrypt client)
2. Temporarily switches to HTTP-only mode
3. Obtains SSL certificate from Let's Encrypt
4. Configures nginx for HTTPS
5. Sets up automatic certificate renewal (every 90 days)
6. Restarts services with HTTPS enabled

**Time:** ~5-10 minutes

---

### 🔐 **setup-https.sh** (Manual SSL)
**Purpose:** Manual HTTPS setup with purchased SSL certificates (e.g., Namecheap, GoDaddy)

**Use this when:**
- You already purchased an SSL certificate
- You have specific SSL requirements (EV certificates, etc.)
- You prefer commercial SSL providers

**Requirements:**
- SSL certificate files (`.crt` and `.key`)
- Certificate downloaded and accessible

**Usage:**
```bash
cd ~/email2kg
./scripts/deployment/setup-https.sh
```

**What it does:**
1. Creates `ssl/` directory
2. Guides you to place certificate files
3. Sets correct file permissions
4. Updates docker-compose configuration
5. Rebuilds containers with HTTPS

**Time:** ~10-15 minutes (including certificate download)

---

### ☁️ **deploy-ec2.sh** (EC2 Quick Deploy)
**Purpose:** Rapid deployment to AWS EC2 instance

**Use this when:**
- Setting up Email2KG on a fresh EC2 instance
- You want automated installation of all dependencies
- Testing or demo deployments

**Requirements:**
- Ubuntu 22.04+ EC2 instance (t3.medium or larger)
- SSH access to the instance
- Ports 22, 80, 443 open in security group

**Usage:**
```bash
# SSH into your EC2 instance first
ssh -i your-key.pem ubuntu@your-ec2-ip

# Then run:
git clone https://github.com/yourusername/email2kg.git
cd email2kg
chmod +x scripts/deployment/deploy-ec2.sh
./scripts/deployment/deploy-ec2.sh
```

**What it does:**
1. Updates system packages
2. Installs Docker and Docker Compose
3. Clones/updates repository
4. Configures environment variables
5. Builds and starts all services
6. Sets up systemd services for auto-start

**Time:** ~20-30 minutes

**Note:** After running this, you should run `setup-letsencrypt.sh` to enable HTTPS.

---

### 🏗️ **deploy-aws.sh** (AWS ECS/Fargate)
**Purpose:** Deploy to AWS ECS/Fargate for scalable production

**Use this when:**
- You need auto-scaling capabilities
- Expecting high traffic volumes
- Want managed infrastructure
- Need high availability

**Requirements:**
- AWS account with ECS access
- AWS CLI configured
- Terraform installed (optional)
- Budget: ~$100-200/month

**Usage:**
```bash
cd ~/email2kg
./scripts/deployment/deploy-aws.sh
```

**What it does:**
1. Creates ECS cluster
2. Sets up load balancer
3. Configures auto-scaling
4. Deploys containers to Fargate
5. Sets up CloudWatch monitoring

**Time:** ~30-45 minutes

---

## 🎯 Which Script Should I Use?

### For Production Deployment:
1. Start with `deploy-ec2.sh` to set up the EC2 instance
2. Then run `setup-letsencrypt.sh` to enable HTTPS
3. Done! Your app is production-ready

### For Development/Testing:
- Use `docker-compose` directly (see [Quick Start Guide](../../docs/guides/quickstart.md))

### For High-Traffic Production:
- Use `deploy-aws.sh` for ECS/Fargate deployment

### For Custom SSL Certificates:
- Use `setup-https.sh` if you have purchased certificates

---

## 🐛 Troubleshooting

### Script Permission Denied
```bash
chmod +x scripts/deployment/*.sh
```

### Port Already in Use
```bash
# Check what's using port 80/443
sudo lsof -i :80
sudo lsof -i :443

# Stop nginx if running
sudo systemctl stop nginx
sudo systemctl disable nginx
```

### Let's Encrypt Rate Limit
- Let's Encrypt has rate limits: 50 certificates per domain per week
- If you hit the limit, wait 7 days or use staging environment for testing

### Docker Not Found
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

---

## 📚 Additional Resources

- [Deployment Documentation](../../docs/deployment/)
- [HTTPS Setup Guide](../../docs/deployment/https-setup.md)
- [AWS EC2 Guide](../../docs/deployment/aws-ec2.md)
- [Troubleshooting Guide](../../docs/deployment/testing.md)

---

**Last Updated:** December 2025
