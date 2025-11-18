"""
Configuration management for L3 M13.1: Multi-Tenant Performance Patterns

Loads environment variables and initializes Redis and PostgreSQL clients.
Services detected: REDIS (primary caching), POSTGRESQL (tenant metadata)
"""

import os
import logging
from typing import Optional, Any, Dict
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Redis Configuration
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# PostgreSQL Configuration
POSTGRES_ENABLED = os.getenv("POSTGRES_ENABLED", "false").lower() == "true"
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "tenant_metadata")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


def init_redis_client() -> Optional[Any]:
    """
    Initialize Redis client for tenant-scoped caching.

    Returns:
        Redis client instance or None if disabled

    Notes:
        - Uses redis.asyncio for async support
        - Cluster mode recommended for production (3+ nodes)
        - Falls back to single-node for development
    """
    if not REDIS_ENABLED:
        logger.warning("⚠️ REDIS disabled - caching unavailable")
        return None

    try:
        # Import here to avoid dependency if Redis not used
        import redis.asyncio as redis

        # Build connection URL
        redis_url = f"redis://"
        if REDIS_PASSWORD:
            redis_url += f":{REDIS_PASSWORD}@"
        redis_url += f"{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

        # Create async Redis client
        client = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=5.0,
            socket_connect_timeout=5.0
        )

        logger.info(f"✓ Redis client initialized: {REDIS_HOST}:{REDIS_PORT}")
        return client

    except ImportError:
        logger.error("❌ redis package not installed. Run: pip install redis[hiredis]")
        return None
    except Exception as e:
        logger.error(f"❌ Failed to initialize Redis: {e}")
        return None


def init_postgres_client() -> Optional[Any]:
    """
    Initialize PostgreSQL client for tenant metadata.

    Returns:
        PostgreSQL connection pool or None if disabled

    Schema:
        - tenants table: tenant_id, tier, cache_quota_gb, created_at
        - performance_metrics table: tenant_id, timestamp, cache_hit_rate, latency
    """
    if not POSTGRES_ENABLED:
        logger.warning("⚠️ POSTGRES disabled - tenant metadata unavailable")
        return None

    try:
        # Import here to avoid dependency if PostgreSQL not used
        import asyncpg

        # Connection pool configuration
        pool_config = {
            'host': POSTGRES_HOST,
            'port': POSTGRES_PORT,
            'database': POSTGRES_DB,
            'user': POSTGRES_USER,
            'password': POSTGRES_PASSWORD,
            'min_size': 2,
            'max_size': 10,
            'command_timeout': 60
        }

        logger.info(f"✓ PostgreSQL pool configuration ready: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
        return pool_config

    except ImportError:
        logger.error("❌ asyncpg package not installed. Run: pip install asyncpg")
        return None
    except Exception as e:
        logger.error(f"❌ Failed to configure PostgreSQL: {e}")
        return None


def get_tenant_tier(tenant_id: str) -> str:
    """
    Get performance tier for a tenant.

    Args:
        tenant_id: Tenant identifier

    Returns:
        Tier name ('platinum', 'gold', 'silver')

    Notes:
        - In production, query PostgreSQL tenants table
        - Here we return mock data for demonstration
    """
    # Mock implementation - replace with PostgreSQL query
    mock_tiers = {
        'tenant_a': 'platinum',
        'tenant_b': 'gold',
        'tenant_c': 'silver'
    }

    tier = mock_tiers.get(tenant_id, 'silver')
    logger.debug(f"Tenant {tenant_id} tier: {tier}")
    return tier


def get_tenant_quota(tenant_id: str) -> float:
    """
    Get cache quota in GB for a tenant.

    Args:
        tenant_id: Tenant identifier

    Returns:
        Cache quota in GB

    Tier defaults:
        - Platinum: 40GB
        - Gold: 20GB
        - Silver: 10GB
    """
    tier = get_tenant_tier(tenant_id)

    quota_map = {
        'platinum': 40.0,
        'gold': 20.0,
        'silver': 10.0
    }

    return quota_map.get(tier, 10.0)


# Global clients - initialized on module import
REDIS_CLIENT = None  # Will be initialized in app.py startup
POSTGRES_POOL = None  # Will be initialized in app.py startup

# Configuration summary
CONFIG_SUMMARY = {
    'redis_enabled': REDIS_ENABLED,
    'redis_host': REDIS_HOST,
    'redis_port': REDIS_PORT,
    'postgres_enabled': POSTGRES_ENABLED,
    'postgres_host': POSTGRES_HOST,
    'postgres_db': POSTGRES_DB,
    'log_level': LOG_LEVEL
}


def print_config_summary():
    """Print configuration summary for debugging."""
    print("\n=== L3 M13.1 Configuration ===")
    for key, value in CONFIG_SUMMARY.items():
        # Mask sensitive values
        if 'password' in key.lower() or 'secret' in key.lower():
            value = '***' if value else '(not set)'
        print(f"  {key}: {value}")
    print("=" * 31 + "\n")


if __name__ == "__main__":
    # Configuration test
    logging.basicConfig(level=LOG_LEVEL)
    print_config_summary()

    if REDIS_ENABLED:
        print("✓ Redis configuration ready")
    else:
        print("⚠️  Redis disabled - set REDIS_ENABLED=true in .env")

    if POSTGRES_ENABLED:
        print("✓ PostgreSQL configuration ready")
    else:
        print("⚠️  PostgreSQL disabled - set POSTGRES_ENABLED=true in .env")
