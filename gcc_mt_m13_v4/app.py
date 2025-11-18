"""
FastAPI application for L3 M13.4: Capacity Planning & Forecasting

Provides REST API endpoints for tenant capacity forecasting, batch processing,
and rebalancing recommendations.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import logging
from typing import Dict, Any, List, Optional
import os

from src.l3_m13_capacity_planning import (
    TenantCapacityForecaster,
    ForecastResult,
    get_alert_level,
    recommend_rebalancing
)
from config import DB_CONNECTION, get_forecasting_config, DB_ENABLED

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="L3 M13.4 Capacity Planning API",
    description="Forecasts tenant capacity needs using time-series analysis and linear regression",
    version="1.0.0"
)

# Initialize forecaster with database connection
forecaster = TenantCapacityForecaster(
    db_connection=DB_CONNECTION,
    headroom_factor=get_forecasting_config()["headroom_factor"]
)


# Request/Response Models
class ForecastRequest(BaseModel):
    """Request model for single tenant forecast"""
    tenant_id: str = Field(..., description="Tenant identifier")
    metric_name: str = Field(
        default="cpu_usage",
        description="Metric to forecast (cpu_usage, memory_usage, storage_usage)"
    )
    months_back: int = Field(default=6, ge=3, description="Historical months to analyze")
    months_ahead: int = Field(default=3, ge=1, le=12, description="Months to forecast")


class BatchForecastRequest(BaseModel):
    """Request model for batch forecasting"""
    tenant_ids: List[str] = Field(..., description="List of tenant identifiers")
    metrics: Optional[List[str]] = Field(
        default=None,
        description="Metrics to forecast (default: cpu, memory, storage)"
    )


class RebalancingRequest(BaseModel):
    """Request model for rebalancing recommendations"""
    tenant_usage: Dict[str, float] = Field(
        ...,
        description="Mapping of tenant_id to current usage percentage"
    )
    imbalance_threshold: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Max acceptable usage imbalance (default: 30%)"
    )


class ForecastResponse(BaseModel):
    """Response model for forecast results"""
    tenant_id: str
    metric_name: str
    current_usage: float
    predicted_usage: float
    predicted_with_headroom: float
    forecast_date: str
    confidence: float
    alert_level: str
    recommendation: str


class BatchForecastResponse(BaseModel):
    """Response model for batch forecasting"""
    total_processed: int
    successful: int
    failed: int
    results: List[ForecastResponse]


class RebalancingResponse(BaseModel):
    """Response model for rebalancing recommendations"""
    imbalance_detected: bool
    imbalance_ratio: float
    recommendations: List[Dict[str, str]]


# API Endpoints
@app.get("/")
def root():
    """Health check and service status"""
    config = get_forecasting_config()
    return {
        "status": "healthy",
        "module": "L3_M13_Capacity_Planning",
        "database_enabled": DB_ENABLED,
        "database_connected": DB_CONNECTION is not None,
        "configuration": {
            "headroom_factor": config["headroom_factor"],
            "history_months": config["history_months"],
            "forecast_months": config["forecast_months"],
            "thresholds": config["thresholds"]
        }
    }


@app.post("/forecast", response_model=ForecastResponse)
def forecast_capacity(request: ForecastRequest):
    """
    Forecast capacity for a single tenant and metric.

    Returns predicted usage 3 months ahead with 20% headroom buffer.
    """
    try:
        # Fetch historical data
        historical = forecaster.get_historical_usage(
            tenant_id=request.tenant_id,
            metric_name=request.metric_name,
            months_back=request.months_back
        )

        # Generate forecast
        result = forecaster.forecast_capacity(
            historical_data=historical,
            months_ahead=request.months_ahead
        )

        # Store forecast to database (if enabled)
        if DB_CONNECTION is not None:
            forecaster.store_forecast(result)

        return ForecastResponse(
            tenant_id=result.tenant_id,
            metric_name=result.metric_name,
            current_usage=result.current_usage,
            predicted_usage=result.predicted_usage,
            predicted_with_headroom=result.predicted_with_headroom,
            forecast_date=result.forecast_date.isoformat(),
            confidence=result.confidence,
            alert_level=result.alert_level,
            recommendation=result.recommendation
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Forecast failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/forecast/batch", response_model=BatchForecastResponse)
def forecast_batch(request: BatchForecastRequest):
    """
    Batch forecast capacity for multiple tenants.

    Processes 50+ tenants × 3 metrics efficiently with error handling.
    """
    if not request.tenant_ids:
        raise HTTPException(status_code=400, detail="tenant_ids cannot be empty")

    try:
        # Run batch forecasting
        results = forecaster.forecast_all_tenants(
            tenant_ids=request.tenant_ids,
            metrics=request.metrics
        )

        # Convert to response format
        response_results = [
            ForecastResponse(
                tenant_id=r.tenant_id,
                metric_name=r.metric_name,
                current_usage=r.current_usage,
                predicted_usage=r.predicted_usage,
                predicted_with_headroom=r.predicted_with_headroom,
                forecast_date=r.forecast_date.isoformat(),
                confidence=r.confidence,
                alert_level=r.alert_level,
                recommendation=r.recommendation
            )
            for r in results
        ]

        total_expected = len(request.tenant_ids) * (len(request.metrics) if request.metrics else 3)
        successful = len(response_results)
        failed = total_expected - successful

        return BatchForecastResponse(
            total_processed=total_expected,
            successful=successful,
            failed=failed,
            results=response_results
        )

    except Exception as e:
        logger.error(f"Batch forecast failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rebalancing", response_model=RebalancingResponse)
def get_rebalancing_recommendations(request: RebalancingRequest):
    """
    Get tenant rebalancing recommendations to address load imbalances.

    Identifies "noisy neighbor" problems and suggests tenant migrations.
    """
    if not request.tenant_usage:
        raise HTTPException(status_code=400, detail="tenant_usage cannot be empty")

    try:
        # Get rebalancing recommendations
        recommendations = recommend_rebalancing(
            tenant_usage=request.tenant_usage,
            imbalance_threshold=request.imbalance_threshold
        )

        # Calculate imbalance ratio
        usages = list(request.tenant_usage.values())
        max_usage = max(usages)
        min_usage = min(usages)
        imbalance_ratio = (max_usage - min_usage) / max_usage if max_usage > 0 else 0.0

        # Format recommendations
        formatted_recommendations = [
            {
                "tenant_id": rec[0],
                "source_node": rec[1],
                "target_node": rec[2],
                "reason": f"High usage tenant causing node imbalance"
            }
            for rec in recommendations
        ]

        return RebalancingResponse(
            imbalance_detected=len(recommendations) > 0,
            imbalance_ratio=imbalance_ratio,
            recommendations=formatted_recommendations
        )

    except Exception as e:
        logger.error(f"Rebalancing analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/alert-level/{usage}")
def check_alert_level(usage: float):
    """
    Check alert level for a given usage percentage.

    Thresholds: 70% (CAUTION), 80% (WARNING), 90% (CRITICAL)
    """
    if usage < 0 or usage > 100:
        raise HTTPException(status_code=400, detail="Usage must be between 0 and 100")

    alert = get_alert_level(usage)

    return {
        "usage_percent": usage,
        "alert_level": alert,
        "thresholds": get_forecasting_config()["thresholds"]
    }


# Shutdown handler
@app.on_event("shutdown")
def shutdown_event():
    """Clean up database connections on shutdown"""
    from config import close_db_connection
    close_db_connection()
    logger.info("API shutdown complete")
