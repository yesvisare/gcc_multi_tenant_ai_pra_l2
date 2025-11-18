"""
FastAPI application for L3 M11.3: Database Isolation & Cross-Tenant Security

Provides REST API endpoints for:
- PostgreSQL RLS queries
- Pinecone namespace queries
- Cross-tenant security testing
- Audit log retrieval

All endpoints require tenant_id (in production: from JWT, not query params).
"""

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
import logging
import os
import uuid
from typing import Dict, Any, List, Optional

from src.l3_m11_multi_tenant_foundations import (
    PostgresRLSManager,
    PineconeNamespaceManager,
    SeparateDatabaseManager,
    TenantContextManager,
    CrossTenantSecurityTests,
    AuditLogger,
    RedisIsolationManager,
    S3PrefixIsolationManager
)
from config import CLIENTS, POSTGRES_ENABLED, PINECONE_ENABLED, REDIS_ENABLED, AWS_ENABLED

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="L3 M11.3: Multi-Tenant Isolation API",
    description="Defense-in-depth multi-tenant isolation with RLS, namespace, and separate DB strategies",
    version="1.0.0"
)

# Initialize managers
tenant_context_mgr = TenantContextManager()
audit_logger = AuditLogger()

# Initialize isolation managers based on available services
postgres_mgr = None
if POSTGRES_ENABLED and CLIENTS.get("postgres"):
    postgres_mgr = PostgresRLSManager(CLIENTS["postgres"])

pinecone_mgr = None
if PINECONE_ENABLED and CLIENTS.get("pinecone"):
    index_name = os.getenv("PINECONE_INDEX", "multi-tenant-rag")
    pinecone_mgr = PineconeNamespaceManager(CLIENTS["pinecone"], index_name)

redis_mgr = None
if REDIS_ENABLED and CLIENTS.get("redis"):
    redis_mgr = RedisIsolationManager(CLIENTS["redis"])

s3_mgr = None
if AWS_ENABLED and CLIENTS.get("aws", {}).get("s3"):
    bucket = os.getenv("AWS_S3_BUCKET", "multi-tenant-docs")
    s3_mgr = S3PrefixIsolationManager(CLIENTS["aws"]["s3"], bucket)

separate_db_mgr = SeparateDatabaseManager()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class QueryRequest(BaseModel):
    """Request model for document queries."""
    tenant_id: str = Field(..., description="Tenant UUID (in production: from JWT)")
    search_pattern: str = Field(..., description="Search pattern for document titles")


class VectorQueryRequest(BaseModel):
    """Request model for vector queries."""
    tenant_id: str = Field(..., description="Tenant UUID")
    query_vector: List[float] = Field(..., description="Query embedding vector")
    top_k: int = Field(5, description="Number of results")


class SecurityTestRequest(BaseModel):
    """Request model for security tests."""
    tenant_ids: List[str] = Field(..., description="List of tenant UUIDs to test")


class CacheRequest(BaseModel):
    """Request model for cache operations."""
    tenant_id: str = Field(..., description="Tenant UUID")
    key: str = Field(..., description="Cache key")
    value: Optional[str] = Field(None, description="Cache value (for set operation)")
    ttl: int = Field(3600, description="Time to live in seconds")


class DocumentQueryResponse(BaseModel):
    """Response model for document queries."""
    documents: List[Dict[str, Any]]
    tenant_id: str
    strategy: str
    count: int


class StatusResponse(BaseModel):
    """Response model for health check."""
    status: str
    module: str
    services_enabled: Dict[str, bool]


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/", response_model=StatusResponse)
def root():
    """Health check endpoint."""
    return StatusResponse(
        status="healthy",
        module="L3_M11.3_Multi_Tenant_Foundations",
        services_enabled={
            "postgres": POSTGRES_ENABLED,
            "pinecone": PINECONE_ENABLED,
            "redis": REDIS_ENABLED,
            "aws": AWS_ENABLED
        }
    )


@app.post("/query/rls", response_model=DocumentQueryResponse)
def query_with_rls(request: QueryRequest):
    """
    Query documents using PostgreSQL RLS strategy.

    Security: RLS policies enforce tenant_id filtering automatically.
    Isolation: 99.9%
    """
    if not POSTGRES_ENABLED or postgres_mgr is None:
        raise HTTPException(
            status_code=503,
            detail="PostgreSQL not enabled. Set POSTGRES_ENABLED=true in .env"
        )

    try:
        tenant_id = uuid.UUID(request.tenant_id)

        # Set tenant context
        tenant_context_mgr.set_tenant_context(tenant_id)

        # Query with RLS enforcement
        documents = postgres_mgr.query_documents(tenant_id, request.search_pattern)

        # Audit log
        audit_logger.log_access(
            tenant_id=tenant_id,
            user_id="api_user",
            action="query_rls",
            resource="documents",
            result="success"
        )

        return DocumentQueryResponse(
            documents=documents,
            tenant_id=str(tenant_id),
            strategy="PostgreSQL RLS",
            count=len(documents)
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid tenant_id: {e}")
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        tenant_context_mgr.clear_tenant_context()


@app.post("/query/namespace")
def query_with_namespace(request: VectorQueryRequest):
    """
    Query vectors using Pinecone namespace isolation strategy.

    Security: Namespace parameter enforces isolation at vector store level.
    Isolation: 99.95%
    """
    if not PINECONE_ENABLED or pinecone_mgr is None:
        raise HTTPException(
            status_code=503,
            detail="Pinecone not enabled. Set PINECONE_ENABLED=true in .env"
        )

    try:
        tenant_id = uuid.UUID(request.tenant_id)

        # Set tenant context
        tenant_context_mgr.set_tenant_context(tenant_id)

        # Query with namespace enforcement
        results = pinecone_mgr.query_vectors(
            tenant_id=tenant_id,
            query_vector=request.query_vector,
            top_k=request.top_k
        )

        # Audit log
        audit_logger.log_access(
            tenant_id=tenant_id,
            user_id="api_user",
            action="query_namespace",
            resource="vectors",
            result="success"
        )

        return {
            "results": results,
            "tenant_id": str(tenant_id),
            "strategy": "Pinecone Namespace",
            "count": len(results.get("matches", []))
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid tenant_id: {e}")
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        tenant_context_mgr.clear_tenant_context()


@app.post("/query/separate-db", response_model=DocumentQueryResponse)
def query_separate_database(request: QueryRequest):
    """
    Query documents using separate database strategy.

    Security: Physical database separation - no shared resources.
    Isolation: 99.999%
    """
    try:
        tenant_id = uuid.UUID(request.tenant_id)

        # Set tenant context
        tenant_context_mgr.set_tenant_context(tenant_id)

        # Query tenant's dedicated database
        documents = separate_db_mgr.query_documents(tenant_id, request.search_pattern)

        # Audit log
        audit_logger.log_access(
            tenant_id=tenant_id,
            user_id="api_user",
            action="query_separate_db",
            resource="documents",
            result="success"
        )

        return DocumentQueryResponse(
            documents=documents,
            tenant_id=str(tenant_id),
            strategy="Separate Database",
            count=len(documents)
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid tenant_id or database not provisioned: {e}")
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        tenant_context_mgr.clear_tenant_context()


@app.post("/security/test")
def run_security_tests(request: SecurityTestRequest):
    """
    Run cross-tenant security tests.

    Tests: 1,000+ adversarial queries attempting to breach isolation.
    """
    if not POSTGRES_ENABLED or postgres_mgr is None:
        raise HTTPException(
            status_code=503,
            detail="Security tests require PostgreSQL. Enable in .env"
        )

    try:
        tenant_ids = [uuid.UUID(tid) for tid in request.tenant_ids]

        # Run security tests
        security_tester = CrossTenantSecurityTests(postgres_mgr)
        results = security_tester.run_adversarial_tests(tenant_ids)

        return {
            "test_results": results,
            "summary": f"{results['passed']}/{results['total_tests']} tests passed",
            "isolation_effective": results["failed"] == 0
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid tenant_id: {e}")
    except Exception as e:
        logger.error(f"Security tests failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cache/set")
def set_cache(request: CacheRequest):
    """
    Set cache value with tenant isolation (key prefixing).

    Pattern: tenant:{uuid}:{key}
    """
    if not REDIS_ENABLED or redis_mgr is None:
        raise HTTPException(
            status_code=503,
            detail="Redis not enabled. Set REDIS_ENABLED=true in .env"
        )

    try:
        tenant_id = uuid.UUID(request.tenant_id)

        if not request.value:
            raise HTTPException(status_code=400, detail="Value required for set operation")

        success = redis_mgr.set_cache(tenant_id, request.key, request.value, request.ttl)

        return {
            "success": success,
            "tenant_id": str(tenant_id),
            "key": request.key,
            "ttl": request.ttl
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid tenant_id: {e}")
    except Exception as e:
        logger.error(f"Cache set failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cache/get")
def get_cache(tenant_id: str, key: str):
    """
    Get cache value with tenant isolation.

    Query params:
        tenant_id: Tenant UUID
        key: Cache key
    """
    if not REDIS_ENABLED or redis_mgr is None:
        raise HTTPException(
            status_code=503,
            detail="Redis not enabled. Set REDIS_ENABLED=true in .env"
        )

    try:
        tid = uuid.UUID(tenant_id)
        value = redis_mgr.get_cache(tid, key)

        return {
            "tenant_id": str(tid),
            "key": key,
            "value": value,
            "found": value is not None
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid tenant_id: {e}")
    except Exception as e:
        logger.error(f"Cache get failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/audit/logs")
def get_audit_logs(tenant_id: Optional[str] = None):
    """
    Get audit logs, optionally filtered by tenant.

    Query params:
        tenant_id: Optional tenant UUID to filter by
    """
    try:
        if tenant_id:
            tid = uuid.UUID(tenant_id)
            logs = audit_logger.get_audit_trail(tid)
        else:
            logs = audit_logger.get_audit_trail()

        return {
            "logs": logs,
            "count": len(logs),
            "filtered_by_tenant": tenant_id is not None
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid tenant_id: {e}")
    except Exception as e:
        logger.error(f"Audit log retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
