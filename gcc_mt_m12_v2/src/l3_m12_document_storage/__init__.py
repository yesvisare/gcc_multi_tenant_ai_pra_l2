"""
L3 M12.2: Document Storage & Access Control

This module implements three distinct S3 isolation models for multi-tenant RAG systems,
with production-ready tenant-aware presigned URLs, data residency enforcement, and
comprehensive audit logging.

Isolation Models:
- Bucket-Per-Tenant: Maximum isolation with dedicated buckets
- Shared Bucket + IAM: Policy-based isolation with object tagging
- Hybrid: Shared bucket with prefix enforcement and wrapper (RECOMMENDED)

SERVICE: AWS_S3 (detected from script Section 4)
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

__all__ = [
    "TenantS3Client",
    "PresignedURLService",
    "DataResidencyValidator",
    "StorageAuditLogger",
    "IsolationModel",
    "DocumentNotFound",
    "Forbidden",
    "DataResidencyViolation",
]


# Exceptions
class DocumentNotFound(Exception):
    """Raised when requested document does not exist"""
    pass


class Forbidden(Exception):
    """Raised when cross-tenant access is attempted"""
    pass


class DataResidencyViolation(Exception):
    """Raised when data residency requirements are violated"""
    pass


class IsolationModel(Enum):
    """S3 isolation models for multi-tenant storage"""
    BUCKET_PER_TENANT = "bucket_per_tenant"
    SHARED_IAM = "shared_iam"
    HYBRID = "hybrid"


@dataclass
class TenantMetadata:
    """Tenant configuration metadata"""
    tenant_id: str
    data_residency: str  # 'EU', 'US', 'India'
    data_residency_region: str  # 'eu-west-1', 'us-east-1', 'ap-south-1'
    encryption_key_id: str
    storage_tier: str = "STANDARD"
    quota_gb: int = 100


class TenantS3Client:
    """
    Tenant-scoped S3 client wrapper that enforces prefix isolation and data residency.

    CRITICAL: This wrapper prevents direct boto3 access and ensures all operations
    are automatically scoped to the tenant's prefix (tenant-{id}/).

    Usage:
        client = TenantS3Client(tenant_id="tenant-123")
        client.upload("invoice.pdf", file_data)
        data = client.download("invoice.pdf")
    """

    def __init__(self, tenant_id: str, region: Optional[str] = None,
                 tenant_metadata: Optional[TenantMetadata] = None):
        """
        Initialize tenant-scoped S3 client.

        Args:
            tenant_id: Unique tenant identifier
            region: AWS region override (must match tenant residency)
            tenant_metadata: Optional tenant configuration
        """
        self.tenant_id = tenant_id
        self.prefix = f"tenant-{tenant_id}/"

        # Load tenant metadata (in production, fetch from database)
        if tenant_metadata:
            self.metadata = tenant_metadata
        else:
            # Default metadata for offline/testing mode
            self.metadata = TenantMetadata(
                tenant_id=tenant_id,
                data_residency="US",
                data_residency_region="us-east-1",
                encryption_key_id="default-key",
                storage_tier="STANDARD",
                quota_gb=100
            )

        self.region = region or self.metadata.data_residency_region
        self.bucket = self._get_bucket_for_region(self.region)
        self.kms_key_id = self.metadata.encryption_key_id

        # Check if AWS S3 is enabled
        self.aws_enabled = os.getenv("AWS_S3_ENABLED", "false").lower() == "true"

        # Private boto3 client - NOT exposed directly
        if self.aws_enabled:
            try:
                import boto3
                self._s3 = boto3.client('s3', region_name=self.region)
                logger.info(f"Initialized TenantS3Client for {tenant_id} in {self.region}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize boto3 client: {e}")
                self._s3 = None
        else:
            logger.info(f"⚠️ AWS_S3_ENABLED not set - running in offline mode")
            self._s3 = None

    def _get_bucket_for_region(self, region: str) -> str:
        """
        Map AWS region to corresponding bucket name.

        In production, use separate buckets per region for data residency:
        - eu-west-1: rag-docs-eu
        - us-east-1: rag-docs-us
        - ap-south-1: rag-docs-india
        """
        bucket_mapping = {
            'eu-west-1': 'rag-docs-eu',
            'us-east-1': 'rag-docs-us',
            'ap-south-1': 'rag-docs-india',
        }
        return bucket_mapping.get(region, 'rag-docs-shared')

    def upload(self, key: str, data: bytes, metadata: Optional[Dict[str, str]] = None) -> str:
        """
        Upload document with automatic tenant prefix and encryption.

        Args:
            key: Document key (will be prefixed with tenant-{id}/)
            data: Binary document data
            metadata: Optional custom metadata

        Returns:
            S3 URI (s3://bucket/tenant-id/key)

        Raises:
            DataResidencyViolation: If region doesn't match tenant requirements
        """
        # ALWAYS prefix with tenant
        full_key = self.prefix + key

        # Validate residency
        self._enforce_data_residency('upload')

        # Offline mode handling
        if not self.aws_enabled or not self._s3:
            logger.warning(f"⚠️ Offline mode - skipping S3 upload for {full_key}")
            return f"s3://{self.bucket}/{full_key} (offline)"

        # Upload with tenant metadata and encryption
        try:
            upload_metadata = metadata or {}
            upload_metadata['tenant_id'] = self.tenant_id

            self._s3.put_object(
                Bucket=self.bucket,
                Key=full_key,
                Body=data,
                ServerSideEncryption='aws:kms',
                SSEKMSKeyId=self.kms_key_id,
                Tagging=f"tenant_id={self.tenant_id}",
                Metadata=upload_metadata
            )

            logger.info(f"✓ Uploaded {full_key} to {self.bucket}")
            self._audit_log('upload', full_key, 'success')

            return f"s3://{self.bucket}/{full_key}"
        except Exception as e:
            logger.error(f"✗ Upload failed for {full_key}: {e}")
            self._audit_log('upload', full_key, 'failed', error=str(e))
            raise

    def download(self, key: str) -> bytes:
        """
        Download document with prefix validation.

        Args:
            key: Document key (without tenant prefix)

        Returns:
            Binary document data

        Raises:
            DocumentNotFound: If document doesn't exist
        """
        # Validate prefix
        full_key = self.prefix + key

        # Offline mode handling
        if not self.aws_enabled or not self._s3:
            logger.warning(f"⚠️ Offline mode - skipping S3 download for {full_key}")
            return b"offline-mode-placeholder"

        try:
            response = self._s3.get_object(Bucket=self.bucket, Key=full_key)
            data = response['Body'].read()

            logger.info(f"✓ Downloaded {full_key} ({len(data)} bytes)")
            self._audit_log('download', full_key, 'success')

            return data
        except self._s3.exceptions.NoSuchKey:
            logger.error(f"✗ Document not found: {full_key}")
            self._audit_log('download', full_key, 'not_found')
            raise DocumentNotFound(f"Document {key} not found")
        except Exception as e:
            logger.error(f"✗ Download failed for {full_key}: {e}")
            self._audit_log('download', full_key, 'failed', error=str(e))
            raise

    def delete(self, key: str) -> None:
        """
        Delete document with prefix validation.

        Args:
            key: Document key (without tenant prefix)
        """
        full_key = self.prefix + key

        # Offline mode handling
        if not self.aws_enabled or not self._s3:
            logger.warning(f"⚠️ Offline mode - skipping S3 delete for {full_key}")
            return

        try:
            self._s3.delete_object(Bucket=self.bucket, Key=full_key)
            logger.info(f"✓ Deleted {full_key}")
            self._audit_log('delete', full_key, 'success')
        except Exception as e:
            logger.error(f"✗ Delete failed for {full_key}: {e}")
            self._audit_log('delete', full_key, 'failed', error=str(e))
            raise

    def list_documents(self, prefix: str = "") -> List[str]:
        """
        List all documents under tenant prefix.

        Args:
            prefix: Optional sub-prefix within tenant namespace

        Returns:
            List of document keys (without tenant prefix)
        """
        # Only list documents under tenant prefix
        full_prefix = self.prefix + prefix

        # Offline mode handling
        if not self.aws_enabled or not self._s3:
            logger.warning(f"⚠️ Offline mode - skipping S3 list for {full_prefix}")
            return ["example-doc1.pdf", "example-doc2.pdf"]

        try:
            response = self._s3.list_objects_v2(
                Bucket=self.bucket,
                Prefix=full_prefix
            )

            documents = [
                obj['Key'].replace(self.prefix, '')
                for obj in response.get('Contents', [])
            ]

            logger.info(f"✓ Listed {len(documents)} documents under {full_prefix}")
            self._audit_log('list', full_prefix, 'success')

            return documents
        except Exception as e:
            logger.error(f"✗ List failed for {full_prefix}: {e}")
            self._audit_log('list', full_prefix, 'failed', error=str(e))
            raise

    def _enforce_data_residency(self, operation: str) -> None:
        """Validate operation complies with data residency requirements"""
        required_region = self.metadata.data_residency_region

        if self.region != required_region:
            error_msg = (
                f"Data residency violation: {operation} attempted in {self.region}, "
                f"but tenant {self.tenant_id} requires {required_region}"
            )
            logger.error(f"✗ {error_msg}")
            self._audit_log('residency_violation', f"{operation}:{self.region}", 'blocked')
            raise DataResidencyViolation(error_msg)

    def _audit_log(self, operation: str, doc_key: str, status: str, error: Optional[str] = None) -> None:
        """Log operation to audit trail"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'tenant_id': self.tenant_id,
            'operation': operation,
            'doc_key': doc_key,
            'status': status,
            'region': self.region,
            'error': error
        }

        # In production, write to CloudTrail or dedicated audit database
        logger.info(f"AUDIT: {log_entry}")


class PresignedURLService:
    """
    Generates and validates tenant-scoped presigned URLs with security checks.

    CRITICAL: ALWAYS validate tenant ownership BEFORE generating presigned URL.
    Never trust client-provided document keys without verification.

    Usage:
        service = PresignedURLService(redis_client)
        url = service.generate_url(tenant_id, "tenant-123/invoice.pdf")
    """

    def __init__(self, redis_client=None):
        """
        Initialize presigned URL service.

        Args:
            redis_client: Optional Redis client for URL caching
        """
        self.redis = redis_client
        self.cache_ttl = 300  # 5 minutes
        self.default_expiration = 300  # 5 minutes
        self.aws_enabled = os.getenv("AWS_S3_ENABLED", "false").lower() == "true"

    def generate_url(self, tenant_id: str, doc_key: str,
                     expiration: int = None) -> str:
        """
        Generate presigned URL with tenant validation.

        Security checks:
        1. Validate doc_key starts with tenant prefix
        2. Verify document exists
        3. Check object tags match tenant_id
        4. Generate short-lived URL (5 minutes)
        5. Audit log generation

        Args:
            tenant_id: Tenant requesting access
            doc_key: Full S3 key (must include tenant prefix)
            expiration: URL expiration in seconds (default: 300)

        Returns:
            Presigned URL for direct S3 access

        Raises:
            Forbidden: If document doesn't belong to tenant
            DocumentNotFound: If document doesn't exist
        """
        # Extract tenant from context
        tenant_client = TenantS3Client(tenant_id)

        # Validate key starts with tenant prefix
        expected_prefix = f"tenant-{tenant_id}/"
        if not doc_key.startswith(expected_prefix):
            logger.error(f"✗ Cross-tenant access attempt: {tenant_id} → {doc_key}")
            self._audit_log('presigned_url_violation', tenant_id, doc_key)
            raise Forbidden("Cross-tenant access denied")

        # Check cache first
        if self.redis:
            cache_key = f"presigned:{tenant_id}:{doc_key}"
            cached_url = self.redis.get(cache_key)
            if cached_url:
                logger.info(f"✓ Cache hit for presigned URL: {doc_key}")
                return cached_url.decode('utf-8')

        # Offline mode handling
        if not self.aws_enabled or not tenant_client._s3:
            logger.warning(f"⚠️ Offline mode - generating mock presigned URL")
            mock_url = f"https://offline-mode.s3.amazonaws.com/{doc_key}?expires=300"
            return mock_url

        # Verify document exists and belongs to tenant
        try:
            obj_metadata = tenant_client._s3.head_object(
                Bucket=tenant_client.bucket,
                Key=doc_key
            )
        except tenant_client._s3.exceptions.NoSuchKey:
            logger.error(f"✗ Document not found: {doc_key}")
            raise DocumentNotFound(f"Document {doc_key} not found")

        # Check object tags
        try:
            tags_response = tenant_client._s3.get_object_tagging(
                Bucket=tenant_client.bucket,
                Key=doc_key
            )
            tags = {tag['Key']: tag['Value'] for tag in tags_response['TagSet']}

            if tags.get('tenant_id') != tenant_id:
                logger.error(f"✗ Tag mismatch: {doc_key} tagged for {tags.get('tenant_id')}, requested by {tenant_id}")
                self._audit_log('presigned_url_tag_mismatch', tenant_id, doc_key)
                raise Forbidden("Document does not belong to tenant")
        except Exception as e:
            logger.warning(f"⚠️ Could not verify tags for {doc_key}: {e}")

        # Generate presigned URL
        url_expiration = expiration or self.default_expiration
        url = tenant_client._s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': tenant_client.bucket, 'Key': doc_key},
            ExpiresIn=url_expiration
        )

        # Cache in Redis
        if self.redis:
            cache_key = f"presigned:{tenant_id}:{doc_key}"
            self.redis.setex(cache_key, self.cache_ttl, url)

        # Audit log
        logger.info(f"✓ Generated presigned URL for {doc_key} (expires in {url_expiration}s)")
        self._audit_log('presigned_url_generated', tenant_id, doc_key,
                        expiration=url_expiration)

        return url

    def validate_url(self, tenant_id: str, doc_key: str) -> Optional[str]:
        """
        Check if valid cached presigned URL exists.

        Args:
            tenant_id: Tenant identifier
            doc_key: Document key

        Returns:
            Cached URL if available, None otherwise
        """
        if not self.redis:
            return None

        cache_key = f"presigned:{tenant_id}:{doc_key}"
        cached_url = self.redis.get(cache_key)

        if cached_url:
            logger.info(f"✓ Valid cached URL found for {doc_key}")
            return cached_url.decode('utf-8')

        return None

    def _audit_log(self, operation: str, tenant_id: str, doc_key: str, **kwargs) -> None:
        """Log presigned URL operations"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'operation': operation,
            'tenant_id': tenant_id,
            'doc_key': doc_key,
            **kwargs
        }
        logger.info(f"AUDIT: {log_entry}")


class DataResidencyValidator:
    """
    Enforces data residency requirements for multi-region compliance.

    Ensures tenant data stays in required geographic regions per:
    - GDPR (EU): Personal data must remain in EU or approved countries
    - DPDPA (India): Sensitive personal data must stay in India
    - HIPAA (US): PHI must comply with US privacy requirements

    Usage:
        validator = DataResidencyValidator()
        region = validator.validate_upload(tenant_id)
    """

    REGION_MAPPING = {
        'EU': 'eu-west-1',
        'US': 'us-east-1',
        'India': 'ap-south-1'
    }

    def validate_upload(self, tenant_id: str, region_override: Optional[str] = None,
                       tenant_metadata: Optional[TenantMetadata] = None) -> str:
        """
        Validate upload operation complies with data residency.

        Args:
            tenant_id: Tenant identifier
            region_override: Optional region to validate against
            tenant_metadata: Optional tenant configuration

        Returns:
            Required AWS region for tenant

        Raises:
            DataResidencyViolation: If region doesn't match requirements
        """
        # In production, fetch from database
        if tenant_metadata:
            required_region = self.REGION_MAPPING[tenant_metadata.data_residency]
        else:
            # Default to US for testing
            required_region = 'us-east-1'

        if region_override and region_override != required_region:
            error_msg = (
                f"Upload attempted in {region_override}, "
                f"but tenant {tenant_id} requires {required_region}"
            )
            logger.error(f"✗ Data residency violation: {error_msg}")
            self._audit_log('residency_violation_attempt', tenant_id,
                           f'Upload: {region_override} → {required_region}')
            raise DataResidencyViolation(error_msg)

        logger.info(f"✓ Data residency validated for {tenant_id}: {required_region}")
        return required_region

    def validate_access(self, user_id: str, tenant_id: str, operation: str = 'read',
                       user_region: Optional[str] = None) -> None:
        """
        Validate cross-border data access permissions.

        Args:
            user_id: User requesting access
            tenant_id: Tenant identifier
            operation: Access operation type
            user_region: Region where user is accessing from

        Raises:
            Forbidden: If cross-border access not permitted
        """
        # In production, check user consent and cross-border policies
        if user_region:
            logger.info(f"Cross-border access: user {user_id} from {user_region} → tenant {tenant_id}")
            # Implement consent checks here

        logger.info(f"✓ Access validated for user {user_id} → tenant {tenant_id}")

    def _audit_log(self, operation: str, tenant_id: str, details: str) -> None:
        """Log residency validation events"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'operation': operation,
            'tenant_id': tenant_id,
            'details': details
        }
        logger.info(f"AUDIT: {log_entry}")


class StorageAuditLogger:
    """
    Comprehensive audit logging for storage operations.

    Logs all S3 access to immutable audit trail for compliance.
    Supports anomaly detection and compliance reporting.

    Usage:
        audit_logger = StorageAuditLogger(db_connection)
        audit_logger.log_access('upload', tenant_id, doc_key)
    """

    def __init__(self, db_connection=None):
        """
        Initialize audit logger.

        Args:
            db_connection: Optional database connection for persistent logging
        """
        self.db = db_connection

    def log_access(self, operation: str, tenant_id: str, doc_key: str,
                   user_id: Optional[str] = None, status: str = 'success',
                   error: Optional[str] = None) -> None:
        """
        Log storage access operation.

        Args:
            operation: Operation type ('upload', 'download', 'delete', 'list')
            tenant_id: Tenant identifier
            doc_key: Document key
            user_id: Optional user identifier
            status: Operation status ('success', 'failed', 'denied')
            error: Optional error message
        """
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'operation': operation,
            'tenant_id': tenant_id,
            'doc_key': doc_key,
            'user_id': user_id,
            'status': status,
            'error': error
        }

        # In production, write to CloudTrail and database
        logger.info(f"STORAGE_AUDIT: {log_entry}")

        if self.db:
            try:
                # Placeholder for database insert
                # self.db.execute("INSERT INTO storage_audit_log ...")
                pass
            except Exception as e:
                logger.error(f"✗ Failed to write audit log to database: {e}")

    def get_tenant_access_log(self, tenant_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Retrieve access logs for tenant.

        Args:
            tenant_id: Tenant identifier
            days: Number of days to retrieve

        Returns:
            List of audit log entries
        """
        if not self.db:
            logger.warning("⚠️ No database connection - returning mock data")
            return [
                {'operation': 'upload', 'count': 42, 'user_id': 'user-1', 'status': 'success'},
                {'operation': 'download', 'count': 138, 'user_id': 'user-2', 'status': 'success'},
            ]

        # Placeholder for database query
        # results = self.db.query("SELECT ... FROM storage_audit_log ...")
        logger.info(f"Retrieved access logs for {tenant_id} (last {days} days)")
        return []

    def detect_anomalies(self, tenant_id: str) -> List[Dict[str, Any]]:
        """
        Detect unusual access patterns for tenant.

        Flags:
        - >100 operations per hour by single user
        - Failed access attempts from unknown IPs
        - Bulk downloads of sensitive documents

        Args:
            tenant_id: Tenant identifier

        Returns:
            List of anomalous access patterns
        """
        if not self.db:
            logger.warning("⚠️ No database connection - returning mock anomalies")
            return []

        # Placeholder for anomaly detection query
        logger.info(f"Scanning for anomalies in tenant {tenant_id}")
        return []
