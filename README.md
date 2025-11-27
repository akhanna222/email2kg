# Email & Document → Knowledge Graph Platform

Convert emails and documents into a structured knowledge graph for intelligent search and analysis.

## Features (MVP1)

- **Gmail Integration**: Connect via OAuth to fetch and process emails
- **PDF Upload**: Manual document upload with automatic processing
- **Smart Extraction**: LLM-powered classification and structured data extraction
- **Knowledge Graph**: Store entities (people, companies, invoices) and relationships
- **Search & Filter**: Filter transactions by date, vendor, and type
- **Basic Q&A**: Answer predefined queries about spending and invoices

## Tech Stack

- **Backend**: FastAPI (Python 3.10+)
- **Database**: PostgreSQL
- **Frontend**: React + TypeScript
- **Processing**: PyPDF2, Tesseract OCR, OpenAI/Anthropic LLM
- **Authentication**: Google OAuth 2.0

## Project Structure

```
email2kg/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Configuration, security
│   │   ├── db/           # Database models, migrations
│   │   ├── services/     # Business logic (email, PDF, LLM)
│   │   └── main.py       # FastAPI application
│   ├── requirements.txt
│   └── alembic.ini       # Database migrations
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   └── App.tsx
│   ├── package.json
│   └── tsconfig.json
├── docker-compose.yml
├── .env.example
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Tesseract OCR

### Backend Setup

1. Create virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp ../.env.example .env
# Edit .env with your credentials
```

4. Initialize database:
```bash
alembic upgrade head
```

5. Run the backend:
```bash
uvicorn app.main:app --reload
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start development server:
```bash
npm start
```

### Using Docker (Recommended)

1. Copy environment file:
```bash
cp .env.example .env
# Edit .env with your credentials
```

2. Start all services:
```bash
docker-compose up -d
```

## Configuration

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `http://localhost:8000/auth/callback`
6. Download credentials and add to `.env`:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`

### LLM API Setup

Add your LLM API key to `.env`:
- For OpenAI: `OPENAI_API_KEY`
- For Anthropic: `ANTHROPIC_API_KEY`

## Usage

1. **Connect Gmail**: Click "Connect Gmail" and authorize access
2. **Upload PDF**: Use the upload box to add documents
3. **View Transactions**: Browse extracted transactions in the dashboard
4. **Filter & Search**: Use date, vendor, and type filters
5. **Ask Questions**: Use predefined queries for spending analysis

## API Endpoints

- `POST /auth/google` - Initiate Gmail OAuth
- `POST /upload/pdf` - Upload PDF document
- `GET /sync/gmail` - Sync emails from Gmail
- `GET /transactions` - List transactions with filters
- `GET /documents/{id}` - Get document details
- `POST /query` - Answer predefined questions

## Development

### Running Tests
```bash
cd backend
pytest
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## Deployment

### Single Instance Deployment (EC2/Render/Railway)

1. Set environment variables in your platform
2. Use `docker-compose.yml` for easy deployment
3. Ensure PostgreSQL database is accessible
4. Set `ALLOWED_ORIGINS` for CORS

## Limitations (MVP1)

- Single user only (no multi-tenancy)
- Only Gmail and PDF upload supported
- Fixed query types (no general NLP)
- Simple entity resolution (name normalization only)
- Local/S3 storage only

## Future Enhancements

- Multi-user support
- Additional email providers (Outlook, IMAP)
- More document types (Word, Excel, images)
- Full graph database (Neo4j)
- Advanced entity resolution
- General natural language queries
- Mobile app

## License

MIT

## Support

For issues and questions, please create an issue in the GitHub repository.
