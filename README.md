# 📧 Email2KG - AI-Powered Knowledge Graph Platform

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![React](https://img.shields.io/badge/react-18.0+-61DAFB.svg)

**Transform your emails and documents into actionable intelligence with AI-powered knowledge graphs**

[Features](#-key-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Deployment](#-deployment) • [Contributing](#-contributing)

</div>

---

## 🎯 What is Email2KG?

Email2KG is an **intelligent document processing platform** that automatically extracts, analyzes, and connects information from emails and documents into a searchable knowledge graph. It uses AI to understand your documents, discover relationships, and help you find insights instantly.

### Why Email2KG?

- **🤖 AI-Powered Extraction** - GPT-4 Vision for 98-99% OCR accuracy on any document
- **🔗 Intelligent Knowledge Graph** - Automatically discovers and visualizes relationships
- **📧 Universal Integration** - Gmail, Outlook, WhatsApp, Telegram, and direct uploads
- **⚡ Real-time Processing** - Instant document analysis and entity extraction
- **🔒 Enterprise Security** - Multi-tenant, JWT auth, data encryption
- **🚀 Production Ready** - Docker-based, scalable, easy to deploy

---

## ✨ Key Features

### Core Capabilities

- **📨 Multi-Platform Integration**: Gmail (OAuth), Outlook, IMAP/SMTP, WhatsApp, Telegram
- **🤖 AI Document Processing**: GPT-4 Vision OCR (98-99% accuracy), intelligent classification
- **🕸️ Knowledge Graph**: Automatic relationship discovery, interactive visualization
- **🔐 Enterprise Auth**: Multi-user support, JWT authentication, OAuth integrations
- **📊 Smart Analytics**: Dashboard insights, transaction tracking, spending analysis
- **🎨 Modern UI**: Responsive React interface, real-time updates, beautiful landing page

### Future Roadmap

- **🔔 Intelligent Reminders**: Payment due dates, flight notifications, contract renewals
- **💬 Conversational AI**: Natural language queries ("How much did I spend on AWS?")
- **📈 Advanced Analytics**: Spending forecasts, anomaly detection, cost optimization
- **🔗 Deep Integrations**: QuickBooks, Xero, calendar sync, Slack notifications
- **🌍 Mobile Apps**: iOS and Android with offline sync

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/email2kg.git
cd email2kg

# Configure environment
cp .env.example .env
nano .env  # Add your API keys and configuration

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Manual Setup

#### Backend
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create database
createdb email2kg

# Run migrations
python manage.py migrate

# Start server
uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

**📖 Complete guide:** [Quick Start Documentation](./docs/guides/quickstart.md)

---

## ⚙️ Configuration

### Required Environment Variables

```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/email2kg

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here

# OpenAI (Required for GPT-4 Vision OCR)
OPENAI_API_KEY=sk-your-openai-api-key

# Google OAuth (Optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
```

**Generate secure keys:**
```bash
openssl rand -hex 32  # SECRET_KEY
openssl rand -hex 32  # JWT_SECRET_KEY
```

**📖 Full configuration guide:** [Configuration Documentation](./docs/guides/configuration.md)

---

## 🚢 Deployment

### Production Deployment (AWS EC2 + HTTPS)

**1. Launch EC2 Instance**
- Instance type: t3.medium or larger
- OS: Ubuntu 22.04+
- Open ports: 22 (SSH), 80 (HTTP), 443 (HTTPS)

**2. Deploy Application**
```bash
# SSH into your EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Clone and deploy
git clone https://github.com/yourusername/email2kg.git
cd email2kg
chmod +x scripts/deployment/deploy-ec2.sh
./scripts/deployment/deploy-ec2.sh
```

**3. Setup HTTPS with Let's Encrypt**
```bash
# Point your domain to EC2 IP first
# Then run:
sudo ./scripts/deployment/setup-letsencrypt.sh
```

**✅ Done!** Your app is now live at `https://yourdomain.com`

**📖 Detailed guides:**
- [AWS EC2 Deployment](./docs/deployment/aws-ec2.md)
- [HTTPS Setup](./docs/deployment/https-setup.md)
- [EC2 Quick Guide](./docs/deployment/ec2-guide.md)
- [Testing & Validation](./docs/deployment/testing.md)

### Other Deployment Options

- **Local Docker**: `docker-compose up -d` (development)
- **AWS ECS/Fargate**: See [AWS Deployment Guide](./docs/deployment/aws-ec2.md#ecs-fargate)
- **Manual SSL**: See [HTTPS Setup Guide](./docs/deployment/https-setup.md)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Frontend (React + TypeScript)              │
│                                                              │
│  ┌──────────┐ ┌──────────┐ ┌────────┐ ┌─────────────────┐  │
│  │  Login   │ │Dashboard │ │ Graph  │ │   Documents     │  │
│  └──────────┘ └──────────┘ └────────┘ └─────────────────┘  │
└──────────────────────────┬───────────────────────────────────┘
                           │ REST API (HTTPS)
┌──────────────────────────┴───────────────────────────────────┐
│                   Backend (FastAPI + Python)                  │
│                                                              │
│  ┌──────────────┐  ┌────────────────┐  ┌─────────────────┐ │
│  │   Auth       │  │  GPT-4 Vision  │  │   Messaging     │ │
│  │   (JWT)      │  │  (98-99% OCR)  │  │   Multi-Platform│ │
│  └──────────────┘  └────────────────┘  └─────────────────┘ │
│                                                              │
│  ┌──────────────┐  ┌────────────────┐  ┌─────────────────┐ │
│  │  Template    │  │  Data Extract  │  │  Graph Builder  │ │
│  │  Learning    │  │  (GPT-4)       │  │  (Neo4j)        │ │
│  └──────────────┘  └────────────────┘  └─────────────────┘ │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────┴───────────────────────────────────┐
│                        Data Layer                             │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ PostgreSQL  │  │    Neo4j     │  │    Redis         │   │
│  │  (Primary)  │  │ (Knowledge   │  │    (Cache)       │   │
│  │             │  │  Graph)      │  │                  │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
└───────────────────────────────────────────────────────────────┘
```

**Technology Stack:**
- **Backend**: FastAPI, PostgreSQL, Neo4j, SQLAlchemy, OpenAI API
- **Frontend**: React 18, TypeScript, Axios, React Router
- **AI**: GPT-4 Vision (OCR), GPT-4 (extraction), Template learning
- **Messaging**: Gmail API, Microsoft Graph, WhatsApp, Telegram
- **Infrastructure**: Docker, Nginx, Let's Encrypt, SystemD

**📖 Detailed architecture:** [Architecture Documentation](./docs/architecture/ARCHITECTURE.md)

---

## 📚 Documentation

### 📖 Comprehensive Documentation

All documentation is organized in the [`docs/`](./docs) directory:

- **[Documentation Index](./docs/README.md)** - Start here for all documentation
- **[Quick Start Guide](./docs/guides/quickstart.md)** - Get started in 5 minutes
- **[Configuration Guide](./docs/guides/configuration.md)** - Environment variables and settings
- **[Gmail Setup](./docs/guides/gmail-setup.md)** - OAuth configuration for production

### 🚀 Deployment Guides

- **[Deployment Overview](./docs/deployment/README.md)** - All deployment options
- **[AWS EC2 Deployment](./docs/deployment/aws-ec2.md)** - Complete production setup
- **[HTTPS Setup](./docs/deployment/https-setup.md)** - SSL/TLS configuration
- **[Testing & Validation](./docs/deployment/testing.md)** - Verify your deployment

### 🏗️ Architecture & Design

- **[Architecture Overview](./docs/architecture/ARCHITECTURE.md)** - System design
- **[Messaging System](./docs/architecture/messaging.md)** - Multi-platform integration
- **[UI Design](./docs/architecture/ui-design.md)** - Frontend design principles

### 🔌 API Reference

- **[API Documentation](./docs/api/README.md)** - Complete REST API reference
- **[Interactive API Docs](http://localhost:8000/docs)** - Swagger UI (when running locally)

### 🛠️ Scripts

All deployment and utility scripts are in [`scripts/`](./scripts):

- **[Deployment Scripts](./scripts/deployment/)** - AWS, EC2, HTTPS setup
- **[Development Scripts](./scripts/development/)** - Local setup, rebuild tools
- **[Utility Scripts](./scripts/utils/)** - Debug and verification tools

---

## 🧪 Testing

### Run Tests

```bash
# Backend tests
cd backend
pytest
pytest --cov=app --cov-report=html  # With coverage

# Frontend tests
cd frontend
npm test
npm test -- --coverage  # With coverage

# E2E tests
docker-compose -f docker-compose.test.yml up -d
npm run test:e2e
```

### Code Quality

```bash
# Backend (Python)
black .          # Format
flake8 .         # Lint
mypy .           # Type check

# Frontend (TypeScript)
npm run prettier # Format
npm run lint     # Lint
npm run type-check # Type check
```

**📖 Testing guide:** [CONTRIBUTING.md](./CONTRIBUTING.md#testing-guidelines)

---

## 📊 Performance

### OCR Accuracy Comparison

| Method | Accuracy | Speed | Cost/Page |
|--------|----------|-------|-----------|
| Tesseract | 70-80% | 2-3s | Free |
| Google Vision | 90-95% | 1-2s | $0.0015 |
| **GPT-4 Vision** | **98-99%** | 3-5s | **$0.01** |

### Cost Optimization

- **First Document**: Uses GPT-4 Vision (~$0.01)
- **Template Created**: Saves document pattern
- **Similar Documents**: Uses template (Free, <1s)
- **Cost Reduction**: **90% after initial learning**

---

## 🤝 Contributing

We welcome contributions! Email2KG is built with best practices and clean code standards.

### How to Contribute

1. **Fork** the repository
2. **Create a branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** following our [coding standards](./CONTRIBUTING.md#coding-standards)
4. **Test** your changes thoroughly
5. **Commit**: `git commit -m 'feat: add amazing feature'`
6. **Push**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

**📖 Full contributing guide:** [CONTRIBUTING.md](./CONTRIBUTING.md)

### Development Standards

- **Python**: PEP 8, Black formatting, type hints, docstrings
- **TypeScript**: Airbnb style, Prettier, functional components
- **Commits**: [Conventional Commits](https://www.conventionalcommits.org/)
- **Tests**: Pytest (backend), Jest (frontend), 80%+ coverage
- **Documentation**: Update docs with code changes

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📞 Support & Community

- **📧 Issues**: [GitHub Issues](https://github.com/yourusername/email2kg/issues)
- **📖 Documentation**: [Full Documentation](./docs/README.md)
- **💬 Discussions**: [GitHub Discussions](https://github.com/yourusername/email2kg/discussions)
- **🐦 Twitter**: [@email2kg](#)
- **💼 LinkedIn**: [Email2KG](#)

---

## 🗺️ Roadmap

### ✅ Phase 1 - MVP (Current)
- [x] Multi-user authentication with JWT
- [x] Gmail OAuth integration
- [x] GPT-4 Vision OCR
- [x] Knowledge graph with Neo4j
- [x] React dashboard
- [x] Docker deployment
- [x] HTTPS with Let's Encrypt

### 🚧 Phase 2 - Intelligence (In Progress)
- [ ] Intelligent reminders and alerts
- [ ] Conversational AI assistant
- [ ] Advanced analytics and forecasting
- [ ] Mobile apps (iOS/Android)
- [ ] Browser extensions

### 🔮 Phase 3 - Enterprise (Planned)
- [ ] Team workspaces and collaboration
- [ ] Integrations (QuickBooks, Xero, Slack)
- [ ] SSO (SAML, LDAP)
- [ ] On-premise deployment option
- [ ] Advanced security and compliance

---

## 🙏 Acknowledgments

Built with ❤️ using:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://react.dev/) - UI library
- [OpenAI](https://openai.com/) - GPT-4 Vision and GPT-4 APIs
- [Neo4j](https://neo4j.com/) - Graph database
- [PostgreSQL](https://www.postgresql.org/) - Relational database
- [Docker](https://www.docker.com/) - Containerization
- [Let's Encrypt](https://letsencrypt.org/) - Free SSL certificates

---

<div align="center">

**[⬆ Back to top](#-email2kg---ai-powered-knowledge-graph-platform)**

Made with 🚀 by developers, for developers

</div>
