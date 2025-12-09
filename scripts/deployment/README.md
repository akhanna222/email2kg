# Deployment Scripts

This directory contains automated deployment scripts for Email2KG.

## 📁 Scripts Overview

### Production Deployment

#### `enable-https.sh` ⭐ **Recommended**
**One-command SSL/HTTPS setup for production**

```bash
sudo ./enable-https.sh
```

**What it does:**
- ✅ Validates prerequisites (DNS, ports, services)
- ✅ Obtains free SSL certificate from Let's Encrypt
- ✅ Configures HTTPS with auto-renewal
- ✅ Restarts services with SSL enabled

**Requirements:**
- Domain pointing to server
- Ports 80 and 443 open
- Docker running

**Documentation:** See `docs/deployment/QUICK_START_SSL.md`

---

#### `setup-letsencrypt.sh`
**Complete Let's Encrypt SSL setup** (Called by `enable-https.sh`)

```bash
sudo ./setup-letsencrypt.sh
```

**What it does:**
- Switches to HTTP-only mode temporarily
- Runs certbot for certificate acquisition
- Copies certificates to `ssl/` directory
- Configures auto-renewal hooks
- Restarts with HTTPS enabled

**Note:** Use `enable-https.sh` instead for better UX.

---

#### `deploy-ec2.sh`
**Automated EC2 first-time deployment**

```bash
sudo ./deploy-ec2.sh
```

**What it does:**
- Detects EC2 public IP automatically
- Creates `.env` from template
- Configures all services
- Builds and starts Docker containers

**Use case:** First-time EC2 setup after SSH

**Documentation:** See `docs/deployment/EC2_DEPLOYMENT.md`

---

#### `deploy-aws.sh`
**AWS ECS/Fargate deployment** (Advanced)

```bash
./deploy-aws.sh
```

**What it does:**
- Deploys to AWS ECS/Fargate
- Creates ECR repositories
- Sets up load balancer
- Configures auto-scaling

**Use case:** Enterprise production on AWS managed services

**Requirements:**
- AWS CLI configured
- Proper IAM permissions

---

## 🚀 Quick Start

### For EC2 Production:

```bash
# 1. First-time setup
cd ~/email2kg
sudo ./scripts/deployment/deploy-ec2.sh

# 2. Enable HTTPS
sudo ./scripts/deployment/enable-https.sh

# 3. Done! Access your site
curl https://yourdomain.com/health
```

### For AWS ECS/Fargate:

```bash
cd ~/email2kg
./scripts/deployment/deploy-aws.sh
```

## 🔧 Development Scripts

See `scripts/development/` for development-related scripts:
- `setup-dev.sh` - Local development setup
- `rebuild-frontend.sh` - Frontend rebuild

## 📚 Documentation

- **EC2 Deployment**: `docs/deployment/EC2_DEPLOYMENT.md`
- **SSL Setup**: `docs/deployment/SSL_SETUP_GUIDE.md`
- **Quick SSL**: `docs/deployment/QUICK_START_SSL.md`
- **IP Management**: `docs/deployment/IP_CHANGE_CHECKLIST.md`
- **DNS Setup**: `docs/deployment/NAMECHEAP_DNS_UPDATE.md`

## ⚡ Common Tasks

### Update domain/IP when EC2 IP changes:
```bash
scripts/utils/update-domain.sh
```

### Restart services:
```bash
sudo docker compose down
sudo docker compose up -d
```

### View logs:
```bash
sudo docker compose logs -f
```

### Check service status:
```bash
sudo docker ps
```

## 🆘 Troubleshooting

**Services not starting:**
```bash
sudo docker compose down
sudo docker compose up -d
sudo docker compose logs -f
```

**SSL certificate issues:**
```bash
sudo certbot certificates
sudo certbot renew --dry-run
```

**Permission denied:**
- Make sure to run scripts with `sudo` for Docker commands
- Check script is executable: `chmod +x script.sh`

---

For detailed troubleshooting, see the full documentation in `docs/deployment/`.
