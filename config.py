"""
Configuration management for L3 M11.4: Tenant Provisioning & Automation

Loads environment variables and manages infrastructure provisioning configuration.

SERVICE: PROVISIONING (infrastructure automation via Terraform)
"""

import os
import logging
from typing import Optional, Any, Dict
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Service detection - Provisioning (Terraform-based infrastructure automation)
PROVISIONING_ENABLED = os.getenv("PROVISIONING_ENABLED", "false").lower() == "true"

# AWS Configuration (for infrastructure provisioning)
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# Terraform Configuration
TERRAFORM_STATE_BUCKET = os.getenv("TERRAFORM_STATE_BUCKET", "terraform-state-bucket")
TERRAFORM_WORKSPACE = os.getenv("TERRAFORM_WORKSPACE", "default")

# Approval Workflow Configuration
AUTO_APPROVE_THRESHOLD = float(os.getenv("AUTO_APPROVE_THRESHOLD", "1000000"))  # ₹10 lakh
CFO_APPROVAL_WEBHOOK = os.getenv("CFO_APPROVAL_WEBHOOK")

# Notification Configuration
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
NOTIFICATION_EMAIL_FROM = os.getenv("NOTIFICATION_EMAIL_FROM", "noreply@gcc.example.com")

# Database Configuration (for tenant registry)
REGISTRY_DB_HOST = os.getenv("REGISTRY_DB_HOST", "localhost")
REGISTRY_DB_PORT = int(os.getenv("REGISTRY_DB_PORT", "5432"))
REGISTRY_DB_NAME = os.getenv("REGISTRY_DB_NAME", "tenant_registry")
REGISTRY_DB_USER = os.getenv("REGISTRY_DB_USER", "registry_user")
REGISTRY_DB_PASSWORD = os.getenv("REGISTRY_DB_PASSWORD")

# Vector Database Configuration (provisioning targets)
VECTOR_DB_TYPE = os.getenv("VECTOR_DB_TYPE", "pinecone")  # pinecone, qdrant, chroma
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")

# Monitoring Configuration
GRAFANA_URL = os.getenv("GRAFANA_URL")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL")

# Validation Configuration
VALIDATION_TIMEOUT_SECONDS = int(os.getenv("VALIDATION_TIMEOUT_SECONDS", "300"))
QUERY_PERFORMANCE_SLA_MS = int(os.getenv("QUERY_PERFORMANCE_SLA_MS", "500"))

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


def init_infrastructure_clients() -> Dict[str, Any]:
    """
    Initialize infrastructure provisioning clients.

    Returns:
        Dict containing initialized clients or None if disabled

    Note:
        When PROVISIONING_ENABLED is False, the system runs in simulation mode.
        This is useful for development, testing, and demonstrations.
    """
    clients = {}

    if not PROVISIONING_ENABLED:
        logger.warning("⚠️ PROVISIONING disabled - running in simulation mode")
        logger.info("   → Infrastructure changes will be simulated")
        logger.info("   → Set PROVISIONING_ENABLED=true in .env to enable")
        return clients

    # Check for required AWS credentials
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        logger.warning("⚠️ AWS credentials not found - provisioning unavailable")
        logger.info("   → Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in .env")
        return clients

    try:
        # Initialize AWS boto3 client (for S3, IAM, RDS, etc.)
        import boto3

        clients["aws_session"] = boto3.Session(
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )

        clients["s3"] = clients["aws_session"].client("s3")
        clients["iam"] = clients["aws_session"].client("iam")
        clients["rds"] = clients["aws_session"].client("rds")

        logger.info("✓ AWS clients initialized")

    except ImportError:
        logger.warning("boto3 not installed - AWS provisioning unavailable")
    except Exception as e:
        logger.error(f"Failed to initialize AWS clients: {e}")

    # Initialize Vector DB client (if credentials provided)
    if VECTOR_DB_TYPE == "pinecone" and PINECONE_API_KEY:
        try:
            import pinecone

            clients["pinecone"] = pinecone.Pinecone(api_key=PINECONE_API_KEY)
            logger.info("✓ Pinecone client initialized")

        except ImportError:
            logger.warning("pinecone-client not installed")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone client: {e}")

    elif VECTOR_DB_TYPE == "qdrant" and QDRANT_URL:
        try:
            from qdrant_client import QdrantClient

            clients["qdrant"] = QdrantClient(url=QDRANT_URL)
            logger.info("✓ Qdrant client initialized")

        except ImportError:
            logger.warning("qdrant-client not installed")
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")

    # Initialize PostgreSQL connection (for tenant registry)
    if REGISTRY_DB_PASSWORD:
        try:
            import psycopg2

            clients["registry_db"] = psycopg2.connect(
                host=REGISTRY_DB_HOST,
                port=REGISTRY_DB_PORT,
                dbname=REGISTRY_DB_NAME,
                user=REGISTRY_DB_USER,
                password=REGISTRY_DB_PASSWORD
            )
            logger.info("✓ Registry database connection established")

        except ImportError:
            logger.warning("psycopg2 not installed")
        except Exception as e:
            logger.error(f"Failed to connect to registry database: {e}")

    if clients:
        logger.info("✓ Infrastructure clients initialized successfully")
    else:
        logger.warning("⚠️ No infrastructure clients initialized - running in simulation mode")

    return clients


# Global clients dictionary
CLIENTS = init_infrastructure_clients()


def get_config_summary() -> Dict[str, Any]:
    """
    Get configuration summary for debugging and health checks.

    Returns:
        Dict with configuration status
    """
    return {
        "provisioning_enabled": PROVISIONING_ENABLED,
        "aws_configured": bool(AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY),
        "aws_region": AWS_REGION,
        "vector_db_type": VECTOR_DB_TYPE,
        "vector_db_configured": bool(
            (VECTOR_DB_TYPE == "pinecone" and PINECONE_API_KEY) or
            (VECTOR_DB_TYPE == "qdrant" and QDRANT_URL)
        ),
        "registry_db_configured": bool(REGISTRY_DB_PASSWORD),
        "terraform_state_bucket": TERRAFORM_STATE_BUCKET,
        "auto_approve_threshold": AUTO_APPROVE_THRESHOLD,
        "validation_timeout": VALIDATION_TIMEOUT_SECONDS,
        "query_sla_ms": QUERY_PERFORMANCE_SLA_MS,
        "clients_initialized": list(CLIENTS.keys())
    }
