# Contributing to Email2KG

Thank you for your interest in contributing to Email2KG! We follow industry-standard practices from Meta, Google, and other top tech companies.

---

## 📋 Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Development Workflow](#development-workflow)
5. [Code Standards](#code-standards)
6. [Testing Guidelines](#testing-guidelines)
7. [Pull Request Process](#pull-request-process)
8. [Review Process](#review-process)
9. [Documentation](#documentation)
10. [Questions?](#questions)

---

## 📜 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of experience level, background, or identity.

### Our Standards

**Positive behavior includes:**
- Being respectful and empathetic
- Providing constructive feedback
- Accepting criticism gracefully
- Focusing on what's best for the project

**Unacceptable behavior includes:**
- Harassment, trolling, or insulting comments
- Personal or political attacks
- Publishing others' private information
- Any conduct inappropriate in a professional setting

### Enforcement

Report violations to team@email2kg.com. All reports will be reviewed confidentially.

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Docker & Docker Compose**
- **Git**
- **PostgreSQL 14+** (for local development without Docker)
- **Redis 7+** (for local development without Docker)

### First-Time Setup

1. **Fork the repository**
   ```bash
   # Visit https://github.com/akhanna222/email2kg and click "Fork"
   ```

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/email2kg.git
   cd email2kg
   ```

3. **Add upstream remote**
   ```bash
   git remote add upstream https://github.com/akhanna222/email2kg.git
   ```

4. **Install pre-commit hooks**
   ```bash
   pip install pre-commit
   pre-commit install
   ```

---

## 💻 Development Setup

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Set up environment
cp ../.env.example ../.env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

### Docker Setup

```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## 🔄 Development Workflow

### 1. Create a Feature Branch

```bash
# Update your main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b bugfix/issue-description

# Or for hotfixes
git checkout -b hotfix/critical-fix
```

**Branch naming convention:**
- `feature/` - New features
- `bugfix/` - Bug fixes
- `hotfix/` - Critical production fixes
- `refactor/` - Code refactoring
- `docs/` - Documentation updates
- `test/` - Test additions/improvements

### 2. Make Your Changes

Follow our [Code Standards](#code-standards) and write tests for new functionality.

### 3. Run Quality Checks

```bash
# Backend checks
cd backend
black .
isort .
ruff check . --fix
mypy app/
pytest

# Frontend checks
cd frontend
npm run lint
npm run type-check
npm test
```

### 4. Commit Your Changes

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Format: <type>(<scope>): <subject>
#
# Types: feat, fix, docs, style, refactor, test, chore
# Scope: api, ui, db, auth, ocr, etc.

git add .
git commit -m "feat(ocr): add template matching cache

Implement in-memory cache for document templates to reduce
OpenAI API costs by 90% for recurring document types.

- Add Redis-based template cache
- Implement template fingerprinting algorithm
- Add cache hit rate metrics

Closes #123"
```

**Commit message guidelines:**
- Use present tense ("add feature" not "added feature")
- Capitalize first letter of subject
- No period at end of subject
- Body explains what and why (not how)
- Reference issues/PRs

### 5. Keep Your Branch Updated

```bash
# Fetch latest changes
git fetch upstream

# Rebase on main
git rebase upstream/main

# Force push (your branch only!)
git push origin feature/your-feature-name --force
```

### 6. Create Pull Request

See [Pull Request Process](#pull-request-process) below.

---

## 💎 Code Standards

### Python (Backend)

#### Style Guide

We follow [PEP 8](https://peps.python.org/pep-0008/) with:
- **Line length:** 100 characters
- **Indentation:** 4 spaces
- **Quotes:** Double quotes for strings
- **Imports:** Grouped and sorted with isort

#### Type Hints

Always use type hints:

```python
# ❌ Bad
def process_document(doc_id, user_id):
    return {"status": "success"}

# ✅ Good
from typing import Dict, Any

def process_document(doc_id: int, user_id: int) -> Dict[str, Any]:
    """
    Process a document for the given user.

    Args:
        doc_id: Document ID to process
        user_id: User who owns the document

    Returns:
        Dictionary with processing result

    Raises:
        DocumentNotFoundError: If document doesn't exist
        PermissionDeniedError: If user doesn't own document
    """
    return {"status": "success"}
```

#### Docstrings

Use Google-style docstrings:

```python
def complex_function(
    param1: str,
    param2: int,
    param3: Optional[List[str]] = None
) -> Tuple[bool, str]:
    """
    One-line summary of what this function does.

    More detailed explanation if needed. Can span multiple
    lines and paragraphs.

    Args:
        param1: Description of first parameter
        param2: Description of second parameter
        param3: Optional list of strings. Defaults to None.

    Returns:
        Tuple of (success, message) where:
            - success: Whether operation succeeded
            - message: Status message

    Raises:
        ValueError: If param2 is negative
        TypeError: If param1 is not a string

    Example:
        >>> result, msg = complex_function("test", 42)
        >>> print(result)
        True

    Note:
        This function has a time complexity of O(n).
    """
    pass
```

#### Error Handling

```python
# ❌ Bad: Bare except
try:
    result = process()
except:
    pass

# ❌ Bad: Generic message
try:
    result = process()
except Exception as e:
    logger.error("An error occurred")

# ✅ Good: Specific exceptions, context logging
try:
    result = process_document(doc_id)
except DocumentNotFoundError as e:
    logger.error(
        "Document not found during processing",
        extra={
            "document_id": doc_id,
            "user_id": user.id,
            "error": str(e)
        }
    )
    raise
except RateLimitExceededError as e:
    logger.warning(
        "Rate limit exceeded, queuing for retry",
        extra={
            "document_id": doc_id,
            "retry_after": e.retry_after
        }
    )
    # Queue for retry
    schedule_retry(doc_id, delay=e.retry_after)
```

### TypeScript/React (Frontend)

#### Style Guide

- **Line length:** 100 characters
- **Indentation:** 2 spaces
- **Quotes:** Single quotes for strings
- **Semicolons:** Always

#### Component Structure

```typescript
// ✅ Good: Functional component with TypeScript
import React, { useState, useEffect } from 'react';

interface DocumentCardProps {
  documentId: number;
  title: string;
  onDelete?: (id: number) => void;
}

export const DocumentCard: React.FC<DocumentCardProps> = ({
  documentId,
  title,
  onDelete
}) => {
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Effect logic
  }, [documentId]);

  const handleDelete = async () => {
    setLoading(true);
    try {
      await deleteDocument(documentId);
      onDelete?.(documentId);
    } catch (error) {
      console.error('Delete failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="document-card">
      <h3>{title}</h3>
      <button onClick={handleDelete} disabled={loading}>
        {loading ? 'Deleting...' : 'Delete'}
      </button>
    </div>
  );
};
```

---

## 🧪 Testing Guidelines

### Test Coverage Requirements

- **Unit tests:** >80% coverage
- **Integration tests:** Critical paths
- **E2E tests:** Key user workflows

### Writing Tests

#### Backend (pytest)

```python
# tests/unit/services/test_processing_service.py
import pytest
from unittest.mock import Mock, patch
from app.services.processing_service import ProcessingService

class TestProcessingService:
    """Unit tests for ProcessingService."""

    @pytest.fixture
    def service(self, db_session):
        """Create service instance."""
        return ProcessingService(db=db_session)

    @pytest.fixture
    def mock_openai(self):
        """Mock OpenAI client."""
        with patch('app.services.processing_service.openai_client') as mock:
            yield mock

    def test_process_document_success(self, service, mock_openai):
        """Test successful document processing."""
        # Arrange
        mock_openai.process_document.return_value = {
            "vendor": "Acme Corp",
            "total": 1234.56
        }

        # Act
        result = service.process_document(doc_id=1)

        # Assert
        assert result.success is True
        assert result.extracted_data["vendor"] == "Acme Corp"
        mock_openai.process_document.assert_called_once()

    def test_process_document_not_found(self, service):
        """Test processing non-existent document."""
        # Arrange & Act & Assert
        with pytest.raises(DocumentNotFoundError):
            service.process_document(doc_id=99999)
```

#### Frontend (Jest/React Testing Library)

```typescript
// src/components/__tests__/DocumentCard.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { DocumentCard } from '../DocumentCard';

describe('DocumentCard', () => {
  it('renders document title', () => {
    render(<DocumentCard documentId={1} title="Test Document" />);
    expect(screen.getByText('Test Document')).toBeInTheDocument();
  });

  it('calls onDelete when delete button clicked', async () => {
    const mockDelete = jest.fn();
    render(
      <DocumentCard
        documentId={1}
        title="Test Document"
        onDelete={mockDelete}
      />
    );

    fireEvent.click(screen.getByText('Delete'));

    await waitFor(() => {
      expect(mockDelete).toHaveBeenCalledWith(1);
    });
  });
});
```

### Running Tests

```bash
# Backend
cd backend
pytest                          # Run all tests
pytest -v                       # Verbose output
pytest --cov=app               # With coverage
pytest -m "not slow"           # Skip slow tests
pytest tests/unit              # Unit tests only

# Frontend
cd frontend
npm test                       # Run all tests
npm test -- --coverage         # With coverage
npm test -- --watch            # Watch mode
```

---

## 📝 Pull Request Process

### Before Creating PR

- [ ] Code follows style guidelines
- [ ] All tests pass locally
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] Branch is rebased on latest main
- [ ] No merge conflicts

### Creating the PR

1. **Push your branch**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create PR on GitHub**
   - Go to repository
   - Click "New Pull Request"
   - Select your branch
   - Fill in PR template

### PR Template

```markdown
## Description
Brief description of the changes and their purpose.

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to not work as expected)
- [ ] Documentation update

## How Has This Been Tested?
Describe the tests you ran to verify your changes.

- [ ] Test A
- [ ] Test B

## Checklist
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

## Screenshots (if applicable)

## Additional Notes
Any additional information that reviewers should know.
```

### PR Size Guidelines

- **Small:** < 200 lines changed (preferred)
- **Medium:** 200-500 lines
- **Large:** > 500 lines (break up if possible)

**Large PRs should be split into smaller, reviewable chunks.**

---

## 👀 Review Process

### For Authors

1. **Respond to feedback promptly** (within 24-48 hours)
2. **Address all comments** or explain why you disagree
3. **Re-request review** after making changes
4. **Don't take feedback personally** - it's about the code, not you

### For Reviewers

1. **Review within 48 hours** of request
2. **Be constructive and specific** in feedback
3. **Approve when:** Code meets standards, tests pass, no blocking issues
4. **Request changes when:** Issues must be fixed before merge
5. **Comment when:** Suggestions for improvement (non-blocking)

### Review Checklist

**Code Quality:**
- [ ] Code is readable and maintainable
- [ ] Follows project conventions
- [ ] No unnecessary complexity
- [ ] Functions are small and focused
- [ ] Variable/function names are descriptive

**Functionality:**
- [ ] Code does what PR description says
- [ ] Edge cases are handled
- [ ] Error handling is appropriate
- [ ] No obvious bugs

**Testing:**
- [ ] Tests are comprehensive
- [ ] Tests are clear and maintainable
- [ ] Coverage is adequate
- [ ] Tests actually test the right things

**Documentation:**
- [ ] Code is documented
- [ ] Complex logic explained
- [ ] README updated if needed
- [ ] API docs updated if needed

**Performance:**
- [ ] No obvious performance issues
- [ ] Database queries are optimized
- [ ] Caching is used where appropriate
- [ ] No N+1 query problems

**Security:**
- [ ] Input validation present
- [ ] No SQL injection vulnerabilities
- [ ] No XSS vulnerabilities
- [ ] Secrets not hardcoded
- [ ] Authentication/authorization correct

---

## 📚 Documentation

### What to Document

1. **Code Comments:** Explain WHY, not WHAT
2. **Docstrings:** All public functions, classes, modules
3. **README:** Setup, usage, examples
4. **Architecture Docs:** System design, data flow
5. **API Docs:** Endpoints, request/response examples

### Documentation Standards

```python
# ❌ Bad: Obvious comment
# Increment counter by 1
counter += 1

# ✅ Good: Explains reasoning
# Use atomic increment to prevent race conditions in multi-threaded context
counter += 1

# ❌ Bad: Outdated/misleading comment
# TODO: Fix this later
# Returns user data
def get_product(id):  # Actually returns product!
    return db.get_product(id)

# ✅ Good: Accurate, helpful comment
def get_product(product_id: int) -> Product:
    """
    Retrieve product by ID.

    Note: This performs a database lookup. Consider using
    get_product_cached() for frequently accessed products.
    """
    return db.get_product(product_id)
```

---

## ❓ Questions?

### Getting Help

- **GitHub Discussions:** For general questions
- **GitHub Issues:** For bug reports and feature requests
- **Email:** team@email2kg.com
- **Slack:** Join our [Slack community](#)

### Common Questions

**Q: My PR is failing CI checks. What do I do?**
A: Click on the failing check to see details. Common issues:
- Code formatting (run `black .` and `isort .`)
- Tests failing (run `pytest` locally)
- Type errors (run `mypy app/`)

**Q: How long until my PR is reviewed?**
A: We aim for initial review within 48 hours. Complex PRs may take longer.

**Q: Can I work on multiple PRs at once?**
A: Yes, but use separate branches for each PR.

**Q: My PR has merge conflicts. How do I fix them?**
A: Rebase on main: `git fetch upstream && git rebase upstream/main`

---

## 🙏 Thank You!

We appreciate your contributions to Email2KG!

**Remember:**
- Be respectful and professional
- Follow the guidelines
- Ask questions if unsure
- Have fun building awesome features!

---

**Last Updated:** December 2025
