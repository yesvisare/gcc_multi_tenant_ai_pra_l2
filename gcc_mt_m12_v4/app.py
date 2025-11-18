"""
FastAPI application for L3 M12.4: Compliance Boundaries & Data Governance

Provides REST API endpoints for:
- Creating/managing per-tenant compliance configurations
- Initiating GDPR Article 17 data deletion requests
- Managing legal holds
- Retrieving compliance audit trail

Services: Pinecone (vector DB), AWS S3/CloudFront, Redis, PostgreSQL
"""

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import logging
import os
from datetime import datetime

from src.l3_m12_compliance_boundaries import (
    TenantComplianceConfig,
    ComplianceDeletionService,
    DeletionRequest,
    RegulationType,
    DataResidency,
    create_compliance_config,
    execute_scheduled_deletion,
    check_legal_hold,
)
from config import get_clients, get_system_config, PINECONE_ENABLED, AWS_ENABLED, OFFLINE_MODE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="L3 M12.4: Compliance Boundaries & Data Governance API",
    description="""
    Multi-tenant compliance management system for RAG applications.

    Features:
    - Per-tenant compliance configuration (GDPR, CCPA, DPDPA, SOX, HIPAA, etc.)
    - Automated data deletion with 30-day SLA
    - Legal hold protection
    - Immutable audit trail (7-10 year retention)
    - Multi-system cascade deletion (vector DB, S3, PostgreSQL, Redis, logs, backups, CDN)

    Services:
    - Pinecone: Vector database deletion
    - AWS S3/CloudFront: Cloud storage deletion
    - Redis: Cache invalidation
    - PostgreSQL: Compliance config & audit trail
    """,
    version="1.0.0",
)

# In-memory storage for demo (production would use PostgreSQL)
COMPLIANCE_CONFIGS: Dict[str, TenantComplianceConfig] = {}
DELETION_REQUESTS: Dict[str, DeletionRequest] = {}


# ===== REQUEST/RESPONSE MODELS =====

class ComplianceConfigCreate(BaseModel):
    """Request model for creating tenant compliance configuration"""

    tenant_id: str = Field(..., description="Unique tenant identifier")
    tenant_name: str = Field(..., min_length=1, max_length=255)
    tenant_email: EmailStr = Field(..., description="Contact email for compliance notifications")
    regulations: List[str] = Field(
        ...,
        description="Applicable regulations (GDPR, CCPA, DPDPA, SOX, HIPAA, PCI-DSS, FINRA)",
    )
    retention_days: int = Field(..., ge=1, le=3650, description="Data retention period (1-3650 days / 10 years max)")
    data_residency: str = Field(..., description="Geographic constraint (EU, US, IN, GLOBAL)")
    encryption_required: bool = Field(default=True)
    encryption_standard: str = Field(default="AES-256")
    audit_retention_days: int = Field(default=2555, ge=2555, description="Audit trail retention (min 2555 days / 7 years)")
    auto_delete_enabled: bool = Field(default=True, description="Enable scheduled deletion")
    compliance_metadata: Optional[Dict[str, Any]] = Field(default=None)

    class Config:
        schema_extra = {
            "example": {
                "tenant_id": "tenant_a_001",
                "tenant_name": "ACME Corp EU Division",
                "tenant_email": "dpo@acme.eu",
                "regulations": ["GDPR", "SOX"],
                "retention_days": 90,
                "data_residency": "EU",
                "encryption_required": True,
                "encryption_standard": "AES-256",
                "audit_retention_days": 2555,
                "auto_delete_enabled": True,
                "compliance_metadata": {"gdpr_dpo_contact": "dpo@acme.eu"},
            }
        }


class ComplianceConfigResponse(BaseModel):
    """Response model for compliance configuration"""

    tenant_id: str
    tenant_name: str
    tenant_email: str
    regulations: List[str]
    retention_days: int
    data_residency: str
    encryption_required: bool
    encryption_standard: str
    audit_retention_days: int
    auto_delete_enabled: bool
    legal_hold_active: bool
    legal_hold_reason: Optional[str]
    legal_hold_start_date: Optional[str]
    compliance_metadata: Dict[str, Any]
    created_at: str
    updated_at: str


class LegalHoldUpdate(BaseModel):
    """Request model for updating legal hold status"""

    legal_hold_active: bool = Field(..., description="Activate/deactivate legal hold")
    legal_hold_reason: Optional[str] = Field(None, max_length=500, description="Justification for legal hold")

    class Config:
        schema_extra = {
            "example": {
                "legal_hold_active": True,
                "legal_hold_reason": "Litigation: Smith vs. ACME Corp (Case #2024-CV-12345)",
            }
        }


class DeletionRequestCreate(BaseModel):
    """Request model for initiating data deletion"""

    user_id: str = Field(..., description="User identifier whose data to delete")
    request_type: str = Field(default="gdpr_article_17", description="Deletion request type")

    class Config:
        schema_extra = {
            "example": {
                "user_id": "user_123456",
                "request_type": "gdpr_article_17",
            }
        }


class DeletionRequestResponse(BaseModel):
    """Response model for deletion request"""

    request_id: str
    tenant_id: str
    user_id: str
    request_type: str
    requested_at: str
    status: str
    message: str


# ===== API ENDPOINTS =====

@app.get("/")
def root():
    """Health check endpoint with service status"""
    clients = get_clients()

    return {
        "status": "healthy",
        "module": "L3_M12_Compliance_Boundaries_Data_Governance",
        "version": "1.0.0",
        "services": {
            "pinecone_enabled": PINECONE_ENABLED,
            "pinecone_available": clients.get("pinecone") is not None,
            "aws_enabled": AWS_ENABLED,
            "aws_s3_available": clients.get("s3") is not None,
            "aws_cloudfront_available": clients.get("cloudfront") is not None,
            "redis_available": clients.get("redis") is not None,
            "offline_mode": OFFLINE_MODE,
        },
        "total_tenants": len(COMPLIANCE_CONFIGS),
        "total_deletion_requests": len(DELETION_REQUESTS),
    }


@app.post(
    "/api/v1/compliance/tenants",
    response_model=ComplianceConfigResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_tenant_compliance_config(request: ComplianceConfigCreate):
    """
    Create per-tenant compliance configuration.

    Sets up retention policies, data residency constraints, and regulatory
    requirements for a tenant.

    **IMPORTANT:** Consult Legal Team before setting retention policies.
    """
    try:
        # Validate regulations
        for reg in request.regulations:
            if reg not in [r.value for r in RegulationType]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid regulation: {reg}. Must be one of: {[r.value for r in RegulationType]}",
                )

        # Validate data residency
        if request.data_residency not in [d.value for d in DataResidency]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid data_residency: {request.data_residency}. Must be one of: {[d.value for d in DataResidency]}",
            )

        # Check if tenant already exists
        if request.tenant_id in COMPLIANCE_CONFIGS:
            raise HTTPException(
                status_code=409,
                detail=f"Compliance config for tenant {request.tenant_id} already exists",
            )

        # Create config
        config = create_compliance_config(
            tenant_id=request.tenant_id,
            tenant_name=request.tenant_name,
            tenant_email=request.tenant_email,
            regulations=request.regulations,
            retention_days=request.retention_days,
            data_residency=request.data_residency,
            encryption_required=request.encryption_required,
            encryption_standard=request.encryption_standard,
            audit_retention_days=request.audit_retention_days,
            auto_delete_enabled=request.auto_delete_enabled,
            compliance_metadata=request.compliance_metadata,
        )

        # Store in-memory (production: save to PostgreSQL)
        COMPLIANCE_CONFIGS[request.tenant_id] = config

        logger.info(f"✓ Created compliance config for tenant {request.tenant_id}")

        return ComplianceConfigResponse(**config.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to create compliance config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/api/v1/compliance/tenants/{tenant_id}",
    response_model=ComplianceConfigResponse,
)
def get_tenant_compliance_config(tenant_id: str):
    """
    Retrieve compliance configuration for a tenant.
    """
    if tenant_id not in COMPLIANCE_CONFIGS:
        raise HTTPException(
            status_code=404,
            detail=f"Compliance config for tenant {tenant_id} not found",
        )

    config = COMPLIANCE_CONFIGS[tenant_id]
    return ComplianceConfigResponse(**config.to_dict())


@app.patch(
    "/api/v1/compliance/tenants/{tenant_id}/legal-hold",
    response_model=ComplianceConfigResponse,
)
def update_legal_hold(tenant_id: str, request: LegalHoldUpdate):
    """
    Update legal hold status for a tenant.

    **CRITICAL:** Legal holds prevent data deletion during litigation/investigation.
    Consult Legal Counsel before activating/deactivating.

    When legal_hold_active=True:
    - All scheduled deletion is BLOCKED
    - Manual deletion requests are REJECTED
    - Data preserved for legal proceedings

    Unauthorized deactivation may constitute evidence destruction (federal crime).
    """
    if tenant_id not in COMPLIANCE_CONFIGS:
        raise HTTPException(
            status_code=404,
            detail=f"Compliance config for tenant {tenant_id} not found",
        )

    config = COMPLIANCE_CONFIGS[tenant_id]
    config.legal_hold_active = request.legal_hold_active
    config.legal_hold_reason = request.legal_hold_reason
    config.legal_hold_start_date = datetime.utcnow() if request.legal_hold_active else None
    config.updated_at = datetime.utcnow()

    logger.warning(
        f"🚨 Legal hold {'ACTIVATED' if request.legal_hold_active else 'DEACTIVATED'} "
        f"for tenant {tenant_id}: {request.legal_hold_reason}"
    )

    return ComplianceConfigResponse(**config.to_dict())


@app.post(
    "/api/v1/tenants/{tenant_id}/data/delete",
    response_model=DeletionRequestResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def initiate_deletion_request(tenant_id: str, request: DeletionRequestCreate):
    """
    Initiate GDPR Article 17 (Right to Erasure) data deletion request.

    **30-day SLA:** Deletion must complete within 30 days of request (GDPR requirement).

    Workflow:
    1. Check legal hold - REJECT if active
    2. Create deletion request (unique ID)
    3. Queue for scheduled deletion (runs daily at 2am UTC)
    4. Cascade delete across 7 systems (vector DB, S3, PostgreSQL, Redis, logs, backups, CDN)
    5. Verify deletion 48 hours post-deletion
    6. Log to immutable audit trail

    If services are disabled (PINECONE_ENABLED=false, AWS_ENABLED=false), returns
    skipped response.
    """
    # Check if tenant exists
    if tenant_id not in COMPLIANCE_CONFIGS:
        raise HTTPException(
            status_code=404,
            detail=f"Compliance config for tenant {tenant_id} not found. Create config first.",
        )

    compliance_config = COMPLIANCE_CONFIGS[tenant_id]

    # Check legal hold
    legal_hold_active, legal_hold_reason = check_legal_hold(tenant_id, compliance_config)
    if legal_hold_active:
        raise HTTPException(
            status_code=403,
            detail=f"Deletion BLOCKED: Legal hold active - {legal_hold_reason}",
        )

    # Create deletion request
    request_id = f"del_{tenant_id}_{request.user_id}_{int(datetime.utcnow().timestamp())}"
    deletion_request = DeletionRequest(
        request_id=request_id,
        tenant_id=tenant_id,
        user_id=request.user_id,
        request_type=request.request_type,
    )

    # Store request
    DELETION_REQUESTS[request_id] = deletion_request

    # Check if services are available
    clients = get_clients()
    if not any([clients.get("pinecone"), clients.get("s3"), clients.get("redis")]):
        logger.warning(f"⚠️ No external services available - deletion will be skipped")
        return DeletionRequestResponse(
            request_id=request_id,
            tenant_id=tenant_id,
            user_id=request.user_id,
            request_type=request.request_type,
            requested_at=deletion_request.requested_at.isoformat(),
            status="skipped",
            message="Services disabled. Set PINECONE_ENABLED=true and/or AWS_ENABLED=true in .env",
        )

    # Initialize deletion service
    deletion_service = ComplianceDeletionService(
        pinecone_client=clients.get("pinecone"),
        s3_client=clients.get("s3"),
        redis_client=clients.get("redis"),
        db_session=clients.get("db_session"),
        cloudfront_client=clients.get("cloudfront"),
        offline_mode=OFFLINE_MODE,
    )

    # Execute deletion (in production, this would be queued for scheduled job)
    system_config = get_system_config()
    deletion_result = execute_scheduled_deletion(
        tenant_id=tenant_id,
        compliance_config=compliance_config,
        deletion_service=deletion_service,
        config=system_config,
    )

    # Update deletion request status
    if deletion_result.get("skipped"):
        status_msg = "skipped"
        message = deletion_result["reason"]
    elif deletion_result.get("all_systems_succeeded"):
        status_msg = "completed"
        message = "Deletion completed successfully across all systems"
    else:
        status_msg = "partial"
        message = "Deletion completed with some failures - check results"

    logger.info(f"Deletion request {request_id}: {status_msg} - {message}")

    return DeletionRequestResponse(
        request_id=request_id,
        tenant_id=tenant_id,
        user_id=request.user_id,
        request_type=request.request_type,
        requested_at=deletion_request.requested_at.isoformat(),
        status=status_msg,
        message=message,
    )


@app.get("/api/v1/deletion-requests/{request_id}")
def get_deletion_request_status(request_id: str):
    """
    Retrieve status of a deletion request.
    """
    if request_id not in DELETION_REQUESTS:
        raise HTTPException(
            status_code=404,
            detail=f"Deletion request {request_id} not found",
        )

    deletion_request = DELETION_REQUESTS[request_id]
    return deletion_request.to_dict()


@app.get("/health")
def health_check():
    """Detailed health check endpoint"""
    clients = get_clients()

    health_status = {
        "status": "healthy" if any(clients.values()) else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "pinecone": {
                "enabled": PINECONE_ENABLED,
                "available": clients.get("pinecone") is not None,
                "status": "healthy" if clients.get("pinecone") else "unavailable",
            },
            "aws_s3": {
                "enabled": AWS_ENABLED,
                "available": clients.get("s3") is not None,
                "status": "healthy" if clients.get("s3") else "unavailable",
            },
            "aws_cloudfront": {
                "enabled": AWS_ENABLED,
                "available": clients.get("cloudfront") is not None,
                "status": "healthy" if clients.get("cloudfront") else "unavailable",
            },
            "redis": {
                "available": clients.get("redis") is not None,
                "status": "healthy" if clients.get("redis") else "unavailable",
            },
        },
        "offline_mode": OFFLINE_MODE,
        "data": {
            "total_tenants": len(COMPLIANCE_CONFIGS),
            "total_deletion_requests": len(DELETION_REQUESTS),
        },
    }

    return health_status
