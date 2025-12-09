# Contributing to Email2KG

Thank you for your interest in contributing to Email2KG! This document provides guidelines and instructions for contributing to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Pull Request Process](#pull-request-process)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)

## 🤝 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all. Please be respectful and constructive in all interactions.

### Expected Behavior

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, discrimination, or offensive comments
- Trolling or insulting/derogatory comments
- Public or private harassment
- Publishing others' private information
- Other unprofessional conduct

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/email2kg.git
   cd email2kg
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/original-owner/email2kg.git
   ```
4. **Create a branch** for your contribution:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 💻 Development Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 14+
- Git

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov black flake8 mypy

# Set up pre-commit hooks (optional but recommended)
pip install pre-commit
pre-commit install
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Install development tools
npm install --save-dev eslint prettier

# Start development server
npm start
```

### Database Setup

```bash
# Create database
createdb email2kg_dev

# Run migrations
cd backend
python manage.py migrate
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

See [Configuration Guide](./docs/guides/configuration.md) for details.

## 🎯 How to Contribute

### Reporting Bugs

1. **Check existing issues** to avoid duplicates
2. **Create a new issue** with:
   - Clear, descriptive title
   - Steps to reproduce the bug
   - Expected vs actual behavior
   - Screenshots (if applicable)
   - Environment details (OS, browser, versions)

**Bug Report Template:**
```markdown
**Description:**
A clear description of the bug.

**Steps to Reproduce:**
1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior:**
What should happen.

**Actual Behavior:**
What actually happens.

**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Browser: [e.g., Chrome 120]
- Python: [e.g., 3.10.8]
- Node: [e.g., 18.16.0]
```

### Suggesting Features

1. **Check existing feature requests** to avoid duplicates
2. **Open a new issue** with:
   - Clear description of the feature
   - Use cases and benefits
   - Proposed implementation (if you have ideas)
   - Mockups or examples (if applicable)

### Contributing Code

1. **Find or create an issue** for your contribution
2. **Comment on the issue** to let others know you're working on it
3. **Fork and create a branch** (see [Getting Started](#getting-started))
4. **Write your code** following our [coding standards](#coding-standards)
5. **Test your changes** thoroughly
6. **Update documentation** if needed
7. **Submit a pull request** (see [PR Process](#pull-request-process))

## 📏 Coding Standards

### Python (Backend)

**Code Style:**
- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use [Black](https://github.com/psf/black) for formatting (line length: 100)
- Use type hints for function parameters and return types
- Write docstrings for all public functions and classes

**Example:**
```python
from typing import List, Optional

def process_document(
    document_id: int,
    user_id: int,
    options: Optional[dict] = None
) -> dict:
    """
    Process a document and extract entities.

    Args:
        document_id: ID of the document to process
        user_id: ID of the user who owns the document
        options: Optional processing options

    Returns:
        Dictionary containing extracted entities and metadata

    Raises:
        DocumentNotFound: If document_id doesn't exist
        PermissionDenied: If user doesn't own the document
    """
    # Implementation here
    pass
```

**Tools:**
```bash
# Format code
black .

# Check linting
flake8 .

# Type checking
mypy .

# Run all checks
black . && flake8 . && mypy .
```

### TypeScript/JavaScript (Frontend)

**Code Style:**
- Follow [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- Use [Prettier](https://prettier.io/) for formatting
- Use TypeScript for all new code
- Use functional components and hooks (React)

**Example:**
```typescript
interface User {
  id: number;
  email: string;
  name: string;
}

interface DashboardProps {
  userId: number;
  onLogout: () => void;
}

const Dashboard: React.FC<DashboardProps> = ({ userId, onLogout }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    fetchUser(userId)
      .then(setUser)
      .finally(() => setLoading(false));
  }, [userId]);

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="dashboard">
      <h1>Welcome, {user?.name}</h1>
      <button onClick={onLogout}>Logout</button>
    </div>
  );
};
```

**Tools:**
```bash
# Format code
npm run prettier

# Check linting
npm run lint

# Type checking
npm run type-check

# Run all checks
npm run lint && npm run type-check
```

### Git Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring (no functional change)
- `perf`: Performance improvement
- `test`: Adding or updating tests
- `chore`: Maintenance tasks (dependencies, build config)

**Examples:**
```
feat(auth): add Google OAuth integration

Implemented Google OAuth 2.0 flow for user authentication.
Added callback handling and token refresh logic.

Closes #123
```

```
fix(frontend): resolve API URL configuration issue

Frontend was using localhost instead of production domain due to
Docker build cache. Forced rebuild with --no-cache to fix.

Fixes #456
```

```
docs(deployment): update HTTPS setup guide

Added troubleshooting section for Let's Encrypt rate limits.
Clarified port 80 requirements.
```

## 🔄 Pull Request Process

### Before Submitting

1. **Update your branch** with latest upstream changes:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all tests**:
   ```bash
   # Backend
   cd backend && pytest

   # Frontend
   cd frontend && npm test
   ```

3. **Check code quality**:
   ```bash
   # Backend
   black . && flake8 . && mypy .

   # Frontend
   npm run lint && npm run type-check
   ```

4. **Update documentation** if you changed:
   - API endpoints
   - Configuration options
   - User-facing features
   - Deployment procedures

### Submitting the PR

1. **Push your branch** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create pull request** on GitHub

3. **Fill out the PR template**:
   - Description of changes
   - Related issue number(s)
   - Type of change (bug fix, feature, etc.)
   - Testing performed
   - Screenshots (if UI changes)

**PR Template:**
```markdown
## Description
Brief description of what this PR does.

## Related Issues
Closes #123
Related to #456

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manually tested in development
- [ ] Tested in production-like environment

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-reviewed my own code
- [ ] Commented complex logic
- [ ] Updated documentation
- [ ] Added tests that prove the fix/feature works
- [ ] New and existing tests pass locally
- [ ] No new warnings or errors
```

### Review Process

1. **Automated checks** must pass:
   - Tests
   - Linting
   - Type checking
   - Build

2. **Code review** by maintainers:
   - At least one approval required
   - Address all comments and suggestions
   - Re-request review after changes

3. **Merge**:
   - Maintainer will merge when approved
   - Squash and merge for feature branches
   - Keep commit history clean

## 🧪 Testing Guidelines

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run specific test
pytest tests/test_auth.py::test_login_success
```

**Writing Tests:**
```python
import pytest
from app.services.auth import AuthService

class TestAuthService:
    @pytest.fixture
    def auth_service(self):
        return AuthService()

    def test_login_success(self, auth_service):
        """Test successful login with valid credentials."""
        result = auth_service.login("user@example.com", "password123")
        assert result["success"] is True
        assert "access_token" in result

    def test_login_invalid_password(self, auth_service):
        """Test login fails with invalid password."""
        with pytest.raises(InvalidCredentials):
            auth_service.login("user@example.com", "wrongpassword")
```

### Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test Dashboard.test.tsx

# Watch mode
npm test -- --watch
```

**Writing Tests:**
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { Dashboard } from './Dashboard';

describe('Dashboard', () => {
  it('renders user name when loaded', async () => {
    render(<Dashboard userId={1} onLogout={() => {}} />);

    const userName = await screen.findByText(/Welcome, John/);
    expect(userName).toBeInTheDocument();
  });

  it('calls onLogout when logout button clicked', () => {
    const mockLogout = jest.fn();
    render(<Dashboard userId={1} onLogout={mockLogout} />);

    const logoutButton = screen.getByText('Logout');
    fireEvent.click(logoutButton);

    expect(mockLogout).toHaveBeenCalledTimes(1);
  });
});
```

### Integration Tests

Test end-to-end workflows:
```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d

# Run E2E tests
npm run test:e2e

# Cleanup
docker-compose -f docker-compose.test.yml down
```

## 📚 Documentation

### Code Documentation

- **Python**: Use docstrings (Google style)
- **TypeScript**: Use JSDoc comments
- **Document**: Public APIs, complex logic, non-obvious behavior

### User Documentation

Update docs when you change:
- **API**: Update `docs/api/README.md`
- **Configuration**: Update `docs/guides/configuration.md`
- **Deployment**: Update `docs/deployment/` guides
- **Architecture**: Update `docs/architecture/` if design changes

### Documentation Style

- Use clear, concise language
- Include code examples
- Add screenshots for UI features
- Keep it up-to-date with code changes

## 🏆 Recognition

Contributors will be:
- Listed in `CONTRIBUTORS.md`
- Mentioned in release notes
- Credited in commit messages

## 🆘 Getting Help

- **Discord**: [Join our community](#)
- **GitHub Discussions**: Ask questions
- **GitHub Issues**: Report bugs or request features
- **Email**: dev@email2kg.com

## 📝 License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

Thank you for contributing to Email2KG! 🚀

**Last Updated:** December 2025
