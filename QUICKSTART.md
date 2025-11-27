# Quick Start Guide

Get Email2KG running in 5 minutes!

## Prerequisites

- Docker & Docker Compose
- Google Cloud Console account (for Gmail OAuth)
- OpenAI or Anthropic API key

## Step 1: Clone and Setup

```bash
cd email2kg
cp .env.example .env
```

## Step 2: Configure Environment

Edit `.env` and add your credentials:

```bash
# Required
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
OPENAI_API_KEY=your_openai_key_here  # or ANTHROPIC_API_KEY

# Generate a secure secret key
SECRET_KEY=your-super-secret-key-change-this
```

### Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project or select existing
3. Enable **Gmail API**
4. Create OAuth 2.0 credentials:
   - Application type: Web application
   - Authorized redirect URI: `http://localhost:8000/api/auth/callback`
5. Copy Client ID and Client Secret to `.env`

## Step 3: Start Services

### Option A: Using Docker (Recommended)

```bash
./setup.sh
```

Or manually:

```bash
docker-compose up -d
```

### Option B: Manual Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up database
alembic upgrade head

# Run server
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm start
```

**PostgreSQL:**
```bash
# Make sure PostgreSQL is running on localhost:5432
createdb email2kg
```

## Step 4: Access the Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## Step 5: Try It Out!

### Connect Gmail

1. Navigate to **Gmail** tab
2. Click **Connect Gmail**
3. Authorize the application
4. Click **Sync Emails**

### Upload a PDF

1. Navigate to **Upload PDF** tab
2. Select a PDF invoice or receipt
3. Click **Upload**
4. Wait for processing to complete

### View Transactions

1. Navigate to **Transactions** tab
2. See extracted transactions
3. Use filters to search

### Ask Questions

1. Navigate to **Ask Question** tab
2. Select a query type:
   - Total spend last X months
   - Top vendors by amount
   - Invoices above $X
3. Enter parameters and click **Run Query**

## Troubleshooting

### Port already in use

```bash
# Change ports in docker-compose.yml or kill existing processes
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:3000 | xargs kill -9  # Frontend
lsof -ti:5432 | xargs kill -9  # PostgreSQL
```

### Database connection error

```bash
# Check if PostgreSQL is running
docker-compose ps

# View logs
docker-compose logs postgres
```

### LLM API errors

- Verify API key is correct in `.env`
- Check API quota/billing
- Try switching provider (OpenAI ↔ Anthropic)

### PDF processing fails

- Ensure Tesseract is installed (included in Docker)
- Check file size (max 10MB)
- Verify PDF is not password-protected

## Next Steps

- Read [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- Check [README.md](README.md) for full documentation
- Explore the API docs at http://localhost:8000/docs

## Common Commands

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Access database
docker-compose exec postgres psql -U postgres -d email2kg

# Run backend tests
cd backend && pytest

# Run frontend tests
cd frontend && npm test
```

## Demo Data

To quickly test the platform with sample data:

1. Upload sample invoices from `samples/` directory (if available)
2. Or create test PDFs with invoice-like content
3. Check the transactions and try queries

## Production Deployment

For production deployment:

1. Use production-grade PostgreSQL (AWS RDS, etc.)
2. Set `ENVIRONMENT=production` in `.env`
3. Use HTTPS for all endpoints
4. Set secure `SECRET_KEY`
5. Configure CORS for your domain
6. Use S3/GCS for file storage
7. Set up monitoring and logging

## Support

Having issues? Check:

1. Docker logs: `docker-compose logs`
2. Backend logs for processing errors
3. Browser console for frontend errors
4. Database connection in `.env`

For bug reports or questions, create an issue in the repository.
