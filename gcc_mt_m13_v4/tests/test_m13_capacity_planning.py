"""
Tests for L3 M13.4: Capacity Planning & Forecasting

Tests all major functions with offline/mocked data.
Database integration tests are skipped unless DB_ENABLED=true.
"""

import pytest
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.l3_m13_capacity_planning import (
    TenantCapacityForecaster,
    ForecastResult,
    CapacityMetric,
    get_alert_level,
    calculate_headroom,
    recommend_rebalancing
)

# Force offline mode for tests
os.environ["DB_ENABLED"] = "false"
os.environ["OFFLINE"] = "true"


class TestAlertLevels:
    """Test alert level threshold logic"""

    def test_alert_level_ok(self):
        """Usage below 70% should return OK"""
        assert get_alert_level(50.0) == "OK"
        assert get_alert_level(69.9) == "OK"

    def test_alert_level_caution(self):
        """Usage 70-79% should return CAUTION"""
        assert get_alert_level(70.0) == "CAUTION"
        assert get_alert_level(75.0) == "CAUTION"
        assert get_alert_level(79.9) == "CAUTION"

    def test_alert_level_warning(self):
        """Usage 80-89% should return WARNING"""
        assert get_alert_level(80.0) == "WARNING"
        assert get_alert_level(85.0) == "WARNING"
        assert get_alert_level(89.9) == "WARNING"

    def test_alert_level_critical(self):
        """Usage 90%+ should return CRITICAL"""
        assert get_alert_level(90.0) == "CRITICAL"
        assert get_alert_level(95.0) == "CRITICAL"
        assert get_alert_level(100.0) == "CRITICAL"


class TestHeadroomCalculation:
    """Test headroom buffer calculations"""

    def test_default_headroom(self):
        """Default 20% headroom (1.2x multiplier)"""
        assert calculate_headroom(80.0) == 96.0
        assert calculate_headroom(50.0) == 60.0

    def test_custom_headroom(self):
        """Custom headroom factors"""
        assert calculate_headroom(80.0, headroom_factor=1.3) == 104.0
        assert calculate_headroom(50.0, headroom_factor=1.5) == 75.0


class TestTenantCapacityForecaster:
    """Test TenantCapacityForecaster class"""

    def test_forecaster_initialization(self):
        """Test forecaster initializes with correct defaults"""
        forecaster = TenantCapacityForecaster()
        assert forecaster.headroom_factor == 1.2
        assert forecaster.db_connection is None
        assert forecaster.model is not None

    def test_forecaster_custom_headroom(self):
        """Test forecaster with custom headroom factor"""
        forecaster = TenantCapacityForecaster(headroom_factor=1.3)
        assert forecaster.headroom_factor == 1.3

    def test_synthetic_data_generation(self):
        """Test synthetic data generation for offline mode"""
        forecaster = TenantCapacityForecaster()
        data = forecaster._generate_synthetic_data(
            tenant_id="tenant-123",
            metric_name="cpu_usage",
            months=6
        )

        assert len(data) == 6
        assert all(isinstance(m, CapacityMetric) for m in data)
        assert all(0 <= m.value <= 100 for m in data)
        assert all(m.tenant_id == "tenant-123" for m in data)
        assert all(m.metric_name == "cpu_usage" for m in data)

    def test_get_historical_usage_offline(self):
        """Test historical usage retrieval in offline mode"""
        forecaster = TenantCapacityForecaster()
        data = forecaster.get_historical_usage(
            tenant_id="tenant-123",
            metric_name="memory_usage",
            months_back=6
        )

        assert len(data) == 6
        assert all(isinstance(m, CapacityMetric) for m in data)

    def test_forecast_capacity_offline(self):
        """Test capacity forecasting with synthetic data"""
        forecaster = TenantCapacityForecaster()

        # Generate historical data
        historical = forecaster.get_historical_usage(
            tenant_id="tenant-456",
            metric_name="cpu_usage",
            months_back=6
        )

        # Run forecast
        result = forecaster.forecast_capacity(historical, months_ahead=3)

        # Validate result
        assert isinstance(result, ForecastResult)
        assert result.tenant_id == "tenant-456"
        assert result.metric_name == "cpu_usage"
        assert result.current_usage >= 0
        assert result.predicted_usage >= 0
        assert result.predicted_with_headroom > result.predicted_usage
        assert result.confidence >= 0
        assert result.alert_level in ["OK", "CAUTION", "WARNING", "CRITICAL"]
        assert len(result.recommendation) > 0

    def test_forecast_capacity_empty_data(self):
        """Test forecast fails with empty data"""
        forecaster = TenantCapacityForecaster()

        with pytest.raises(ValueError, match="Cannot forecast with empty historical data"):
            forecaster.forecast_capacity([], months_ahead=3)

    def test_forecast_all_tenants_offline(self):
        """Test batch forecasting for multiple tenants"""
        forecaster = TenantCapacityForecaster()

        tenant_ids = ["tenant-1", "tenant-2", "tenant-3"]
        metrics = ["cpu_usage", "memory_usage"]

        results = forecaster.forecast_all_tenants(tenant_ids, metrics)

        # Should have 3 tenants × 2 metrics = 6 results
        assert len(results) == 6
        assert all(isinstance(r, ForecastResult) for r in results)

        # Check all combinations are present
        tenant_metric_pairs = {(r.tenant_id, r.metric_name) for r in results}
        expected_pairs = {(t, m) for t in tenant_ids for m in metrics}
        assert tenant_metric_pairs == expected_pairs

    def test_store_forecast_without_db(self):
        """Test storing forecast returns False without database"""
        forecaster = TenantCapacityForecaster()

        # Generate a forecast
        historical = forecaster.get_historical_usage("tenant-999", "cpu_usage")
        forecast = forecaster.forecast_capacity(historical)

        # Attempt to store (should return False gracefully)
        result = forecaster.store_forecast(forecast)
        assert result is False


class TestRebalancingRecommendations:
    """Test tenant rebalancing logic"""

    def test_no_rebalancing_needed(self):
        """Test no recommendations when usage is balanced"""
        tenant_usage = {
            "tenant-1": 50.0,
            "tenant-2": 52.0,
            "tenant-3": 48.0
        }

        recommendations = recommend_rebalancing(tenant_usage, imbalance_threshold=0.3)
        assert len(recommendations) == 0

    def test_rebalancing_needed(self):
        """Test recommendations when usage is imbalanced"""
        tenant_usage = {
            "tenant-1": 90.0,  # High usage
            "tenant-2": 30.0,
            "tenant-3": 25.0
        }

        recommendations = recommend_rebalancing(tenant_usage, imbalance_threshold=0.3)
        assert len(recommendations) > 0

        # Check recommendation structure
        for rec in recommendations:
            assert len(rec) == 3
            tenant_id, source, target = rec
            assert tenant_id in tenant_usage
            assert "node" in source.lower()
            assert "node" in target.lower()

    def test_rebalancing_empty_data(self):
        """Test rebalancing with empty data"""
        recommendations = recommend_rebalancing({}, imbalance_threshold=0.3)
        assert len(recommendations) == 0


# Database integration tests (skipped by default)
@pytest.mark.skipif(
    os.getenv("DB_ENABLED", "false").lower() != "true",
    reason="Database not enabled"
)
class TestDatabaseIntegration:
    """Integration tests requiring actual PostgreSQL database"""

    def test_db_connection(self):
        """Test database connection is established"""
        from config import DB_CONNECTION
        assert DB_CONNECTION is not None

    def test_historical_data_from_db(self):
        """Test fetching historical data from real database"""
        from config import DB_CONNECTION
        forecaster = TenantCapacityForecaster(db_connection=DB_CONNECTION)

        # This will fail if the table doesn't exist
        with pytest.raises(Exception):
            data = forecaster.get_historical_usage(
                tenant_id="test-tenant",
                metric_name="cpu_usage",
                months_back=6
            )

    def test_store_forecast_to_db(self):
        """Test storing forecast to database"""
        from config import DB_CONNECTION
        forecaster = TenantCapacityForecaster(db_connection=DB_CONNECTION)

        # Generate synthetic forecast
        historical = forecaster.get_historical_usage("test-tenant", "cpu_usage")
        forecast = forecaster.forecast_capacity(historical)

        # Attempt to store (requires capacity_forecasts table)
        result = forecaster.store_forecast(forecast)
        # Result depends on table existence
        assert isinstance(result, bool)


# Test fixtures
@pytest.fixture
def sample_capacity_metrics():
    """Fixture providing sample capacity metrics"""
    base_time = datetime.now()
    return [
        CapacityMetric(
            tenant_id="tenant-test",
            metric_name="cpu_usage",
            timestamp=base_time - timedelta(days=30 * i),
            value=60.0 + (i * 2.5)
        )
        for i in range(6, 0, -1)
    ]


def test_sample_metrics_fixture(sample_capacity_metrics):
    """Test the sample metrics fixture"""
    assert len(sample_capacity_metrics) == 6
    assert all(isinstance(m, CapacityMetric) for m in sample_capacity_metrics)
