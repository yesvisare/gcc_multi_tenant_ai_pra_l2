"""
Configuration management for L3 M12.1: Vector Database Multi-Tenancy Patterns

Loads environment variables and initializes Pinecone client.
SERVICE: PINECONE (auto-detected from script Section 4)
"""

import os
import logging
from typing import Optional, Any, Dict
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# PINECONE Configuration (detected service from script)
PINECONE_ENABLED = os.getenv("PINECONE_ENABLED", "false").lower() == "true"
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp")

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def init_clients() -> Dict[str, Any]:
    """
    Initialize Pinecone client based on environment configuration.

    Returns:
        Dict containing initialized clients or empty dict if disabled

    Example:
        >>> clients = init_clients()
        >>> if "pinecone" in clients:
        >>>     index = clients["pinecone"].Index("my-index")
    """
    clients = {}

    if not PINECONE_ENABLED:
        logger.warning("⚠️ PINECONE disabled - skipping client initialization")
        logger.info("   Set PINECONE_ENABLED=true in .env to enable")
        return clients

    if not PINECONE_API_KEY:
        logger.warning("⚠️ PINECONE_API_KEY not found - client unavailable")
        logger.info("   Add PINECONE_API_KEY to .env file")
        return clients

    try:
        # Import Pinecone SDK only if enabled
        from pinecone import Pinecone

        # Initialize Pinecone client
        pc = Pinecone(api_key=PINECONE_API_KEY)
        clients["pinecone"] = pc

        logger.info("✓ Pinecone client initialized successfully")
        logger.info(f"   Environment: {PINECONE_ENVIRONMENT}")

    except ImportError:
        logger.error("❌ Pinecone SDK not installed")
        logger.info("   Install with: pip install pinecone-client")
    except Exception as e:
        logger.error(f"❌ Pinecone client initialization failed: {e}")

    return clients


def get_pinecone_client() -> Optional[Any]:
    """
    Get initialized Pinecone client or None if unavailable.

    Returns:
        Pinecone client instance or None
    """
    clients = init_clients()
    return clients.get("pinecone")


# Global clients dictionary (lazy initialization)
CLIENTS: Dict[str, Any] = {}


def ensure_clients_initialized() -> Dict[str, Any]:
    """
    Ensure clients are initialized (lazy loading).

    Returns:
        Dict of initialized clients
    """
    global CLIENTS
    if not CLIENTS:
        CLIENTS = init_clients()
    return CLIENTS


# Configuration summary
def get_config_summary() -> Dict[str, Any]:
    """
    Get configuration summary for debugging.

    Returns:
        Dict with configuration status
    """
    return {
        "pinecone_enabled": PINECONE_ENABLED,
        "pinecone_configured": bool(PINECONE_API_KEY),
        "pinecone_environment": PINECONE_ENVIRONMENT,
        "log_level": LOG_LEVEL,
        "clients_initialized": bool(CLIENTS)
    }


if __name__ == "__main__":
    # Test configuration
    print("Configuration Test")
    print("=" * 50)

    summary = get_config_summary()
    for key, value in summary.items():
        print(f"{key}: {value}")

    print("\nInitializing clients...")
    clients = init_clients()

    if clients:
        print(f"✓ {len(clients)} client(s) initialized")
    else:
        print("⚠️ No clients initialized (check .env configuration)")
