"""
FastAPI application for L3 M12.3: Query Isolation & Rate Limiting

Provides REST API endpoints with per-tenant rate limiting middleware.
Demonstrates production-grade noisy neighbor protection for multi-tenant RAG systems.

Services: Redis (rate limiting), PostgreSQL (tenant registry), Prometheus (metrics)
"""

from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import logging
import time
from typing import Dict, Any, Optional
import os

from src.l3_m12_data_isolation_security import (
    TenantRateLimiter,
    TenantConfigLoader,
    NoisyNeighborMitigator,
    NotificationService,
    TenantTier,
    RateLimitResult
)
from config import CLIENTS, OFFLINE, DEFAULT_RATE_LIMIT_PER_MINUTE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="L3 M12.3: Query Isolation & Rate Limiting",
    description="Production-grade per-tenant rate limiting using Redis token bucket algorithm",
    version="1.0.0"
)

# Initialize services
rate_limiter = TenantRateLimiter(
    redis_client=CLIENTS.get("redis"),
    fallback_limiter=CLIENTS.get("in_memory_limiter")
)
config_loader = TenantConfigLoader(postgres_pool=CLIENTS.get("postgres"))
mitigator = NoisyNeighborMitigator(rate_limiter, config_loader)
notifier = NotificationService(
    slack_webhook=os.getenv("SLACK_WEBHOOK_URL"),
    smtp_config=None  # Configure as needed
)

# Prometheus metrics (if enabled)
metrics = CLIENTS.get("prometheus")


# Request/Response Models
class QueryRequest(BaseModel):
    """Query request with tenant context"""
    query: str = Field(..., min_length=1, max_length=1000)
    tenant_id: Optional[str] = Field(None, description="Tenant identifier (can also use X-Tenant-ID header)")
    metadata: Optional[Dict[str, Any]] = None


class QueryResponse(BaseModel):
    """Query response with rate limit metadata"""
    result: Dict[str, Any]
    rate_limit_info: Dict[str, Any]


class TenantStatsResponse(BaseModel):
    """Tenant usage statistics"""
    tenant_id: str
    current_usage: int
    limit: int
    tier: str
    circuit_broken: bool


# Middleware for rate limiting
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limiting middleware - intercepts all requests before handler execution.

    Checks per-tenant rate limits using Redis token bucket algorithm.
    Returns 429 Too Many Requests if limit exceeded.
    """
    # Skip rate limiting for health check
    if request.url.path == "/" or request.url.path == "/health":
        return await call_next(request)

    # Extract tenant_id from header or query param
    tenant_id = request.headers.get("X-Tenant-ID") or request.query_params.get("tenant_id")

    if not tenant_id:
        return JSONResponse(
            status_code=400,
            content={"error": "Missing tenant_id in X-Tenant-ID header or query parameter"}
        )

    # Get tenant config
    try:
        config = await config_loader.get_config(tenant_id)
    except Exception as e:
        logger.error(f"Failed to load config for {tenant_id}: {e}")
        # Use default limit
        limit = DEFAULT_RATE_LIMIT_PER_MINUTE
        config = None

    # Check circuit breaker
    if mitigator.is_circuit_broken(tenant_id):
        return JSONResponse(
            status_code=503,
            content={
                "error": "Service temporarily unavailable",
                "reason": "Circuit breaker engaged due to excessive usage",
                "tenant_id": tenant_id,
                "retry_after_seconds": 300
            },
            headers={"Retry-After": "300"}
        )

    # Check rate limit
    limit = config.queries_per_minute if config else DEFAULT_RATE_LIMIT_PER_MINUTE
    result: RateLimitResult = rate_limiter.check_limit(tenant_id, limit)

    # Update Prometheus metrics
    if metrics:
        tier_label = config.tier.value if config else "unknown"
        metrics["query_total"].labels(tenant_id=tenant_id, tier=tier_label).inc()

        if not result.allowed:
            metrics["query_blocked"].labels(tenant_id=tenant_id, reason="rate_limit").inc()

    # Rate limit exceeded
    if not result.allowed:
        logger.warning(f"⚠️ Rate limit exceeded for {tenant_id}: {result.current_usage}/{result.limit}")

        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "tenant_id": tenant_id,
                "current_usage": result.current_usage,
                "limit": result.limit,
                "retry_after_seconds": result.retry_after_seconds
            },
            headers={"Retry-After": str(result.retry_after_seconds or 60)}
        )

    # Check for noisy neighbor behavior
    if config:
        is_noisy, severity = mitigator.check_noisy_neighbor(
            tenant_id,
            baseline=config.queries_per_minute,
            current=result.current_usage
        )

        if is_noisy:
            # Apply mitigation
            mitigation = await mitigator.apply_mitigation(tenant_id, severity)

            # Send notification
            await notifier.send_rate_limit_alert(
                tenant_id,
                severity,
                {
                    "action": mitigation["action"],
                    "current_usage": result.current_usage,
                    "limit": limit
                }
            )

    # Process request
    start_time = time.time()
    response = await call_next(request)
    latency = time.time() - start_time

    # Update latency metrics
    if metrics:
        metrics["query_latency"].labels(tenant_id=tenant_id).observe(latency)

    # Add rate limit headers
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(max(0, limit - result.current_usage))
    response.headers["X-RateLimit-Reset"] = str(60 - (int(time.time()) % 60))

    return response


# API Endpoints
@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "module": "L3_M12_Data_Isolation_Security",
        "version": "1.0.0",
        "services": {
            "redis": CLIENTS.get("redis") is not None,
            "postgres": CLIENTS.get("postgres") is not None,
            "prometheus": CLIENTS.get("prometheus") is not None
        },
        "offline_mode": OFFLINE
    }


@app.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
):
    """
    Process a query with rate limiting.

    Rate limiting is enforced by middleware before this handler executes.
    If you see this response, the rate limit check passed.
    """
    tenant_id = request.tenant_id or x_tenant_id

    if not tenant_id:
        raise HTTPException(status_code=400, detail="Missing tenant_id")

    # Simulate query processing
    logger.info(f"Processing query for {tenant_id}: {request.query[:50]}...")

    # Get current rate limit info
    config = await config_loader.get_config(tenant_id)
    current_usage = rate_limiter.get_current_usage(tenant_id)

    result = {
        "query": request.query,
        "tenant_id": tenant_id,
        "processed_at": time.time(),
        "message": "Query processed successfully (rate limit passed)"
    }

    rate_limit_info = {
        "current_usage": current_usage,
        "limit": config.queries_per_minute if config else DEFAULT_RATE_LIMIT_PER_MINUTE,
        "tier": config.tier.value if config else "unknown",
        "remaining": max(0, (config.queries_per_minute if config else DEFAULT_RATE_LIMIT_PER_MINUTE) - current_usage)
    }

    return QueryResponse(result=result, rate_limit_info=rate_limit_info)


@app.get("/tenant/{tenant_id}/stats", response_model=TenantStatsResponse)
async def get_tenant_stats(tenant_id: str):
    """Get current usage statistics for a tenant"""
    try:
        config = await config_loader.get_config(tenant_id)
        current_usage = rate_limiter.get_current_usage(tenant_id)
        circuit_broken = mitigator.is_circuit_broken(tenant_id)

        return TenantStatsResponse(
            tenant_id=tenant_id,
            current_usage=current_usage,
            limit=config.queries_per_minute,
            tier=config.tier.value,
            circuit_broken=circuit_broken
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@app.post("/admin/mitigate/{tenant_id}")
async def manual_mitigation(tenant_id: str, severity: str = "high", duration: int = 300):
    """
    Manually trigger mitigation for a tenant (admin endpoint).

    Args:
        tenant_id: Tenant to mitigate
        severity: 'high' (50% reduction) or 'critical' (circuit breaker)
        duration: Duration in seconds (default 300 = 5 minutes)
    """
    if severity not in ["high", "critical"]:
        raise HTTPException(status_code=400, detail="Severity must be 'high' or 'critical'")

    try:
        mitigation = await mitigator.apply_mitigation(tenant_id, severity, duration)

        # Send notification
        config = await config_loader.get_config(tenant_id)
        await notifier.send_rate_limit_alert(
            tenant_id,
            severity,
            {
                "action": mitigation["action"],
                "current_usage": rate_limiter.get_current_usage(tenant_id),
                "limit": config.queries_per_minute,
                "manual_trigger": True
            }
        )

        return mitigation
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mitigation failed: {str(e)}")


@app.post("/admin/refresh-config")
async def refresh_tenant_configs():
    """Refresh tenant configuration cache (admin endpoint)"""
    try:
        await config_loader.refresh_cache()
        return {"status": "success", "message": "Tenant configs refreshed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refresh failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
