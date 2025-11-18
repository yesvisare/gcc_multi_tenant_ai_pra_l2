"""
Configuration management for L3 M13.3: Cost Optimization Strategies

Loads environment variables and manages optional infrastructure connections.

This module does NOT require external AI services (OpenAI, Anthropic, etc.).
It uses local processing with optional infrastructure components:
- Prometheus (metrics collection)
- StatsD (event recording)
- PostgreSQL (historical data storage)

All functionality works without these services (in-memory mode for development).
"""

import os
import logging
from typing import Optional, Any, Dict
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Infrastructure configuration (optional)
PROMETHEUS_ENABLED = os.getenv("PROMETHEUS_ENABLED", "false").lower() == "true"
STATSD_ENABLED = os.getenv("STATSD_ENABLED", "false").lower() == "true"
POSTGRES_ENABLED = os.getenv("POSTGRES_ENABLED", "false").lower() == "true"

# Prometheus settings
PROMETHEUS_HOST = os.getenv("PROMETHEUS_HOST", "localhost")
PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", "9090"))

# StatsD settings
STATSD_HOST = os.getenv("STATSD_HOST", "localhost")
STATSD_PORT = int(os.getenv("STATSD_PORT", "8125"))

# PostgreSQL settings
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "cost_attribution")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def init_infrastructure_clients() -> Dict[str, Any]:
    """
    Initialize optional infrastructure clients.

    Returns:
        Dict containing initialized clients (empty if all disabled)

    Note:
        All infrastructure is OPTIONAL. The module works without any external services
        using in-memory storage for development/testing.
    """
    clients = {}

    # Prometheus client (optional)
    if PROMETHEUS_ENABLED:
        try:
            # Example: from prometheus_client import CollectorRegistry, Counter
            # clients["prometheus"] = setup_prometheus()
            logger.info(f"✓ Prometheus enabled at {PROMETHEUS_HOST}:{PROMETHEUS_PORT}")
        except Exception as e:
            logger.warning(f"⚠️ Prometheus connection failed: {e}")
            logger.warning("   Continuing with in-memory metrics")

    # StatsD client (optional)
    if STATSD_ENABLED:
        try:
            # Example: from statsd import StatsClient
            # clients["statsd"] = StatsClient(STATSD_HOST, STATSD_PORT)
            logger.info(f"✓ StatsD enabled at {STATSD_HOST}:{STATSD_PORT}")
        except Exception as e:
            logger.warning(f"⚠️ StatsD connection failed: {e}")
            logger.warning("   Continuing with in-memory metrics")

    # PostgreSQL client (optional)
    if POSTGRES_ENABLED:
        try:
            # Example: import psycopg2
            # clients["postgres"] = psycopg2.connect(...)
            logger.info(f"✓ PostgreSQL enabled at {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
        except Exception as e:
            logger.warning(f"⚠️ PostgreSQL connection failed: {e}")
            logger.warning("   Continuing with in-memory storage")

    if not clients:
        logger.info("⚠️ No infrastructure services enabled - using in-memory mode")
        logger.info("   This is fine for development/testing")
        logger.info("   Set PROMETHEUS_ENABLED=true, STATSD_ENABLED=true, or POSTGRES_ENABLED=true for production")

    return clients


# Global clients dict (initialized on import)
CLIENTS = init_infrastructure_clients()


def get_config_summary() -> Dict[str, Any]:
    """
    Get configuration summary for debugging.

    Returns:
        Dict with configuration status
    """
    return {
        "infrastructure": {
            "prometheus_enabled": PROMETHEUS_ENABLED,
            "statsd_enabled": STATSD_ENABLED,
            "postgres_enabled": POSTGRES_ENABLED
        },
        "settings": {
            "log_level": LOG_LEVEL,
            "prometheus_host": PROMETHEUS_HOST if PROMETHEUS_ENABLED else None,
            "statsd_host": STATSD_HOST if STATSD_ENABLED else None,
            "postgres_host": POSTGRES_HOST if POSTGRES_ENABLED else None
        },
        "mode": "production" if any([PROMETHEUS_ENABLED, STATSD_ENABLED, POSTGRES_ENABLED]) else "development"
    }
