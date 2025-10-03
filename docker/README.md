# Docker Development Environment

This directory contains Docker Compose configuration for local development.

## Quick Start

1. **Copy environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Start services**:
   ```bash
   docker compose -f docker/docker-compose.dev.yml up -d
   ```

3. **Check service health**:
   ```bash
   docker compose -f docker/docker-compose.dev.yml ps
   ```

4. **View logs**:
   ```bash
   docker compose -f docker/docker-compose.dev.yml logs -f
   ```

5. **Stop services**:
   ```bash
   docker compose -f docker/docker-compose.dev.yml down
   ```

## Services

### PostgreSQL

- **Port**: 5432 (configurable via `POSTGRES_PORT`)
- **User**: `digital_spiral` (configurable via `POSTGRES_USER`)
- **Password**: `dev_password` (configurable via `POSTGRES_PASSWORD`)
- **Database**: `digital_spiral` (configurable via `POSTGRES_DB`)

**Connection String**:
```
postgresql://digital_spiral:dev_password@localhost:5432/digital_spiral
```

**Extensions Enabled**:
- `uuid-ossp` - UUID generation
- `pg_trgm` - Trigram matching for text search
- `btree_gin` - GIN indexes for JSONB
- `pg_stat_statements` - Query performance monitoring

### Redis

- **Port**: 6379 (configurable via `REDIS_PORT`)
- **Password**: `dev_password` (configurable via `REDIS_PASSWORD`)

**Connection String**:
```
redis://:dev_password@localhost:6379/0
```

### PgAdmin (Optional)

Web-based PostgreSQL management tool.

- **Port**: 5050 (configurable via `PGADMIN_PORT`)
- **Email**: `admin@digital-spiral.local`
- **Password**: `admin`
- **URL**: http://localhost:5050

**To enable**:
```bash
docker compose -f docker/docker-compose.dev.yml --profile tools up -d
```

### Redis Commander (Optional)

Web-based Redis management tool.

- **Port**: 8081 (configurable via `REDIS_COMMANDER_PORT`)
- **URL**: http://localhost:8081

**To enable**:
```bash
docker compose -f docker/docker-compose.dev.yml --profile tools up -d
```

## Database Initialization

The `init-db.sql` script runs automatically when the PostgreSQL container is first created. It:

1. Enables required extensions
2. Creates custom types (`sync_status`, `webhook_status`)
3. Enables Row Level Security (RLS)
4. Creates application user (`digital_spiral_app`)
5. Creates read-only user (`digital_spiral_readonly`)
6. Sets up default privileges
7. Creates audit trigger function

## Data Persistence

Data is persisted in Docker volumes:

- `postgres_data` - PostgreSQL data
- `redis_data` - Redis data
- `pgadmin_data` - PgAdmin configuration

**To reset all data**:
```bash
docker compose -f docker/docker-compose.dev.yml down -v
```

## Health Checks

All services have health checks configured:

- **PostgreSQL**: `pg_isready` command
- **Redis**: `redis-cli ping` command

Services will be marked as healthy when they pass their health checks.

## Networking

All services are connected via the `digital-spiral-network` bridge network, allowing them to communicate using service names (e.g., `postgres`, `redis`).

## Troubleshooting

### PostgreSQL connection refused

```bash
# Check if PostgreSQL is running
docker compose -f docker/docker-compose.dev.yml ps postgres

# Check PostgreSQL logs
docker compose -f docker/docker-compose.dev.yml logs postgres

# Restart PostgreSQL
docker compose -f docker/docker-compose.dev.yml restart postgres
```

### Redis connection refused

```bash
# Check if Redis is running
docker compose -f docker/docker-compose.dev.yml ps redis

# Check Redis logs
docker compose -f docker/docker-compose.dev.yml logs redis

# Test Redis connection
docker compose -f docker/docker-compose.dev.yml exec redis redis-cli -a dev_password ping
```

### Reset database

```bash
# Stop services and remove volumes
docker compose -f docker/docker-compose.dev.yml down -v

# Start services (will reinitialize database)
docker compose -f docker/docker-compose.dev.yml up -d
```

## Production Considerations

This configuration is for **development only**. For production:

1. Use strong passwords (not `dev_password`)
2. Enable SSL/TLS for PostgreSQL and Redis
3. Use managed database services (AWS RDS, Google Cloud SQL, etc.)
4. Configure proper backup and recovery
5. Set up monitoring and alerting
6. Use secrets management (Vault, AWS Secrets Manager, etc.)
7. Enable connection pooling (PgBouncer)
8. Configure resource limits and autoscaling

