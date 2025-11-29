# Testing and Deployment Guide

## Pre-Deployment Checklist

### ✅ Code Quality Verification

All modules have been verified:
- ✓ Backend Python modules compile without syntax errors
- ✓ Database models validated
- ✓ API routes and authentication modules verified
- ✓ Messaging providers (Gmail, Outlook, IMAP, WhatsApp, Telegram) validated
- ✓ Optimized OCR service verified
- ✓ Frontend TypeScript files structured correctly

### ✅ Dependencies

**Backend (`requirements.txt`):**
```bash
# Core Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pydantic==2.5.0
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9

# Authentication & OAuth
google-auth==2.23.4
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1
google-api-python-client==2.108.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# OCR & PDF Processing
PyPDF2==3.0.1
pdfplumber==0.10.3
pytesseract==0.3.10
pdf2image==1.16.3
Pillow==10.1.0
opencv-python==4.8.1.78
numpy==1.24.3

# Messaging Platforms
requests==2.31.0
email-validator==2.1.0

# LLM Integration
openai==1.3.7
anthropic==0.7.7

# Background Jobs
celery==5.3.4
redis==5.0.1

# Utilities
python-dotenv==1.0.0
httpx==0.25.2
aiofiles==23.2.1
```

**Frontend (`package.json`):**
- React 18
- TypeScript
- React Router
- Axios
- date-fns

### ✅ System Requirements

**For OCR:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y tesseract-ocr poppler-utils

# macOS
brew install tesseract poppler

# Windows
# Download and install:
# - Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
# - Poppler: http://blog.alivate.com.au/poppler-windows/
```

## Installation Steps

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp ../.env.example .env
# Edit .env with your actual credentials

# Create database
# PostgreSQL should be running
createdb email2kg

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build
```

### 3. Database Migration

Since we added new models, you need to:

```bash
cd backend

# Drop existing database (development only!)
dropdb email2kg
createdb email2kg

# Or run migrations
alembic revision --autogenerate -m "Add messaging and feedback models"
alembic upgrade head
```

## Testing Guide

### 1. Test Authentication

```bash
# Register a new user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "full_name": "Test User"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123"
  }'

# Save the access_token from response
```

### 2. Test Email Provider (Gmail)

```bash
# Get OAuth URL
curl http://localhost:8000/api/auth/google

# After OAuth callback, sync Gmail
curl -X POST http://localhost:8000/api/sync/gmail \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 3. Test Document Upload with Optimized OCR

```bash
# Upload a PDF
curl -X POST http://localhost:8000/api/upload/pdf \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@test_document.pdf"

# Check document processing
curl http://localhost:8000/api/documents/1 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 4. Test Messaging Providers

**WhatsApp Test:**
```python
from app.services.messaging import WhatsAppProvider

whatsapp = WhatsAppProvider({
    'phone_number_id': 'YOUR_PHONE_NUMBER_ID',
    'app_id': 'YOUR_APP_ID',
    'app_secret': 'YOUR_APP_SECRET'
})

# Send message
message_id = whatsapp.send_message(
    access_token='YOUR_ACCESS_TOKEN',
    recipient='+1234567890',
    message='Hello from Email2KG!'
)
print(f"Message sent: {message_id}")
```

**Telegram Test:**
```python
from app.services.messaging import TelegramProvider

telegram = TelegramProvider({
    'bot_token': 'YOUR_BOT_TOKEN',
    'bot_username': 'your_bot'
})

# Send message
message_id = telegram.send_message(
    access_token='',
    recipient='YOUR_CHAT_ID',
    message='Hello from Email2KG!'
)
print(f"Message sent: {message_id}")
```

### 5. Test Knowledge Graph

```bash
# Get full knowledge graph
curl http://localhost:8000/api/graph \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Get document-specific graph
curl http://localhost:8000/api/graph/document/1 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 6. Test User Feedback

```bash
# Submit feedback
curl -X POST http://localhost:8000/api/feedback/submit \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": 1,
    "feedback_type": "correction",
    "original_data": {"amount": 100.00},
    "corrected_data": {"amount": 150.00},
    "field_name": "amount",
    "comments": "Amount was extracted incorrectly"
  }'

# Get documents needing review
curl http://localhost:8000/api/feedback/documents/needs-review \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Performance Testing

### OCR Performance Test

```python
from app.services.optimized_ocr_service import OptimizedOCRService
import time

ocr = OptimizedOCRService()

# Test with preprocessing
start = time.time()
result = ocr.extract_text_from_pdf('test.pdf', use_preprocessing=True)
elapsed = time.time() - start

print(f"Processing time: {elapsed:.2f}s")
print(f"Confidence: {result['confidence']:.2%}")
print(f"Method: {result['method']}")
```

### Load Testing

```bash
# Install locust
pip install locust

# Create locustfile.py
cat > locustfile.py << 'EOF'
from locust import HttpUser, task, between

class Email2KGUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Login
        response = self.client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "testpassword123"
        })
        self.token = response.json()["access_token"]

    @task
    def get_stats(self):
        self.client.get("/api/stats", headers={
            "Authorization": f"Bearer {self.token}"
        })

    @task
    def get_transactions(self):
        self.client.get("/api/transactions", headers={
            "Authorization": f"Bearer {self.token}"
        })
EOF

# Run load test
locust -f locustfile.py --host=http://localhost:8000
```

## Production Deployment

### Docker Deployment

```bash
# Build and start services
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Environment Variables (Production)

```bash
# Generate secure keys
JWT_SECRET_KEY=$(openssl rand -hex 32)
SECRET_KEY=$(openssl rand -hex 32)

# Set in production .env
echo "JWT_SECRET_KEY=$JWT_SECRET_KEY" >> .env
echo "SECRET_KEY=$SECRET_KEY" >> .env
```

### Database Backup

```bash
# Backup
pg_dump email2kg > backup_$(date +%Y%m%d).sql

# Restore
psql email2kg < backup_20240115.sql
```

### Monitoring

**Health Check:**
```bash
curl http://localhost:8000/health
```

**API Status:**
```bash
curl http://localhost:8000/
```

## Troubleshooting

### Common Issues

**1. OCR Not Working**
```bash
# Check Tesseract installation
tesseract --version

# Check Poppler installation
pdftoppm -v
```

**2. Authentication Errors**
```bash
# Verify JWT secret is set
echo $JWT_SECRET_KEY

# Check token expiration
# Tokens expire after 7 days by default
```

**3. WhatsApp/Telegram Not Sending**
```bash
# Test API connectivity
curl https://graph.facebook.com/v18.0/me  # WhatsApp
curl https://api.telegram.org/botYOUR_TOKEN/getMe  # Telegram
```

**4. Database Connection Issues**
```bash
# Check PostgreSQL is running
pg_isready

# Test connection
psql -d email2kg -c "SELECT 1"
```

## Security Checklist

- [ ] Change all default passwords
- [ ] Generate secure JWT_SECRET_KEY
- [ ] Enable HTTPS in production
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Enable database encryption
- [ ] Rotate API keys regularly
- [ ] Set up backup strategy
- [ ] Configure firewall rules
- [ ] Enable audit logging

## Performance Optimization

### Database Indexing

```sql
-- Add indexes for common queries
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_document ON transactions(document_id);
CREATE INDEX idx_feedback_user ON user_feedback(user_id);
```

### Caching

```python
# Add Redis caching for frequently accessed data
from redis import Redis

redis_client = Redis(host='localhost', port=6379)

# Cache knowledge graph
@cache_result(ttl=300)  # 5 minutes
def get_knowledge_graph(user_id):
    return graph_service.build_knowledge_graph()
```

### Background Processing

```python
# Use Celery for heavy tasks
from celery import Celery

app = Celery('tasks', broker='redis://localhost:6379')

@app.task
def process_document_async(document_id):
    # OCR and processing in background
    pass
```

## Monitoring & Logging

### Setup Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email2kg.log'),
        logging.StreamHandler()
    ]
)
```

### Metrics to Monitor

- API response times
- OCR processing times
- Database query performance
- Memory usage
- Disk space
- Error rates
- Active users
- Message processing rates

## Scaling Strategies

### Horizontal Scaling

1. **Load Balancer**: Use Nginx/HAProxy
2. **Multiple Workers**: Run multiple Uvicorn workers
3. **Database Replicas**: Read replicas for queries
4. **Message Queue**: Use RabbitMQ/Redis for async tasks

### Vertical Scaling

1. **Increase OCR DPI selectively**
2. **More CPU cores for parallel processing**
3. **More RAM for caching**
4. **SSD for faster I/O**

## Success Metrics

System is working optimally when:

- ✓ API response time < 200ms (95th percentile)
- ✓ OCR accuracy > 90%
- ✓ OCR processing < 5s per page
- ✓ Zero authentication errors
- ✓ All messaging platforms sending successfully
- ✓ Database queries < 100ms
- ✓ No memory leaks
- ✓ 99.9% uptime

## Next Steps

After successful deployment:

1. Set up monitoring dashboards (Grafana/Prometheus)
2. Configure automated backups
3. Set up CI/CD pipeline
4. Implement A/B testing for OCR improvements
5. Add more messaging platforms
6. Implement advanced analytics
7. Add machine learning for document classification
