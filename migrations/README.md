# Database Migrations

This directory contains Alembic database migrations for Digital Spiral.

## Quick Start

### Prerequisites

1. Ensure PostgreSQL is running:
   ```bash
   docker compose -f docker/docker-compose.dev.yml up -d postgres
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

### Common Commands

#### Create a new migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Create empty migration (for data migrations or custom SQL)
alembic revision -m "Description of changes"
```

#### Apply migrations

```bash
# Upgrade to latest version
alembic upgrade head

# Upgrade to specific version
alembic upgrade <revision_id>

# Upgrade one version forward
alembic upgrade +1
```

#### Rollback migrations

```bash
# Downgrade one version
alembic downgrade -1

# Downgrade to specific version
alembic downgrade <revision_id>

# Downgrade to base (remove all migrations)
alembic downgrade base
```

#### View migration history

```bash
# Show current version
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic history --verbose
```

## Migration Best Practices

### 1. Always Review Auto-Generated Migrations

Alembic's autogenerate is helpful but not perfect. Always review generated migrations before applying them.

**Common issues to check**:
- Index names (ensure they're meaningful)
- Foreign key constraints
- Data type changes (may require data migration)
- Enum changes (PostgreSQL requires special handling)

### 2. Test Migrations Both Ways

Always test both upgrade and downgrade:

```bash
# Test upgrade
alembic upgrade head

# Test downgrade
alembic downgrade -1

# Re-apply
alembic upgrade head
```

### 3. Use Transactions

Migrations run in transactions by default. For data migrations, consider:

```python
from alembic import op
import sqlalchemy as sa

def upgrade():
    # DDL changes
    op.create_table(...)
    
    # Data migration in separate transaction
    connection = op.get_bind()
    connection.execute(sa.text("UPDATE ..."))

def downgrade():
    op.drop_table(...)
```

### 4. Handle Enum Changes Carefully

PostgreSQL enums require special handling:

```python
from alembic import op
from sqlalchemy.dialects import postgresql

def upgrade():
    # Add new enum value
    op.execute("ALTER TYPE status_enum ADD VALUE 'new_status'")
    
    # Or recreate enum (requires data migration)
    op.execute("ALTER TABLE issues ALTER COLUMN status TYPE VARCHAR(50)")
    op.execute("DROP TYPE status_enum")
    op.execute("CREATE TYPE status_enum AS ENUM ('open', 'closed', 'new_status')")
    op.execute("ALTER TABLE issues ALTER COLUMN status TYPE status_enum USING status::status_enum")
```

### 5. Add Indexes for Performance

Always add indexes for:
- Foreign keys
- Frequently queried columns
- JSONB fields (use GIN indexes)

```python
def upgrade():
    op.create_index(
        'ix_issues_project_id',
        'issues',
        ['project_id']
    )
    
    # GIN index for JSONB
    op.create_index(
        'ix_issues_raw_jsonb',
        'issues',
        ['raw_jsonb'],
        postgresql_using='gin'
    )
```

### 6. Document Complex Migrations

Add comments to explain complex logic:

```python
def upgrade():
    """
    Migrate issue status from string to enum.
    
    Steps:
    1. Add new status_enum column
    2. Migrate data from old status column
    3. Drop old column
    4. Rename new column
    """
    # Implementation...
```

## Migration Naming Convention

Use descriptive names that indicate the change:

- `create_users_table` - Creating new table
- `add_email_to_users` - Adding column
- `remove_deprecated_fields` - Removing columns
- `migrate_status_to_enum` - Data migration
- `add_indexes_for_performance` - Adding indexes

## Troubleshooting

### Migration fails with "relation already exists"

```bash
# Mark migration as applied without running it
alembic stamp head
```

### Reset database and reapply all migrations

```bash
# Drop all tables
alembic downgrade base

# Reapply all migrations
alembic upgrade head
```

### Check current database state

```bash
# Connect to database
docker compose -f docker/docker-compose.dev.yml exec postgres psql -U digital_spiral -d digital_spiral

# List tables
\dt

# Describe table
\d table_name

# List indexes
\di
```

## Environment Variables

Migrations use the `DATABASE_URL` environment variable:

```bash
# Development
DATABASE_URL=postgresql+psycopg://digital_spiral:dev_password@localhost:5433/digital_spiral

# Testing
TEST_DATABASE_URL=postgresql+psycopg://digital_spiral:dev_password@localhost:5433/digital_spiral_test

# Production (use secrets management)
DATABASE_URL=postgresql+psycopg://user:password@host:port/database
```

## CI/CD Integration

Migrations should run automatically in CI/CD:

```yaml
# Example GitHub Actions workflow
- name: Run migrations
  run: alembic upgrade head
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

## References

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

