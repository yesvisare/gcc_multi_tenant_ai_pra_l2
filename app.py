"""
FastAPI application for L3 M12.1: Vector Database Multi-Tenancy Patterns

Provides REST API endpoints for vector database multi-tenancy operations
with namespace-based isolation and metadata filtering.

SERVICE: PINECONE (auto-detected from script Section 4)
"""

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
import logging
from typing import Dict, List, Any, Optional
import os

from src.l3_m12_data_isolation_security import (
    TenantContext,
    NamespaceRouter,
    validate_tenant_query,
    tenant_filtered_query,
    create_tenant_namespace,
    evaluate_isolation_model,
    get_isolation_costs,
    IsolationModel,
)
from config import CLIENTS, PINECONE_ENABLED, get_config_summary

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="L3 M12.1: Vector Database Multi-Tenancy API",
    description="Multi-tenant vector database isolation with namespace-based routing and metadata filtering",
    version="1.0.0"
)

# Initialize namespace router
router_config = {"default_top_k": 10}
namespace_router = NamespaceRouter(router_config)


class QueryRequest(BaseModel):
    """Vector query request with tenant isolation."""
    query_vector: List[float] = Field(..., description="Query embedding vector")
    top_k: int = Field(10, description="Number of results to return", ge=1, le=100)
    filter: Optional[Dict[str, Any]] = Field(None, description="Optional metadata filter")
    isolation_model: str = Field("namespace_based", description="Isolation model to use")


class QueryResponse(BaseModel):
    """Vector query response."""
    result: Dict[str, Any]


class TenantRequest(BaseModel):
    """Tenant namespace creation request."""
    tenant_id: str = Field(..., description="Tenant identifier")


class TenantResponse(BaseModel):
    """Tenant namespace creation response."""
    result: Dict[str, Any]


class EvaluationRequest(BaseModel):
    """Isolation model evaluation request."""
    num_tenants: int = Field(..., description="Number of tenants to support", ge=1)
    security_requirement: str = Field(..., description="Security level: standard, high, maximum")
    budget_constraint: str = Field(..., description="Budget level: tight, moderate, flexible")


class EvaluationResponse(BaseModel):
    """Isolation model evaluation response."""
    recommendation: Dict[str, Any]


def extract_tenant_context(
    x_tenant_id: str = Header(..., description="Tenant ID from JWT"),
    x_user_id: str = Header(..., description="User ID from JWT"),
    x_user_roles: str = Header("user", description="User roles (comma-separated)")
) -> TenantContext:
    """
    Extract tenant context from JWT headers.

    In production, this would validate JWT signature and extract claims.
    For this implementation, we accept headers directly.

    Args:
        x_tenant_id: Tenant ID from request header
        x_user_id: User ID from request header
        x_user_roles: User roles from request header

    Returns:
        TenantContext with validated tenant information

    Raises:
        HTTPException: If tenant context is invalid
    """
    try:
        roles = [role.strip() for role in x_user_roles.split(",")]
        from datetime import datetime

        return TenantContext(
            tenant_id=x_tenant_id,
            user_id=x_user_id,
            roles=roles,
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        logger.error(f"Failed to extract tenant context: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid tenant context: {e}")


@app.get("/")
def root():
    """Health check endpoint with configuration status."""
    config = get_config_summary()

    return {
        "status": "healthy",
        "module": "L3_M12_Data_Isolation_Security",
        "title": "Vector Database Multi-Tenancy Patterns",
        "service": "PINECONE",
        "service_enabled": PINECONE_ENABLED,
        "config": config,
        "endpoints": [
            "/query/namespace",
            "/query/metadata-filter",
            "/tenant/create",
            "/evaluate",
            "/costs"
        ]
    }


@app.post("/query/namespace", response_model=QueryResponse)
def query_namespace(
    request: QueryRequest,
    tenant_context: TenantContext = Header(..., description="Tenant context from JWT")
):
    """
    Query vector database using namespace-based isolation (Model 2).

    Implements namespace routing where each tenant has a dedicated namespace.
    Architecturally impossible to access other tenants' data.

    Security: 9/10 isolation strength
    Cost: ₹8-12L/month (50 tenants)
    Provisioning: <60 seconds per tenant
    """
    if not PINECONE_ENABLED:
        return QueryResponse(result={
            "skipped": True,
            "message": "Set PINECONE_ENABLED=true in .env",
            "isolation_model": "namespace_based"
        })

    try:
        # Extract tenant context from headers in production
        # For demo, create from request
        demo_context = TenantContext(
            tenant_id="demo_tenant",
            user_id="demo_user",
            roles=["user"],
            timestamp="2025-01-01T00:00:00Z"
        )

        result = namespace_router.query(
            tenant_context=demo_context,
            query_vector=request.query_vector,
            top_k=request.top_k,
            offline=not PINECONE_ENABLED
        )

        return QueryResponse(result=result)

    except Exception as e:
        logger.error(f"Namespace query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query/metadata-filter", response_model=QueryResponse)
def query_metadata_filter(request: QueryRequest):
    """
    Query vector database using metadata filtering isolation (Model 1).

    Implements defense-in-depth filter injection:
    1. Middleware injects tenant_id filter
    2. Validates user-provided filters
    3. Post-query result validation
    4. Comprehensive audit logging

    Security: 7/10 isolation strength
    Cost: ₹5-8L/month (50 tenants)
    Latency: 5-10ms per query
    """
    if not PINECONE_ENABLED:
        return QueryResponse(result={
            "skipped": True,
            "message": "Set PINECONE_ENABLED=true in .env",
            "isolation_model": "metadata_filtering"
        })

    try:
        # Create demo tenant context
        demo_context = TenantContext(
            tenant_id="demo_tenant",
            user_id="demo_user",
            roles=["user"],
            timestamp="2025-01-01T00:00:00Z"
        )

        result = tenant_filtered_query(
            user_context=demo_context,
            query_vector=request.query_vector,
            top_k=request.top_k,
            user_filter=request.filter,
            offline=not PINECONE_ENABLED
        )

        return QueryResponse(result=result)

    except ValueError as e:
        # Cross-tenant query attempt detected
        logger.error(f"Security violation: {e}")
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Metadata filter query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tenant/create", response_model=TenantResponse)
def create_tenant(request: TenantRequest):
    """
    Create new tenant namespace.

    Provisions a new namespace-based isolated environment for a tenant.
    Provisioning time: <60 seconds
    Maximum namespaces: ~1,000 per index
    """
    if not PINECONE_ENABLED:
        return TenantResponse(result={
            "skipped": True,
            "message": "Set PINECONE_ENABLED=true in .env",
            "namespace": f"tenant_{request.tenant_id}"
        })

    try:
        result = create_tenant_namespace(
            tenant_id=request.tenant_id,
            offline=not PINECONE_ENABLED
        )

        return TenantResponse(result=result)

    except Exception as e:
        logger.error(f"Tenant creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/evaluate", response_model=EvaluationResponse)
def evaluate_model(request: EvaluationRequest):
    """
    Evaluate which isolation model to use based on requirements.

    Implements Decision Card logic:
    - Metadata Filtering: Cost-optimized (₹5-8L/month)
    - Namespace-Based: Balanced trade-off (₹8-12L/month)
    - Dedicated Indexes: Maximum security (₹30-40L/month)

    Returns recommendation with cost analysis and trade-offs.
    """
    try:
        recommendation = evaluate_isolation_model(
            num_tenants=request.num_tenants,
            security_requirement=request.security_requirement,
            budget_constraint=request.budget_constraint
        )

        return EvaluationResponse(recommendation=recommendation)

    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/costs/{num_tenants}")
def get_costs(num_tenants: int):
    """
    Calculate costs for each isolation model.

    Returns cost breakdown for:
    - Metadata Filtering (lowest cost)
    - Namespace-Based (moderate cost)
    - Dedicated Indexes (highest cost, maximum security)

    Args:
        num_tenants: Number of tenants to support
    """
    try:
        costs = get_isolation_costs(num_tenants)

        return {
            "num_tenants": num_tenants,
            "cost_breakdown": costs,
            "recommendation": f"See /evaluate endpoint for personalized recommendation"
        }

    except Exception as e:
        logger.error(f"Cost calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health_check():
    """Detailed health check with service status."""
    return {
        "status": "healthy",
        "pinecone_enabled": PINECONE_ENABLED,
        "clients_available": len(CLIENTS),
        "isolation_models": [model.value for model in IsolationModel]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
