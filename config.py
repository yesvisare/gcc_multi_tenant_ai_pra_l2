"""
Configuration management for L3 M14.1: Multi-Tenant Monitoring & Observability

Loads environment variables and manages Prometheus metrics server lifecycle.
This module handles graceful degradation when Prometheus is not available.
"""

import os
import logging
from typing import Optional, Any, Dict
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ============================================================================
# ENVIRONMENT CONFIGURATION
# ============================================================================

# Prometheus server settings
PROMETHEUS_ENABLED = os.getenv("PROMETHEUS_ENABLED", "false").lower() == "true"
PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", "8000"))

# Offline mode (for notebooks and testing)
OFFLINE = os.getenv("OFFLINE", "false").lower() == "true"

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Application settings
APP_NAME = "L3_M14_Monitoring_Observability"
APP_VERSION = "1.0.0"

# ============================================================================
# METRICS SERVER INITIALIZATION
# ============================================================================

class PrometheusConfig:
    """Manages Prometheus metrics server configuration and lifecycle."""

    def __init__(self):
        self.enabled = PROMETHEUS_ENABLED
        self.port = PROMETHEUS_PORT
        self.server_started = False
        self._metrics_available = False

        # Check if prometheus_client is available
        try:
            import prometheus_client
            self._metrics_available = True
            logger.info("✅ Prometheus client library available")
        except ImportError:
            self._metrics_available = False
            logger.warning("⚠️ prometheus_client not installed - metrics disabled")

    def start_server(self, port: Optional[int] = None) -> bool:
        """
        Start Prometheus metrics server if enabled.

        Args:
            port: Optional port override (uses PROMETHEUS_PORT if not specified)

        Returns:
            True if server started successfully, False otherwise
        """
        if not self.enabled:
            logger.info("ℹ️ Prometheus server disabled (PROMETHEUS_ENABLED=false)")
            return False

        if not self._metrics_available:
            logger.warning("⚠️ Cannot start Prometheus server - client library not installed")
            logger.info("   → Install with: pip install prometheus-client")
            return False

        if self.server_started:
            logger.info("ℹ️ Prometheus server already running")
            return True

        target_port = port or self.port

        try:
            from src.l3_m14_monitoring_observability import start_metrics_server
            start_metrics_server(target_port)
            self.server_started = True
            self.port = target_port
            logger.info(f"✅ Prometheus metrics server started on port {target_port}")
            return True
        except Exception as e:
            logger.error(f"Failed to start Prometheus server: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """
        Get current Prometheus configuration status.

        Returns:
            Dictionary with configuration and runtime status
        """
        return {
            'enabled': self.enabled,
            'port': self.port,
            'server_started': self.server_started,
            'library_available': self._metrics_available,
            'offline_mode': OFFLINE
        }


# ============================================================================
# GLOBAL CONFIGURATION INSTANCES
# ============================================================================

# Global Prometheus configuration
prometheus_config = PrometheusConfig()


def init_monitoring() -> Dict[str, Any]:
    """
    Initialize monitoring infrastructure.

    This function should be called at application startup to:
    1. Check Prometheus availability
    2. Start metrics server if enabled
    3. Configure logging

    Returns:
        Dictionary containing initialization status
    """
    logging.basicConfig(level=LOG_LEVEL)

    logger.info(f"Initializing {APP_NAME} v{APP_VERSION}")
    logger.info(f"Configuration: PROMETHEUS_ENABLED={PROMETHEUS_ENABLED}, OFFLINE={OFFLINE}")

    result = {
        'app_name': APP_NAME,
        'version': APP_VERSION,
        'prometheus': prometheus_config.get_status()
    }

    if PROMETHEUS_ENABLED and not OFFLINE:
        success = prometheus_config.start_server()
        result['prometheus']['startup_success'] = success

        if success:
            logger.info(f"✅ Metrics available at http://localhost:{PROMETHEUS_PORT}/metrics")
        else:
            logger.warning("⚠️ Running without Prometheus metrics")
    else:
        logger.info("ℹ️ Running in offline mode - metrics will be stored in-memory")

    return result


def get_config() -> Dict[str, Any]:
    """
    Get current application configuration.

    Returns:
        Dictionary containing all configuration values
    """
    return {
        'prometheus_enabled': PROMETHEUS_ENABLED,
        'prometheus_port': PROMETHEUS_PORT,
        'offline': OFFLINE,
        'log_level': LOG_LEVEL,
        'app_name': APP_NAME,
        'app_version': APP_VERSION
    }
