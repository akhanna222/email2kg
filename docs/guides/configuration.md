# Environment Variables & Configuration Guide

This guide explains where and how to add environment variables and email configurations.

## 📍 Configuration Files Location

### 1. **Main Environment File (Primary)**
**File**: `/.env`
**Created from**: `/.env.example`

```bash
# Create your .env file
cp .env.example .env
```

This is where you add ALL your configuration values. The backend automatically reads from this file.

### 2. **Backend Configuration Class**
**File**: `/backend/app/core/config.py`

This file defines which environment variables are available and their types.

### 3. **Docker Compose Environment**
**File**: `/docker-compose.yml`

Environment variables for Docker containers.

### 4. **Frontend Environment**
**File**: `/frontend/.env`
**Created from**: `/frontend/.env.example`

Configuration for React frontend (API URL, etc.)

---

## 🔧 How to Add New Environment Variables

### Step 1: Add to `.env.example` (for documentation)

Edit `/.env.example`:

```bash
# Your new configuration section
NEW_FEATURE_ENABLED=true
NEW_API_KEY=your_api_key_here
```

### Step 2: Add to Backend Config Class

Edit `/backend/app/core/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Your new settings
    NEW_FEATURE_ENABLED: bool = False
    NEW_API_KEY: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True
```

### Step 3: Create Your `.env` File

```bash
cp .env.example .env
# Edit .env and add your actual values
```

### Step 4: Use in Your Code

```python
from app.core.config import settings

# Access your configuration
if settings.NEW_FEATURE_ENABLED:
    api_key = settings.NEW_API_KEY
    # Use the configuration
```

---

## 📧 Email Provider Configuration

### Current Support: Gmail (OAuth)

**Already configured** - Just add your credentials:

```bash
# .env
EMAIL_PROVIDER=gmail
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/callback
```

### Adding Outlook Support

**Step 1: Add to `.env`**

```bash
EMAIL_PROVIDER=outlook

# Outlook OAuth
OUTLOOK_CLIENT_ID=your_outlook_client_id
OUTLOOK_CLIENT_SECRET=your_outlook_client_secret
OUTLOOK_REDIRECT_URI=http://localhost:8000/api/auth/outlook/callback
```

**Step 2: Create Outlook Service**

Create `/backend/app/services/outlook_service.py`:

```python
from app.core.config import settings

class OutlookService:
    """Service for Outlook OAuth and email fetching."""

    SCOPES = ['Mail.Read']

    @staticmethod
    def get_auth_url() -> str:
        # Implement Outlook OAuth flow
        pass
```

**Step 3: Add API Routes**

Edit `/backend/app/api/routes.py` to add Outlook endpoints.

### Adding IMAP Support

**Step 1: Add to `.env`**

```bash
EMAIL_PROVIDER=imap

# IMAP Configuration
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
IMAP_USERNAME=your_email@example.com
IMAP_PASSWORD=your_app_password
IMAP_USE_SSL=true
```

**Step 2: Create IMAP Service**

Create `/backend/app/services/imap_service.py`:

```python
import imaplib
from app.core.config import settings

class IMAPService:
    """Service for IMAP email fetching."""

    @staticmethod
    def fetch_emails():
        mail = imaplib.IMAP4_SSL(settings.IMAP_SERVER, settings.IMAP_PORT)
        mail.login(settings.IMAP_USERNAME, settings.IMAP_PASSWORD)
        # Implement email fetching
```

---

## 🐳 Docker Configuration

### Option 1: Using `.env` File (Recommended)

Docker Compose automatically reads from `.env`:

```yaml
# docker-compose.yml
services:
  backend:
    environment:
      DATABASE_URL: ${DATABASE_URL}
      GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID}
      # ... other variables
```

### Option 2: Environment File

Create `/backend/.env.docker`:

```bash
DATABASE_URL=postgresql://postgres:password@postgres:5432/email2kg
GOOGLE_CLIENT_ID=your_client_id
```

Update `docker-compose.yml`:

```yaml
services:
  backend:
    env_file:
      - ./backend/.env.docker
```

### Option 3: Direct in Docker Compose

```yaml
services:
  backend:
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/email2kg
      - GOOGLE_CLIENT_ID=your_client_id
```

---

## 🌐 Frontend Environment Variables

### Location: `/frontend/.env`

```bash
# API Base URL
REACT_APP_API_URL=http://localhost:8000/api

# Optional: Feature Flags
REACT_APP_ENABLE_ANALYTICS=false
```

**Important**: Frontend variables MUST start with `REACT_APP_`

**Usage in React:**

```typescript
// frontend/src/services/api.ts
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
```

---

## 🔒 Security Best Practices

### 1. Never Commit `.env` Files

Already in `.gitignore`:
```
.env
.env.local
```

### 2. Use Strong Secret Keys

```bash
# Generate secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Different Configs for Different Environments

```bash
# Development
.env

# Production
.env.production

# Testing
.env.test
```

---

## 📋 Common Configuration Patterns

### Database URLs

```bash
# PostgreSQL
DATABASE_URL=postgresql://user:password@host:port/database

# With Docker
DATABASE_URL=postgresql://postgres:password@postgres:5432/email2kg

# Production (AWS RDS)
DATABASE_URL=postgresql://user:pass@your-rds.amazonaws.com:5432/email2kg
```

### API Keys

```bash
# OpenAI
OPENAI_API_KEY=sk-proj-...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# AWS
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
```

### URLs and Endpoints

```bash
# Local Development
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/callback
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Production
GOOGLE_REDIRECT_URI=https://yourdomain.com/api/auth/callback
ALLOWED_ORIGINS=https://yourdomain.com
```

---

## 🔄 Loading Environment Variables

### Backend (Python)

The backend automatically loads from `.env` when you import settings:

```python
from app.core.config import settings

# Access any setting
print(settings.DATABASE_URL)
print(settings.GOOGLE_CLIENT_ID)
```

### Frontend (React)

Create `.env` in frontend directory:

```bash
REACT_APP_API_URL=http://localhost:8000/api
```

Access in code:

```typescript
const apiUrl = process.env.REACT_APP_API_URL;
```

### Docker

Docker Compose reads from root `.env` automatically:

```bash
# Start with .env file
docker-compose up

# Or specify env file
docker-compose --env-file .env.production up
```

---

## 🧪 Testing Configuration

Create `/backend/.env.test`:

```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/email2kg_test
GOOGLE_CLIENT_ID=test_client_id
OPENAI_API_KEY=test_key
```

Run tests:

```bash
cd backend
pytest --env-file=.env.test
```

---

## 📝 Complete Example

### `.env` File
```bash
# Database
DATABASE_URL=postgresql://postgres:mypassword@localhost:5432/email2kg

# Email Provider
EMAIL_PROVIDER=gmail
GOOGLE_CLIENT_ID=123456789.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abc123
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/callback

# LLM
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-abc123

# App Settings
SECRET_KEY=super-secret-key-change-in-production
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760

# Email Sync
EMAIL_FETCH_MONTHS=3
EMAIL_SYNC_LIMIT=500

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Environment
ENVIRONMENT=development
```

### Using in Code

```python
# backend/app/services/my_service.py
from app.core.config import settings

def my_function():
    if settings.EMAIL_PROVIDER == "gmail":
        client_id = settings.GOOGLE_CLIENT_ID
        # Use Gmail
    elif settings.EMAIL_PROVIDER == "outlook":
        client_id = settings.OUTLOOK_CLIENT_ID
        # Use Outlook
```

---

## 🚀 Quick Reference

| Configuration | Location | Purpose |
|---------------|----------|---------|
| `/.env` | Root | Main config (backend) |
| `/backend/app/core/config.py` | Backend | Define available settings |
| `/frontend/.env` | Frontend | React config (must start with `REACT_APP_`) |
| `/docker-compose.yml` | Root | Docker environment |
| `/.env.example` | Root | Template/documentation |

---

## ❓ FAQ

**Q: Where do I add my Gmail credentials?**
A: Add to `/.env` file (create from `.env.example`)

**Q: How do I add a new email provider?**
A: 1) Add credentials to `.env`, 2) Update `config.py`, 3) Create service class

**Q: Can I have different configs for dev/prod?**
A: Yes! Use `.env` for dev, `.env.production` for prod

**Q: How do I use env vars in Docker?**
A: Docker Compose automatically reads from `.env` in the root directory

**Q: How to access frontend env vars?**
A: Prefix with `REACT_APP_` and access via `process.env.REACT_APP_VARNAME`

---

## 🛠️ Troubleshooting

### Environment Variable Not Loading

1. Check file name is exactly `.env` (not `.env.txt`)
2. Restart backend server
3. Check `config.py` has the variable defined
4. Verify no typos in variable names

### Docker Not Reading .env

1. Ensure `.env` is in same directory as `docker-compose.yml`
2. Restart containers: `docker-compose down && docker-compose up`
3. Check docker-compose.yml syntax

### Frontend Env Vars Not Working

1. Must start with `REACT_APP_`
2. Restart dev server: `npm start`
3. Check `.env` is in `/frontend/` directory
