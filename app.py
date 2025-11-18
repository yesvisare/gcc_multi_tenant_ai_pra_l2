"""
FastAPI application for L3 M14.1: Multi-Tenant Monitoring & Observability

Provides REST API endpoints for:
- Starting and ending query tracking
- Recording metrics retroactively
- Updating quota usage
- Retrieving tenant metrics
- Health checks and configuration status

SERVICE: Prometheus (self-hosted metrics collection)
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import logging
from typing import Dict, Any, Optional
import os

from src.l3_m14_monitoring_observability import (
    start_query_tracking,
    end_query_tracking,
    track_query,
    update_quota_usage,
    get_tenant_metrics
)
from config import init_monitoring, get_config, prometheus_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize monitoring on startup
init_monitoring()

app = FastAPI(
    title="L3 M14.1: Multi-Tenant Monitoring & Observability API",
    description="Tenant-aware metrics collection and observability for RAG systems",
    version="1.0.0"
)

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class StartTrackingRequest(BaseModel):
    """Request to start tracking a query"""
    tenant_id: str = Field(..., description="Unique tenant identifier")

class StartTrackingResponse(BaseModel):
    """Context for tracking a query"""
    context: Dict[str, Any] = Field(..., description="Tracking context (pass to end_tracking)")

class EndTrackingRequest(BaseModel):
    """Request to end query tracking"""
    context: Dict[str, Any] = Field(..., description="Context from start_tracking")
    status: str = Field(..., description="Query status: 'success' or 'error'")
    docs_retrieved: int = Field(0, description="Number of documents retrieved")
    llm_tokens: int = Field(0, description="LLM tokens consumed")

class TrackQueryRequest(BaseModel):
    """Request to track a completed query"""
    tenant_id: str = Field(..., description="Unique tenant identifier")
    status: str = Field("success", description="Query status")
    duration: float = Field(0.0, description="Query duration in seconds")
    docs_retrieved: int = Field(0, description="Documents retrieved")
    llm_tokens: int = Field(0, description="LLM tokens consumed")

class UpdateQuotaRequest(BaseModel):
    """Request to update tenant quota usage"""
    tenant_id: str = Field(..., description="Unique tenant identifier")
    resource_type: str = Field(..., description="Resource type: 'queries', 'tokens', 'storage'")
    usage_percent: float = Field(..., description="Usage percentage (0-100)", ge=0, le=100)

class MetricsResponse(BaseModel):
    """Tenant metrics summary"""
    metrics: Dict[str, Any] = Field(..., description="Tenant metrics data")

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    module: str
    prometheus_enabled: bool
    prometheus_server_running: bool
    offline_mode: bool

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/", response_model=HealthResponse)
def root():
    """
    Health check endpoint.

    Returns current system status including Prometheus configuration.
    """
    config = get_config()
    prom_status = prometheus_config.get_status()

    return HealthResponse(
        status="healthy",
        module="L3_M14_Monitoring_Observability",
        prometheus_enabled=prom_status['enabled'],
        prometheus_server_running=prom_status['server_started'],
        offline_mode=config['offline']
    )

@app.post("/tracking/start", response_model=StartTrackingResponse)
def start_tracking(request: StartTrackingRequest):
    """
    Start tracking a RAG query for a tenant.

    This endpoint:
    1. Increments active query gauge for the tenant
    2. Returns a context object with start timestamp
    3. Context must be passed to /tracking/end to complete tracking

    Example:
        POST /tracking/start
        {"tenant_id": "finance-team"}

        Returns:
        {"context": {"tenant_id": "finance-team", "start_time": 1699999999.123, ...}}
    """
    try:
        context = start_query_tracking(request.tenant_id)
        return StartTrackingResponse(context=context)
    except Exception as e:
        logger.error(f"Failed to start tracking for {request.tenant_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tracking start failed: {str(e)}"
        )

@app.post("/tracking/end")
def end_tracking(request: EndTrackingRequest):
    """
    End query tracking and record final metrics.

    This endpoint:
    1. Calculates query duration from context
    2. Records query counter, duration histogram, docs/tokens
    3. Decrements active query gauge

    Example:
        POST /tracking/end
        {
            "context": {"tenant_id": "finance-team", "start_time": 1699999999.123},
            "status": "success",
            "docs_retrieved": 5,
            "llm_tokens": 1200
        }
    """
    try:
        end_query_tracking(
            request.context,
            request.status,
            request.docs_retrieved,
            request.llm_tokens
        )
        return {"message": "Tracking completed", "tenant_id": request.context.get('tenant_id')}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to end tracking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tracking end failed: {str(e)}"
        )

@app.post("/track")
def track_query_endpoint(request: TrackQueryRequest):
    """
    Track a completed query in a single call.

    Useful for:
    - Recording metrics from logs or event streams
    - Backfilling historical data
    - Simple tracking without start/end context management

    Example:
        POST /track
        {
            "tenant_id": "marketing-team",
            "status": "success",
            "duration": 1.5,
            "docs_retrieved": 3,
            "llm_tokens": 800
        }
    """
    try:
        track_query(
            request.tenant_id,
            request.status,
            request.duration,
            request.docs_retrieved,
            request.llm_tokens
        )
        return {"message": "Query tracked", "tenant_id": request.tenant_id}
    except Exception as e:
        logger.error(f"Failed to track query for {request.tenant_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query tracking failed: {str(e)}"
        )

@app.post("/quota/update")
def update_quota_endpoint(request: UpdateQuotaRequest):
    """
    Update tenant quota usage metrics.

    Used to track consumption against monthly/daily limits.

    Example:
        POST /quota/update
        {
            "tenant_id": "finance-team",
            "resource_type": "queries",
            "usage_percent": 75.0
        }

    This indicates the tenant has used 75% of their query quota.
    """
    try:
        update_quota_usage(
            request.tenant_id,
            request.resource_type,
            request.usage_percent
        )
        return {
            "message": "Quota updated",
            "tenant_id": request.tenant_id,
            "resource_type": request.resource_type,
            "usage_percent": request.usage_percent
        }
    except Exception as e:
        logger.error(f"Failed to update quota for {request.tenant_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quota update failed: {str(e)}"
        )

@app.get("/metrics/{tenant_id}", response_model=MetricsResponse)
def get_metrics(tenant_id: str):
    """
    Retrieve current metrics for a specific tenant.

    When Prometheus is enabled, this provides basic info and directs
    to the /metrics endpoint for full Prometheus exposition format.

    When running in-memory mode, returns aggregated metrics.

    Example:
        GET /metrics/finance-team

        Returns:
        {
            "metrics": {
                "tenant_id": "finance-team",
                "total_queries": 150,
                "success_count": 145,
                "error_count": 5,
                "avg_duration_seconds": 1.234
            }
        }
    """
    try:
        metrics = get_tenant_metrics(tenant_id)
        return MetricsResponse(metrics=metrics)
    except Exception as e:
        logger.error(f"Failed to retrieve metrics for {tenant_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Metrics retrieval failed: {str(e)}"
        )

@app.get("/config")
def get_config_endpoint():
    """
    Retrieve current application configuration.

    Returns all environment settings and runtime status.
    """
    config = get_config()
    prom_status = prometheus_config.get_status()

    return {
        "config": config,
        "prometheus_status": prom_status
    }

# ============================================================================
# STARTUP/SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Log startup information"""
    logger.info("="*60)
    logger.info("L3 M14.1: Multi-Tenant Monitoring & Observability API")
    logger.info("="*60)

    config = get_config()
    logger.info(f"Prometheus Enabled: {config['prometheus_enabled']}")
    logger.info(f"Offline Mode: {config['offline']}")

    if config['prometheus_enabled'] and prometheus_config.server_started:
        logger.info(f"Prometheus Metrics: http://localhost:{config['prometheus_port']}/metrics")

    logger.info("API Documentation: http://localhost:8000/docs")
    logger.info("="*60)

@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown information"""
    logger.info("Shutting down L3 M14.1 API...")
