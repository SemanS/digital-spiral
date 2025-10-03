.PHONY: help install test lint format clean docker-up docker-down migrate mcp-jira mcp-sql

# Default target
help:
	@echo "Digital Spiral - MCP & SQL Enhancement"
	@echo ""
	@echo "Available targets:"
	@echo "  install       - Install dependencies"
	@echo "  test          - Run all tests"
	@echo "  test-unit     - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-mcp      - Run MCP tests only"
	@echo "  lint          - Run linters"
	@echo "  format        - Format code"
	@echo "  clean         - Clean up generated files"
	@echo "  migrate       - Run database migrations"
	@echo "  migrate-down  - Rollback last migration"
	@echo "  docker-up     - Start all services with Docker Compose"
	@echo "  docker-down   - Stop all services"
	@echo "  mcp-jira      - Run MCP Jira server locally"
	@echo "  mcp-sql       - Run MCP SQL server locally"
	@echo "  mcp-both      - Run both MCP servers locally"

# Installation
install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

# Testing
test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v -m unit

test-integration:
	pytest tests/integration/ -v -m integration

test-mcp:
	pytest tests/ -v -m mcp

test-coverage:
	pytest tests/ --cov=src --cov-report=html --cov-report=term

# Linting and formatting
lint:
	ruff check src/ tests/
	mypy src/

format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

# Database migrations
migrate:
	alembic upgrade head

migrate-down:
	alembic downgrade -1

migrate-create:
	@read -p "Enter migration message: " msg; \
	alembic revision -m "$$msg"

# Docker Compose
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-logs-mcp-jira:
	docker-compose logs -f mcp-jira

docker-logs-mcp-sql:
	docker-compose logs -f mcp-sql

docker-rebuild:
	docker-compose up -d --build

# MCP Servers (local development)
mcp-jira:
	uvicorn src.interfaces.mcp.jira.server:app --host 0.0.0.0 --port 8055 --reload

mcp-sql:
	uvicorn src.interfaces.mcp.sql.server:app --host 0.0.0.0 --port 8056 --reload

mcp-both:
	@echo "Starting MCP Jira on port 8055..."
	@uvicorn src.interfaces.mcp.jira.server:app --host 0.0.0.0 --port 8055 --reload & \
	echo "Starting MCP SQL on port 8056..." && \
	uvicorn src.interfaces.mcp.sql.server:app --host 0.0.0.0 --port 8056 --reload

# Health checks
health-check:
	@echo "Checking MCP Jira..."
	@curl -s http://localhost:8055/health | jq .
	@echo ""
	@echo "Checking MCP SQL..."
	@curl -s http://localhost:8056/health | jq .

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/

# Development setup
dev-setup: install migrate
	@echo "Development environment ready!"
	@echo "Run 'make mcp-both' to start MCP servers"

# Quick start
quickstart: docker-up
	@echo "Waiting for services to be healthy..."
	@sleep 10
	@echo "Services are up!"
	@echo ""
	@echo "MCP Jira: http://localhost:8055"
	@echo "MCP SQL:  http://localhost:8056"
	@echo ""
	@echo "Run 'make health-check' to verify"

