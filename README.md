# 📧 Email2KG - AI-Powered Knowledge Graph from Emails & Documents

<div align="center">

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![React](https://img.shields.io/badge/react-18.0+-61DAFB.svg)
![Docker](https://img.shields.io/badge/docker-compose-2496ED.svg)

**Transform emails and documents into actionable intelligence with AI-powered OCR and knowledge graphs**

[Quick Start](#-quick-start) • [Features](#-features) • [Documentation](#-documentation) • [Deployment](#-deployment)

</div>

---

## 🎯 What is Email2KG?

Email2KG is an **intelligent document processing platform** that automatically extracts, analyzes, and connects information from emails and documents using:

- **🤖 GPT-4 Vision OCR** - 98-99% accuracy on scanned documents and images
- **📊 Knowledge Graphs** - Automatic relationship discovery and visualization
- **⚡ Background Processing** - Celery + Redis for scalable async task handling
- **🔐 Multi-tenant Auth** - JWT authentication with OAuth (Gmail, Outlook)
- **📧 Email Integration** - Gmail, Outlook, IMAP with automated attachment processing

---

## ✨ Features

### Core Capabilities
- **📨 Email Processing**: Automatic email categorization, attachment extraction, OCR processing
- **🖼️ Document OCR**: Supports PDFs, images (JPG, PNG, TIFF, WEBP, BMP) with GPT-4 Vision
- **🕸️ Knowledge Graph**: Entity extraction, relationship mapping, interactive visualization
- **📊 Analytics Dashboard**: Transaction tracking, spending analysis, insights
- **🔔 Smart Categorization**: Invoices, receipts, contracts, travel documents
- **⚡ Real-time Processing**: Background workers for scalable async processing

### Platform Integrations
- **Email**: Gmail (OAuth), Outlook (OAuth), IMAP/SMTP
- **Messaging**: WhatsApp Business API, Telegram Bot (optional)
- **Storage**: Local filesystem, AWS S3 (optional)

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API key (for GPT-4 Vision OCR)
- (Optional) Google OAuth credentials for Gmail

### Installation

```bash
# 1. Clone repository
git clone https://github.com/akhanna222/email2kg.git
cd email2kg

# 2. Configure environment
cp .env.example .env
nano .env  # Add your API keys

# 3. Start all services
docker compose up -d

# 4. Access application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Services Running
After `docker compose up -d`, you'll have 5 services:
- **PostgreSQL** - Database (port 5432, internal only)
- **Redis** - Message broker (port 6379, internal only)
- **Backend** - FastAPI API (port 8000)
- **Celery Worker** - Background task processor
- **Frontend** - React UI with Nginx (port 80/443)

---

## 🏗️ Architecture

```
┌─────────────┐
│   Frontend  │  React + TypeScript + Nginx
│  (Port 80)  │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌──────────────┐
│   Backend   │────▶│  PostgreSQL  │
│  (FastAPI)  │     │   Database   │
└──────┬──────┘     └──────────────┘
       │
       ▼
┌─────────────┐     ┌──────────────┐
│    Redis    │────▶│    Celery    │
│   Broker    │     │   Workers    │
└─────────────┘     └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  GPT-4 Vision│
                    │  OCR Service │
                    └──────────────┘
```

### Tech Stack
- **Backend**: Python 3.10+, FastAPI, SQLAlchemy, Celery
- **Frontend**: React 18, TypeScript, D3.js (graphs)
- **Database**: PostgreSQL 14
- **Cache/Queue**: Redis 7
- **OCR**: OpenAI GPT-4 Vision API
- **Deployment**: Docker Compose, Nginx

---

## 📚 Documentation

### Getting Started
- **[Quickstart Guide](docs/guides/quickstart.md)** - Get up and running in 5 minutes
- **[Gmail Setup](docs/guides/gmail-setup.md)** - Configure Gmail OAuth integration
- **[Configuration](docs/guides/configuration.md)** - Environment variables explained

### Deployment
- **[EC2 Deployment](docs/deployment/EC2_DEPLOYMENT.md)** - Complete AWS EC2 production setup
- **[SSL/HTTPS Setup](docs/deployment/QUICK_START_SSL.md)** - Enable HTTPS in one command
- **[IP Management](docs/deployment/IP_CHANGE_CHECKLIST.md)** - Handle EC2 IP changes
- **[DNS Configuration](docs/deployment/NAMECHEAP_DNS_UPDATE.md)** - Namecheap DNS setup

### Features
- **[OCR Email Extraction](docs/features/OCR_EMAIL_EXTRACTION.md)** - Automated email attachment processing
- **[Architecture](docs/architecture/ARCHITECTURE.md)** - System design and data flow

### Development
- **[API Documentation](docs/api/README.md)** - REST API reference
- **[Contributing](.github/CONTRIBUTING.md)** - Contribution guidelines

---

## 🌐 Deployment

### Development (Local)
```bash
docker compose up -d
```

### Production (EC2)
```bash
# 1. First-time setup
sudo ./scripts/deployment/deploy-ec2.sh

# 2. Enable HTTPS
sudo ./scripts/deployment/enable-https.sh

# 3. Access your site
curl https://yourdomain.com/health
```

See **[EC2 Deployment Guide](docs/deployment/EC2_DEPLOYMENT.md)** for detailed instructions.

---

## 🔧 Configuration

### Required Environment Variables
```bash
# OpenAI API (required for OCR)
OPENAI_API_KEY=sk-...

# Database
DB_PASSWORD=your_secure_password

# Security (generate with: openssl rand -hex 32)
SECRET_KEY=...
JWT_SECRET_KEY=...

# Domain/IP
PUBLIC_DOMAIN=yourdomain.com
PUBLIC_PROTOCOL=https
```

### Optional Integrations
```bash
# Gmail OAuth
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# WhatsApp Business
WHATSAPP_PHONE_NUMBER_ID=...
WHATSAPP_APP_ID=...

# Telegram Bot
TELEGRAM_BOT_TOKEN=...
```

See **[.env.example](.env.example)** for complete configuration.

---

## 📊 Usage Examples

### 1. Process Gmail Emails
```python
# Sync emails from last 3 months
POST /api/sync/gmail?process_attachments=true

# Automatically:
# - Fetches emails
# - Downloads attachments (PDFs, images)
# - Runs OCR extraction
# - Categorizes documents
# - Builds knowledge graph
```

### 2. Upload & Process Document
```python
# Upload a scanned invoice
POST /api/documents/upload
Content-Type: multipart/form-data

# Returns extracted data:
{
  "vendor": "AWS",
  "amount": "$456.78",
  "date": "2024-12-01",
  "category": "Cloud Services"
}
```

### 3. Query Knowledge Graph
```python
# Natural language queries
POST /api/query
{
  "question": "How much did I spend on cloud services?"
}

# Returns intelligent analysis with sources
```

---

## 🔒 Security

- **JWT Authentication** - Secure token-based auth
- **OAuth Integration** - Gmail/Outlook without storing passwords
- **Multi-tenant** - User data isolation
- **SSL/TLS** - HTTPS encryption (Let's Encrypt)
- **Environment Variables** - Secrets never in code
- **Docker Network Isolation** - Services on private network

---

## 📈 Performance

- **Background Processing** - Celery workers handle heavy OCR tasks
- **Async Operations** - Non-blocking email/document processing
- **Database Indexing** - Optimized queries for fast search
- **Redis Caching** - Quick access to frequent data
- **Connection Pooling** - Efficient database connections

---

## 🐛 Troubleshooting

### Services not starting
```bash
sudo docker compose down
sudo docker compose up -d
sudo docker compose logs -f
```

### OCR not working
- Check `OPENAI_API_KEY` is set correctly
- Verify API key has GPT-4 Vision access
- Check Celery worker logs: `docker compose logs celery_worker`

### Gmail sync failing
- Verify OAuth credentials in Google Cloud Console
- Check redirect URI matches: `https://yourdomain.com/api/auth/google/callback`
- See [Gmail Setup Guide](docs/guides/gmail-setup.md)

### HTTPS/SSL issues
- Run: `sudo ./scripts/deployment/enable-https.sh`
- See [SSL Setup Guide](docs/deployment/SSL_SETUP_GUIDE.md)

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](.github/CONTRIBUTING.md) for guidelines.

### Development Setup
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm start
```

---

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details

---

## 🙏 Acknowledgments

- **OpenAI GPT-4 Vision** - Best-in-class OCR accuracy
- **FastAPI** - Modern Python web framework
- **React** - UI framework
- **Let's Encrypt** - Free SSL certificates

---

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/akhanna222/email2kg/issues)
- **Discussions**: [GitHub Discussions](https://github.com/akhanna222/email2kg/discussions)

---

<div align="center">

**Built with ❤️ by the Email2KG Team**

[⭐ Star us on GitHub](https://github.com/akhanna222/email2kg) | [🐛 Report Bug](https://github.com/akhanna222/email2kg/issues) | [💡 Request Feature](https://github.com/akhanna222/email2kg/issues)

</div>
