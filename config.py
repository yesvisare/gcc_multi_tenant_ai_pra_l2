"""
Configuration management for L3 M12.3: Query Isolation & Rate Limiting

Loads environment variables and initializes external service clients.
Services: Redis (rate limiting), PostgreSQL (tenant registry), Prometheus (metrics)
"""

import os
import logging
from typing import Optional, Any, Dict
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Service availability flags
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"
POSTGRES_ENABLED = os.getenv("POSTGRES_ENABLED", "false").lower() == "true"
PROMETHEUS_ENABLED = os.getenv("PROMETHEUS_ENABLED", "false").lower() == "true"
OFFLINE = os.getenv("OFFLINE", "true").lower() == "true"

# Configuration values
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://user:password@localhost:5432/tenants")
PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", "8001"))

# Rate limiting defaults
DEFAULT_RATE_LIMIT_PER_MINUTE = int(os.getenv("DEFAULT_RATE_LIMIT_PER_MINUTE", "100"))
NOISY_NEIGHBOR_THRESHOLD_MULTIPLIER = int(os.getenv("NOISY_NEIGHBOR_THRESHOLD_MULTIPLIER", "5"))
CIRCUIT_BREAKER_DURATION_SECONDS = int(os.getenv("CIRCUIT_BREAKER_DURATION_SECONDS", "300"))


def init_redis_client() -> Optional[Any]:
    """
    Initialize Redis client for token bucket rate limiting.

    Returns:
        Redis client or None if disabled/unavailable
    """
    if OFFLINE or not REDIS_ENABLED:
        logger.warning("⚠️ Redis disabled - using in-memory fallback")
        return None

    try:
        import redis
        client = redis.from_url(
            REDIS_URL,
            decode_responses=True,
            max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))
        )
        # Test connection
        client.ping()
        logger.info("✓ Redis client initialized")
        return client
    except ImportError:
        logger.warning("⚠️ redis-py not installed - install with: pip install redis")
        return None
    except Exception as e:
        logger.error(f"⚠️ Redis connection failed: {e}")
        return None


def init_postgres_pool() -> Optional[Any]:
    """
    Initialize PostgreSQL connection pool for tenant configuration.

    Returns:
        AsyncPG pool or None if disabled/unavailable
    """
    if OFFLINE or not POSTGRES_ENABLED:
        logger.warning("⚠️ PostgreSQL disabled - using static tenant configs")
        return None

    try:
        # Note: asyncpg pool must be created asynchronously in async context
        # This function returns None; actual pool creation happens in app startup
        logger.info("✓ PostgreSQL pool will be initialized on app startup")
        return None  # Placeholder - actual pool created in FastAPI lifespan
    except Exception as e:
        logger.error(f"⚠️ PostgreSQL setup failed: {e}")
        return None


def init_prometheus_metrics() -> Optional[Any]:
    """
    Initialize Prometheus metrics collectors.

    Returns:
        Metrics dict or None if disabled
    """
    if OFFLINE or not PROMETHEUS_ENABLED:
        logger.warning("⚠️ Prometheus disabled - metrics collection skipped")
        return None

    try:
        from prometheus_client import Counter, Histogram, Gauge

        metrics = {
            "query_total": Counter(
                "tenant_queries_total",
                "Total queries per tenant",
                ["tenant_id", "tier"]
            ),
            "query_blocked": Counter(
                "tenant_queries_blocked_total",
                "Queries blocked by rate limiter",
                ["tenant_id", "reason"]
            ),
            "query_latency": Histogram(
                "tenant_query_latency_seconds",
                "Query processing latency",
                ["tenant_id"]
            ),
            "rate_limit_active": Gauge(
                "tenant_rate_limit_active",
                "Current rate limit per tenant",
                ["tenant_id"]
            )
        }

        logger.info("✓ Prometheus metrics initialized")
        return metrics
    except ImportError:
        logger.warning("⚠️ prometheus-client not installed")
        return None
    except Exception as e:
        logger.error(f"⚠️ Prometheus setup failed: {e}")
        return None


# Initialize clients on module import
CLIENTS: Dict[str, Any] = {
    "redis": init_redis_client(),
    "postgres": init_postgres_pool(),
    "prometheus": init_prometheus_metrics()
}


# In-memory fallback for offline mode
class InMemoryRateLimiter:
    """Simple in-memory rate limiter for offline/testing mode"""

    def __init__(self):
        self.buckets: Dict[str, int] = {}
        logger.info("Using in-memory rate limiter (offline mode)")

    def check_limit(self, tenant_id: str, limit: int) -> bool:
        """Check if tenant is within rate limit"""
        import time
        minute = int(time.time() / 60)
        key = f"{tenant_id}:{minute}"

        current = self.buckets.get(key, 0)
        if current >= limit:
            return False

        self.buckets[key] = current + 1

        # Clean old keys
        self.buckets = {k: v for k, v in self.buckets.items() if int(k.split(":")[1]) >= minute - 1}
        return True


# Fallback for offline mode
if CLIENTS["redis"] is None:
    CLIENTS["in_memory_limiter"] = InMemoryRateLimiter()
