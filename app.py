"""
FastAPI application for L3 M14.3: Tenant Lifecycle & Migrations

Provides REST API endpoints for:
- Zero-downtime blue-green migrations
- GDPR Article 17 compliant data deletion
- Per-tenant backup and restore
- Tenant cloning for staging/testing
- Migration rollback with sub-second execution
- Data consistency verification

SERVICE: Infrastructure orchestration (PostgreSQL, Redis, Celery, Pinecone, S3)
Default mode: OFFLINE (runs without external dependencies)
"""

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import logging
import os
from datetime import datetime

from src.l3_m14_tenant_lifecycle import (
    migrate_tenant_blue_green,
    execute_gdpr_deletion,
    create_tenant_backup,
    restore_tenant_backup,
    clone_tenant,
    rollback_migration,
    verify_data_consistency,
    verify_gdpr_deletion,
)
from config import OFFLINE, CLIENTS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="L3 M14.3: Tenant Lifecycle & Migrations API",
    description="Zero-downtime migrations, GDPR deletion, backup/restore, and tenant cloning for multi-tenant RAG systems",
    version="1.0.0"
)


# Request/Response Models

class MigrationRequest(BaseModel):
    """Request model for blue-green migration"""
    tenant_id: str = Field(..., description="Unique tenant identifier")
    source_env: str = Field(..., description="Source environment name (e.g., 'blue')")
    target_env: str = Field(..., description="Target environment name (e.g., 'green')")


class GDPRDeletionRequest(BaseModel):
    """Request model for GDPR deletion"""
    tenant_id: str = Field(..., description="Unique tenant identifier")
    request_id: str = Field(..., description="Deletion request UUID")


class BackupRequest(BaseModel):
    """Request model for tenant backup"""
    tenant_id: str = Field(..., description="Unique tenant identifier")
    retention_days: int = Field(90, description="Days to retain backup")
    cross_region: bool = Field(False, description="Enable cross-region replication")


class RestoreRequest(BaseModel):
    """Request model for tenant restore"""
    backup_id: str = Field(..., description="Backup identifier to restore from")
    tenant_id: str = Field(..., description="Tenant to restore")
    point_in_time: Optional[str] = Field(None, description="ISO timestamp for point-in-time recovery")


class CloneRequest(BaseModel):
    """Request model for tenant cloning"""
    source_tenant_id: str = Field(..., description="Original tenant ID")
    target_tenant_id: str = Field(..., description="New cloned tenant ID")
    anonymize_data: bool = Field(True, description="Anonymize PII during clone")
    selective_sync: Optional[List[str]] = Field(None, description="Data types to include (None = all)")


class RollbackRequest(BaseModel):
    """Request model for migration rollback"""
    tenant_id: str = Field(..., description="Tenant to rollback")
    rollback_snapshot: str = Field(..., description="Backup ID to restore from")


class ConsistencyCheckRequest(BaseModel):
    """Request model for data consistency verification"""
    tenant_id: str = Field(..., description="Tenant to verify")
    source_env: str = Field(..., description="Source environment name")
    target_env: str = Field(..., description="Target environment name")


class VerifyDeletionRequest(BaseModel):
    """Request model for GDPR deletion verification"""
    tenant_id: str = Field(..., description="Tenant to verify deletion for")
    systems: List[str] = Field(..., description="List of system names to check")


class OperationResponse(BaseModel):
    """Generic response model for operations"""
    status: str
    data: Dict[str, Any]


# API Endpoints

@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "module": "L3_M14_Tenant_Lifecycle_Migrations",
        "offline_mode": OFFLINE,
        "available_endpoints": [
            "/migrate",
            "/gdpr-delete",
            "/backup",
            "/restore",
            "/clone",
            "/rollback",
            "/verify-consistency",
            "/verify-deletion"
        ]
    }


@app.get("/health")
def health_check():
    """Detailed health check with infrastructure status"""
    infrastructure_status = {
        "postgres": CLIENTS.get("postgres") is not None,
        "redis": CLIENTS.get("redis") is not None,
        "celery": CLIENTS.get("celery") is not None,
        "pinecone": CLIENTS.get("pinecone") is not None,
        "s3": CLIENTS.get("s3") is not None
    }

    return {
        "status": "healthy",
        "offline_mode": OFFLINE,
        "infrastructure": infrastructure_status,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/migrate", response_model=OperationResponse)
def migrate_tenant(request: MigrationRequest):
    """
    Execute zero-downtime blue-green migration for a tenant.

    Implements six-phase migration with gradual traffic cutover.
    If OFFLINE mode is enabled, returns simulated response.
    """
    logger.info(f"Migration request: {request.tenant_id} ({request.source_env} → {request.target_env})")

    try:
        result = migrate_tenant_blue_green(
            tenant_id=request.tenant_id,
            source_env=request.source_env,
            target_env=request.target_env,
            offline=OFFLINE
        )

        return OperationResponse(status="success", data=result)

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/gdpr-delete", response_model=OperationResponse)
def gdpr_delete_tenant(request: GDPRDeletionRequest):
    """
    Execute GDPR Article 17 compliant data deletion across all systems.

    Deletes data from: PostgreSQL, Redis, Pinecone, S3, CloudWatch, backups, analytics.
    Generates cryptographically signed deletion certificate.
    """
    logger.info(f"GDPR deletion request: {request.tenant_id}, request_id={request.request_id}")

    try:
        result = execute_gdpr_deletion(
            tenant_id=request.tenant_id,
            request_id=request.request_id,
            offline=OFFLINE
        )

        return OperationResponse(status="success", data=result)

    except ValueError as e:
        logger.error(f"Validation error (legal hold?): {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"GDPR deletion failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/backup", response_model=OperationResponse)
def backup_tenant(request: BackupRequest):
    """
    Create per-tenant backup with point-in-time recovery capability.

    Backs up: PostgreSQL, Redis, Pinecone, S3.
    Optional cross-region replication for disaster recovery.
    """
    logger.info(f"Backup request: {request.tenant_id}, retention={request.retention_days} days")

    try:
        result = create_tenant_backup(
            tenant_id=request.tenant_id,
            retention_days=request.retention_days,
            cross_region=request.cross_region,
            offline=OFFLINE
        )

        return OperationResponse(status="success", data=result)

    except Exception as e:
        logger.error(f"Backup creation failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/restore", response_model=OperationResponse)
def restore_tenant(request: RestoreRequest):
    """
    Restore tenant from backup with optional point-in-time recovery.

    Validates schema compatibility before restoration.
    Verifies restore integrity after completion.
    """
    logger.info(f"Restore request: {request.tenant_id} from backup {request.backup_id}")

    try:
        # Parse point_in_time if provided
        point_in_time = None
        if request.point_in_time:
            point_in_time = datetime.fromisoformat(request.point_in_time)

        result = restore_tenant_backup(
            backup_id=request.backup_id,
            tenant_id=request.tenant_id,
            point_in_time=point_in_time,
            offline=OFFLINE
        )

        return OperationResponse(status="success", data=result)

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/clone", response_model=OperationResponse)
def clone_tenant_endpoint(request: CloneRequest):
    """
    Clone tenant for staging/testing with optional data anonymization.

    Use cases:
    - Create staging environment for testing
    - Duplicate tenant configuration
    - Anonymize production data for development

    PII is anonymized by default to prevent data leakage.
    """
    logger.info(f"Clone request: {request.source_tenant_id} → {request.target_tenant_id}")

    try:
        result = clone_tenant(
            source_tenant_id=request.source_tenant_id,
            target_tenant_id=request.target_tenant_id,
            anonymize_data=request.anonymize_data,
            selective_sync=request.selective_sync,
            offline=OFFLINE
        )

        return OperationResponse(status="success", data=result)

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Clone failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/rollback", response_model=OperationResponse)
def rollback_migration_endpoint(request: RollbackRequest):
    """
    Rollback failed migration to previous state with sub-second execution.

    Immediately routes traffic back to source environment.
    Restores from rollback snapshot for data consistency.
    Target: <60 second rollback time.
    """
    logger.info(f"Rollback request: {request.tenant_id} to snapshot {request.rollback_snapshot}")

    try:
        result = rollback_migration(
            tenant_id=request.tenant_id,
            rollback_snapshot=request.rollback_snapshot,
            offline=OFFLINE
        )

        return OperationResponse(status="success", data=result)

    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/verify-consistency", response_model=OperationResponse)
def verify_consistency_endpoint(request: ConsistencyCheckRequest):
    """
    Verify data consistency between source and target environments using checksums.

    Checks: PostgreSQL, Redis, Pinecone, S3.
    Returns list of differences if inconsistent.
    """
    logger.info(f"Consistency check: {request.tenant_id} ({request.source_env} vs {request.target_env})")

    try:
        result = verify_data_consistency(
            tenant_id=request.tenant_id,
            source_env=request.source_env,
            target_env=request.target_env,
            offline=OFFLINE
        )

        return OperationResponse(status="success", data=result)

    except Exception as e:
        logger.error(f"Consistency verification failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/verify-deletion", response_model=OperationResponse)
def verify_deletion_endpoint(request: VerifyDeletionRequest):
    """
    Verify complete GDPR deletion across all systems.

    Returns per-system deletion status and overall completeness.
    Critical for GDPR compliance audit trail.
    """
    logger.info(f"Deletion verification: {request.tenant_id} across {len(request.systems)} systems")

    try:
        result = verify_gdpr_deletion(
            tenant_id=request.tenant_id,
            systems=request.systems,
            offline=OFFLINE
        )

        return OperationResponse(status="success", data=result)

    except Exception as e:
        logger.error(f"Deletion verification failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
