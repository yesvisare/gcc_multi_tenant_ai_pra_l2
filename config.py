"""
Configuration management for L3 M14.4: Platform Governance & Operating Model

Loads environment variables and configures logging.
No external service clients needed - this module implements governance logic only.
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ============================================================================
# ENVIRONMENT CONFIGURATION
# ============================================================================

# Operating mode (offline is default - no external services needed)
OFFLINE = os.getenv("OFFLINE", "true").lower() == "true"

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Configure logging format
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# ============================================================================
# PLATFORM GOVERNANCE SETTINGS
# ============================================================================

# Default team sizing assumptions (can be overridden via environment)
AVG_ENGINEER_SALARY_INR = int(os.getenv("AVG_ENGINEER_SALARY_INR", "3000000"))  # ₹30L/year
CHAMPION_COST_PER_HOUR_INR = int(os.getenv("CHAMPION_COST_PER_HOUR_INR", "2000"))  # ₹2000/hour

# Default operating model thresholds
SMALL_SCALE_THRESHOLD = int(os.getenv("SMALL_SCALE_THRESHOLD", "10"))  # < 10 tenants
LARGE_SCALE_THRESHOLD = int(os.getenv("LARGE_SCALE_THRESHOLD", "50"))  # > 50 tenants

# Self-service targets
SELF_SERVICE_TARGET_PERCENTAGE = int(os.getenv("SELF_SERVICE_TARGET_PERCENTAGE", "80"))  # 80% tier 1

logger.info("Configuration loaded successfully")
logger.info(f"Offline mode: {OFFLINE}")
logger.info(f"Log level: {LOG_LEVEL}")
logger.info(f"Team sizing: ₹{AVG_ENGINEER_SALARY_INR/100_000:.0f}L salary, ₹{CHAMPION_COST_PER_HOUR_INR}/hour champions")


def get_config() -> dict:
    """
    Get current configuration as dictionary.

    Useful for debugging and validation.

    Returns:
        Dict containing all configuration values
    """
    return {
        "offline": OFFLINE,
        "log_level": LOG_LEVEL,
        "avg_engineer_salary_inr": AVG_ENGINEER_SALARY_INR,
        "champion_cost_per_hour_inr": CHAMPION_COST_PER_HOUR_INR,
        "small_scale_threshold": SMALL_SCALE_THRESHOLD,
        "large_scale_threshold": LARGE_SCALE_THRESHOLD,
        "self_service_target_percentage": SELF_SERVICE_TARGET_PERCENTAGE
    }


def validate_config() -> bool:
    """
    Validate that configuration is reasonable.

    Checks:
    - Salary and cost values are positive
    - Thresholds are logical (small < large)
    - Self-service target is between 0-100%

    Returns:
        True if config is valid, raises ValueError otherwise
    """
    if AVG_ENGINEER_SALARY_INR <= 0:
        raise ValueError(f"AVG_ENGINEER_SALARY_INR must be positive, got {AVG_ENGINEER_SALARY_INR}")

    if CHAMPION_COST_PER_HOUR_INR <= 0:
        raise ValueError(f"CHAMPION_COST_PER_HOUR_INR must be positive, got {CHAMPION_COST_PER_HOUR_INR}")

    if SMALL_SCALE_THRESHOLD >= LARGE_SCALE_THRESHOLD:
        raise ValueError(f"SMALL_SCALE_THRESHOLD ({SMALL_SCALE_THRESHOLD}) must be < LARGE_SCALE_THRESHOLD ({LARGE_SCALE_THRESHOLD})")

    if not 0 <= SELF_SERVICE_TARGET_PERCENTAGE <= 100:
        raise ValueError(f"SELF_SERVICE_TARGET_PERCENTAGE must be 0-100, got {SELF_SERVICE_TARGET_PERCENTAGE}")

    logger.info("Configuration validation passed")
    return True


# Validate config on import
try:
    validate_config()
except ValueError as e:
    logger.error(f"Configuration validation failed: {e}")
    raise
