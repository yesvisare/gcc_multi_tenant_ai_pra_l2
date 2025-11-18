"""
Configuration management for L3 M12.2: Document Storage & Access Control

Loads environment variables and initializes AWS S3 clients.
SERVICE: AWS_S3 (auto-detected from script Section 4)

Environment Variables:
- AWS_S3_ENABLED: Enable/disable S3 operations (default: false)
- AWS_ACCESS_KEY_ID: AWS access key
- AWS_SECRET_ACCESS_KEY: AWS secret key
- AWS_REGION: AWS region (default: us-east-1)
- AWS_DEFAULT_BUCKET: Default S3 bucket name
"""

import os
import logging
from typing import Optional, Any, Dict
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# AWS S3 Configuration
AWS_S3_ENABLED = os.getenv("AWS_S3_ENABLED", "false").lower() == "true"
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_DEFAULT_BUCKET = os.getenv("AWS_DEFAULT_BUCKET", "rag-docs-shared")

# Redis Configuration (for presigned URL caching)
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

# Database Configuration (for audit logging)
DATABASE_URL = os.getenv("DATABASE_URL", "")


def init_s3_client(region: Optional[str] = None):
    """
    Initialize AWS S3 client.

    Args:
        region: AWS region override

    Returns:
        boto3 S3 client or None if disabled
    """
    if not AWS_S3_ENABLED:
        logger.warning("⚠️ AWS_S3_ENABLED is false - S3 operations disabled")
        return None

    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

    if not access_key or not secret_key:
        logger.warning("⚠️ AWS credentials not found - S3 client unavailable")
        return None

    try:
        import boto3
        client = boto3.client(
            's3',
            region_name=region or AWS_REGION,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        logger.info(f"✓ AWS S3 client initialized (region: {region or AWS_REGION})")
        return client
    except Exception as e:
        logger.error(f"✗ Failed to initialize S3 client: {e}")
        return None


def init_redis_client():
    """
    Initialize Redis client for presigned URL caching.

    Returns:
        Redis client or None if disabled
    """
    if not REDIS_ENABLED:
        logger.info("⚠️ Redis disabled - presigned URL caching unavailable")
        return None

    try:
        import redis
        client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=False
        )
        # Test connection
        client.ping()
        logger.info(f"✓ Redis client initialized ({REDIS_HOST}:{REDIS_PORT})")
        return client
    except Exception as e:
        logger.warning(f"⚠️ Redis connection failed: {e}")
        return None


def init_database_connection():
    """
    Initialize database connection for audit logging.

    Returns:
        Database connection or None if not configured
    """
    if not DATABASE_URL:
        logger.info("⚠️ DATABASE_URL not set - audit logging to console only")
        return None

    try:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        logger.info("✓ Database connection established")
        return conn
    except Exception as e:
        logger.warning(f"⚠️ Database connection failed: {e}")
        return None


# Initialize global clients
S3_CLIENT = init_s3_client()
REDIS_CLIENT = init_redis_client()
DB_CONNECTION = init_database_connection()


def get_service_status() -> Dict[str, Any]:
    """
    Get status of all configured services.

    Returns:
        Dict with service availability status
    """
    return {
        "aws_s3": {
            "enabled": AWS_S3_ENABLED,
            "available": S3_CLIENT is not None,
            "region": AWS_REGION,
            "bucket": AWS_DEFAULT_BUCKET
        },
        "redis": {
            "enabled": REDIS_ENABLED,
            "available": REDIS_CLIENT is not None,
            "host": REDIS_HOST,
            "port": REDIS_PORT
        },
        "database": {
            "configured": bool(DATABASE_URL),
            "available": DB_CONNECTION is not None
        }
    }


if __name__ == "__main__":
    # Print service status for debugging
    import json
    status = get_service_status()
    print(json.dumps(status, indent=2))
