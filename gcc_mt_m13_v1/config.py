"""
Configuration management for L3 M13.1

Loads environment variables and initializes Redis client for tenant caching.
SERVICE: REDIS (caching infrastructure)
"""

import os
import logging
from typing import Optional, Any, Dict
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ============================================================================
# ENVIRONMENT CONFIGURATION
# ============================================================================

# Redis Configuration
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_SSL = os.getenv("REDIS_SSL", "false").lower() == "true"

# Offline Mode (for development/testing without Redis)
OFFLINE = os.getenv("OFFLINE", "false").lower() == "true"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# PostgreSQL (for tenant metadata - optional)
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "tenant_metadata")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")


# ============================================================================
# CLIENT INITIALIZATION
# ============================================================================

def init_redis_client() -> Optional[Any]:
    """
    Initialize async Redis client.

    Returns:
        Redis client or None if disabled/offline

    Note:
        Uses redis.asyncio for async/await support
    """
    if OFFLINE:
        logger.warning("âš ï¸ OFFLINE mode - Redis disabled")
        return None

    if not REDIS_ENABLED:
        logger.warning("âš ï¸ REDIS_ENABLED not set - Redis disabled")
        return None

    try:
        import redis.asyncio as redis

        client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            db=REDIS_DB,
            ssl=REDIS_SSL,
            decode_responses=False  # We handle decoding in TenantCache
        )

        logger.info(
            f"âœ" Redis client initialized: {REDIS_HOST}:{REDIS_PORT}, db={REDIS_DB}"
        )
        return client

    except ImportError:
        logger.error("âŒ redis.asyncio not installed - run: pip install 'redis[asyncio]'")
        return None
    except Exception as e:
        logger.error(f"âŒ Redis client initialization failed: {e}")
        return None


def init_postgres_client() -> Optional[Any]:
    """
    Initialize PostgreSQL client for tenant metadata.

    Returns:
        PostgreSQL connection pool or None if disabled

    Note:
        This is optional - only needed for tenant tier management
    """
    if OFFLINE:
        return None

    try:
        import asyncpg

        # In production, use connection pool
        # pool = await asyncpg.create_pool(
        #     host=POSTGRES_HOST,
        #     port=POSTGRES_PORT,
        #     database=POSTGRES_DB,
        #     user=POSTGRES_USER,
        #     password=POSTGRES_PASSWORD
        # )

        logger.info("PostgreSQL client ready (connection pool to be created at runtime)")
        return None  # Placeholder - actual pool created in async context

    except ImportError:
        logger.warning("asyncpg not installed - tenant metadata DB unavailable")
        return None
    except Exception as e:
        logger.error(f"PostgreSQL client initialization failed: {e}")
        return None


# ============================================================================
# GLOBAL CLIENTS
# ============================================================================

# Initialize Redis client (synchronous - lazy initialization for async context)
REDIS_CLIENT = None  # Will be initialized in app startup

# Mock tenant tier data (in production, load from PostgreSQL)
TENANT_TIERS = {
    "tenant_a": "platinum",
    "tenant_b": "gold",
    "tenant_c": "silver",
    "tenant_demo": "gold",
    "tenant_test": "silver"
}


def get_tenant_tier(tenant_id: str) -> str:
    """
    Get performance tier for tenant.

    Args:
        tenant_id: Tenant identifier

    Returns:
        Tier name (platinum, gold, silver) - defaults to silver

    Note:
        In production, this would query PostgreSQL
    """
    tier = TENANT_TIERS.get(tenant_id, "silver")
    logger.debug(f"Tenant {tenant_id} tier: {tier}")
    return tier


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

def configure_logging():
    """Configure logging based on environment"""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger.info(f"Logging configured: level={LOG_LEVEL}")


# Configure logging on import
configure_logging()
