# AWS Deployment Guide - Email2KG

Complete guide to deploying Email2KG on AWS with production-grade configuration.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         AWS Cloud                            │
│                                                               │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │ CloudFront   │────────▶│  S3 Bucket   │                  │
│  │   (CDN)      │         │  (Frontend)  │                  │
│  └──────────────┘         └──────────────┘                  │
│         │                                                     │
│         │                                                     │
│         ▼                                                     │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │     ALB      │────────▶│  ECS/Fargate │                  │
│  │ Load Balancer│         │  (Backend)   │                  │
│  └──────────────┘         └──────────────┘                  │
│                                  │                            │
│                                  ▼                            │
│                           ┌──────────────┐                   │
│                           │  RDS Postgres│                   │
│                           │  (Database)  │                   │
│                           └──────────────┘                   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Prerequisites

### AWS Account Setup
- AWS Account with appropriate permissions
- AWS CLI installed and configured
- Domain name (optional but recommended)

### Install AWS CLI
```bash
# macOS
brew install awscli

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS CLI
aws configure
# Enter: AWS Access Key ID, Secret Access Key, Region (us-east-1), Output format (json)
```

---

## 🚀 Deployment Option 1: Docker + ECS Fargate (Recommended)

**Best for**: Production workloads with auto-scaling and minimal server management

### Step 1: Create Docker Images

Already provided in the repository:
- `Dockerfile` (backend)
- `frontend/Dockerfile` (frontend)

### Step 2: Setup AWS Resources

#### 2.1 Create RDS PostgreSQL Database

```bash
# Create DB subnet group
aws rds create-db-subnet-group \
  --db-subnet-group-name email2kg-db-subnet \
  --db-subnet-group-description "Email2KG DB Subnet Group" \
  --subnet-ids subnet-xxxxx subnet-yyyyy

# Create RDS PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier email2kg-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 14.7 \
  --master-username postgres \
  --master-user-password YOUR_SECURE_PASSWORD \
  --allocated-storage 20 \
  --vpc-security-group-ids sg-xxxxx \
  --db-subnet-group-name email2kg-db-subnet \
  --publicly-accessible \
  --backup-retention-period 7

# Get RDS endpoint
aws rds describe-db-instances \
  --db-instance-identifier email2kg-db \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text
```

#### 2.2 Create ECR Repositories

```bash
# Create ECR repository for backend
aws ecr create-repository --repository-name email2kg-backend

# Create ECR repository for frontend
aws ecr create-repository --repository-name email2kg-frontend

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
```

#### 2.3 Build and Push Docker Images

```bash
# Backend
cd /path/to/email2kg/backend
docker build -t email2kg-backend .
docker tag email2kg-backend:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/email2kg-backend:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/email2kg-backend:latest

# Frontend
cd /path/to/email2kg/frontend
docker build -t email2kg-frontend .
docker tag email2kg-frontend:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/email2kg-frontend:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/email2kg-frontend:latest
```

#### 2.4 Create ECS Cluster

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name email2kg-cluster
```

#### 2.5 Create Task Definitions

Create `backend-task-definition.json`:
```json
{
  "family": "email2kg-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "email2kg-backend",
      "image": "YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/email2kg-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://postgres:PASSWORD@RDS_ENDPOINT:5432/email2kg"
        },
        {
          "name": "OPENAI_API_KEY",
          "value": "YOUR_OPENAI_API_KEY"
        },
        {
          "name": "SECRET_KEY",
          "value": "YOUR_SECRET_KEY"
        },
        {
          "name": "JWT_SECRET_KEY",
          "value": "YOUR_JWT_SECRET"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/email2kg-backend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

Register task definition:
```bash
aws ecs register-task-definition --cli-input-json file://backend-task-definition.json
```

#### 2.6 Create Application Load Balancer

```bash
# Create ALB
aws elbv2 create-load-balancer \
  --name email2kg-alb \
  --subnets subnet-xxxxx subnet-yyyyy \
  --security-groups sg-xxxxx

# Create target group
aws elbv2 create-target-group \
  --name email2kg-backend-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-xxxxx \
  --target-type ip \
  --health-check-path /health

# Create listener
aws elbv2 create-listener \
  --load-balancer-arn ALB_ARN \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=TARGET_GROUP_ARN
```

#### 2.7 Create ECS Service

```bash
aws ecs create-service \
  --cluster email2kg-cluster \
  --service-name email2kg-backend-service \
  --task-definition email2kg-backend \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx,subnet-yyyyy],securityGroups=[sg-xxxxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=TARGET_GROUP_ARN,containerName=email2kg-backend,containerPort=8000"
```

### Step 3: Deploy Frontend to S3 + CloudFront

```bash
# Build frontend
cd frontend
npm run build

# Create S3 bucket
aws s3 mb s3://email2kg-frontend

# Configure bucket for static website hosting
aws s3 website s3://email2kg-frontend --index-document index.html --error-document index.html

# Upload build files
aws s3 sync build/ s3://email2kg-frontend --acl public-read

# Create CloudFront distribution
aws cloudfront create-distribution --origin-domain-name email2kg-frontend.s3-website-us-east-1.amazonaws.com
```

---

## 🖥️ Deployment Option 2: EC2 (Simple & Full Control)

**Best for**: Quick setup, learning, or when you need full server control

### Step 1: Launch EC2 Instance

```bash
# Launch Ubuntu EC2 instance (t3.medium recommended)
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.medium \
  --key-name YOUR_KEY_PAIR \
  --security-group-ids sg-xxxxx \
  --subnet-id subnet-xxxxx \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=email2kg-server}]'
```

### Step 2: Connect to EC2 Instance

```bash
ssh -i your-key.pem ubuntu@EC2_PUBLIC_IP
```

### Step 3: Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python, Node.js, PostgreSQL
sudo apt install -y python3.10 python3-pip nodejs npm postgresql postgresql-contrib nginx

# Install Docker (optional)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
```

### Step 4: Setup PostgreSQL

```bash
sudo -u postgres psql

CREATE DATABASE email2kg;
CREATE USER email2kg_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE email2kg TO email2kg_user;
\q
```

### Step 5: Clone and Setup Application

```bash
# Clone repository
git clone https://github.com/yourusername/email2kg.git
cd email2kg

# Setup backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://email2kg_user:your_secure_password@localhost:5432/email2kg
OPENAI_API_KEY=your_openai_key
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
ALLOWED_ORIGINS=["http://your-domain.com"]
EOF

# Run migrations (if using Alembic)
# alembic upgrade head

# Setup frontend
cd ../frontend
npm install
npm run build
```

### Step 6: Setup Nginx as Reverse Proxy

```bash
sudo nano /etc/nginx/sites-available/email2kg
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /home/ubuntu/email2kg/frontend/build;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/email2kg /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 7: Setup Systemd Service for Backend

```bash
sudo nano /etc/systemd/system/email2kg.service
```

```ini
[Unit]
Description=Email2KG FastAPI Application
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/email2kg/backend
Environment="PATH=/home/ubuntu/email2kg/backend/venv/bin"
EnvironmentFile=/home/ubuntu/email2kg/backend/.env
ExecStart=/home/ubuntu/email2kg/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Start service
sudo systemctl daemon-reload
sudo systemctl enable email2kg
sudo systemctl start email2kg
sudo systemctl status email2kg
```

### Step 8: Setup SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is set up automatically
sudo certbot renew --dry-run
```

---

## 🔐 Security Best Practices

### 1. Security Groups

**Backend Security Group:**
```bash
# Allow HTTPS from ALB
Port 443 from ALB Security Group

# Allow HTTP from ALB
Port 8000 from ALB Security Group

# Allow SSH (for management only)
Port 22 from YOUR_IP
```

**Database Security Group:**
```bash
# PostgreSQL from backend only
Port 5432 from Backend Security Group
```

### 2. Environment Variables

**NEVER** commit sensitive values. Use AWS Secrets Manager:

```bash
# Store secrets
aws secretsmanager create-secret \
  --name email2kg/database-url \
  --secret-string "postgresql://..."

aws secretsmanager create-secret \
  --name email2kg/openai-api-key \
  --secret-string "sk-..."

# Retrieve in application
aws secretsmanager get-secret-value --secret-id email2kg/database-url
```

### 3. IAM Roles

Create IAM role for ECS tasks with minimum required permissions:
- ECR pull images
- CloudWatch logs write
- Secrets Manager read

---

## 📊 Monitoring & Logging

### CloudWatch Logs

```bash
# Create log group
aws logs create-log-group --log-group-name /ecs/email2kg-backend

# View logs
aws logs tail /ecs/email2kg-backend --follow
```

### CloudWatch Metrics

Monitor:
- ECS CPU and Memory utilization
- ALB request count and latency
- RDS connections and query performance
- Custom application metrics

### Setup Alarms

```bash
# High CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name email2kg-high-cpu \
  --alarm-description "Alert when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

---

## 🔄 CI/CD with GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to AWS

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1

      - name: Build and push backend
        run: |
          cd backend
          docker build -t email2kg-backend .
          docker tag email2kg-backend:latest ${{ steps.login-ecr.outputs.registry }}/email2kg-backend:latest
          docker push ${{ steps.login-ecr.outputs.registry }}/email2kg-backend:latest

      - name: Deploy to ECS
        run: |
          aws ecs update-service --cluster email2kg-cluster --service email2kg-backend-service --force-new-deployment
```

---

## 💰 Cost Estimation (Monthly)

### Option 1: ECS Fargate + RDS
- **ECS Fargate** (2 tasks): ~$30-40
- **RDS db.t3.micro**: ~$15-20
- **Application Load Balancer**: ~$20
- **CloudFront + S3**: ~$5-10
- **Data Transfer**: ~$10-20
- **Total**: ~$80-110/month

### Option 2: Single EC2
- **EC2 t3.medium**: ~$30
- **EBS Storage (50GB)**: ~$5
- **Elastic IP**: ~$3.60
- **Data Transfer**: ~$10
- **Total**: ~$50/month

---

## 🚀 Quick Start Commands

### Deploy with Docker Compose (for testing)

```bash
# Clone repo
git clone https://github.com/yourusername/email2kg.git
cd email2kg

# Create .env file
cp .env.example .env
# Edit .env with your values

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Access application
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

---

## 📝 Post-Deployment Checklist

- [ ] SSL certificate installed and auto-renewal configured
- [ ] Database backups enabled (RDS automated backups)
- [ ] CloudWatch alarms configured
- [ ] Security groups properly configured
- [ ] Secrets stored in AWS Secrets Manager
- [ ] Domain DNS configured
- [ ] CORS properly configured for your domain
- [ ] Rate limiting enabled
- [ ] Monitoring dashboard created
- [ ] Backup strategy implemented
- [ ] Disaster recovery plan documented

---

## 🆘 Troubleshooting

### Backend not starting
```bash
# Check ECS task logs
aws logs tail /ecs/email2kg-backend --follow

# Check task status
aws ecs describe-tasks --cluster email2kg-cluster --tasks TASK_ARN
```

### Database connection issues
```bash
# Test connection from backend
psql postgresql://user:pass@rds-endpoint:5432/email2kg

# Check RDS security group
# Ensure backend security group is allowed
```

### High costs
```bash
# Check cost explorer
aws ce get-cost-and-usage --time-period Start=2024-01-01,End=2024-01-31 --granularity MONTHLY --metrics UnblendedCost

# Optimize:
# - Use reserved instances for predictable workloads
# - Enable S3 lifecycle policies
# - Use CloudFront caching
# - Reduce RDS instance size if possible
```

---

## 📚 Additional Resources

- [AWS ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [React Deployment](https://create-react-app.dev/docs/deployment/)
- [PostgreSQL on AWS](https://aws.amazon.com/rds/postgresql/)

---

**Need Help?**
- Check CloudWatch logs first
- Review security group settings
- Verify environment variables
- Test database connectivity
- Check IAM permissions
