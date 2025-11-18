"""
L3 M13.4: Capacity Planning & Forecasting

This module implements tenant capacity forecasting for multi-tenant platforms using
time-series analysis and linear regression. Analyzes historical usage patterns to
predict capacity needs 3 months ahead with 20% headroom buffer.

Key Capabilities:
- Historical usage pattern analysis from PostgreSQL
- Linear regression-based trend prediction
- Multi-threshold alerting (70%, 80%, 90% utilization)
- Tenant rebalancing strategy recommendations
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np
from sklearn.linear_model import LinearRegression

logger = logging.getLogger(__name__)

__all__ = [
    "TenantCapacityForecaster",
    "ForecastResult",
    "CapacityMetric",
    "get_alert_level",
    "calculate_headroom",
    "recommend_rebalancing"
]


@dataclass
class CapacityMetric:
    """Represents a capacity metric for a tenant."""
    tenant_id: str
    metric_name: str  # cpu_usage, memory_usage, storage_usage
    timestamp: datetime
    value: float
    unit: str = "%"


@dataclass
class ForecastResult:
    """Results from capacity forecasting."""
    tenant_id: str
    metric_name: str
    current_usage: float
    predicted_usage: float
    predicted_with_headroom: float
    forecast_date: datetime
    confidence: float
    alert_level: str
    recommendation: str


class TenantCapacityForecaster:
    """
    Forecasts capacity needs for multi-tenant platforms using linear regression.

    Uses 6 months of historical data to predict 3 months ahead with 20% headroom
    buffer to absorb quarter-end spikes.
    """

    def __init__(self, db_connection=None, headroom_factor: float = 1.2):
        """
        Initialize the capacity forecaster.

        Args:
            db_connection: PostgreSQL database connection (optional)
            headroom_factor: Safety buffer multiplier (default: 1.2 for 20% headroom)
        """
        self.db_connection = db_connection
        self.headroom_factor = headroom_factor
        self.model = LinearRegression()
        logger.info(f"Initialized TenantCapacityForecaster with {headroom_factor}x headroom")

    def get_historical_usage(
        self,
        tenant_id: str,
        metric_name: str,
        months_back: int = 6
    ) -> List[CapacityMetric]:
        """
        Retrieves historical usage data from PostgreSQL.

        Args:
            tenant_id: Tenant identifier
            metric_name: Metric to retrieve (cpu_usage, memory_usage, storage_usage)
            months_back: Number of months of history to fetch (default: 6)

        Returns:
            List of CapacityMetric objects sorted by timestamp

        Raises:
            ValueError: If insufficient data (< 3 months minimum required)
        """
        logger.info(f"Fetching {months_back} months of {metric_name} for tenant {tenant_id}")

        if self.db_connection is None:
            # Generate synthetic data for offline mode
            logger.warning("⚠️ No database connection - generating synthetic data")
            return self._generate_synthetic_data(tenant_id, metric_name, months_back)

        try:
            # Query PostgreSQL for monthly aggregates
            query = """
                SELECT
                    tenant_id,
                    metric_name,
                    DATE_TRUNC('month', timestamp) as month,
                    AVG(value) as avg_value
                FROM capacity_metrics
                WHERE tenant_id = %s
                  AND metric_name = %s
                  AND timestamp >= NOW() - INTERVAL '%s months'
                GROUP BY tenant_id, metric_name, month
                ORDER BY month ASC
            """

            cursor = self.db_connection.cursor()
            cursor.execute(query, (tenant_id, metric_name, months_back))
            rows = cursor.fetchall()

            if len(rows) < 3:
                raise ValueError(
                    f"Insufficient historical data: {len(rows)} months found, "
                    f"minimum 3 months required"
                )

            metrics = [
                CapacityMetric(
                    tenant_id=row[0],
                    metric_name=row[1],
                    timestamp=row[2],
                    value=float(row[3])
                )
                for row in rows
            ]

            logger.info(f"Retrieved {len(metrics)} data points")
            return metrics

        except Exception as e:
            logger.error(f"Database query failed: {e}")
            raise

    def _generate_synthetic_data(
        self,
        tenant_id: str,
        metric_name: str,
        months: int
    ) -> List[CapacityMetric]:
        """Generate synthetic time-series data for testing."""
        base_usage = 60.0  # Start at 60% utilization
        growth_rate = 2.5  # 2.5% growth per month
        noise_level = 5.0  # ±5% random variation

        data = []
        for i in range(months):
            timestamp = datetime.now() - timedelta(days=30 * (months - i))
            value = base_usage + (growth_rate * i) + np.random.normal(0, noise_level)
            value = max(0, min(100, value))  # Clamp to 0-100%

            data.append(CapacityMetric(
                tenant_id=tenant_id,
                metric_name=metric_name,
                timestamp=timestamp,
                value=value
            ))

        return data

    def forecast_capacity(
        self,
        historical_data: List[CapacityMetric],
        months_ahead: int = 3
    ) -> ForecastResult:
        """
        Forecasts future capacity using linear regression with headroom buffer.

        Algorithm:
        1. Fit linear regression to historical monthly aggregates
        2. Predict usage N months ahead
        3. Apply headroom factor (default 20%) for spike absorption
        4. Calculate alert level and recommendation

        Args:
            historical_data: Historical capacity metrics
            months_ahead: Number of months to forecast (default: 3)

        Returns:
            ForecastResult with predictions and recommendations

        Raises:
            ValueError: If historical_data is empty or invalid
        """
        if not historical_data:
            raise ValueError("Cannot forecast with empty historical data")

        tenant_id = historical_data[0].tenant_id
        metric_name = historical_data[0].metric_name

        logger.info(f"Forecasting {metric_name} for {tenant_id}, {months_ahead} months ahead")

        # Prepare data for regression
        timestamps = np.array([
            (m.timestamp - historical_data[0].timestamp).days
            for m in historical_data
        ]).reshape(-1, 1)

        values = np.array([m.value for m in historical_data])

        # Fit linear regression
        self.model.fit(timestamps, values)

        # Predict future usage
        last_timestamp = (historical_data[-1].timestamp - historical_data[0].timestamp).days
        future_timestamp = last_timestamp + (months_ahead * 30)
        predicted_usage = self.model.predict([[future_timestamp]])[0]

        # Apply headroom factor
        predicted_with_headroom = predicted_usage * self.headroom_factor

        # Calculate confidence (R² score)
        confidence = self.model.score(timestamps, values)

        # Determine alert level and recommendation
        current_usage = historical_data[-1].value
        alert_level = get_alert_level(predicted_with_headroom)
        recommendation = self._generate_recommendation(
            current_usage,
            predicted_with_headroom,
            alert_level
        )

        forecast_date = historical_data[-1].timestamp + timedelta(days=months_ahead * 30)

        result = ForecastResult(
            tenant_id=tenant_id,
            metric_name=metric_name,
            current_usage=current_usage,
            predicted_usage=predicted_usage,
            predicted_with_headroom=predicted_with_headroom,
            forecast_date=forecast_date,
            confidence=confidence,
            alert_level=alert_level,
            recommendation=recommendation
        )

        logger.info(
            f"Forecast complete: {current_usage:.1f}% → {predicted_usage:.1f}% "
            f"(+headroom: {predicted_with_headroom:.1f}%) | Alert: {alert_level}"
        )

        return result

    def _generate_recommendation(
        self,
        current: float,
        predicted: float,
        alert_level: str
    ) -> str:
        """Generate actionable recommendation based on forecast."""
        if alert_level == "CRITICAL":
            return "URGENT: Begin emergency capacity expansion immediately"
        elif alert_level == "WARNING":
            return "Action required: Initiate procurement process for additional resources"
        elif alert_level == "CAUTION":
            return "Plan ahead: Review capacity roadmap and budget allocation"
        else:
            return "No action needed: Capacity adequate for forecast period"

    def forecast_all_tenants(
        self,
        tenant_ids: List[str],
        metrics: List[str] = None
    ) -> List[ForecastResult]:
        """
        Batch forecast capacity for multiple tenants and metrics.

        Processes 50+ tenants × 3 metrics efficiently with error handling.

        Args:
            tenant_ids: List of tenant identifiers
            metrics: List of metric names (default: cpu, memory, storage)

        Returns:
            List of ForecastResult objects for all combinations
        """
        if metrics is None:
            metrics = ["cpu_usage", "memory_usage", "storage_usage"]

        logger.info(f"Batch forecasting for {len(tenant_ids)} tenants × {len(metrics)} metrics")

        results = []
        total_combinations = len(tenant_ids) * len(metrics)
        processed = 0

        for tenant_id in tenant_ids:
            for metric_name in metrics:
                try:
                    # Fetch historical data
                    historical = self.get_historical_usage(tenant_id, metric_name)

                    # Generate forecast
                    forecast = self.forecast_capacity(historical)
                    results.append(forecast)

                    processed += 1
                    if processed % 10 == 0:
                        logger.info(f"Progress: {processed}/{total_combinations} forecasts completed")

                except Exception as e:
                    logger.error(f"Forecast failed for {tenant_id}/{metric_name}: {e}")
                    # Continue processing other tenants
                    continue

        logger.info(f"Batch forecast complete: {len(results)}/{total_combinations} successful")
        return results

    def store_forecast(
        self,
        forecast: ForecastResult,
        table_name: str = "capacity_forecasts"
    ) -> bool:
        """
        Persists forecast results to PostgreSQL for auditing and dashboard display.

        Args:
            forecast: ForecastResult to store
            table_name: Target table name

        Returns:
            True if stored successfully, False otherwise
        """
        if self.db_connection is None:
            logger.warning("⚠️ No database connection - skipping persistence")
            return False

        try:
            query = f"""
                INSERT INTO {table_name} (
                    tenant_id, metric_name, current_usage, predicted_usage,
                    predicted_with_headroom, forecast_date, confidence,
                    alert_level, recommendation, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """

            cursor = self.db_connection.cursor()
            cursor.execute(query, (
                forecast.tenant_id,
                forecast.metric_name,
                forecast.current_usage,
                forecast.predicted_usage,
                forecast.predicted_with_headroom,
                forecast.forecast_date,
                forecast.confidence,
                forecast.alert_level,
                forecast.recommendation
            ))

            self.db_connection.commit()
            logger.info(f"Stored forecast for {forecast.tenant_id}/{forecast.metric_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to store forecast: {e}")
            return False


def get_alert_level(usage_percent: float) -> str:
    """
    Determines alert level based on usage percentage thresholds.

    Thresholds:
    - < 70%: OK (no action)
    - 70-80%: CAUTION (plan ahead)
    - 80-90%: WARNING (procurement)
    - >= 90%: CRITICAL (emergency expansion)

    Args:
        usage_percent: Predicted usage percentage

    Returns:
        Alert level string
    """
    if usage_percent >= 90:
        return "CRITICAL"
    elif usage_percent >= 80:
        return "WARNING"
    elif usage_percent >= 70:
        return "CAUTION"
    else:
        return "OK"


def calculate_headroom(
    predicted_usage: float,
    headroom_factor: float = 1.2
) -> float:
    """
    Calculates capacity with headroom buffer.

    Industry standard: 20% headroom (1.2x multiplier) absorbs quarter-end spikes
    without excessive waste.

    Args:
        predicted_usage: Base predicted usage percentage
        headroom_factor: Safety buffer multiplier (default: 1.2)

    Returns:
        Usage with headroom applied
    """
    return predicted_usage * headroom_factor


def recommend_rebalancing(
    tenant_usage: Dict[str, float],
    imbalance_threshold: float = 0.3
) -> List[Tuple[str, str, str]]:
    """
    Recommends tenant rebalancing to address "noisy neighbor" problems.

    Identifies tenants causing uneven load distribution and suggests migrations.

    Args:
        tenant_usage: Dict mapping tenant_id to usage percentage
        imbalance_threshold: Max acceptable usage difference (default: 30%)

    Returns:
        List of (tenant_id, source_node, target_node) recommendations
    """
    if not tenant_usage:
        return []

    # Calculate usage distribution
    usages = list(tenant_usage.values())
    max_usage = max(usages)
    min_usage = min(usages)
    imbalance = (max_usage - min_usage) / max_usage

    recommendations = []

    if imbalance > imbalance_threshold:
        # Find high-usage tenants on overloaded nodes
        sorted_tenants = sorted(tenant_usage.items(), key=lambda x: x[1], reverse=True)

        for tenant_id, usage in sorted_tenants[:3]:  # Top 3 resource consumers
            if usage > max_usage * 0.7:  # Tenant using > 70% of node capacity
                recommendations.append((
                    tenant_id,
                    "overloaded_node",
                    "underutilized_node"
                ))
                logger.info(f"Rebalancing recommendation: Move {tenant_id} (usage: {usage:.1f}%)")

    return recommendations
