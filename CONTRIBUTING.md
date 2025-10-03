# Contributing to Digital Spiral

Thank you for your interest in contributing to Digital Spiral! This document provides guidelines and instructions for contributing.

---

## 🎯 Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other community members

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Git
- Docker & Docker Compose (optional)

### Development Setup

```bash
# Clone repository
git clone https://github.com/SemanS/digital-spiral.git
cd digital-spiral

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
make install

# Set up database
make migrate

# Run tests
make test
```

---

## 📝 How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/SemanS/digital-spiral/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)
   - Screenshots if applicable

### Suggesting Features

1. Check if the feature has been suggested in [Issues](https://github.com/SemanS/digital-spiral/issues)
2. If not, create a new issue with:
   - Clear description of the feature
   - Use cases and benefits
   - Possible implementation approach
   - Any relevant examples

### Submitting Pull Requests

1. **Fork the repository**

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the code style guidelines
   - Add tests for new functionality
   - Update documentation as needed

4. **Run tests**
   ```bash
   make test
   make lint
   ```

5. **Commit your changes**
   ```bash
   git commit -m "feat: add amazing feature"
   ```
   Follow [Conventional Commits](https://www.conventionalcommits.org/)

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create Pull Request**
   - Use the PR template in [PULL_REQUEST.md](PULL_REQUEST.md)
   - Link related issues
   - Provide clear description
   - Add screenshots if applicable

---

## 💻 Development Guidelines

### Code Style

- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use meaningful variable names

### Running Linters

```bash
# Check code style
make lint

# Auto-format code
make format
```

### Writing Tests

- Write tests for all new functionality
- Aim for 80%+ code coverage
- Use pytest fixtures
- Mock external dependencies

```python
# Example test
import pytest
from src.application.services.audit_log_service import AuditLogService

@pytest.mark.asyncio
async def test_create_audit_log(db_session):
    service = AuditLogService(db_session)
    log = await service.create_log(
        tenant_id=uuid4(),
        action="create",
        resource_type="issue",
        resource_id="TEST-1",
    )
    assert log.action == "create"
```

### Documentation

- Update README.md if adding major features
- Add docstrings to all functions and classes
- Update relevant documentation files
- Include examples where helpful

```python
def create_adapter(
    source_type: SourceType,
    instance_id: UUID,
    base_url: str,
    auth_config: Dict[str, Any],
) -> SourceAdapter:
    """Create an adapter instance.

    Args:
        source_type: Source type (jira, github, etc.)
        instance_id: Instance UUID
        base_url: Base URL for the source API
        auth_config: Authentication configuration

    Returns:
        Adapter instance

    Example:
        >>> adapter = create_adapter(
        ...     source_type=SourceType.JIRA,
        ...     instance_id=uuid4(),
        ...     base_url="https://company.atlassian.net",
        ...     auth_config={"email": "...", "api_token": "..."},
        ... )
    """
```

---

## 🏗️ Project Structure

```
digital-spiral/
├── src/
│   ├── application/        # Business logic
│   ├── domain/            # Domain models and adapters
│   ├── infrastructure/    # External integrations
│   └── interfaces/        # API and UI
├── tests/
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── e2e/              # End-to-end tests
├── examples/             # Example scripts
├── scripts/              # Utility scripts
└── migrations/           # Database migrations
```

---

## 🧪 Testing

### Running Tests

```bash
# All tests
make test

# Unit tests only
make test-unit

# Integration tests
make test-integration

# E2E tests
make test-e2e

# With coverage
make test-coverage
```

### Test Categories

- **Unit tests** - Test individual functions/classes
- **Integration tests** - Test component interactions
- **E2E tests** - Test complete workflows

---

## 📦 Adding Dependencies

1. Add to `requirements.txt` (production) or `requirements-dev.txt` (development)
2. Run `make install`
3. Update documentation if needed
4. Commit both files

---

## 🔄 Git Workflow

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new feature
fix: fix bug
docs: update documentation
test: add tests
refactor: refactor code
chore: update dependencies
```

### Branch Naming

```
feature/feature-name
bugfix/bug-description
hotfix/critical-fix
docs/documentation-update
```

---

## 🎨 Adding a New Source Adapter

1. **Create adapter file**
   ```bash
   touch src/domain/adapters/newsource_adapter.py
   ```

2. **Implement SourceAdapter interface**
   ```python
   from .base import SourceAdapter
   
   class NewSourceAdapter(SourceAdapter):
       async def test_connection(self) -> bool:
           # Implementation
           pass
       
       # Implement all abstract methods
   ```

3. **Register adapter**
   ```python
   # In factory.py
   from .newsource_adapter import NewSourceAdapter
   
   _adapters = {
       SourceType.NEWSOURCE: NewSourceAdapter,
   }
   ```

4. **Add tests**
   ```bash
   touch tests/unit/adapters/test_newsource_adapter.py
   ```

5. **Update documentation**
   - Add to `src/domain/adapters/README.md`
   - Update main README.md

---

## 📚 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://pydantic.dev/)
- [pytest Documentation](https://docs.pytest.org/)

---

## ❓ Questions?

- Open an issue for questions
- Check existing documentation
- Email: slavomir.seman@hotovo.com

---

## 🙏 Thank You!

Your contributions make Digital Spiral better for everyone!

---

**Last Updated:** 2025-10-03

