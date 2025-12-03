# Email2KG Architecture

## Overview

Email2KG is a platform that converts emails and documents into a structured knowledge graph, enabling intelligent search and analysis.

## System Architecture

```
┌─────────────────┐
│   React UI      │
│  (Frontend)     │
└────────┬────────┘
         │
         │ HTTP/REST
         │
┌────────▼────────┐
│   FastAPI       │
│   (Backend)     │
└────────┬────────┘
         │
    ┌────┴────┬─────────┬──────────┐
    │         │         │          │
┌───▼───┐ ┌──▼──┐  ┌───▼────┐ ┌──▼───┐
│Gmail  │ │ LLM │  │  PDF   │ │ Postgres│
│OAuth  │ │ API │  │Extract │ │   DB   │
└───────┘ └─────┘  └────────┘ └────────┘
```

## Components

### Frontend (React + TypeScript)

**Location:** `/frontend/src/`

**Components:**
- `Dashboard.tsx` - Statistics overview
- `TransactionList.tsx` - Filterable transaction table
- `DocumentViewer.tsx` - Document details and extracted data
- `Upload.tsx` - PDF upload interface
- `Query.tsx` - Predefined query interface
- `GmailConnect.tsx` - Gmail OAuth connection

**Services:**
- `api.ts` - API client using Axios

### Backend (FastAPI + Python)

**Location:** `/backend/app/`

**Structure:**
```
app/
├── api/
│   └── routes.py          # API endpoints
├── core/
│   ├── config.py          # Configuration
│   └── security.py        # JWT tokens
├── db/
│   ├── database.py        # SQLAlchemy setup
│   └── models.py          # Database models
├── services/
│   ├── gmail_service.py   # Gmail OAuth & fetching
│   ├── pdf_service.py     # PDF text extraction
│   ├── llm_service.py     # LLM classification/extraction
│   ├── processing_service.py  # Document processing pipeline
│   └── query_service.py   # Query answering
└── main.py                # FastAPI app
```

### Database Schema (PostgreSQL)

**Tables:**

1. **emails**
   - id, gmail_id, subject, sender, receiver, timestamp, body_text

2. **documents**
   - id, filename, file_path, file_size, processing_status, document_type
   - extracted_text, extracted_data (JSON)

3. **parties** (Vendors, Companies, People)
   - id, name, normalized_name, party_type, metadata (JSON)

4. **transactions**
   - id, document_id (FK), party_id (FK)
   - amount, currency, transaction_date, transaction_type
   - metadata (JSON)

5. **email_document_links**
   - id, email_id (FK), document_id (FK)

6. **users**
   - id, email, google_id, gmail_access_token, gmail_refresh_token

**Relationships:**
- Email ↔ Document (many-to-many via email_document_links)
- Document → Transaction (one-to-many)
- Party → Transaction (one-to-many)

## Data Flow

### PDF Upload Flow

1. User uploads PDF via frontend
2. Backend saves file and creates `Document` record
3. Processing service:
   - Extracts text (PyPDF2 → OCR fallback)
   - Classifies document type (LLM)
   - Extracts structured data (LLM)
   - Creates/finds Party entity
   - Creates Transaction record
4. Updates document status to "completed"

### Gmail Sync Flow

1. User initiates OAuth flow
2. Backend exchanges code for tokens
3. Stores tokens in database
4. On sync request:
   - Fetches last 3 months of emails
   - Saves email records
   - Downloads PDF attachments
   - Processes attachments same as uploaded PDFs

### Query Flow

1. User selects predefined query type and params
2. Frontend sends query request
3. Backend QueryService:
   - Runs SQL aggregation query
   - Formats results
4. Frontend displays formatted results

## Processing Pipeline

```
Document Upload
      │
      ▼
Text Extraction (PyPDF2/OCR)
      │
      ▼
Classification (LLM)
      │
      ├─► Other → Skip
      │
      ▼
Structured Extraction (LLM)
      │
      ▼
Entity Resolution (Party)
      │
      ▼
Transaction Creation
      │
      ▼
Knowledge Graph Update
```

## LLM Integration

**Providers Supported:**
- OpenAI (GPT-4)
- Anthropic (Claude)

**Tasks:**
1. **Classification:** Categorize document (invoice, receipt, bank statement, other)
2. **Extraction:** Extract structured fields (amount, date, vendor, etc.)

**Prompts:**
- Classification: Simple category selection
- Extraction: JSON schema with specific fields

## Entity Resolution

**Current Implementation (MVP):**
- Normalize party names (lowercase, remove punctuation)
- Match by normalized name

**Future Enhancements:**
- Fuzzy matching
- LLM-based entity resolution
- Cross-reference multiple attributes

## API Endpoints

### Authentication
- `GET /api/auth/google` - Get OAuth URL
- `POST /api/auth/callback` - Handle OAuth callback

### Email Sync
- `POST /api/sync/gmail` - Sync Gmail emails

### Documents
- `POST /api/upload/pdf` - Upload PDF
- `GET /api/documents/{id}` - Get document details

### Transactions
- `GET /api/transactions` - List with filters

### Query
- `POST /api/query` - Run predefined query
- `GET /api/filters` - Get filter options

### Stats
- `GET /api/stats` - Overall statistics

## Security

- OAuth 2.0 for Gmail authentication
- JWT tokens for session management
- CORS configuration for frontend
- Input validation with Pydantic
- File size limits on uploads

## Deployment

**Development:**
- Docker Compose for all services
- Hot reload for backend and frontend

**Production Considerations:**
- Use environment variables for secrets
- PostgreSQL with persistent volumes
- S3 for file storage (optional)
- HTTPS for all endpoints
- Rate limiting on API
- Background job queue for processing

## Scalability

**Current Limitations (MVP):**
- Single user only
- Synchronous document processing
- Local file storage

**Scalability Improvements:**
- Multi-tenancy support
- Celery for background jobs
- Redis for job queue
- S3/GCS for file storage
- Horizontal scaling with load balancer
- Database read replicas

## Technology Stack

**Frontend:**
- React 18
- TypeScript
- Axios
- React Router
- date-fns

**Backend:**
- FastAPI
- SQLAlchemy
- Alembic (migrations)
- Pydantic

**Processing:**
- PyPDF2 (text extraction)
- Tesseract OCR (scanned PDFs)
- OpenAI / Anthropic (LLM)

**Database:**
- PostgreSQL 14+

**Infrastructure:**
- Docker & Docker Compose
- Nginx (production)

## Development Workflow

1. Clone repository
2. Copy `.env.example` to `.env`
3. Configure API keys and credentials
4. Run `docker-compose up`
5. Backend: http://localhost:8000
6. Frontend: http://localhost:3000
7. Make changes (hot reload enabled)
8. Run tests: `pytest` (backend), `npm test` (frontend)

## Testing

**Backend Tests:**
- Unit tests for services
- Integration tests for API endpoints
- Mock LLM responses for testing

**Frontend Tests:**
- Component tests with React Testing Library
- API mocking with MSW

## Future Enhancements

1. **Advanced Entity Resolution**
   - Fuzzy matching
   - LLM-based deduplication

2. **More Data Sources**
   - Outlook/IMAP
   - Dropbox, Google Drive
   - Scanned images (JPG, PNG)

3. **Advanced Queries**
   - Natural language queries
   - Custom SQL builder

4. **Graph Visualization**
   - Neo4j integration
   - Interactive graph UI

5. **Multi-user Support**
   - User authentication
   - Role-based access control
   - Data isolation

6. **Background Processing**
   - Celery task queue
   - Progress notifications
   - Bulk processing

7. **Analytics**
   - Spending trends
   - Vendor analysis
   - Anomaly detection
