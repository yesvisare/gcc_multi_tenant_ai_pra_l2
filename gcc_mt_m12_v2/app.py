"""
FastAPI application for L3 M12.2: Document Storage & Access Control

Provides REST API endpoints for multi-tenant document storage operations.
SERVICE: AWS_S3 (auto-detected from script Section 4)

Endpoints:
- GET / : Health check and service status
- POST /documents/upload : Upload document for tenant
- GET /documents/{doc_key}/download : Download document
- DELETE /documents/{doc_key} : Delete document
- GET /documents/list : List all tenant documents
- POST /documents/presigned-url : Generate presigned URL
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Header, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
import logging
from typing import Dict, Any, Optional, List
import os
from uuid import UUID

from src.l3_m12_document_storage import (
    TenantS3Client,
    PresignedURLService,
    DataResidencyValidator,
    StorageAuditLogger,
    DocumentNotFound,
    Forbidden,
    DataResidencyViolation
)
from config import REDIS_CLIENT, DB_CONNECTION, get_service_status

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="L3 M12.2: Document Storage & Access Control",
    description="Multi-tenant document storage with S3 isolation models, presigned URLs, and data residency enforcement",
    version="1.0.0"
)

# Initialize services
presigned_url_service = PresignedURLService(redis_client=REDIS_CLIENT)
residency_validator = DataResidencyValidator()
audit_logger = StorageAuditLogger(db_connection=DB_CONNECTION)

# Check if AWS S3 is enabled
AWS_S3_ENABLED = os.getenv("AWS_S3_ENABLED", "false").lower() == "true"


# Pydantic models
class UploadResponse(BaseModel):
    """Response model for document upload"""
    filename: str
    s3_location: str
    tenant_id: str
    status: str = "uploaded"


class PresignedURLRequest(BaseModel):
    """Request model for presigned URL generation"""
    doc_key: str = Field(..., description="Document key (without tenant prefix)")
    expiration: Optional[int] = Field(300, description="URL expiration in seconds", ge=60, le=3600)


class PresignedURLResponse(BaseModel):
    """Response model for presigned URL"""
    presigned_url: str
    expires_in: int
    tenant_id: str


class DocumentListResponse(BaseModel):
    """Response model for document listing"""
    tenant_id: str
    documents: List[str]
    count: int


class StatusResponse(BaseModel):
    """Response model for service status"""
    status: str
    module: str
    services: Dict[str, Any]


# Helper function to extract tenant ID from headers
def get_tenant_id(x_tenant_id: str = Header(..., description="Tenant identifier")) -> str:
    """
    Extract and validate tenant ID from request headers.

    In production, this would integrate with authentication middleware
    to verify the user has access to the specified tenant.
    """
    return x_tenant_id


@app.get("/", response_model=StatusResponse)
def root():
    """
    Health check endpoint.

    Returns service status and configuration.
    """
    services = get_service_status()

    return StatusResponse(
        status="healthy",
        module="L3_M12_Data_Isolation_Security",
        services=services
    )


@app.post("/documents/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(..., description="Document to upload"),
    tenant_id: str = Header(..., alias="X-Tenant-ID", description="Tenant identifier"),
    region: Optional[str] = Query(None, description="AWS region override")
):
    """
    Upload document for tenant with automatic prefix isolation.

    Security:
    - Document automatically prefixed with tenant-{id}/
    - Data residency validated before upload
    - Object tagged with tenant_id
    - Encrypted with tenant-specific KMS key

    Headers:
        X-Tenant-ID: Tenant identifier (required)

    Query Parameters:
        region: Optional AWS region override (must match tenant residency)

    Returns:
        Upload confirmation with S3 location
    """
    if not AWS_S3_ENABLED:
        return UploadResponse(
            filename=file.filename,
            s3_location=f"s3://offline/{tenant_id}/{file.filename}",
            tenant_id=tenant_id,
            status="skipped (AWS_S3_ENABLED not set)"
        )

    try:
        # Validate data residency if region specified
        if region:
            residency_validator.validate_upload(tenant_id, region_override=region)

        # Initialize tenant-scoped client
        client = TenantS3Client(tenant_id, region=region)

        # Read file data
        file_data = await file.read()

        # Upload with metadata
        s3_url = client.upload(
            file.filename,
            file_data,
            metadata={'filename': file.filename, 'content_type': file.content_type}
        )

        # Audit log
        audit_logger.log_access('upload', tenant_id, file.filename, status='success')

        logger.info(f"✓ Uploaded {file.filename} for tenant {tenant_id}")

        return UploadResponse(
            filename=file.filename,
            s3_location=s3_url,
            tenant_id=tenant_id,
            status="uploaded"
        )

    except DataResidencyViolation as e:
        logger.error(f"✗ Data residency violation: {e}")
        audit_logger.log_access('upload', tenant_id, file.filename, status='residency_violation')
        raise HTTPException(status_code=403, detail=str(e))

    except Exception as e:
        logger.error(f"✗ Upload failed: {e}")
        audit_logger.log_access('upload', tenant_id, file.filename, status='failed', error=str(e))
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/documents/{doc_key}/download")
async def download_document(
    doc_key: str,
    tenant_id: str = Header(..., alias="X-Tenant-ID", description="Tenant identifier")
):
    """
    Download document for tenant.

    Security:
    - Validates document belongs to tenant via prefix check
    - Audit logs download access

    Headers:
        X-Tenant-ID: Tenant identifier (required)

    Returns:
        Binary document data
    """
    if not AWS_S3_ENABLED:
        return Response(
            content=b"offline-mode-placeholder",
            media_type="application/octet-stream",
            headers={"X-Status": "offline-mode"}
        )

    try:
        # Initialize tenant-scoped client
        client = TenantS3Client(tenant_id)

        # Download with prefix validation
        data = client.download(doc_key)

        # Audit log
        audit_logger.log_access('download', tenant_id, doc_key, status='success')

        logger.info(f"✓ Downloaded {doc_key} for tenant {tenant_id}")

        return Response(
            content=data,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={doc_key}"}
        )

    except DocumentNotFound as e:
        logger.error(f"✗ Document not found: {e}")
        audit_logger.log_access('download', tenant_id, doc_key, status='not_found')
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        logger.error(f"✗ Download failed: {e}")
        audit_logger.log_access('download', tenant_id, doc_key, status='failed', error=str(e))
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@app.delete("/documents/{doc_key}")
async def delete_document(
    doc_key: str,
    tenant_id: str = Header(..., alias="X-Tenant-ID", description="Tenant identifier")
):
    """
    Delete document for tenant.

    Security:
    - Validates document belongs to tenant via prefix check
    - Audit logs deletion

    Headers:
        X-Tenant-ID: Tenant identifier (required)

    Returns:
        Deletion confirmation
    """
    if not AWS_S3_ENABLED:
        return {"status": "skipped", "message": "AWS_S3_ENABLED not set"}

    try:
        # Initialize tenant-scoped client
        client = TenantS3Client(tenant_id)

        # Delete with prefix validation
        client.delete(doc_key)

        # Audit log
        audit_logger.log_access('delete', tenant_id, doc_key, status='success')

        logger.info(f"✓ Deleted {doc_key} for tenant {tenant_id}")

        return {
            "status": "deleted",
            "doc_key": doc_key,
            "tenant_id": tenant_id
        }

    except DocumentNotFound as e:
        logger.error(f"✗ Document not found: {e}")
        audit_logger.log_access('delete', tenant_id, doc_key, status='not_found')
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        logger.error(f"✗ Delete failed: {e}")
        audit_logger.log_access('delete', tenant_id, doc_key, status='failed', error=str(e))
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@app.get("/documents/list", response_model=DocumentListResponse)
async def list_documents(
    tenant_id: str = Header(..., alias="X-Tenant-ID", description="Tenant identifier"),
    prefix: str = Query("", description="Optional sub-prefix filter")
):
    """
    List all documents for tenant.

    Security:
    - Only lists documents under tenant prefix
    - Audit logs list operation

    Headers:
        X-Tenant-ID: Tenant identifier (required)

    Query Parameters:
        prefix: Optional sub-prefix within tenant namespace

    Returns:
        List of document keys (without tenant prefix)
    """
    if not AWS_S3_ENABLED:
        return DocumentListResponse(
            tenant_id=tenant_id,
            documents=["example-doc1.pdf", "example-doc2.pdf"],
            count=2
        )

    try:
        # Initialize tenant-scoped client
        client = TenantS3Client(tenant_id)

        # List with prefix validation
        documents = client.list_documents(prefix=prefix)

        # Audit log
        audit_logger.log_access('list', tenant_id, f"prefix={prefix}", status='success')

        logger.info(f"✓ Listed {len(documents)} documents for tenant {tenant_id}")

        return DocumentListResponse(
            tenant_id=tenant_id,
            documents=documents,
            count=len(documents)
        )

    except Exception as e:
        logger.error(f"✗ List failed: {e}")
        audit_logger.log_access('list', tenant_id, f"prefix={prefix}", status='failed', error=str(e))
        raise HTTPException(status_code=500, detail=f"List failed: {str(e)}")


@app.post("/documents/presigned-url", response_model=PresignedURLResponse)
async def generate_presigned_url(
    request: PresignedURLRequest,
    tenant_id: str = Header(..., alias="X-Tenant-ID", description="Tenant identifier")
):
    """
    Generate presigned URL for direct S3 access.

    CRITICAL SECURITY:
    - Validates document belongs to tenant BEFORE generating URL
    - Checks object tags match tenant_id
    - Short expiration (5 minutes default)
    - Audit logs URL generation

    Headers:
        X-Tenant-ID: Tenant identifier (required)

    Returns:
        Presigned URL with expiration time
    """
    if not AWS_S3_ENABLED:
        return PresignedURLResponse(
            presigned_url=f"https://offline-mode.s3.amazonaws.com/{tenant_id}/{request.doc_key}",
            expires_in=request.expiration,
            tenant_id=tenant_id
        )

    try:
        # Build full S3 key with tenant prefix
        full_key = f"tenant-{tenant_id}/{request.doc_key}"

        # Generate presigned URL with validation
        url = presigned_url_service.generate_url(
            tenant_id,
            full_key,
            expiration=request.expiration
        )

        # Audit log
        audit_logger.log_access('presigned_url', tenant_id, request.doc_key,
                               status='success')

        logger.info(f"✓ Generated presigned URL for {request.doc_key} (tenant {tenant_id})")

        return PresignedURLResponse(
            presigned_url=url,
            expires_in=request.expiration,
            tenant_id=tenant_id
        )

    except Forbidden as e:
        logger.error(f"✗ Forbidden: {e}")
        audit_logger.log_access('presigned_url', tenant_id, request.doc_key,
                               status='forbidden')
        raise HTTPException(status_code=403, detail=str(e))

    except DocumentNotFound as e:
        logger.error(f"✗ Document not found: {e}")
        audit_logger.log_access('presigned_url', tenant_id, request.doc_key,
                               status='not_found')
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        logger.error(f"✗ Presigned URL generation failed: {e}")
        audit_logger.log_access('presigned_url', tenant_id, request.doc_key,
                               status='failed', error=str(e))
        raise HTTPException(status_code=500, detail=f"URL generation failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
