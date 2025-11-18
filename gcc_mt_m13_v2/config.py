"""
Configuration management for L3 M13.2

Loads environment variables and initializes Redis and Prometheus clients
for auto-scaling infrastructure management.

Service dependencies:
- REDIS: Cache for pod warm-up state and tenant metadata
- PROMETHEUS: Metrics collection for HPA custom metrics
"""

import os
import logging
from typing import Optional, Any, Dict
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Infrastructure service configuration
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"
PROMETHEUS_ENABLED = os.getenv("PROMETHEUS_ENABLED", "false").lower() == "true"

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

# Prometheus configuration
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")

# HPA configuration
MIN_REPLICAS = int(os.getenv("MIN_REPLICAS", "3"))
MAX_REPLICAS = int(os.getenv("MAX_REPLICAS", "20"))
TARGET_QUEUE_DEPTH = int(os.getenv("TARGET_QUEUE_DEPTH", "10"))


def init_redis_client() -> Optional[Any]:
    """
    Initialize Redis client for cache and warm-up state management.

    Returns:
        Redis client instance or None if disabled

    Example:
        >>> redis_client = init_redis_client()
        >>> if redis_client:
        ...     redis_client.set("pod:warming_up", "true", ex=300)
    """
    if not REDIS_ENABLED:
        logger.warning("⚠️ REDIS disabled - cache functionality unavailable")
        return None

    try:
        import redis

        client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD if REDIS_PASSWORD else None,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )

        # Test connection
        client.ping()
        logger.info(f"âœ" Redis connected: {REDIS_HOST}:{REDIS_PORT}")
        return client

    except ImportError:
        logger.error("❌ redis package not installed. Install with: pip install redis")
        return None
    except Exception as e:
        logger.error(f"❌ Failed to connect to Redis: {e}")
        return None


def init_prometheus_client() -> Optional[Any]:
    """
    Initialize Prometheus client for metrics queries.

    Returns:
        Prometheus API client or None if disabled

    Example:
        >>> prom = init_prometheus_client()
        >>> if prom:
        ...     result = prom.query('tenant_queue_depth{tenant_id="finance"}')
    """
    if not PROMETHEUS_ENABLED:
        logger.warning("⚠️ PROMETHEUS disabled - metrics queries unavailable")
        return None

    try:
        from prometheus_api_client import PrometheusConnect

        client = PrometheusConnect(
            url=PROMETHEUS_URL,
            disable_ssl=True  # For local development
        )

        # Test connection
        client.check_prometheus_connection()
        logger.info(f"âœ" Prometheus connected: {PROMETHEUS_URL}")
        return client

    except ImportError:
        logger.error("❌ prometheus-api-client package not installed. Install with: pip install prometheus-api-client")
        return None
    except Exception as e:
        logger.error(f"❌ Failed to connect to Prometheus: {e}")
        return None


def init_clients() -> Dict[str, Any]:
    """
    Initialize all infrastructure service clients.

    Returns:
        Dict containing initialized clients

    Example:
        >>> clients = init_clients()
        >>> if clients.get("redis"):
        ...     clients["redis"].set("key", "value")
    """
    clients = {}

    # Initialize Redis
    redis_client = init_redis_client()
    if redis_client:
        clients["redis"] = redis_client

    # Initialize Prometheus
    prom_client = init_prometheus_client()
    if prom_client:
        clients["prometheus"] = prom_client

    if not clients:
        logger.warning(
            "⚠️ No infrastructure services enabled. "
            "Set REDIS_ENABLED=true and/or PROMETHEUS_ENABLED=true in .env"
        )

    return clients


# Global clients dict
CLIENTS = init_clients()


def get_redis_client() -> Optional[Any]:
    """Get Redis client from global clients dict"""
    return CLIENTS.get("redis")


def get_prometheus_client() -> Optional[Any]:
    """Get Prometheus client from global clients dict"""
    return CLIENTS.get("prometheus")
