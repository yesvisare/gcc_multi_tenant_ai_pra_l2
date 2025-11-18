"""
FastAPI application for L3 M13.1: Multi-Tenant Performance Patterns

Provides REST API endpoints for tenant-isolated caching with performance tier enforcement.
SERVICE: REDIS (caching infrastructure)
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import logging
from typing import Dict, Any, Optional
import os

from src.l3_m13_performance_patterns import (
    TenantCache,
    PerformanceTierEnforcer,
    execute_cached_query,
    mock_vector_query,
    QuotaExceededError,
    TierViolationError,
    generate_query_hash
)
from config import (
    REDIS_ENABLED,
    OFFLINE,
    init_redis_client,
    get_tenant_tier
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="L3 M13.1: Multi-Tenant Performance Patterns API",
    description="Performance-isolated multi-tenant caching with tier enforcement",
    version="1.0.0"
)

# Global Redis client (initialized on startup)
redis_client = None


# ============================================================================
# STARTUP/SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize Redis client on startup"""
    global redis_client
    redis_client = init_redis_client()

    if redis_client:
        logger.info("âœ" Redis client initialized")
    else:
        logger.warning("âš ï¸ Running without Redis (offline/disabled mode)")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("Redis client closed")


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class QueryRequest(BaseModel):
    """Request model for query endpoint"""
    tenant_id: str = Field(..., description="Tenant identifier")
    query: str = Field(..., description="Query text")


class QueryResponse(BaseModel):
    """Response model for query endpoint"""
    result: Dict[str, Any]
    source: str = Field(..., description="cache or query")
    tenant_id: str
    tier: str
    cached: bool
    latency_ms: Optional[float] = None


class CacheMetricsResponse(BaseModel):
    """Response model for cache metrics"""
    tenant_id: str
    hits: int
    misses: int
    size_gb: float
    key_count: int
    hit_rate: float


class InvalidateRequest(BaseModel):
    """Request model for cache invalidation"""
    tenant_id: str = Field(..., description="Tenant identifier")


class InvalidateResponse(BaseModel):
    """Response model for cache invalidation"""
    tenant_id: str
    deleted_keys: int
    message: str


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "module": "L3_M13_Performance_Patterns",
        "service": "REDIS",
        "redis_enabled": REDIS_ENABLED,
        "offline": OFFLINE
    }


@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    """
    Execute query with tenant-isolated caching and performance tier enforcement.

    - Checks cache first (tenant-namespaced)
    - If miss, executes query with tier-specific timeout
    - Caches result with tier-specific TTL

    If REDIS_ENABLED is false, returns query result without caching.
    """
    import time
    start_time = time.time()

    try:
        # Get tenant tier
        tier = get_tenant_tier(request.tenant_id)

        # Execute with caching
        result = await execute_cached_query(
            query=request.query,
            tenant_id=request.tenant_id,
            tier=tier,
            redis_client=redis_client,
            query_executor=mock_vector_query,
            offline=OFFLINE or not REDIS_ENABLED
        )

        latency_ms = (time.time() - start_time) * 1000

        return QueryResponse(
            result=result["result"],
            source=result["source"],
            tenant_id=result["tenant_id"],
            tier=result["tier"],
            cached=result["cached"],
            latency_ms=round(latency_ms, 2)
        )

    except TierViolationError as e:
        logger.error(f"Tier violation: {e}")
        raise HTTPException(status_code=408, detail=f"Query timeout: {str(e)}")
    except QuotaExceededError as e:
        logger.error(f"Quota exceeded: {e}")
        raise HTTPException(status_code=429, detail=f"Cache quota exceeded: {str(e)}")
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cache/metrics/{tenant_id}", response_model=CacheMetricsResponse)
async def get_cache_metrics(tenant_id: str):
    """
    Get cache metrics for a tenant.

    Returns hit rate, cache size, key count, etc.
    """
    if OFFLINE or not REDIS_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Cache metrics unavailable - Redis disabled"
        )

    try:
        tier = get_tenant_tier(tenant_id)
        cache = TenantCache(tenant_id, tier, redis_client)
        metrics = await cache.get_metrics()

        return CacheMetricsResponse(
            tenant_id=metrics.tenant_id,
            hits=metrics.hits,
            misses=metrics.misses,
            size_gb=metrics.size_gb,
            key_count=metrics.key_count,
            hit_rate=metrics.hit_rate
        )

    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cache/invalidate", response_model=InvalidateResponse)
async def invalidate_cache(request: InvalidateRequest):
    """
    Invalidate all cache entries for a tenant.

    CRITICAL: Only affects the specified tenant's cache - scoped invalidation.
    """
    if OFFLINE or not REDIS_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Cache invalidation unavailable - Redis disabled"
        )

    try:
        tier = get_tenant_tier(request.tenant_id)
        cache = TenantCache(request.tenant_id, tier, redis_client)
        deleted = await cache.invalidate_tenant()

        return InvalidateResponse(
            tenant_id=request.tenant_id,
            deleted_keys=deleted,
            message=f"Invalidated {deleted} keys for tenant {request.tenant_id}"
        )

    except Exception as e:
        logger.error(f"Cache invalidation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tiers/{tenant_id}")
def get_tenant_tier_info(tenant_id: str):
    """
    Get performance tier configuration for a tenant.

    Returns tier name and configuration (timeout, TTL, QPS limit, quota).
    """
    from src.l3_m13_performance_patterns import get_tenant_tier_config

    try:
        tier = get_tenant_tier(tenant_id)
        config = get_tenant_tier_config(tier)

        return {
            "tenant_id": tenant_id,
            "tier": tier,
            "config": {
                "timeout_ms": config.timeout_ms,
                "cache_ttl": config.cache_ttl,
                "max_qps": config.max_qps,
                "cache_quota_gb": config.cache_quota_gb
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get tier info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(QuotaExceededError)
async def quota_exceeded_handler(request: Request, exc: QuotaExceededError):
    """Handle cache quota exceeded errors"""
    return JSONResponse(
        status_code=429,
        content={"error": "quota_exceeded", "message": str(exc)}
    )


@app.exception_handler(TierViolationError)
async def tier_violation_handler(request: Request, exc: TierViolationError):
    """Handle tier SLA timeout violations"""
    return JSONResponse(
        status_code=408,
        content={"error": "tier_violation", "message": str(exc)}
    )


# ============================================================================
# MAIN (for development)
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
