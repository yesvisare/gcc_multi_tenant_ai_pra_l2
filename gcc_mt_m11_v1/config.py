"""
Configuration management for L3 M11.1: Multi-Tenant RAG Architecture

Loads environment variables and initializes external service clients.
Services detected from script Section 4:
- PINECONE: Vector database with namespace isolation
- OPENAI: Embeddings and LLM for RAG pipeline
- PostgreSQL: Metadata storage with Row-Level Security (offline mode uses in-memory)
- Redis: Distributed caching (offline mode skips caching)
"""

import os
import logging
from typing import Optional, Any, Dict
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Service detection - Multiple services from script
PINECONE_ENABLED = os.getenv("PINECONE_ENABLED", "false").lower() == "true"
OPENAI_ENABLED = os.getenv("OPENAI_ENABLED", "false").lower() == "true"
OFFLINE = os.getenv("OFFLINE", "false").lower() == "true"

# JWT configuration for tenant routing
JWT_SECRET = os.getenv("JWT_SECRET", "development-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"


def init_clients() -> Dict[str, Any]:
    """
    Initialize external service clients based on environment config.

    Returns:
        Dict containing initialized clients or None if disabled:
        - 'pinecone': Pinecone client (if PINECONE_ENABLED)
        - 'openai': OpenAI client (if OPENAI_ENABLED)
        - 'redis': Redis client (if enabled)
    """
    clients = {}

    if OFFLINE:
        logger.warning("⚠️ OFFLINE mode enabled - all external services disabled")
        return clients

    # Initialize Pinecone client
    if PINECONE_ENABLED:
        api_key = os.getenv("PINECONE_API_KEY")

        if not api_key:
            logger.warning("⚠️ PINECONE_API_KEY not found - Pinecone unavailable")
        else:
            try:
                from pinecone import Pinecone

                clients["pinecone"] = Pinecone(api_key=api_key)
                logger.info("✓ Pinecone client initialized")
            except ImportError:
                logger.error("❌ Pinecone library not installed (pip install pinecone-client)")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Pinecone: {e}")
    else:
        logger.info("ℹ️ PINECONE_ENABLED=false - Pinecone client skipped")

    # Initialize OpenAI client
    if OPENAI_ENABLED:
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            logger.warning("⚠️ OPENAI_API_KEY not found - OpenAI unavailable")
        else:
            try:
                from openai import OpenAI

                clients["openai"] = OpenAI(api_key=api_key)
                logger.info("✓ OpenAI client initialized")
            except ImportError:
                logger.error("❌ OpenAI library not installed (pip install openai)")
            except Exception as e:
                logger.error(f"❌ Failed to initialize OpenAI: {e}")
    else:
        logger.info("ℹ️ OPENAI_ENABLED=false - OpenAI client skipped")

    # Initialize Redis client (optional)
    redis_enabled = os.getenv("REDIS_ENABLED", "false").lower() == "true"
    if redis_enabled:
        try:
            import redis

            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))

            clients["redis"] = redis.Redis(
                host=redis_host,
                port=redis_port,
                decode_responses=True
            )
            logger.info("✓ Redis client initialized")
        except ImportError:
            logger.error("❌ Redis library not installed (pip install redis)")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Redis: {e}")

    return clients


# Global clients dict - initialized once at module import
CLIENTS = init_clients()


def get_pinecone_client():
    """
    Get Pinecone client.

    Returns:
        Pinecone client instance or None

    Raises:
        RuntimeError: If Pinecone not enabled or initialized
    """
    if not PINECONE_ENABLED:
        raise RuntimeError("Pinecone not enabled - set PINECONE_ENABLED=true")

    client = CLIENTS.get("pinecone")
    if client is None:
        raise RuntimeError("Pinecone client not initialized - check API key")

    return client


def get_openai_client():
    """
    Get OpenAI client.

    Returns:
        OpenAI client instance or None

    Raises:
        RuntimeError: If OpenAI not enabled or initialized
    """
    if not OPENAI_ENABLED:
        raise RuntimeError("OpenAI not enabled - set OPENAI_ENABLED=true")

    client = CLIENTS.get("openai")
    if client is None:
        raise RuntimeError("OpenAI client not initialized - check API key")

    return client


def get_redis_client():
    """
    Get Redis client.

    Returns:
        Redis client instance or None
    """
    return CLIENTS.get("redis")


def check_services_available() -> Dict[str, bool]:
    """
    Check which services are available.

    Returns:
        Dict mapping service name to availability status
    """
    return {
        "pinecone": "pinecone" in CLIENTS,
        "openai": "openai" in CLIENTS,
        "redis": "redis" in CLIENTS,
        "offline": OFFLINE
    }
