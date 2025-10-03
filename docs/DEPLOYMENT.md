# Digital Spiral Deployment Guide

This guide covers deploying Digital Spiral to production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Database Setup](#database-setup)
- [Monitoring](#monitoring)
- [Security](#security)
- [Scaling](#scaling)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **CPU**: 2+ cores (4+ recommended)
- **RAM**: 4GB minimum (8GB+ recommended)
- **Storage**: 20GB minimum (SSD recommended)
- **OS**: Linux (Ubuntu 20.04+, Debian 11+, or RHEL 8+)

### Software Requirements

- Docker 20.10+
- Docker Compose 2.0+
- PostgreSQL 14+
- Redis 6+
- Python 3.10+ (for local development)

### External Services

- **Jira**: Atlassian account with API access
- **OpenAI**: API key for AI features
- **Anthropic** (optional): API key for Claude

## Environment Setup

### 1. Create Environment File

```bash
# Copy example environment file
cp .env.example .env

# Edit with your values
nano .env
```

### 2. Required Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://digital_spiral:STRONG_PASSWORD@postgres:5432/digital_spiral
POSTGRES_PASSWORD=STRONG_PASSWORD

# Redis
REDIS_URL=redis://:STRONG_PASSWORD@redis:6379/0
REDIS_PASSWORD=STRONG_PASSWORD

# Jira
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_CLIENT_ID=your-client-id
JIRA_CLIENT_SECRET=your-client-secret
JIRA_REDIRECT_URI=https://your-domain.com/auth/callback

# AI
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...  # Optional

# Security
SECRET_KEY=generate-strong-random-key-here
JWT_SECRET_KEY=generate-another-strong-key

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# API
API_HOST=0.0.0.0
API_PORT=8000
WORKERS=4

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_PASSWORD=STRONG_PASSWORD
```

### 3. Generate Secret Keys

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Docker Deployment

### Production Deployment

```bash
# 1. Clone repository
git clone https://github.com/SemanS/digital-spiral.git
cd digital-spiral

# 2. Set up environment
cp .env.example .env
# Edit .env with your values

# 3. Build and start services
docker-compose -f docker/docker-compose.prod.yml up -d

# 4. Check logs
docker-compose -f docker/docker-compose.prod.yml logs -f api

# 5. Verify deployment
curl http://localhost:8000/health
```

### Update Deployment

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose -f docker/docker-compose.prod.yml up -d --build

# Run migrations
docker-compose -f docker/docker-compose.prod.yml exec api alembic upgrade head
```

### Backup and Restore

```bash
# Backup database
docker-compose -f docker/docker-compose.prod.yml exec postgres \
  pg_dump -U digital_spiral digital_spiral > backup.sql

# Restore database
docker-compose -f docker/docker-compose.prod.yml exec -T postgres \
  psql -U digital_spiral digital_spiral < backup.sql

# Backup Redis
docker-compose -f docker/docker-compose.prod.yml exec redis \
  redis-cli --rdb /data/dump.rdb
```

## Kubernetes Deployment

### 1. Create Namespace

```bash
kubectl create namespace digital-spiral
```

### 2. Create Secrets

```bash
# Database credentials
kubectl create secret generic postgres-credentials \
  --from-literal=username=digital_spiral \
  --from-literal=password=STRONG_PASSWORD \
  -n digital-spiral

# Redis credentials
kubectl create secret generic redis-credentials \
  --from-literal=password=STRONG_PASSWORD \
  -n digital-spiral

# API keys
kubectl create secret generic api-keys \
  --from-literal=openai-key=sk-... \
  --from-literal=anthropic-key=sk-ant-... \
  --from-literal=secret-key=... \
  --from-literal=jwt-secret=... \
  -n digital-spiral

# Jira credentials
kubectl create secret generic jira-credentials \
  --from-literal=client-id=... \
  --from-literal=client-secret=... \
  -n digital-spiral
```

### 3. Deploy Services

```bash
# Apply configurations
kubectl apply -f k8s/ -n digital-spiral

# Check deployment status
kubectl get pods -n digital-spiral
kubectl get services -n digital-spiral

# Check logs
kubectl logs -f deployment/digital-spiral-api -n digital-spiral
```

### 4. Scale Deployment

```bash
# Scale API pods
kubectl scale deployment digital-spiral-api --replicas=4 -n digital-spiral

# Auto-scaling
kubectl autoscale deployment digital-spiral-api \
  --min=2 --max=10 --cpu-percent=70 \
  -n digital-spiral
```

## Database Setup

### Initial Setup

```bash
# Create database
createdb digital_spiral

# Create extensions
psql digital_spiral -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
psql digital_spiral -c "CREATE EXTENSION IF NOT EXISTS btree_gin;"

# Run migrations
alembic upgrade head
```

### Performance Tuning

```sql
-- PostgreSQL configuration (postgresql.conf)
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB
max_worker_processes = 4
max_parallel_workers_per_gather = 2
max_parallel_workers = 4
```

### Backup Strategy

```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR="/backups/digital-spiral"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
pg_dump -U digital_spiral digital_spiral | gzip > \
  "$BACKUP_DIR/db_backup_$DATE.sql.gz"

# Backup Redis
redis-cli --rdb "$BACKUP_DIR/redis_backup_$DATE.rdb"

# Keep only last 7 days
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.rdb" -mtime +7 -delete
```

## Monitoring

### Prometheus Metrics

Access Prometheus at http://localhost:9090

Key metrics to monitor:
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency
- `database_query_duration_seconds` - Database performance
- `cache_hit_rate` - Cache effectiveness
- `ai_api_calls_total` - AI API usage

### Grafana Dashboards

Access Grafana at http://localhost:3000

Pre-configured dashboards:
- API Performance
- Database Metrics
- Cache Performance
- AI Usage
- Error Rates

### Alerts

```yaml
# prometheus/alerts.yml
groups:
  - name: digital_spiral
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"
          
      - alert: SlowDatabase
        expr: database_query_duration_seconds > 1
        for: 5m
        annotations:
          summary: "Database queries are slow"
          
      - alert: LowCacheHitRate
        expr: cache_hit_rate < 0.7
        for: 10m
        annotations:
          summary: "Cache hit rate is low"
```

## Security

### SSL/TLS Configuration

```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Firewall Rules

```bash
# Allow only necessary ports
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw enable
```

### Security Headers

```python
# Already configured in FastAPI app
app.add_middleware(
    SecurityHeadersMiddleware,
    headers={
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    }
)
```

## Scaling

### Horizontal Scaling

```bash
# Docker Swarm
docker service scale digital-spiral_api=4

# Kubernetes
kubectl scale deployment digital-spiral-api --replicas=4
```

### Load Balancing

```nginx
# nginx.conf
upstream api_backend {
    least_conn;
    server api1:8000;
    server api2:8000;
    server api3:8000;
    server api4:8000;
}

server {
    location / {
        proxy_pass http://api_backend;
    }
}
```

### Database Scaling

```bash
# Read replicas
# Configure in DATABASE_URL_REPLICA environment variable

# Connection pooling
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
```

## Troubleshooting

### Common Issues

#### API not starting

```bash
# Check logs
docker-compose logs api

# Check database connection
docker-compose exec api python -c "from src.infrastructure.database import engine; print('OK')"

# Check migrations
docker-compose exec api alembic current
```

#### High memory usage

```bash
# Check container stats
docker stats

# Reduce workers
WORKERS=2 docker-compose up -d

# Increase memory limit
docker-compose up -d --memory=2g
```

#### Slow queries

```sql
-- Enable query logging
ALTER SYSTEM SET log_min_duration_statement = 1000;
SELECT pg_reload_conf();

-- Check slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Database health
docker-compose exec postgres pg_isready

# Redis health
docker-compose exec redis redis-cli ping
```

### Performance Tuning

```bash
# Increase worker processes
WORKERS=8

# Tune database connections
DATABASE_POOL_SIZE=30
DATABASE_MAX_OVERFLOW=20

# Increase Redis memory
redis-cli CONFIG SET maxmemory 2gb
```

## Support

For deployment issues:
- Check logs: `docker-compose logs -f`
- Review documentation: [docs/](../docs/)
- Open issue: [GitHub Issues](https://github.com/SemanS/digital-spiral/issues)
- Email: slavomir.seman@hotovo.com

