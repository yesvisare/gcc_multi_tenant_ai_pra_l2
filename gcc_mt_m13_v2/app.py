"""
FastAPI application for L3 M13.2: Auto-Scaling Multi-Tenant Infrastructure

Provides REST API endpoints for queue management and metrics export to support
Kubernetes HPA with per-tenant custom metrics.

Services: Prometheus (metrics), Redis (cache), Kubernetes (orchestration)
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from prometheus_client import Gauge, Counter, generate_latest, CONTENT_TYPE_LATEST
import logging
from typing import Dict, Any, Optional, List
import os
import asyncio

from src.l3_m13_scale_performance_optimization import (
    TenantTier,
    GCCAutoScalingPolicy,
    TenantQueueManager,
    calculate_target_replicas,
    validate_resource_quota,
    log_scale_event,
    generate_cost_report
)
from config import CLIENTS, REDIS_ENABLED, PROMETHEUS_ENABLED

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="L3 M13.2 Auto-Scaling API",
    description="Multi-tenant auto-scaling infrastructure with HPA custom metrics",
    version="1.0.0"
)

# Initialize tenant queue manager
queue_manager = TenantQueueManager(max_queue_size=100)

# Prometheus metrics
tenant_queue_depth = Gauge(
    'tenant_queue_depth',
    'Number of queries queued per tenant',
    ['tenant_id']
)

total_queries_processed = Counter(
    'total_queries_processed',
    'Total queries processed',
    ['tenant_id']
)

scaling_events = Counter(
    'scaling_events_total',
    'Total scaling events',
    ['tenant_id', 'direction']
)


# Pydantic models
class QueryRequest(BaseModel):
    """Request model for query submission"""
    tenant_id: str = Field(..., description="Tenant identifier")
    query: str = Field(..., description="Query text")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Optional metadata")


class ScalingConfigRequest(BaseModel):
    """Request model for scaling configuration"""
    tenant_tier: str = Field(..., description="Tenant tier: premium, standard, or free")


class ScalingRecommendation(BaseModel):
    """Response model for scaling recommendations"""
    current_queue_depth: int
    target_replicas: int
    tenant_tier: str
    config: Dict[str, Any]


class CostReportRequest(BaseModel):
    """Request model for cost report generation"""
    tenant_id: str
    avg_replicas: float
    peak_replicas: int
    budget: Optional[float] = None


# API Endpoints

@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "module": "L3_M13_Auto_Scaling_Multi_Tenant_Infrastructure",
        "redis_enabled": REDIS_ENABLED,
        "prometheus_enabled": PROMETHEUS_ENABLED
    }


@app.post("/queue/enqueue")
async def enqueue_query(request: QueryRequest):
    """
    Enqueue a query for processing.

    Adds query to tenant-specific queue and updates metrics.
    If queue is full (>100 queries), returns HTTP 429 (Too Many Requests),
    which triggers HPA scale-up.
    """
    query_data = {
        "query": request.query,
        "metadata": request.metadata
    }

    success = await queue_manager.enqueue(request.tenant_id, query_data)

    if not success:
        # Queue full - trigger backpressure
        raise HTTPException(
            status_code=429,
            detail=f"Queue full for tenant {request.tenant_id}. HPA should scale up."
        )

    # Update Prometheus metrics
    current_depth = queue_manager.get_queue_depth(request.tenant_id)
    tenant_queue_depth.labels(tenant_id=request.tenant_id).set(current_depth)

    logger.info(f"Enqueued query for {request.tenant_id}, queue depth: {current_depth}")

    return {
        "status": "enqueued",
        "tenant_id": request.tenant_id,
        "queue_depth": current_depth
    }


@app.post("/queue/dequeue/{tenant_id}")
async def dequeue_query(tenant_id: str):
    """
    Dequeue a query for processing.

    Returns next query from tenant's queue or 204 if empty.
    """
    query = await queue_manager.dequeue(tenant_id, timeout=0.1)

    if query is None:
        return {"status": "empty", "tenant_id": tenant_id}

    # Update metrics
    current_depth = queue_manager.get_queue_depth(tenant_id)
    tenant_queue_depth.labels(tenant_id=tenant_id).set(current_depth)
    total_queries_processed.labels(tenant_id=tenant_id).inc()

    logger.info(f"Dequeued query for {tenant_id}, remaining: {current_depth}")

    return {
        "status": "success",
        "tenant_id": tenant_id,
        "query": query,
        "remaining_depth": current_depth
    }


@app.get("/queue/depth/{tenant_id}")
def get_queue_depth(tenant_id: str):
    """Get current queue depth for a specific tenant"""
    depth = queue_manager.get_queue_depth(tenant_id)
    return {
        "tenant_id": tenant_id,
        "queue_depth": depth
    }


@app.get("/queue/depths")
def get_all_queue_depths():
    """Get queue depths for all tenants (for monitoring dashboards)"""
    depths = queue_manager.get_all_queue_depths()
    return {
        "tenants": depths,
        "total_queued": sum(depths.values())
    }


@app.post("/scaling/recommend", response_model=ScalingRecommendation)
def get_scaling_recommendation(request: ScalingConfigRequest):
    """
    Get scaling recommendation for a tenant.

    Calculates target replicas based on tier and current queue depth.
    """
    # Parse tenant tier
    try:
        tier = TenantTier(request.tenant_tier.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tenant_tier. Must be one of: premium, standard, free"
        )

    # Get tenant's queue depth (if exists)
    # Note: This endpoint uses tier as input, not tenant_id,
    # so we can't look up actual queue depth without tenant_id
    # For demo purposes, return configuration
    policy = GCCAutoScalingPolicy(tier)
    config = policy.get_scaling_config()

    return ScalingRecommendation(
        current_queue_depth=0,  # Placeholder - need tenant_id for actual depth
        target_replicas=config.min_replicas,
        tenant_tier=tier.value,
        config={
            "min_replicas": config.min_replicas,
            "max_replicas": config.max_replicas,
            "scale_up_cooldown": config.scale_up_cooldown,
            "scale_down_cooldown": config.scale_down_cooldown,
            "resource_quota_percent": config.resource_quota_percent,
            "sla_target": config.sla_target
        }
    )


@app.post("/scaling/validate")
def validate_scaling(
    tenant_tier: str,
    requested_replicas: int,
    total_cluster_capacity: int = 100
):
    """
    Validate if requested replica count is within tenant's resource quota.

    Returns 200 if valid, 400 if quota would be exceeded.
    """
    try:
        tier = TenantTier(tenant_tier.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tenant_tier. Must be one of: premium, standard, free"
        )

    is_valid, message = validate_resource_quota(
        tier,
        requested_replicas,
        total_cluster_capacity
    )

    if not is_valid:
        raise HTTPException(status_code=400, detail=message)

    return {
        "valid": True,
        "message": message,
        "requested_replicas": requested_replicas,
        "quota_percent": (requested_replicas / total_cluster_capacity) * 100
    }


@app.post("/scaling/log-event")
def log_scaling_event(
    tenant_id: str,
    old_replicas: int,
    new_replicas: int,
    reason: str
):
    """
    Log a scaling event for compliance audit trail.

    All scale events must be logged for SOX/DPDPA compliance.
    """
    event = log_scale_event(
        tenant_id=tenant_id,
        old_replicas=old_replicas,
        new_replicas=new_replicas,
        reason=reason
    )

    # Update Prometheus counter
    direction = "up" if new_replicas > old_replicas else "down"
    scaling_events.labels(tenant_id=tenant_id, direction=direction).inc()

    return event


@app.post("/cost/report")
def create_cost_report(request: CostReportRequest):
    """
    Generate per-tenant cost report for CFO chargeback.

    Provides transparent cost attribution based on actual resource usage.
    """
    report = generate_cost_report(
        tenant_id=request.tenant_id,
        avg_replicas=request.avg_replicas,
        peak_replicas=request.peak_replicas,
        budget=request.budget
    )

    return report


@app.get("/metrics")
def metrics():
    """
    Prometheus metrics endpoint.

    This endpoint is scraped by Prometheus every 15 seconds to collect
    tenant_queue_depth metrics that drive HPA scaling decisions.
    """
    # Update all queue depth metrics before scrape
    for tenant_id, depth in queue_manager.get_all_queue_depths().items():
        tenant_queue_depth.labels(tenant_id=tenant_id).set(depth)

    return PlainTextResponse(
        content=generate_latest().decode('utf-8'),
        media_type=CONTENT_TYPE_LATEST
    )


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🚀 Starting L3 M13.2 Auto-Scaling API")

    if REDIS_ENABLED:
        redis_client = CLIENTS.get("redis")
        if redis_client:
            logger.info("âœ" Redis cache available for warm-up state")
        else:
            logger.warning("⚠️ Redis enabled but connection failed")
    else:
        logger.warning("⚠️ Redis disabled - cache functionality unavailable")

    if PROMETHEUS_ENABLED:
        prom_client = CLIENTS.get("prometheus")
        if prom_client:
            logger.info("âœ" Prometheus client available for metrics queries")
        else:
            logger.warning("⚠️ Prometheus enabled but connection failed")
    else:
        logger.warning("⚠️ Prometheus disabled - metrics queries unavailable")

    logger.info("✅ API ready to accept requests")


@app.on_event("shutdown")
async def shutdown_event():
    """Graceful shutdown handling"""
    logger.info("🔄 Shutting down gracefully...")

    # Drain all queues (give 30 seconds)
    logger.info("Draining query queues...")
    total_drained = 0

    for tenant_id in list(queue_manager.queues.keys()):
        depth = queue_manager.get_queue_depth(tenant_id)
        total_drained += depth
        logger.info(f"  {tenant_id}: {depth} queries pending")

    if total_drained > 0:
        logger.warning(
            f"⚠️ {total_drained} queries still pending. "
            "In production, these would be persisted to Redis or database."
        )

    logger.info("✅ Shutdown complete")
