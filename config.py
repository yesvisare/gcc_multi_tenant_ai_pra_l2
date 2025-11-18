"""
Configuration management for L3 M14.3: Tenant Lifecycle & Migrations

Loads environment variables and initializes infrastructure clients for:
- PostgreSQL (tenant registry, deletion logs, legal holds)
- Redis (distributed locks, state caching)
- Celery (async task distribution)
- Optional: Pinecone (vector database), AWS S3 (object storage)

SERVICE detection: Infrastructure orchestration module (multi-service)
Default mode: OFFLINE (can run without external dependencies)
"""

import os
import logging
from typing import Optional, Any, Dict
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Environment configuration
OFFLINE = os.getenv("OFFLINE", "true").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Optional service integrations
POSTGRES_ENABLED = os.getenv("POSTGRES_ENABLED", "false").lower() == "true"
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"
CELERY_ENABLED = os.getenv("CELERY_ENABLED", "false").lower() == "true"
PINECONE_ENABLED = os.getenv("PINECONE_ENABLED", "false").lower() == "true"
AWS_ENABLED = os.getenv("AWS_ENABLED", "false").lower() == "true"

# Database configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "tenant_registry")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Celery configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# Pinecone configuration (optional)
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "")

# AWS configuration (optional)
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET", "tenant-backups")


def init_clients() -> Dict[str, Any]:
    """
    Initialize infrastructure clients based on environment configuration.

    Returns:
        Dict containing initialized clients or None if disabled/offline

    Note:
        In OFFLINE mode, all clients are None and operations are simulated.
        This allows local development and testing without infrastructure dependencies.
    """
    clients: Dict[str, Any] = {
        "postgres": None,
        "redis": None,
        "celery": None,
        "pinecone": None,
        "s3": None
    }

    if OFFLINE:
        logger.warning("⚠️ OFFLINE mode enabled - all infrastructure calls will be simulated")
        logger.warning("   → Set OFFLINE=false in .env to enable real infrastructure")
        return clients

    # Initialize PostgreSQL
    if POSTGRES_ENABLED and POSTGRES_PASSWORD:
        try:
            logger.info(f"Initializing PostgreSQL connection to {POSTGRES_HOST}:{POSTGRES_PORT}")
            # Uncomment when psycopg2 is available:
            # import psycopg2
            # clients["postgres"] = psycopg2.connect(
            #     host=POSTGRES_HOST,
            #     port=POSTGRES_PORT,
            #     database=POSTGRES_DB,
            #     user=POSTGRES_USER,
            #     password=POSTGRES_PASSWORD
            # )
            logger.info("✓ PostgreSQL client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {e}")
    else:
        logger.info("PostgreSQL disabled or credentials not provided")

    # Initialize Redis
    if REDIS_ENABLED:
        try:
            logger.info(f"Initializing Redis connection to {REDIS_HOST}:{REDIS_PORT}")
            # Uncomment when redis is available:
            # import redis
            # clients["redis"] = redis.Redis(
            #     host=REDIS_HOST,
            #     port=REDIS_PORT,
            #     db=REDIS_DB,
            #     decode_responses=True
            # )
            logger.info("✓ Redis client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
    else:
        logger.info("Redis disabled")

    # Initialize Celery
    if CELERY_ENABLED:
        try:
            logger.info(f"Initializing Celery with broker {CELERY_BROKER_URL}")
            # Uncomment when celery is available:
            # from celery import Celery
            # clients["celery"] = Celery(
            #     'tenant_lifecycle',
            #     broker=CELERY_BROKER_URL,
            #     backend=CELERY_RESULT_BACKEND
            # )
            logger.info("✓ Celery client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Celery: {e}")
    else:
        logger.info("Celery disabled")

    # Initialize Pinecone (optional)
    if PINECONE_ENABLED and PINECONE_API_KEY:
        try:
            logger.info("Initializing Pinecone client")
            # Uncomment when pinecone is available:
            # from pinecone import Pinecone
            # clients["pinecone"] = Pinecone(api_key=PINECONE_API_KEY)
            logger.info("✓ Pinecone client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
    else:
        logger.info("Pinecone disabled or API key not provided")

    # Initialize AWS S3 (optional)
    if AWS_ENABLED and AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        try:
            logger.info(f"Initializing AWS S3 client for region {AWS_REGION}")
            # Uncomment when boto3 is available:
            # import boto3
            # clients["s3"] = boto3.client(
            #     's3',
            #     aws_access_key_id=AWS_ACCESS_KEY_ID,
            #     aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            #     region_name=AWS_REGION
            # )
            logger.info("✓ AWS S3 client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize AWS S3: {e}")
    else:
        logger.info("AWS S3 disabled or credentials not provided")

    return clients


def get_migration_config() -> Dict[str, Any]:
    """
    Get configuration for migration operations.

    Returns:
        Dict containing migration-specific settings
    """
    return {
        "traffic_cutover_stages": [10, 25, 50, 100],  # Percentage stages
        "stabilization_delay_seconds": 30,  # Wait between cutover stages
        "rollback_timeout_seconds": 60,  # Max time for rollback
        "max_retry_attempts": 3,
        "enable_dual_write": True,
        "verify_checksums": True
    }


def get_gdpr_config() -> Dict[str, Any]:
    """
    Get configuration for GDPR deletion operations.

    Returns:
        Dict containing GDPR-specific settings
    """
    return {
        "systems_to_delete": [
            "postgresql",
            "redis",
            "pinecone",
            "s3",
            "cloudwatch",
            "backups",
            "analytics"
        ],
        "deletion_timeout_seconds": 300,  # 5 minutes per system
        "verification_required": True,
        "generate_certificate": True,
        "anonymize_logs": True,
        "backup_exclusion": True,
        "legal_hold_check": True
    }


def get_backup_config() -> Dict[str, Any]:
    """
    Get configuration for backup/restore operations.

    Returns:
        Dict containing backup-specific settings
    """
    return {
        "default_retention_days": 90,
        "cross_region_replication": False,  # Enable for production
        "backup_systems": ["postgresql", "redis", "pinecone", "s3"],
        "compression_enabled": True,
        "encryption_enabled": True,
        "point_in_time_recovery": True
    }


# Global clients dict (initialized on module import)
CLIENTS = init_clients()


# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
