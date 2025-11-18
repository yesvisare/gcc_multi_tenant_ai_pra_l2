"""
Configuration management for L3 M13.4: Capacity Planning & Forecasting

Loads environment variables and initializes PostgreSQL database connections.
Supports offline mode for testing without database credentials.
"""

import os
import logging
from typing import Optional, Any, Dict
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Database configuration
DB_ENABLED = os.getenv("DB_ENABLED", "false").lower() == "true"
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "capacity_planning")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Forecasting parameters
HEADROOM_FACTOR = float(os.getenv("HEADROOM_FACTOR", "1.2"))  # 20% headroom
HISTORY_MONTHS = int(os.getenv("HISTORY_MONTHS", "6"))
FORECAST_MONTHS = int(os.getenv("FORECAST_MONTHS", "3"))

# Alert thresholds
THRESHOLD_CAUTION = float(os.getenv("THRESHOLD_CAUTION", "70.0"))
THRESHOLD_WARNING = float(os.getenv("THRESHOLD_WARNING", "80.0"))
THRESHOLD_CRITICAL = float(os.getenv("THRESHOLD_CRITICAL", "90.0"))


def init_db_connection() -> Optional[Any]:
    """
    Initialize PostgreSQL database connection.

    Returns:
        Database connection object or None if disabled/unavailable

    Raises:
        Exception: If connection fails with valid credentials
    """
    if not DB_ENABLED:
        logger.warning("⚠️ Database disabled - running in offline mode")
        logger.info("   → Set DB_ENABLED=true in .env to enable PostgreSQL")
        return None

    if not DB_PASSWORD:
        logger.warning("⚠️ DB_PASSWORD not set - database unavailable")
        return None

    try:
        # Import psycopg2 only if database is enabled
        import psycopg2

        connection = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )

        logger.info(f"✓ Connected to PostgreSQL: {DB_HOST}:{DB_PORT}/{DB_NAME}")
        return connection

    except ImportError:
        logger.error("❌ psycopg2 not installed. Install with: pip install psycopg2-binary")
        return None

    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise


def get_forecasting_config() -> Dict[str, Any]:
    """
    Returns forecasting configuration parameters.

    Returns:
        Dict with headroom_factor, history_months, forecast_months, thresholds
    """
    return {
        "headroom_factor": HEADROOM_FACTOR,
        "history_months": HISTORY_MONTHS,
        "forecast_months": FORECAST_MONTHS,
        "thresholds": {
            "caution": THRESHOLD_CAUTION,
            "warning": THRESHOLD_WARNING,
            "critical": THRESHOLD_CRITICAL
        }
    }


# Global database connection
DB_CONNECTION = init_db_connection()


# Utility function for graceful shutdown
def close_db_connection():
    """Closes the global database connection if open."""
    global DB_CONNECTION
    if DB_CONNECTION is not None:
        try:
            DB_CONNECTION.close()
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")
        finally:
            DB_CONNECTION = None
