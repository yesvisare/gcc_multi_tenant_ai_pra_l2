"""
Configuration management for L3 M11.2: Tenant Metadata & Registry Design

Manages environment variables and database connections for the tenant registry system.
This module uses local databases only (PostgreSQL + Redis) with no external API dependencies.
"""

import os
from typing import Optional, Dict
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://localhost:5432/tenant_registry"
)

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0"
)

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Cache configuration
CACHE_TTL_CRITICAL = int(os.getenv("CACHE_TTL_CRITICAL", "60"))  # 1 minute for critical fields
CACHE_TTL_STANDARD = int(os.getenv("CACHE_TTL_STANDARD", "300"))  # 5 minutes for standard fields
CACHE_TTL_STATIC = int(os.getenv("CACHE_TTL_STATIC", "3600"))  # 1 hour for static fields

# Service configuration
SERVICE_NAME = "tenant-registry"
SERVICE_VERSION = "1.0.0"


def get_database_config() -> Dict[str, str]:
    """
    Get database configuration.

    Returns:
        Dictionary with database connection strings
    """
    return {
        "postgresql": DATABASE_URL,
        "redis": REDIS_URL
    }


def check_database_connection() -> bool:
    """
    Check if database configuration is loaded.

    In a production deployment, this would actually test connections to PostgreSQL and Redis.
    For this demo/learning module, we simply verify that configuration is present.

    Returns:
        Boolean indicating configuration is loaded
    """
    logger.info("=" * 60)
    logger.info("Database Configuration (Demo Mode)")
    logger.info("=" * 60)
    logger.info(f"PostgreSQL: {DATABASE_URL}")
    logger.info(f"Redis: {REDIS_URL}")
    logger.info("")
    logger.info("NOTE: This module demonstrates tenant registry design patterns.")
    logger.info("      Live database connections are optional for learning purposes.")
    logger.info("      The code includes schema definitions and works without live DB.")
    logger.info("=" * 60)

    return True


def get_cache_config() -> Dict[str, int]:
    """
    Get cache TTL configuration.

    Returns:
        Dictionary with cache TTL values in seconds
    """
    return {
        "critical_fields_ttl": CACHE_TTL_CRITICAL,
        "standard_fields_ttl": CACHE_TTL_STANDARD,
        "static_fields_ttl": CACHE_TTL_STATIC
    }


def configure_logging(level: Optional[str] = None) -> None:
    """
    Configure application logging.

    Args:
        level: Optional logging level override (DEBUG/INFO/WARNING/ERROR)
    """
    log_level = level or LOG_LEVEL

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    logger.info(f"Logging configured at {log_level} level")


# PostgreSQL schema definition (for reference)
POSTGRES_SCHEMA = """
-- Tenant Registry Schema
-- This schema is provided for reference in production deployments

CREATE TABLE IF NOT EXISTS tenants (
    tenant_id VARCHAR(255) PRIMARY KEY,
    tenant_name VARCHAR(255) NOT NULL,
    tier VARCHAR(50) NOT NULL CHECK (tier IN ('platinum', 'gold', 'silver', 'bronze')),
    status VARCHAR(50) NOT NULL CHECK (status IN ('active', 'suspended', 'migrating', 'archived', 'deleted')),
    max_users INTEGER DEFAULT 10,
    max_documents INTEGER DEFAULT 1000,
    max_queries_per_day INTEGER DEFAULT 1000,
    sla_target DECIMAL(5, 4) DEFAULT 0.99,
    support_level VARCHAR(50) DEFAULT 'email-only',
    health_score INTEGER DEFAULT 100 CHECK (health_score >= 0 AND health_score <= 100),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_tenants_status ON tenants(status);
CREATE INDEX IF NOT EXISTS idx_tenants_tier ON tenants(tier);
CREATE INDEX IF NOT EXISTS idx_tenants_health ON tenants(health_score);

-- Feature flags table
CREATE TABLE IF NOT EXISTS feature_flags (
    id SERIAL PRIMARY KEY,
    feature_name VARCHAR(255) NOT NULL,
    enabled BOOLEAN DEFAULT FALSE,
    scope VARCHAR(50) NOT NULL CHECK (scope IN ('tenant', 'tier', 'global')),
    scope_id VARCHAR(255),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(feature_name, scope, scope_id)
);

-- Tier defaults table
CREATE TABLE IF NOT EXISTS tier_defaults (
    tier VARCHAR(50) PRIMARY KEY,
    max_users INTEGER DEFAULT 10,
    max_documents INTEGER DEFAULT 1000,
    max_queries_per_day INTEGER DEFAULT 1000,
    sla_target DECIMAL(5, 4) DEFAULT 0.99,
    support_level VARCHAR(50) DEFAULT 'email-only',
    config JSONB DEFAULT '{}'
);

-- Audit log table (immutable, append-only)
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),
    tenant_id VARCHAR(255),
    operation VARCHAR(100) NOT NULL,
    actor VARCHAR(255),
    previous_state JSONB,
    new_state JSONB,
    reason TEXT,
    metadata JSONB DEFAULT '{}'
);

-- Audit log index
CREATE INDEX IF NOT EXISTS idx_audit_tenant ON audit_log(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);

-- Trigger for automatic audit logging
CREATE OR REPLACE FUNCTION log_tenant_changes()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (tenant_id, operation, previous_state, new_state)
    VALUES (
        NEW.tenant_id,
        TG_OP,
        row_to_json(OLD),
        row_to_json(NEW)
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tenant_audit_trigger
AFTER INSERT OR UPDATE ON tenants
FOR EACH ROW EXECUTE FUNCTION log_tenant_changes();

-- Row-level security (RLS) for multi-tenant isolation
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;

-- Example RLS policy (customize based on your authentication system)
CREATE POLICY tenant_isolation_policy ON tenants
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE));
"""


def print_schema() -> str:
    """
    Print PostgreSQL schema definition.

    Returns:
        PostgreSQL schema SQL
    """
    return POSTGRES_SCHEMA
