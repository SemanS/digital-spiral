#!/usr/bin/env bash
# Start Everything - Complete Digital Spiral System

set -e

echo "🚀 Starting Digital Spiral - Complete System"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_step() {
    echo -e "${BLUE}▶ ${NC}$1"
}

print_success() {
    echo -e "${GREEN}✓ ${NC}$1"
}

print_warning() {
    echo -e "${YELLOW}⚠ ${NC}$1"
}

# Step 1: Check prerequisites
print_step "Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo "Docker not found. Please install Docker."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "Python 3 not found. Please install Python 3.11+."; exit 1; }
print_success "Prerequisites OK"
echo ""

# Step 2: Start Docker services
print_step "Starting Docker services (PostgreSQL, Mock Jira)..."
docker compose up -d postgres mock-jira
print_success "Docker services started"
echo ""

# Step 3: Wait for PostgreSQL
print_step "Waiting for PostgreSQL to be ready..."
sleep 5
until docker exec ds-postgres pg_isready -U ds -d ds_orchestrator >/dev/null 2>&1; do
    echo "  Waiting for PostgreSQL..."
    sleep 2
done
print_success "PostgreSQL is ready"
echo ""

# Step 4: Run database migrations
print_step "Running database migrations..."
alembic upgrade head
print_success "Migrations complete"
echo ""

# Step 5: Seed metrics catalog
print_step "Seeding metrics catalog..."
if [ -f "scripts/seed_metrics_catalog.py" ]; then
    python scripts/seed_metrics_catalog.py
    print_success "Metrics catalog seeded"
else
    print_warning "Metrics catalog seeder not found (will be created in implementation)"
fi
echo ""

# Step 6: Refresh materialized views
print_step "Refreshing materialized views..."
if [ -f "scripts/refresh_materialized_views.py" ]; then
    python scripts/refresh_materialized_views.py
    print_success "Materialized views refreshed"
else
    print_warning "Materialized views script not found (will be created in implementation)"
fi
echo ""

# Step 7: Start Celery worker (if implemented)
print_step "Starting Celery worker..."
if [ -f "src/infrastructure/queue/celery_config.py" ]; then
    celery -A src.infrastructure.queue.celery_config worker --loglevel=info --detach
    print_success "Celery worker started"
else
    print_warning "Celery not yet implemented (Phase 4)"
fi
echo ""

# Step 8: Start FastAPI server
print_step "Starting FastAPI server..."
print_warning "Run in separate terminal: uvicorn src.interfaces.api.main:app --reload --port 8000"
echo ""

# Step 9: Start Admin UI
print_step "Starting Admin UI..."
print_warning "Run in separate terminal: cd admin-ui && npm run dev"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
print_success "System startup complete!"
echo ""
echo "📊 Services:"
echo "  - PostgreSQL: localhost:5432"
echo "  - Mock Jira: http://localhost:9000"
echo "  - FastAPI: http://localhost:8000 (start manually)"
echo "  - Admin UI: http://localhost:3000 (start manually)"
echo "  - API Docs: http://localhost:8000/docs"
echo ""
echo "🧪 Test the system:"
echo "  curl http://localhost:8000/health"
echo "  curl http://localhost:8000/analytics/metrics"
echo ""
echo "📚 Documentation:"
echo "  - AUGGIE.md - Main guide"
echo "  - QUICKSTART_FEATURE_004.md - Quick start"
echo "  - .specify/features/004-llm-sql-analytics/ - Feature docs"
echo ""
echo "🚀 Ready for testing!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
