"""
Configuration management for L3 M12.4: Compliance Boundaries & Data Governance

Loads environment variables and initializes external service clients.

Services:
- Pinecone: Vector database for RAG system
- AWS S3: Object storage for documents
- AWS CloudFront: CDN for cached content
- Redis: Cache layer
- PostgreSQL: Primary database

All services are optional - system runs in degraded mode without credentials.
"""

import os
import logging
from typing import Optional, Any, Dict
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ===== SERVICE DETECTION from script Section 4 =====
# PRIMARY: Pinecone (vector database)
# SECONDARY: AWS (S3 + CloudFront)
# INFRASTRUCTURE: PostgreSQL, Redis (can run locally)

PINECONE_ENABLED = os.getenv("PINECONE_ENABLED", "false").lower() == "true"
AWS_ENABLED = os.getenv("AWS_ENABLED", "false").lower() == "true"
OFFLINE_MODE = os.getenv("OFFLINE", "false").lower() == "true"

# Environment variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "compliance-rag")

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "compliance-documents")
CLOUDFRONT_DISTRIBUTION_ID = os.getenv("CLOUDFRONT_DISTRIBUTION_ID")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "compliance_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def init_pinecone_client() -> Optional[Any]:
    """
    Initialize Pinecone client for vector database operations.

    Returns:
        Pinecone client instance or None if disabled/unavailable
    """
    if OFFLINE_MODE:
        logger.warning("⚠️ OFFLINE mode - skipping Pinecone client initialization")
        return None

    if not PINECONE_ENABLED:
        logger.warning("⚠️ PINECONE_ENABLED=false - skipping client initialization")
        return None

    if not PINECONE_API_KEY:
        logger.warning("⚠️ PINECONE_API_KEY not found - Pinecone unavailable")
        return None

    try:
        # Import Pinecone SDK
        import pinecone

        # Initialize Pinecone
        pinecone.init(
            api_key=PINECONE_API_KEY,
            environment=PINECONE_ENVIRONMENT,
        )

        # Get index
        if PINECONE_INDEX_NAME not in pinecone.list_indexes():
            logger.warning(f"⚠️ Pinecone index '{PINECONE_INDEX_NAME}' not found - create it first")
            return None

        index = pinecone.Index(PINECONE_INDEX_NAME)
        logger.info(f"✓ Pinecone client initialized (index={PINECONE_INDEX_NAME})")
        return index

    except ImportError:
        logger.warning("⚠️ pinecone-client not installed - run: pip install pinecone-client")
        return None
    except Exception as e:
        logger.error(f"❌ Pinecone initialization failed: {e}")
        return None


def init_s3_client() -> Optional[Any]:
    """
    Initialize AWS S3 client for object storage operations.

    Returns:
        boto3 S3 client instance or None if disabled/unavailable
    """
    if OFFLINE_MODE:
        logger.warning("⚠️ OFFLINE mode - skipping S3 client initialization")
        return None

    if not AWS_ENABLED:
        logger.warning("⚠️ AWS_ENABLED=false - skipping S3 client initialization")
        return None

    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        logger.warning("⚠️ AWS credentials not found - S3 unavailable")
        return None

    try:
        import boto3

        s3_client = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION,
        )

        logger.info(f"✓ S3 client initialized (region={AWS_REGION})")
        return s3_client

    except ImportError:
        logger.warning("⚠️ boto3 not installed - run: pip install boto3")
        return None
    except Exception as e:
        logger.error(f"❌ S3 client initialization failed: {e}")
        return None


def init_cloudfront_client() -> Optional[Any]:
    """
    Initialize AWS CloudFront client for CDN cache invalidation.

    Returns:
        boto3 CloudFront client instance or None if disabled/unavailable
    """
    if OFFLINE_MODE:
        logger.warning("⚠️ OFFLINE mode - skipping CloudFront client initialization")
        return None

    if not AWS_ENABLED:
        logger.warning("⚠️ AWS_ENABLED=false - skipping CloudFront client initialization")
        return None

    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        logger.warning("⚠️ AWS credentials not found - CloudFront unavailable")
        return None

    try:
        import boto3

        cloudfront_client = boto3.client(
            "cloudfront",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION,
        )

        logger.info(f"✓ CloudFront client initialized")
        return cloudfront_client

    except ImportError:
        logger.warning("⚠️ boto3 not installed - run: pip install boto3")
        return None
    except Exception as e:
        logger.error(f"❌ CloudFront client initialization failed: {e}")
        return None


def init_redis_client() -> Optional[Any]:
    """
    Initialize Redis client for cache operations.

    Returns:
        Redis client instance or None if unavailable
    """
    if OFFLINE_MODE:
        logger.warning("⚠️ OFFLINE mode - skipping Redis client initialization")
        return None

    try:
        import redis

        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,
        )

        # Test connection
        redis_client.ping()

        logger.info(f"✓ Redis client initialized ({REDIS_HOST}:{REDIS_PORT})")
        return redis_client

    except ImportError:
        logger.warning("⚠️ redis not installed - run: pip install redis")
        return None
    except Exception as e:
        logger.warning(f"⚠️ Redis connection failed: {e}")
        return None


def init_clients() -> Dict[str, Any]:
    """
    Initialize all external service clients.

    Returns:
        Dict containing initialized clients (or None for unavailable services)
    """
    clients = {
        "pinecone": init_pinecone_client(),
        "s3": init_s3_client(),
        "cloudfront": init_cloudfront_client(),
        "redis": init_redis_client(),
        "db_session": None,  # SQLAlchemy session (initialized in app.py)
    }

    # Log summary
    enabled_services = [k for k, v in clients.items() if v is not None]
    disabled_services = [k for k, v in clients.items() if v is None]

    if enabled_services:
        logger.info(f"✓ Enabled services: {', '.join(enabled_services)}")
    if disabled_services:
        logger.warning(f"⚠️ Disabled services: {', '.join(disabled_services)}")

    return clients


# Global clients dict (lazy initialization)
CLIENTS: Dict[str, Any] = {}


def get_clients() -> Dict[str, Any]:
    """
    Get initialized clients (lazy loading).

    Returns:
        Dict of client instances
    """
    global CLIENTS
    if not CLIENTS:
        CLIENTS = init_clients()
    return CLIENTS


def get_system_config() -> Dict[str, Any]:
    """
    Get system configuration for deletion service.

    Returns:
        Dict with S3 bucket, CloudFront distribution, etc.
    """
    return {
        "s3_bucket": S3_BUCKET_NAME,
        "cloudfront_distribution_id": CLOUDFRONT_DISTRIBUTION_ID,
        "pinecone_index": PINECONE_INDEX_NAME,
        "redis_host": REDIS_HOST,
        "redis_port": REDIS_PORT,
    }
