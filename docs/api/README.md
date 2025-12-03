# Email2KG API Documentation

This document provides a comprehensive overview of the Email2KG REST API.

## 🔑 Base URL

```
Production: https://agenticrag360.com/api
Development: http://localhost:8000/api
```

## 🔐 Authentication

All API requests (except login/register) require JWT authentication.

### Headers
```http
Authorization: Bearer <your-jwt-token>
Content-Type: application/json
```

## 📋 API Endpoints

### Authentication

#### POST `/api/auth/register`
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

#### POST `/api/auth/login`
Authenticate and receive JWT tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "gmail_connected": true
  }
}
```

#### POST `/api/auth/token/refresh`
Refresh an expired access token.

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Gmail Integration

#### GET `/api/auth/google/login`
Initiate Gmail OAuth flow (redirects to Google).

**Response:** Redirects to Google OAuth consent screen

#### GET `/api/auth/google/callback`
OAuth callback endpoint (handled automatically).

**Query Parameters:**
- `code`: Authorization code from Google
- `state`: CSRF protection state

#### POST `/api/auth/google/disconnect`
Disconnect Gmail account from Email2KG.

**Response:**
```json
{
  "message": "Gmail account disconnected successfully"
}
```

### Email Sync

#### POST `/api/emails/sync`
Manually trigger email synchronization from Gmail.

**Request Body:**
```json
{
  "days": 7,
  "labels": ["INBOX", "SENT"]
}
```

**Response:**
```json
{
  "status": "syncing",
  "message": "Email sync started",
  "job_id": "abc123"
}
```

#### GET `/api/emails/sync/status`
Check email sync status.

**Response:**
```json
{
  "status": "completed",
  "emails_synced": 247,
  "last_sync": "2025-12-03T10:30:00Z"
}
```

### Knowledge Graph

#### GET `/api/graph/entities`
Retrieve extracted entities from emails.

**Query Parameters:**
- `type`: Entity type (person, organization, location, date, etc.)
- `limit`: Number of results (default: 50)
- `offset`: Pagination offset (default: 0)

**Response:**
```json
{
  "count": 150,
  "next": "/api/graph/entities?offset=50",
  "previous": null,
  "results": [
    {
      "id": "ent_123",
      "name": "John Smith",
      "type": "person",
      "confidence": 0.95,
      "mentions": 12,
      "created_at": "2025-12-01T10:00:00Z"
    }
  ]
}
```

#### GET `/api/graph/relationships`
Retrieve relationships between entities.

**Query Parameters:**
- `entity_id`: Filter by specific entity
- `relationship_type`: Type of relationship
- `limit`: Number of results (default: 50)

**Response:**
```json
{
  "count": 75,
  "results": [
    {
      "id": "rel_456",
      "source": {"id": "ent_123", "name": "John Smith"},
      "target": {"id": "ent_789", "name": "Acme Corp"},
      "type": "works_at",
      "confidence": 0.92,
      "evidence_count": 8
    }
  ]
}
```

#### POST `/api/graph/query`
Execute a custom Cypher query on the knowledge graph.

**Request Body:**
```json
{
  "query": "MATCH (p:Person)-[:WORKS_AT]->(o:Organization) RETURN p, o LIMIT 10"
}
```

**Response:**
```json
{
  "results": [
    {
      "p": {"name": "John Smith", "email": "john@example.com"},
      "o": {"name": "Acme Corp", "industry": "Technology"}
    }
  ],
  "execution_time_ms": 45
}
```

### Dashboard

#### GET `/api/dashboard/stats`
Get dashboard statistics and metrics.

**Response:**
```json
{
  "total_emails": 1247,
  "total_entities": 856,
  "total_relationships": 2341,
  "gmail_connected": true,
  "last_sync": "2025-12-03T10:30:00Z",
  "top_entities": [
    {"name": "John Smith", "type": "person", "mentions": 45},
    {"name": "Acme Corp", "type": "organization", "mentions": 38}
  ]
}
```

## 🚨 Error Responses

All errors follow this format:

```json
{
  "error": "Error type",
  "message": "Detailed error message",
  "code": "ERROR_CODE",
  "details": {}
}
```

### Common HTTP Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

## 🔒 Rate Limiting

- **Authenticated requests:** 1000 requests per hour
- **Unauthenticated requests:** 100 requests per hour

Rate limit headers:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1638360000
```

## 📡 WebSocket Endpoints

### `/ws/sync-status`
Real-time email sync status updates.

**Connection:**
```javascript
const ws = new WebSocket('wss://agenticrag360.com/ws/sync-status');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.status, data.progress);
};
```

## 🧪 Testing the API

### Using cURL

```bash
# Register
curl -X POST https://agenticrag360.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Login
curl -X POST https://agenticrag360.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Get entities (with auth token)
curl -X GET https://agenticrag360.com/api/graph/entities \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Using Python

```python
import requests

# Login
response = requests.post('https://agenticrag360.com/api/auth/login', json={
    'email': 'test@example.com',
    'password': 'test123'
})
token = response.json()['access']

# Get entities
headers = {'Authorization': f'Bearer {token}'}
entities = requests.get('https://agenticrag360.com/api/graph/entities', headers=headers)
print(entities.json())
```

## 📚 Additional Resources

- [Postman Collection](#) - Import for easy testing
- [OpenAPI/Swagger Spec](#) - Full API specification
- [GraphQL Playground](#) - Interactive GraphQL endpoint

---

**API Version:** 1.0.0
**Last Updated:** December 2025
