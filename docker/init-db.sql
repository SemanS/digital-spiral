-- Digital Spiral Database Initialization Script
-- This script runs automatically when the PostgreSQL container is first created

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";      -- UUID generation
CREATE EXTENSION IF NOT EXISTS "pg_trgm";        -- Trigram matching for text search
CREATE EXTENSION IF NOT EXISTS "btree_gin";      -- GIN indexes for JSONB
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements"; -- Query performance monitoring

-- Create custom types
DO $$ BEGIN
    CREATE TYPE sync_status AS ENUM ('pending', 'in_progress', 'completed', 'failed');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE webhook_status AS ENUM ('pending', 'processing', 'completed', 'failed', 'retrying');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Enable Row Level Security (RLS) globally
ALTER DATABASE digital_spiral SET row_security = on;

-- Create application user (used by the application)
DO $$ BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'digital_spiral_app') THEN
        CREATE ROLE digital_spiral_app WITH LOGIN PASSWORD 'app_password';
    END IF;
END $$;

-- Grant necessary permissions
GRANT CONNECT ON DATABASE digital_spiral TO digital_spiral_app;
GRANT USAGE ON SCHEMA public TO digital_spiral_app;
GRANT CREATE ON SCHEMA public TO digital_spiral_app;

-- Create read-only user for analytics/reporting
DO $$ BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'digital_spiral_readonly') THEN
        CREATE ROLE digital_spiral_readonly WITH LOGIN PASSWORD 'readonly_password';
    END IF;
END $$;

GRANT CONNECT ON DATABASE digital_spiral TO digital_spiral_readonly;
GRANT USAGE ON SCHEMA public TO digital_spiral_readonly;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO digital_spiral_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO digital_spiral_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO digital_spiral_readonly;

-- Create audit trigger function for tracking changes
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Log successful initialization
DO $$ BEGIN
    RAISE NOTICE 'Digital Spiral database initialized successfully';
    RAISE NOTICE 'Extensions enabled: uuid-ossp, pg_trgm, btree_gin, pg_stat_statements';
    RAISE NOTICE 'Custom types created: sync_status, webhook_status';
    RAISE NOTICE 'Application user: digital_spiral_app';
    RAISE NOTICE 'Read-only user: digital_spiral_readonly';
END $$;

