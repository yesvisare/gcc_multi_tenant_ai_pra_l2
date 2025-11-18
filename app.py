"""
FastAPI entrypoint for L3 M11.2: Tenant Metadata & Registry Design

Provides REST API for tenant registry operations including:
- Tenant CRUD (create, read, update, delete)
- Feature flag management and evaluation
- Lifecycle state transitions
- Cascading operations
- Health monitoring
"""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging

from src.l3_m11_multi_tenant_foundations import (
    TenantRegistry,
    TenantStatus,
    Tenant,
    FeatureFlag,
)
import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="L3 M11.2 - Tenant Registry API",
    description="Production-ready tenant metadata and registry system for multi-tenant RAG platforms",
    version="1.0.0"
)

# Initialize registry
registry = TenantRegistry()

# Initialize database config
config.check_database_connection()


# Pydantic models for request/response validation
class TenantCreate(BaseModel):
    """Request model for tenant creation."""
    tenant_id: str = Field(..., description="Unique tenant identifier", example="finance_dept")
    tenant_name: str = Field(..., description="Tenant display name", example="Finance Department")
    tier: str = Field(..., description="Service tier (platinum/gold/silver/bronze)", example="gold")
    max_users: int = Field(default=10, description="Maximum concurrent users", example=100)
    max_documents: int = Field(default=1000, description="Maximum document storage limit", example=50000)
    max_queries_per_day: int = Field(default=1000, description="Daily query quota", example=10000)
    sla_target: float = Field(default=0.99, description="SLA uptime target (0-1)", example=0.999)
    support_level: str = Field(default="email-only", description="Support tier", example="24/7")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class TenantUpdate(BaseModel):
    """Request model for tenant updates."""
    tenant_name: Optional[str] = Field(None, description="Updated tenant name")
    tier: Optional[str] = Field(None, description="Updated service tier")
    max_users: Optional[int] = Field(None, description="Updated max users")
    max_documents: Optional[int] = Field(None, description="Updated max documents")
    max_queries_per_day: Optional[int] = Field(None, description="Updated daily quota")
    sla_target: Optional[float] = Field(None, description="Updated SLA target")
    support_level: Optional[str] = Field(None, description="Updated support level")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")


class TenantResponse(BaseModel):
    """Response model for tenant data."""
    tenant_id: str
    tenant_name: str
    tier: str
    status: str
    max_users: int
    max_documents: int
    max_queries_per_day: int
    sla_target: float
    support_level: str
    health_score: int
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]


class FeatureFlagCreate(BaseModel):
    """Request model for feature flag creation."""
    feature_name: str = Field(..., description="Feature flag name", example="advanced_analytics")
    enabled: bool = Field(..., description="Whether feature is enabled", example=True)
    scope: str = Field(..., description="Scope level (tenant/tier/global)", example="tier")
    scope_id: Optional[str] = Field(None, description="Scope identifier (tenant_id or tier)", example="platinum")
    description: str = Field(default="", description="Feature description", example="Advanced analytics dashboard")


class FeatureFlagResponse(BaseModel):
    """Response model for feature flag data."""
    feature_name: str
    enabled: bool
    scope: str
    scope_id: Optional[str]


class LifecycleTransition(BaseModel):
    """Request model for lifecycle state transitions."""
    new_status: str = Field(..., description="Target lifecycle status", example="suspended")
    reason: str = Field(default="", description="Reason for transition", example="Non-payment")


class HealthMetrics(BaseModel):
    """Request model for health score calculation."""
    latency_p95: float = Field(default=0.0, description="P95 API latency in ms", example=350.5)
    error_rate: float = Field(default=0.0, description="Error rate (0-1)", example=0.01)
    query_success_rate: float = Field(default=1.0, description="Query success rate (0-1)", example=0.98)
    storage_utilization: float = Field(default=0.0, description="Storage utilization (0-1)", example=0.75)


# API Endpoints

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "active",
        "module": "L3_M11_Multi_Tenant_Foundations",
        "version": "1.0.0",
        "description": "Tenant Registry & Metadata Management",
        "database_config": "PostgreSQL + Redis (demo mode)"
    }


@app.get("/health")
async def health_check():
    """Detailed health check with registry statistics."""
    stats = registry.get_statistics()
    return {
        "status": "healthy",
        "registry": stats,
        "database": {
            "postgresql": "configured",
            "redis": "configured"
        }
    }


# Tenant CRUD Operations

@app.post("/tenants", response_model=TenantResponse, status_code=201)
async def create_tenant(tenant_data: TenantCreate):
    """
    Create a new tenant.

    Creates a tenant with complete metadata including tier, limits, and SLA targets.
    """
    try:
        tenant = registry.create_tenant(tenant_data.dict())
        return TenantResponse(**tenant.to_dict())
    except ValueError as e:
        logger.error(f"Tenant creation validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Tenant creation error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(tenant_id: str):
    """
    Retrieve tenant by ID.

    Returns complete tenant metadata including current status and health score.
    """
    tenant = registry.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant not found: {tenant_id}")
    return TenantResponse(**tenant.to_dict())


@app.get("/tenants", response_model=List[TenantResponse])
async def list_tenants(
    status: Optional[str] = Query(None, description="Filter by status"),
    tier: Optional[str] = Query(None, description="Filter by tier"),
    min_health_score: Optional[int] = Query(None, description="Minimum health score")
):
    """
    List all tenants with optional filtering.

    Supports filtering by status, tier, and minimum health score.
    """
    try:
        status_enum = TenantStatus(status) if status else None
        tenants = registry.list_tenants(
            status=status_enum,
            tier=tier,
            min_health_score=min_health_score
        )
        return [TenantResponse(**t.to_dict()) for t in tenants]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid filter value: {e}")


@app.put("/tenants/{tenant_id}", response_model=TenantResponse)
async def update_tenant(tenant_id: str, updates: TenantUpdate):
    """
    Update tenant attributes.

    Allows updating tier, limits, SLA targets, and metadata.
    """
    try:
        # Filter out None values
        update_dict = {k: v for k, v in updates.dict().items() if v is not None}

        if not update_dict:
            raise HTTPException(status_code=400, detail="No valid updates provided")

        tenant = registry.update_tenant(tenant_id, update_dict)
        return TenantResponse(**tenant.to_dict())
    except ValueError as e:
        logger.error(f"Tenant update error: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Tenant update error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.delete("/tenants/{tenant_id}")
async def delete_tenant(tenant_id: str):
    """
    Delete tenant (must be in DELETED status).

    Permanently removes tenant from registry. Tenant must be transitioned to
    DELETED status before removal (compliance requirement).
    """
    try:
        registry.delete_tenant(tenant_id)
        return {"message": f"Tenant {tenant_id} deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Lifecycle Management

@app.post("/tenants/{tenant_id}/transition")
async def transition_tenant(tenant_id: str, transition: LifecycleTransition):
    """
    Transition tenant to new lifecycle state.

    Validates transition against state machine rules before executing.
    """
    try:
        tenant = registry.get_tenant(tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail=f"Tenant not found: {tenant_id}")

        new_status = TenantStatus(transition.new_status)
        registry.lifecycle_manager.transition(tenant, new_status, transition.reason)

        return {
            "tenant_id": tenant_id,
            "previous_status": tenant.status.value,
            "new_status": new_status.value,
            "reason": transition.reason
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/tenants/{tenant_id}/suspend")
async def suspend_tenant(tenant_id: str, reason: str = ""):
    """
    Suspend tenant with cascading operations.

    Propagates suspension across PostgreSQL, Vector DB, S3, Redis, and Monitoring.
    """
    try:
        result = registry.suspend_tenant(tenant_id, reason)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Suspension error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/tenants/{tenant_id}/activate")
async def activate_tenant(tenant_id: str, reason: str = ""):
    """
    Activate tenant with cascading operations.

    Propagates activation across all systems.
    """
    try:
        result = registry.activate_tenant(tenant_id, reason)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Activation error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/tenants/{tenant_id}/valid-transitions")
async def get_valid_transitions(tenant_id: str):
    """
    Get valid lifecycle transitions for tenant's current state.

    Returns list of allowed target states.
    """
    tenant = registry.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant not found: {tenant_id}")

    valid_transitions = registry.lifecycle_manager.get_valid_transitions(tenant.status)

    return {
        "tenant_id": tenant_id,
        "current_status": tenant.status.value,
        "valid_transitions": valid_transitions
    }


# Feature Flag Management

@app.post("/feature-flags", response_model=FeatureFlagResponse, status_code=201)
async def create_feature_flag(flag_data: FeatureFlagCreate):
    """
    Create or update a feature flag.

    Supports tenant-level, tier-level, and global scope.
    """
    try:
        flag = FeatureFlag(**flag_data.dict())
        registry.feature_service.set_flag(flag)
        return FeatureFlagResponse(
            feature_name=flag.feature_name,
            enabled=flag.enabled,
            scope=flag.scope,
            scope_id=flag.scope_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/feature-flags")
async def list_feature_flags(
    scope: Optional[str] = Query(None, description="Filter by scope"),
    scope_id: Optional[str] = Query(None, description="Filter by scope ID")
):
    """
    List all feature flags with optional filtering.

    Supports filtering by scope (tenant/tier/global) and scope_id.
    """
    flags = registry.feature_service.list_flags(scope=scope, scope_id=scope_id)
    return {"flags": flags}


@app.get("/feature-flags/{tenant_id}/{feature_name}")
async def evaluate_feature_flag(tenant_id: str, feature_name: str):
    """
    Evaluate feature flag for specific tenant.

    Uses hierarchical evaluation: tenant override > tier default > global default.
    """
    tenant = registry.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant not found: {tenant_id}")

    enabled = registry.feature_service.evaluate(tenant_id, feature_name, tenant.tier)

    return {
        "tenant_id": tenant_id,
        "feature_name": feature_name,
        "enabled": enabled,
        "evaluation_hierarchy": "tenant > tier > global"
    }


# Health Monitoring

@app.post("/tenants/{tenant_id}/health")
async def update_health_score(tenant_id: str, metrics: HealthMetrics):
    """
    Calculate and update tenant health score.

    Computes score from latency, error rate, query success rate, and storage utilization.
    """
    tenant = registry.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant not found: {tenant_id}")

    health_score = registry.health_monitor.calculate_health_score(
        tenant_id=tenant_id,
        latency_p95=metrics.latency_p95,
        error_rate=metrics.error_rate,
        query_success_rate=metrics.query_success_rate,
        storage_utilization=metrics.storage_utilization
    )

    # Update tenant health score
    tenant.update_health_score(health_score)

    return {
        "tenant_id": tenant_id,
        "health_score": health_score,
        "metrics": metrics.dict()
    }


@app.get("/tenants/{tenant_id}/health")
async def get_health_metrics(tenant_id: str):
    """
    Retrieve cached health metrics for tenant.

    Returns last calculated health score and contributing metrics.
    """
    metrics = registry.health_monitor.get_metrics(tenant_id)
    if not metrics:
        raise HTTPException(status_code=404, detail=f"No health metrics found for {tenant_id}")

    return metrics


# Registry Statistics

@app.get("/statistics")
async def get_registry_statistics():
    """
    Get registry-wide statistics.

    Returns tenant counts by status and tier, plus average health score.
    """
    return registry.get_statistics()


# Audit Log

@app.get("/audit-log")
async def get_audit_log(tenant_id: Optional[str] = Query(None, description="Filter by tenant ID")):
    """
    Retrieve audit log entries.

    Returns log of all cascading operations with optional tenant filter.
    """
    log_entries = registry.cascade_ops.get_audit_log(tenant_id=tenant_id)
    return {
        "total_entries": len(log_entries),
        "entries": log_entries
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
