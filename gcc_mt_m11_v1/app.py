"""
FastAPI application for L3 M11.1: Multi-Tenant RAG Architecture

Provides REST API endpoints for multi-tenant RAG operations:
- Tenant management (create, list, update, delete)
- Document ingestion with tenant isolation
- RAG query with namespace enforcement
- Audit log retrieval

Services: PINECONE (vector DB), OPENAI (embeddings/LLM)
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, Optional, List
import logging
import os

from src.l3_m11_multi_tenant_foundations import (
    TenantRegistry,
    VectorDBIsolation,
    set_current_tenant,
    get_current_tenant,
    TenantContextManager,
)
from config import (
    PINECONE_ENABLED,
    OPENAI_ENABLED,
    OFFLINE,
    check_services_available,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Multi-Tenant RAG API",
    description="Production multi-tenant RAG system with namespace isolation and cost attribution",
    version="1.0.0"
)

# In-memory storage for offline mode
tenant_registry = TenantRegistry()
vector_db = VectorDBIsolation()


# Pydantic models
class TenantCreateRequest(BaseModel):
    """Request model for creating a tenant."""
    tenant_id: str
    tenant_name: str
    tier: str = 'standard'
    isolation_model: str = 'shared-db'
    admin_email: EmailStr


class TenantResponse(BaseModel):
    """Response model for tenant information."""
    tenant_id: str
    tenant_name: str
    tier: str
    status: str
    isolation_model: str
    admin_email: str
    created_at: str


class DocumentIngestRequest(BaseModel):
    """Request model for document ingestion."""
    documents: List[Dict[str, Any]]


class QueryRequest(BaseModel):
    """Request model for RAG query."""
    query: str
    top_k: int = 5


class QueryResponse(BaseModel):
    """Response model for RAG query results."""
    tenant_id: str
    query: str
    results: List[Dict[str, Any]]
    skipped: Optional[bool] = False
    message: Optional[str] = None


# Dependency for extracting tenant_id from header
def get_tenant_id_from_header(x_tenant_id: Optional[str] = Header(None)) -> str:
    """
    Extract tenant_id from X-Tenant-Id header.

    In production, this would extract from JWT or API key.
    For simplicity in offline mode, we use a custom header.

    Args:
        x_tenant_id: Tenant identifier from header

    Returns:
        Tenant identifier

    Raises:
        HTTPException: If header missing or tenant not found
    """
    if not x_tenant_id:
        raise HTTPException(
            status_code=401,
            detail="Missing X-Tenant-Id header"
        )

    # Validate tenant exists
    tenant = tenant_registry.get_tenant(x_tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=404,
            detail=f"Tenant {x_tenant_id} not found"
        )

    if tenant['status'] != 'active':
        raise HTTPException(
            status_code=403,
            detail=f"Tenant {x_tenant_id} is {tenant['status']}"
        )

    # Set in context for async propagation
    set_current_tenant(x_tenant_id)

    return x_tenant_id


@app.get("/")
def root():
    """
    Health check endpoint.

    Returns:
        Service status and configuration
    """
    services = check_services_available()

    return {
        "status": "healthy",
        "module": "L3_M11_Multi_Tenant_Foundations",
        "services": {
            "pinecone_enabled": PINECONE_ENABLED,
            "pinecone_available": services["pinecone"],
            "openai_enabled": OPENAI_ENABLED,
            "openai_available": services["openai"],
            "offline": OFFLINE
        },
        "isolation_models": ["shared-db", "shared-schema", "separate-db", "hybrid"],
        "tiers": ["premium", "standard", "trial"]
    }


@app.post("/tenants", response_model=TenantResponse, status_code=201)
def create_tenant(request: TenantCreateRequest):
    """
    Create a new tenant with infrastructure provisioning.

    Args:
        request: Tenant creation parameters

    Returns:
        Created tenant information

    Raises:
        HTTPException: If tenant creation fails
    """
    try:
        tenant = tenant_registry.create_tenant(
            tenant_id=request.tenant_id,
            tenant_name=request.tenant_name,
            tier=request.tier,
            isolation_model=request.isolation_model,
            admin_email=request.admin_email
        )

        # Provision vector namespace
        vector_db.provision_tenant_namespace(request.tenant_id)

        logger.info(f"Tenant created: {request.tenant_id}")

        return TenantResponse(**tenant)

    except ValueError as e:
        logger.error(f"Tenant creation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating tenant: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/tenants/{tenant_id}", response_model=TenantResponse)
def get_tenant(tenant_id: str):
    """
    Retrieve tenant information by ID.

    Args:
        tenant_id: Tenant identifier

    Returns:
        Tenant information

    Raises:
        HTTPException: If tenant not found
    """
    tenant = tenant_registry.get_tenant(tenant_id)

    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")

    return TenantResponse(**tenant)


@app.patch("/tenants/{tenant_id}/status")
def update_tenant_status(tenant_id: str, new_status: str):
    """
    Update tenant status (active, suspended, archived).

    Args:
        tenant_id: Tenant identifier
        new_status: New status value

    Returns:
        Updated tenant information

    Raises:
        HTTPException: If update fails
    """
    try:
        tenant = tenant_registry.update_tenant_status(tenant_id, new_status)
        logger.info(f"Tenant {tenant_id} status updated to {new_status}")
        return TenantResponse(**tenant)

    except ValueError as e:
        logger.error(f"Status update failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/tenants/{tenant_id}", status_code=204)
def delete_tenant(tenant_id: str):
    """
    Soft delete tenant (GDPR compliance).

    Args:
        tenant_id: Tenant identifier

    Raises:
        HTTPException: If deletion fails
    """
    try:
        tenant_registry.soft_delete_tenant(tenant_id)
        vector_db.delete_tenant_namespace(tenant_id)
        logger.info(f"Tenant {tenant_id} soft deleted")

    except ValueError as e:
        logger.error(f"Tenant deletion failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/documents")
def ingest_documents(
    request: DocumentIngestRequest,
    tenant_id: str = Depends(get_tenant_id_from_header)
):
    """
    Ingest documents for a tenant with namespace isolation.

    Args:
        request: Document ingestion parameters
        tenant_id: Tenant identifier from header

    Returns:
        Ingestion status

    Raises:
        HTTPException: If ingestion fails
    """
    try:
        # Verify tenant context is set
        current_tenant = get_current_tenant()
        assert current_tenant == tenant_id, "Tenant context mismatch"

        vector_db.upsert_documents_for_tenant(
            tenant_id=tenant_id,
            documents=request.documents
        )

        logger.info(f"Ingested {len(request.documents)} documents for tenant: {tenant_id}")

        return {
            "status": "success",
            "tenant_id": tenant_id,
            "document_count": len(request.documents)
        }

    except Exception as e:
        logger.error(f"Document ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse)
def query_rag(
    request: QueryRequest,
    tenant_id: str = Depends(get_tenant_id_from_header)
):
    """
    Query RAG system with tenant isolation.

    If PINECONE or OPENAI not enabled, returns skipped response.

    Args:
        request: Query parameters
        tenant_id: Tenant identifier from header

    Returns:
        Query results with tenant isolation
    """
    # Check if services are enabled
    if OFFLINE or (not PINECONE_ENABLED and not OPENAI_ENABLED):
        return QueryResponse(
            tenant_id=tenant_id,
            query=request.query,
            results=[],
            skipped=True,
            message="Services disabled - set PINECONE_ENABLED=true and OPENAI_ENABLED=true in .env"
        )

    try:
        # Verify tenant context
        current_tenant = get_current_tenant()
        assert current_tenant == tenant_id, "Tenant context mismatch"

        # In production, generate embedding with OpenAI
        # For offline mode, use placeholder vector
        query_embedding = [0.1] * 1536

        # Query vectors with namespace isolation
        results = vector_db.query_vectors_for_tenant(
            tenant_id=tenant_id,
            query_embedding=query_embedding,
            top_k=request.top_k
        )

        logger.info(f"Query executed for tenant {tenant_id}: {request.query}")

        return QueryResponse(
            tenant_id=tenant_id,
            query=request.query,
            results=results
        )

    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/audit-logs")
def get_audit_logs(tenant_id: str = Depends(get_tenant_id_from_header)):
    """
    Retrieve audit logs for tenant.

    Args:
        tenant_id: Tenant identifier from header

    Returns:
        Filtered audit logs for tenant
    """
    # Filter audit logs by tenant_id
    tenant_logs = [
        log for log in tenant_registry.audit_logs
        if log['tenant_id'] == tenant_id
    ]

    return {
        "tenant_id": tenant_id,
        "log_count": len(tenant_logs),
        "logs": tenant_logs
    }


@app.exception_handler(ValueError)
def value_error_handler(request, exc):
    """Handle ValueError exceptions."""
    return JSONResponse(
        status_code=400,
        content={"error": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
