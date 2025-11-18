"""
Configuration management for L3 M11.3: Database Isolation & Cross-Tenant Security

Loads environment variables and initializes multi-service clients for:
- PostgreSQL (RLS strategy)
- Pinecone (Namespace isolation strategy)
- Redis (Cache key prefixing)
- AWS S3 (Prefix isolation)
"""

import os
import logging
from typing import Optional, Any, Dict
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Service Configuration
POSTGRES_ENABLED = os.getenv("POSTGRES_ENABLED", "false").lower() == "true"
PINECONE_ENABLED = os.getenv("PINECONE_ENABLED", "false").lower() == "true"
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"
AWS_ENABLED = os.getenv("AWS_ENABLED", "false").lower() == "true"
OFFLINE = os.getenv("OFFLINE", "true").lower() == "true"


def init_postgres_client() -> Optional[Any]:
    """
    Initialize PostgreSQL connection pool for RLS strategy.

    Returns:
        Connection pool or None if disabled
    """
    if not POSTGRES_ENABLED:
        logger.warning("⚠️ PostgreSQL disabled - RLS strategy unavailable")
        return None

    try:
        import psycopg2
        from psycopg2 import pool

        connection_pool = pool.SimpleConnectionPool(
            1, 20,
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "multi_tenant_rag"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "")
        )
        logger.info("✓ PostgreSQL connection pool initialized")
        return connection_pool
    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL: {e}")
        return None


def init_pinecone_client() -> Optional[Any]:
    """
    Initialize Pinecone client for namespace isolation strategy.

    Returns:
        Pinecone client or None if disabled
    """
    if not PINECONE_ENABLED:
        logger.warning("⚠️ Pinecone disabled - Namespace strategy unavailable")
        return None

    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        logger.warning("⚠️ PINECONE_API_KEY not found")
        return None

    try:
        import pinecone

        pc = pinecone.Pinecone(api_key=api_key)
        logger.info("✓ Pinecone client initialized")
        return pc
    except Exception as e:
        logger.error(f"Failed to initialize Pinecone: {e}")
        return None


def init_redis_client() -> Optional[Any]:
    """
    Initialize Redis client for cache key prefixing.

    Returns:
        Redis client or None if disabled
    """
    if not REDIS_ENABLED:
        logger.warning("⚠️ Redis disabled - Cache isolation unavailable")
        return None

    try:
        import redis

        redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD", ""),
            decode_responses=True
        )
        redis_client.ping()  # Test connection
        logger.info("✓ Redis client initialized")
        return redis_client
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {e}")
        return None


def init_aws_clients() -> Dict[str, Any]:
    """
    Initialize AWS service clients (S3, etc.) for prefix isolation.

    Returns:
        Dict of AWS clients or empty dict if disabled
    """
    if not AWS_ENABLED:
        logger.warning("⚠️ AWS disabled - S3 prefix isolation unavailable")
        return {}

    try:
        import boto3

        clients = {
            "s3": boto3.client(
                "s3",
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=os.getenv("AWS_REGION", "us-east-1")
            )
        }
        logger.info("✓ AWS clients initialized")
        return clients
    except Exception as e:
        logger.error(f"Failed to initialize AWS clients: {e}")
        return {}


def init_clients() -> Dict[str, Any]:
    """
    Initialize all external service clients based on environment config.

    Returns:
        Dict containing initialized clients or None values if disabled
    """
    if OFFLINE:
        logger.warning("⚠️ OFFLINE mode - all external services disabled")
        return {
            "postgres": None,
            "pinecone": None,
            "redis": None,
            "aws": {}
        }

    clients = {
        "postgres": init_postgres_client(),
        "pinecone": init_pinecone_client(),
        "redis": init_redis_client(),
        "aws": init_aws_clients()
    }

    enabled_services = [k for k, v in clients.items() if v is not None and (not isinstance(v, dict) or v)]
    logger.info(f"Services initialized: {', '.join(enabled_services) if enabled_services else 'None (offline mode)'}")

    return clients


# Global clients dict
CLIENTS = init_clients()
