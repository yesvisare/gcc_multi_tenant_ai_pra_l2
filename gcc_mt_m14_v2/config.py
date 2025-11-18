"""
Configuration management for L3 M14.2: Incident Management & Blast Radius

Loads environment variables and initializes Prometheus connection.
SERVICE: PROMETHEUS (monitoring/metrics system)
"""

import os
import logging
from typing import Optional, Any, Dict
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ============================================================================
# Environment Configuration
# ============================================================================

# Prometheus Configuration
PROMETHEUS_ENABLED = os.getenv("PROMETHEUS_ENABLED", "false").lower() == "true"
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")

# PagerDuty Configuration (optional)
PAGERDUTY_ENABLED = os.getenv("PAGERDUTY_ENABLED", "false").lower() == "true"
PAGERDUTY_API_KEY = os.getenv("PAGERDUTY_API_KEY")

# Slack Configuration (optional)
SLACK_ENABLED = os.getenv("SLACK_ENABLED", "false").lower() == "true"
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# Detection Parameters
ERROR_THRESHOLD = float(os.getenv("ERROR_THRESHOLD", "0.50"))  # 50% error rate
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL_SECONDS", "10"))  # 10 seconds
CHECK_WINDOW = os.getenv("CHECK_WINDOW", "5m")  # 5 minutes

# Circuit Breaker Parameters
FAILURE_THRESHOLD = int(os.getenv("FAILURE_THRESHOLD", "5"))  # 5 failures
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "60"))  # 60 seconds

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# ============================================================================
# Client Initialization
# ============================================================================

def init_detector() -> Optional[Any]:
    """
    Initialize BlastRadiusDetector with configuration.

    Returns:
        BlastRadiusDetector instance or None if Prometheus disabled
    """
    if not PROMETHEUS_ENABLED:
        logger.warning("⚠️ Prometheus disabled - detector unavailable")
        logger.info("   → Set PROMETHEUS_ENABLED=true in .env to enable")
        return None

    try:
        from src.l3_m14_operations_governance import BlastRadiusDetector

        detector = BlastRadiusDetector(
            prometheus_url=PROMETHEUS_URL,
            error_threshold=ERROR_THRESHOLD,
            check_interval_seconds=CHECK_INTERVAL,
            check_window=CHECK_WINDOW
        )

        logger.info(f"✓ BlastRadiusDetector initialized: url={PROMETHEUS_URL}")
        return detector

    except ImportError as e:
        logger.error(f"Failed to import BlastRadiusDetector: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize detector: {e}")
        return None


def get_notification_config() -> Dict[str, bool]:
    """
    Get notification system configuration.

    Returns:
        Dict with notification system status
    """
    config = {
        "pagerduty_enabled": PAGERDUTY_ENABLED and bool(PAGERDUTY_API_KEY),
        "slack_enabled": SLACK_ENABLED and bool(SLACK_WEBHOOK_URL),
    }

    if PAGERDUTY_ENABLED and not PAGERDUTY_API_KEY:
        logger.warning("⚠️ PagerDuty enabled but PAGERDUTY_API_KEY not set")

    if SLACK_ENABLED and not SLACK_WEBHOOK_URL:
        logger.warning("⚠️ Slack enabled but SLACK_WEBHOOK_URL not set")

    return config


def validate_config() -> bool:
    """
    Validate configuration and log warnings.

    Returns:
        bool: True if configuration is valid for production use
    """
    warnings = []

    if not PROMETHEUS_ENABLED:
        warnings.append("Prometheus is disabled - monitoring unavailable")

    if ERROR_THRESHOLD < 0.1 or ERROR_THRESHOLD > 0.9:
        warnings.append(f"ERROR_THRESHOLD={ERROR_THRESHOLD} is unusual (recommend 0.3-0.7)")

    if CHECK_INTERVAL < 5:
        warnings.append(f"CHECK_INTERVAL={CHECK_INTERVAL}s is very aggressive")

    if FAILURE_THRESHOLD < 3:
        warnings.append(f"FAILURE_THRESHOLD={FAILURE_THRESHOLD} may cause false positives")

    if warnings:
        logger.warning("Configuration warnings:")
        for warning in warnings:
            logger.warning(f"  - {warning}")
        return False

    logger.info("✓ Configuration validated")
    return True


# ============================================================================
# Initialize on Import
# ============================================================================

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize detector (lazy - created when needed)
DETECTOR = None

# Validate configuration
validate_config()

logger.info("Configuration loaded successfully")
