# Digital Spiral 🌀

**AI-Powered Jira Analytics Platform**

Digital Spiral is a production-ready platform that integrates with Jira to provide advanced analytics, AI-powered insights, and intelligent automation for project management.

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-135%20passing-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-90%25+-brightgreen.svg)](tests/)

## 🚀 Features

### Core Features
- ✅ **Jira Integration** - Full REST API integration with OAuth 2.0
- ✅ **Real-time Sync** - Webhooks and incremental sync
- ✅ **Multi-tenant** - Row-level security and tenant isolation
- ✅ **High Performance** - Redis caching, materialized views, 80+ indexes
- ✅ **REST API** - 20 endpoints with OpenAPI documentation

### AI-Powered Features
- 🤖 **Issue Classification** - Automatic type, priority, and label suggestions
- 💭 **Sentiment Analysis** - Track sentiment in issues and comments
- 🔍 **Semantic Search** - Natural language search with vector embeddings
- 💡 **AI Insights** - Automated recommendations and next steps
- 📊 **Pattern Detection** - Identify trends and recurring issues
- 📝 **Auto-generated Release Notes** - AI-powered documentation

### Technical Features
- 🏗️ **Clean Architecture** - Domain-driven design with SOLID principles
- 🔒 **Security** - OAuth 2.0, RLS, webhook signature verification
- 📈 **Observability** - Prometheus metrics, OpenTelemetry tracing, structured logging
- 🧪 **Well Tested** - 135 unit tests with 90%+ coverage
- 📚 **Documentation** - OpenAPI/Swagger, technical docs

## ⚡ Quick Start

```bash
# Clone repository
git clone https://github.com/SemanS/digital-spiral.git
cd digital-spiral

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your-openai-key"
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/digital_spiral"

# Run database migrations
alembic upgrade head

# Start application
python src/interfaces/rest/main.py
```

Visit http://localhost:8000/docs for API documentation.

## 📖 API Documentation

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Key Endpoints

#### Issues
- `GET /issues/{issue_id}` - Get issue by ID
- `GET /issues/key/{issue_key}` - Get issue by key
- `GET /issues` - Search issues
- `POST /issues/sync` - Sync issue from Jira

#### Sync
- `POST /sync/full/{instance_id}` - Full sync
- `POST /sync/incremental` - Incremental sync
- `GET /sync/status/{instance_id}` - Sync status

#### AI
- `POST /ai/classify` - Classify issue
- `POST /ai/sentiment` - Analyze sentiment
- `POST /ai/insights` - Generate insights
- `POST /ai/embed` - Generate embeddings

## 🤖 AI Features

### Issue Classification

```bash
curl -X POST http://localhost:8000/ai/classify \
  -H "Content-Type: application/json" \
  -d '{
    "summary": "Login page crashes on mobile",
    "description": "Users report app crashes when trying to login on iOS"
  }'
```

### Sentiment Analysis

```bash
curl -X POST http://localhost:8000/ai/sentiment \
  -H "Content-Type: application/json" \
  -d '{"text": "This feature is amazing! Works perfectly."}'
```

### AI Insights

```bash
curl -X POST http://localhost:8000/ai/insights \
  -H "Content-Type: application/json" \
  -d '{
    "issue_summary": "API performance degradation",
    "issue_description": "Response times increased from 100ms to 2s"
  }'
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│           Interfaces Layer              │
│  (REST API, GraphQL, CLI, WebSockets)   │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Application Layer               │
│  (Use Cases, DTOs, Services, Validation)│
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│           Domain Layer                  │
│    (Entities, Value Objects, Events)    │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│        Infrastructure Layer             │
│ (Database, Cache, Jira, AI, Observability)│
└─────────────────────────────────────────┘
```

### Technology Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL 14+ with asyncpg
- **Cache**: Redis 6+
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **AI**: OpenAI GPT-4, Anthropic Claude
- **Observability**: Prometheus, OpenTelemetry
- **Testing**: pytest, pytest-asyncio

## 💻 Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/application/test_validators.py
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## 🚀 Deployment

```bash
# Build Docker image
docker build -t digital-spiral:latest .

# Run with docker-compose
docker-compose -f docker/docker-compose.prod.yml up -d

# Or use production server
uvicorn src.interfaces.rest.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4
```

## 📊 Project Statistics

- **Lines of Code**: 18,000+
- **Files**: 165+
- **Tests**: 135 passing
- **Coverage**: 90%+
- **Endpoints**: 20
- **AI Features**: 15+
- **Documentation**: 2,000+ lines

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/SemanS/digital-spiral/issues)
- **Email**: slavomir.seman@hotovo.com

---

**Built with ❤️ by the Digital Spiral Team**

