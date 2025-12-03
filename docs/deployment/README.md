# Email2KG Deployment Guide

This directory contains comprehensive guides for deploying Email2KG in various environments.

## 🚀 Deployment Options

### Option 1: AWS EC2 (Recommended for Production)
**Best for:** Production deployments with custom domain and HTTPS

📖 **Start here:** [AWS EC2 Deployment Guide](./aws-ec2.md)

**What you'll get:**
- ✅ Full production setup on AWS EC2
- ✅ Custom domain with HTTPS/SSL
- ✅ Automated deployment scripts
- ✅ SystemD service management
- ✅ Auto-renewal SSL certificates

**Requirements:**
- AWS account
- Custom domain name
- Basic Linux knowledge

**Time to deploy:** ~30 minutes

---

### Option 2: Local Development
**Best for:** Development and testing

📖 **Start here:** [Quick Start Guide](../guides/quickstart.md)

**What you'll get:**
- ✅ Local Docker environment
- ✅ Hot reload for development
- ✅ Local database and services

**Requirements:**
- Docker & Docker Compose
- 8GB RAM minimum

**Time to setup:** ~10 minutes

---

### Option 3: Quick EC2 Deploy
**Best for:** Quick testing or demo on EC2

📖 **Start here:** [EC2 Quick Guide](./ec2-guide.md)

**What you'll get:**
- ✅ Rapid deployment on EC2
- ✅ HTTP access (IP address)
- ✅ Basic functionality

**Note:** Not suitable for production (no HTTPS, uses IP)

---

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] Domain name configured (for production)
- [ ] DNS A records point to server IP
- [ ] Google OAuth credentials created
- [ ] AWS EC2 instance launched (t3.medium or larger)
- [ ] Security groups configured (ports 22, 80, 443)

### During Deployment
- [ ] Clone repository
- [ ] Configure environment variables
- [ ] Run deployment script
- [ ] Verify services are running
- [ ] Test HTTPS access

### Post-Deployment
- [ ] Configure Gmail OAuth redirect URI
- [ ] Test user registration and login
- [ ] Connect Gmail account
- [ ] Verify email sync works
- [ ] Set up monitoring (optional)

---

## 🔧 Configuration Files

### Environment Variables
All deployments require a `.env` file. See [Configuration Guide](../guides/configuration.md) for details.

**Required variables:**
```bash
# Database
POSTGRES_USER=email2kg
POSTGRES_PASSWORD=your-secure-password
POSTGRES_DB=email2kg_db

# Django
SECRET_KEY=your-django-secret-key
ALLOWED_HOSTS=agenticrag360.com,www.agenticrag360.com

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=https://agenticrag360.com/api/auth/google/callback

# Neo4j
NEO4J_PASSWORD=your-neo4j-password
```

### SystemD Services
Located in [`./systemd/`](./systemd/) - used for production deployments to ensure services auto-start on reboot.

---

## 🔒 HTTPS/SSL Setup

Production deployments require HTTPS. We use Let's Encrypt for free SSL certificates.

📖 **Full guide:** [HTTPS Setup](./https-setup.md)

**Quick setup:**
```bash
cd ~/email2kg
./scripts/deployment/setup-letsencrypt.sh
```

**What it does:**
- Obtains SSL certificate from Let's Encrypt
- Configures nginx for HTTPS
- Sets up HTTP → HTTPS redirect
- Enables auto-renewal (every 90 days)

---

## 🧪 Testing Your Deployment

After deployment, verify everything works:

📖 **Full testing guide:** [Testing & Validation](./testing.md)

**Quick tests:**
```bash
# Check services are running
docker ps

# Test backend API
curl https://agenticrag360.com/api/health

# Test frontend
curl -I https://agenticrag360.com/

# Check SSL certificate
curl -vI https://agenticrag360.com/ 2>&1 | grep -A 10 "SSL connection"
```

---

## 🔄 Updating Your Deployment

### Pull Latest Code
```bash
cd ~/email2kg
git pull origin main
```

### Rebuild and Restart
```bash
# Full rebuild (with cache)
docker-compose up --build -d

# Force rebuild (no cache)
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Database Migrations
```bash
# Run Django migrations
docker-compose exec backend python manage.py migrate

# Check migration status
docker-compose exec backend python manage.py showmigrations
```

---

## 🐛 Troubleshooting

### Services Won't Start
```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres

# Check service health
docker ps
```

### Can't Access Website
```bash
# Check nginx is running
docker ps | grep frontend

# Check ports
sudo lsof -i :80
sudo lsof -i :443

# Check DNS
nslookup agenticrag360.com
```

### SSL Certificate Issues
```bash
# Check certificate validity
sudo certbot certificates

# Renew certificate manually
sudo certbot renew

# Test auto-renewal
sudo certbot renew --dry-run
```

### Database Connection Errors
```bash
# Check PostgreSQL is running
docker-compose exec postgres pg_isready

# Check connection from backend
docker-compose exec backend python manage.py dbshell
```

---

## 📊 Monitoring & Maintenance

### Log Files
```bash
# View real-time logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Save logs to file
docker-compose logs > deployment.log
```

### Disk Space
```bash
# Check disk usage
df -h

# Clean up Docker images
docker system prune -a
```

### Backup Database
```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U email2kg email2kg_db > backup.sql

# Backup Neo4j
docker-compose exec neo4j neo4j-admin dump --to=/backups/neo4j-backup.dump
```

---

## 🆘 Getting Help

1. Check the [troubleshooting section](#-troubleshooting) above
2. Review [testing guide](./testing.md) for validation steps
3. Check Docker logs for specific error messages
4. Verify environment variables in `.env` file
5. Report issues on GitHub with full error logs

---

## 📚 Additional Resources

- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Nginx Configuration Guide](https://nginx.org/en/docs/)

---

**Last Updated:** December 2025
**Deployment Scripts Version:** 1.0.0
