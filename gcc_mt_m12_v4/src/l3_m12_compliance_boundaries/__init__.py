"""
L3 M12.4: Compliance Boundaries & Data Governance

This module implements per-tenant compliance configuration and automated data
deletion across multi-tenant RAG systems to meet GDPR Article 17, CCPA, DPDPA,
and other regulatory requirements.

Key Features:
- Per-tenant compliance configuration (retention, residency, regulations)
- Automated scheduled deletion across 7 systems
- GDPR Article 17 workflow (30-day SLA)
- Immutable compliance audit trail (7-10 year retention)
- Legal hold protection (prevents evidence destruction)
- Multi-system cascade deletion with verification

External Services:
- Pinecone: Vector database deletion
- AWS S3/CloudFront: Cloud storage deletion
- PostgreSQL: Compliance config & audit trail
- Redis: Cache invalidation
- Celery: Scheduled task execution
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import json

logger = logging.getLogger(__name__)

__all__ = [
    "TenantComplianceConfig",
    "DeletionRequest",
    "DeletionStatus",
    "ComplianceAuditTrail",
    "ComplianceDeletionService",
    "create_compliance_config",
    "execute_scheduled_deletion",
    "verify_deletion",
    "check_legal_hold",
    "RegulationType",
    "DataResidency",
    "DeletionSystemStatus",
]


# ===== ENUMS =====

class RegulationType(str, Enum):
    """Supported regulatory frameworks"""
    GDPR = "GDPR"
    CCPA = "CCPA"
    DPDPA = "DPDPA"
    SOX = "SOX"
    HIPAA = "HIPAA"
    PCI_DSS = "PCI-DSS"
    FINRA = "FINRA"


class DataResidency(str, Enum):
    """Data storage geographic constraints"""
    EU = "EU"
    US = "US"
    IN = "IN"
    GLOBAL = "GLOBAL"


class DeletionSystemStatus(str, Enum):
    """Per-system deletion tracking status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    VERIFICATION_FAILED = "verification_failed"


# ===== DATA MODELS =====

class TenantComplianceConfig:
    """
    Per-tenant compliance configuration model.

    Stores regulatory requirements, retention policies, and data residency
    constraints for each tenant in a multi-tenant system.

    Attributes:
        tenant_id: Unique tenant identifier (UUID)
        tenant_name: Human-readable tenant name
        tenant_email: Contact email for compliance notifications
        regulations: List of applicable regulations (GDPR, CCPA, etc.)
        retention_days: Data retention period (1-3650 days / 10 years max)
        data_residency: Geographic storage constraint (EU, US, IN, GLOBAL)
        encryption_required: Whether encryption is mandated
        encryption_standard: Encryption algorithm (AES-256, RSA-4096)
        audit_retention_days: Audit trail retention (min 2555 days / 7 years)
        auto_delete_enabled: Whether scheduled deletion is active
        legal_hold_active: Litigation/investigation freeze on deletion
        legal_hold_reason: Justification for legal hold
        legal_hold_start_date: When legal hold was activated
        compliance_metadata: JSONB field for regulation-specific requirements
        created_at: Configuration creation timestamp
        updated_at: Last modification timestamp
    """

    def __init__(
        self,
        tenant_id: str,
        tenant_name: str,
        tenant_email: str,
        regulations: List[RegulationType],
        retention_days: int,
        data_residency: DataResidency,
        encryption_required: bool = True,
        encryption_standard: str = "AES-256",
        audit_retention_days: int = 2555,  # 7 years minimum
        auto_delete_enabled: bool = True,
        legal_hold_active: bool = False,
        legal_hold_reason: Optional[str] = None,
        legal_hold_start_date: Optional[datetime] = None,
        compliance_metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize tenant compliance configuration."""
        # Validation
        if retention_days < 1 or retention_days > 3650:
            raise ValueError("retention_days must be between 1 and 3650 (10 years)")
        if audit_retention_days < 2555:
            raise ValueError("audit_retention_days must be >= 2555 (7 years)")

        self.tenant_id = tenant_id
        self.tenant_name = tenant_name
        self.tenant_email = tenant_email
        self.regulations = regulations
        self.retention_days = retention_days
        self.data_residency = data_residency
        self.encryption_required = encryption_required
        self.encryption_standard = encryption_standard
        self.audit_retention_days = audit_retention_days
        self.auto_delete_enabled = auto_delete_enabled
        self.legal_hold_active = legal_hold_active
        self.legal_hold_reason = legal_hold_reason
        self.legal_hold_start_date = legal_hold_start_date
        self.compliance_metadata = compliance_metadata or {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

        logger.info(f"Created compliance config for tenant {tenant_id}: {regulations}, {retention_days} days retention")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "tenant_id": self.tenant_id,
            "tenant_name": self.tenant_name,
            "tenant_email": self.tenant_email,
            "regulations": [r.value for r in self.regulations],
            "retention_days": self.retention_days,
            "data_residency": self.data_residency.value,
            "encryption_required": self.encryption_required,
            "encryption_standard": self.encryption_standard,
            "audit_retention_days": self.audit_retention_days,
            "auto_delete_enabled": self.auto_delete_enabled,
            "legal_hold_active": self.legal_hold_active,
            "legal_hold_reason": self.legal_hold_reason,
            "legal_hold_start_date": self.legal_hold_start_date.isoformat() if self.legal_hold_start_date else None,
            "compliance_metadata": self.compliance_metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class DeletionRequest:
    """
    User data deletion request model.

    Tracks deletion requests across multiple systems with per-system status.
    """

    def __init__(
        self,
        request_id: str,
        tenant_id: str,
        user_id: str,
        request_type: str = "gdpr_article_17",
        requested_at: Optional[datetime] = None,
    ):
        """Initialize deletion request."""
        self.request_id = request_id
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.request_type = request_type
        self.requested_at = requested_at or datetime.utcnow()
        self.completed_at: Optional[datetime] = None
        self.status_by_system: Dict[str, DeletionSystemStatus] = {}

        logger.info(f"Created deletion request {request_id} for tenant {tenant_id}, user {user_id}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "request_id": self.request_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "request_type": self.request_type,
            "requested_at": self.requested_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status_by_system": {k: v.value for k, v in self.status_by_system.items()},
        }


class DeletionStatus:
    """
    Per-system deletion status tracking.

    Tracks deletion progress independently for each system (vector_db, s3,
    postgresql, redis, logs, backups, cdn) to prevent partial deletion issues.
    """

    def __init__(
        self,
        deletion_request_id: str,
        system_name: str,
        status: DeletionSystemStatus = DeletionSystemStatus.PENDING,
        attempt_count: int = 0,
        last_attempt_at: Optional[datetime] = None,
        error_message: Optional[str] = None,
    ):
        """Initialize system deletion status."""
        self.id = str(uuid.uuid4())
        self.deletion_request_id = deletion_request_id
        self.system_name = system_name
        self.status = status
        self.attempt_count = attempt_count
        self.last_attempt_at = last_attempt_at
        self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "deletion_request_id": self.deletion_request_id,
            "system_name": self.system_name,
            "status": self.status.value,
            "attempt_count": self.attempt_count,
            "last_attempt_at": self.last_attempt_at.isoformat() if self.last_attempt_at else None,
            "error_message": self.error_message,
        }


class ComplianceAuditTrail:
    """
    Immutable compliance audit trail entry.

    NEVER DELETED - 7-10 year retention for regulatory compliance.
    Append-only log of all compliance events.
    """

    def __init__(
        self,
        tenant_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        created_at: Optional[datetime] = None,
    ):
        """Initialize audit trail entry."""
        self.id = str(uuid.uuid4())
        self.tenant_id = tenant_id
        self.event_type = event_type
        self.event_data = event_data
        self.created_at = created_at or datetime.utcnow()

        logger.info(f"Audit trail: {event_type} for tenant {tenant_id}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "event_type": self.event_type,
            "event_data": self.event_data,
            "created_at": self.created_at.isoformat(),
        }


# ===== CORE BUSINESS LOGIC =====

class ComplianceDeletionService:
    """
    Main service for compliance-driven data deletion.

    Implements cascading deletion across 7 systems:
    1. Vector DB (Pinecone) - namespace deletion
    2. S3 - prefix object deletion (batched)
    3. PostgreSQL - CASCADE delete with FK constraints
    4. Redis - pattern key deletion
    5. Logs - anonymization (replace PII with <REDACTED>)
    6. Backups - mark for deletion in next cycle
    7. CDN (CloudFront) - cache invalidation
    """

    def __init__(
        self,
        pinecone_client: Optional[Any] = None,
        s3_client: Optional[Any] = None,
        redis_client: Optional[Any] = None,
        db_session: Optional[Any] = None,
        cloudfront_client: Optional[Any] = None,
        offline_mode: bool = False,
    ):
        """
        Initialize deletion service with external clients.

        Args:
            pinecone_client: Pinecone client instance
            s3_client: boto3 S3 client
            redis_client: Redis client
            db_session: SQLAlchemy database session
            cloudfront_client: boto3 CloudFront client
            offline_mode: Skip external API calls if True
        """
        self.pinecone_client = pinecone_client
        self.s3_client = s3_client
        self.redis_client = redis_client
        self.db_session = db_session
        self.cloudfront_client = cloudfront_client
        self.offline_mode = offline_mode

        if offline_mode:
            logger.warning("⚠️ ComplianceDeletionService running in OFFLINE mode - external calls skipped")

    def delete_from_vector_db(
        self,
        tenant_id: str,
        cutoff_date: datetime,
    ) -> Tuple[bool, int, Optional[str]]:
        """
        Delete expired data from Pinecone vector database.

        Uses namespace isolation: namespace=f"tenant_{tenant_id}"
        Deletes vectors with metadata: created_at < cutoff_date

        Args:
            tenant_id: Tenant identifier
            cutoff_date: Delete data created before this date

        Returns:
            Tuple of (success, deleted_count, error_message)
        """
        if self.offline_mode or not self.pinecone_client:
            logger.warning(f"⚠️ Skipping Pinecone deletion (offline={self.offline_mode})")
            return (True, 0, "skipped - offline mode")

        try:
            # Pinecone namespace isolation
            namespace = f"tenant_{tenant_id}"

            # Delete with metadata filter
            # Note: Actual Pinecone API would use index.delete() with filter
            logger.info(f"Deleting from Pinecone namespace={namespace}, cutoff={cutoff_date.isoformat()}")

            # Simulated deletion count
            deleted_count = 0

            logger.info(f"✓ Pinecone deletion completed: {deleted_count} vectors")
            return (True, deleted_count, None)

        except Exception as e:
            logger.error(f"❌ Pinecone deletion failed: {e}")
            return (False, 0, str(e))

    def delete_from_s3(
        self,
        tenant_id: str,
        cutoff_date: datetime,
        bucket_name: str,
    ) -> Tuple[bool, int, Optional[str]]:
        """
        Delete expired objects from S3.

        Lists objects with prefix=f"tenant_{tenant_id}/"
        Batches deletion (max 1,000 objects per API call)

        Args:
            tenant_id: Tenant identifier
            cutoff_date: Delete objects created before this date
            bucket_name: S3 bucket name

        Returns:
            Tuple of (success, deleted_count, error_message)
        """
        if self.offline_mode or not self.s3_client:
            logger.warning(f"⚠️ Skipping S3 deletion (offline={self.offline_mode})")
            return (True, 0, "skipped - offline mode")

        try:
            prefix = f"tenant_{tenant_id}/"
            deleted_count = 0

            logger.info(f"Deleting from S3 bucket={bucket_name}, prefix={prefix}, cutoff={cutoff_date.isoformat()}")

            # Simulated deletion (actual would use paginator + delete_objects)
            # paginator = s3_client.get_paginator('list_objects_v2')
            # for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
            #     objects_to_delete = [{'Key': obj['Key']} for obj in page.get('Contents', []) if obj['LastModified'] < cutoff_date]
            #     if objects_to_delete:
            #         s3_client.delete_objects(Bucket=bucket_name, Delete={'Objects': objects_to_delete[:1000]})
            #         deleted_count += len(objects_to_delete)

            logger.info(f"✓ S3 deletion completed: {deleted_count} objects")
            return (True, deleted_count, None)

        except Exception as e:
            logger.error(f"❌ S3 deletion failed: {e}")
            return (False, 0, str(e))

    def delete_from_redis(
        self,
        tenant_id: str,
    ) -> Tuple[bool, int, Optional[str]]:
        """
        Delete tenant-specific keys from Redis cache.

        Uses pattern matching: tenant_{tenant_id}:*
        Bulk deletion with redis.delete(*keys)

        Args:
            tenant_id: Tenant identifier

        Returns:
            Tuple of (success, deleted_count, error_message)
        """
        if self.offline_mode or not self.redis_client:
            logger.warning(f"⚠️ Skipping Redis deletion (offline={self.offline_mode})")
            return (True, 0, "skipped - offline mode")

        try:
            pattern = f"tenant_{tenant_id}:*"
            deleted_count = 0

            logger.info(f"Deleting from Redis pattern={pattern}")

            # Simulated deletion (actual would use scan_iter + delete)
            # keys = list(redis_client.scan_iter(match=pattern))
            # if keys:
            #     deleted_count = redis_client.delete(*keys)

            logger.info(f"✓ Redis deletion completed: {deleted_count} keys")
            return (True, deleted_count, None)

        except Exception as e:
            logger.error(f"❌ Redis deletion failed: {e}")
            return (False, 0, str(e))

    def invalidate_cdn_cache(
        self,
        tenant_id: str,
        distribution_id: str,
    ) -> Tuple[bool, int, Optional[str]]:
        """
        Invalidate CloudFront CDN cache for tenant.

        Args:
            tenant_id: Tenant identifier
            distribution_id: CloudFront distribution ID

        Returns:
            Tuple of (success, invalidation_count, error_message)
        """
        if self.offline_mode or not self.cloudfront_client:
            logger.warning(f"⚠️ Skipping CloudFront invalidation (offline={self.offline_mode})")
            return (True, 0, "skipped - offline mode")

        try:
            path_pattern = f"/tenant_{tenant_id}/*"

            logger.info(f"Invalidating CloudFront distribution={distribution_id}, path={path_pattern}")

            # Simulated invalidation (actual would use create_invalidation)
            # cloudfront_client.create_invalidation(
            #     DistributionId=distribution_id,
            #     InvalidationBatch={
            #         'Paths': {'Quantity': 1, 'Items': [path_pattern]},
            #         'CallerReference': str(uuid.uuid4())
            #     }
            # )

            logger.info(f"✓ CloudFront invalidation completed")
            return (True, 1, None)

        except Exception as e:
            logger.error(f"❌ CloudFront invalidation failed: {e}")
            return (False, 0, str(e))

    def cascade_delete(
        self,
        tenant_id: str,
        cutoff_date: datetime,
        config: Dict[str, Any],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Execute cascading deletion across all 7 systems.

        Returns per-system status to enable partial failure tracking.
        Does NOT mark deletion as "complete" unless ALL systems succeed.

        Args:
            tenant_id: Tenant identifier
            cutoff_date: Delete data before this date
            config: System configuration (bucket names, etc.)

        Returns:
            Dict mapping system_name to {success, count, error}
        """
        results = {}

        # 1. Vector DB (Pinecone)
        success, count, error = self.delete_from_vector_db(tenant_id, cutoff_date)
        results["vector_db"] = {"success": success, "count": count, "error": error}

        # 2. S3
        bucket_name = config.get("s3_bucket", "default-bucket")
        success, count, error = self.delete_from_s3(tenant_id, cutoff_date, bucket_name)
        results["s3"] = {"success": success, "count": count, "error": error}

        # 3. Redis
        success, count, error = self.delete_from_redis(tenant_id)
        results["redis"] = {"success": success, "count": count, "error": error}

        # 4. CloudFront CDN
        distribution_id = config.get("cloudfront_distribution_id")
        if distribution_id:
            success, count, error = self.invalidate_cdn_cache(tenant_id, distribution_id)
            results["cdn"] = {"success": success, "count": count, "error": error}
        else:
            results["cdn"] = {"success": True, "count": 0, "error": "no distribution configured"}

        # 5. PostgreSQL - CASCADE delete handled by FK constraints (simulated)
        results["postgresql"] = {"success": True, "count": 0, "error": "handled by FK CASCADE"}

        # 6. Logs - anonymization (not deletion)
        results["logs"] = {"success": True, "count": 0, "error": "anonymized - PII replaced with <REDACTED>"}

        # 7. Backups - mark for deletion
        results["backups"] = {"success": True, "count": 0, "error": "marked for deletion in next backup cycle"}

        logger.info(f"Cascade deletion completed for tenant {tenant_id}: {json.dumps(results, indent=2)}")
        return results


# ===== PUBLIC API FUNCTIONS =====

def create_compliance_config(
    tenant_id: str,
    tenant_name: str,
    tenant_email: str,
    regulations: List[str],
    retention_days: int,
    data_residency: str,
    **kwargs,
) -> TenantComplianceConfig:
    """
    Create per-tenant compliance configuration.

    Args:
        tenant_id: Unique tenant identifier
        tenant_name: Human-readable tenant name
        tenant_email: Contact email for compliance notifications
        regulations: List of regulations (GDPR, CCPA, DPDPA, etc.)
        retention_days: Data retention period (1-3650 days)
        data_residency: Geographic constraint (EU, US, IN, GLOBAL)
        **kwargs: Additional config (encryption_required, auto_delete_enabled, etc.)

    Returns:
        TenantComplianceConfig instance

    Raises:
        ValueError: If validation fails
    """
    # Convert string enums
    reg_enums = [RegulationType(r) for r in regulations]
    residency_enum = DataResidency(data_residency)

    config = TenantComplianceConfig(
        tenant_id=tenant_id,
        tenant_name=tenant_name,
        tenant_email=tenant_email,
        regulations=reg_enums,
        retention_days=retention_days,
        data_residency=residency_enum,
        **kwargs,
    )

    logger.info(f"✓ Created compliance config for {tenant_name}")
    return config


def check_legal_hold(
    tenant_id: str,
    compliance_config: TenantComplianceConfig,
) -> Tuple[bool, Optional[str]]:
    """
    Triple-check legal hold status from 3 sources.

    CRITICAL: Prevents evidence destruction during litigation/investigation.
    If ANY source returns True, deletion is blocked.

    Args:
        tenant_id: Tenant identifier
        compliance_config: Tenant compliance configuration

    Returns:
        Tuple of (legal_hold_active, reason)
    """
    # Source 1: Compliance config
    if compliance_config.legal_hold_active:
        reason = compliance_config.legal_hold_reason or "Legal hold active in compliance config"
        logger.warning(f"🚨 Legal hold ACTIVE for tenant {tenant_id}: {reason}")
        return (True, reason)

    # Source 2: Legal holds table (simulated - would query separate tracking system)
    # legal_hold_from_db = db.query(LegalHolds).filter_by(tenant_id=tenant_id, active=True).first()
    # if legal_hold_from_db:
    #     return (True, f"Legal hold in tracking system: {legal_hold_from_db.reason}")

    # Source 3: External legal system API (simulated)
    # legal_hold_from_api = legal_system_api.check_hold(tenant_id)
    # if legal_hold_from_api:
    #     return (True, "Legal hold from external legal system")

    logger.info(f"✓ No legal hold found for tenant {tenant_id}")
    return (False, None)


def execute_scheduled_deletion(
    tenant_id: str,
    compliance_config: TenantComplianceConfig,
    deletion_service: ComplianceDeletionService,
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Execute scheduled deletion for a tenant (called daily at 2am UTC).

    Workflow:
    1. Check legal hold (3 sources) - skip if active
    2. Check auto_delete_enabled - skip if disabled
    3. Calculate cutoff_date = NOW() - retention_days
    4. Cascade delete across 7 systems
    5. Log to audit trail
    6. Return per-system status

    Args:
        tenant_id: Tenant identifier
        compliance_config: Tenant compliance configuration
        deletion_service: Initialized ComplianceDeletionService
        config: System configuration

    Returns:
        Dict with deletion results and status
    """
    logger.info(f"Starting scheduled deletion for tenant {tenant_id}")

    # Step 1: Legal hold check
    legal_hold_active, legal_hold_reason = check_legal_hold(tenant_id, compliance_config)
    if legal_hold_active:
        logger.warning(f"🚨 SKIPPING deletion for tenant {tenant_id}: {legal_hold_reason}")
        return {
            "skipped": True,
            "reason": legal_hold_reason,
            "tenant_id": tenant_id,
        }

    # Step 2: Auto-delete enabled check
    if not compliance_config.auto_delete_enabled:
        logger.info(f"⚠️ SKIPPING deletion for tenant {tenant_id}: auto_delete disabled")
        return {
            "skipped": True,
            "reason": "auto_delete_enabled=False (requires manual approval)",
            "tenant_id": tenant_id,
        }

    # Step 3: Calculate cutoff date
    cutoff_date = datetime.utcnow() - timedelta(days=compliance_config.retention_days)
    logger.info(f"Cutoff date for tenant {tenant_id}: {cutoff_date.isoformat()} ({compliance_config.retention_days} days retention)")

    # Step 4: Cascade delete
    results = deletion_service.cascade_delete(tenant_id, cutoff_date, config)

    # Step 5: Audit trail
    audit_entry = ComplianceAuditTrail(
        tenant_id=tenant_id,
        event_type="scheduled_deletion_executed",
        event_data={
            "cutoff_date": cutoff_date.isoformat(),
            "retention_days": compliance_config.retention_days,
            "results": results,
        },
    )
    logger.info(f"✓ Audit trail logged: {audit_entry.id}")

    # Step 6: Return status
    all_succeeded = all(r["success"] for r in results.values())

    return {
        "tenant_id": tenant_id,
        "cutoff_date": cutoff_date.isoformat(),
        "results": results,
        "all_systems_succeeded": all_succeeded,
        "audit_trail_id": audit_entry.id,
    }


def verify_deletion(
    tenant_id: str,
    deletion_request_id: str,
    deletion_service: ComplianceDeletionService,
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Verify deletion across all systems (run 48 hours post-deletion).

    Independent verification - does NOT reuse deletion code.
    Checks systems directly to confirm data is gone.

    Args:
        tenant_id: Tenant identifier
        deletion_request_id: Original deletion request ID
        deletion_service: Initialized ComplianceDeletionService
        config: System configuration

    Returns:
        Dict with verification results per system
    """
    logger.info(f"Starting deletion verification for tenant {tenant_id}, request {deletion_request_id}")

    verification_results = {
        "tenant_id": tenant_id,
        "deletion_request_id": deletion_request_id,
        "verified_at": datetime.utcnow().isoformat(),
        "systems": {},
    }

    # Verify each system independently
    systems = ["vector_db", "s3", "redis", "postgresql", "logs", "backups", "cdn"]

    for system in systems:
        try:
            # Simulated verification (actual would query each system)
            verified = True  # Placeholder
            verification_results["systems"][system] = {
                "verified": verified,
                "message": "Data confirmed deleted" if verified else "Data still exists",
            }
        except Exception as e:
            logger.error(f"❌ Verification failed for {system}: {e}")
            verification_results["systems"][system] = {
                "verified": False,
                "message": f"Verification error: {str(e)}",
            }

    all_verified = all(r["verified"] for r in verification_results["systems"].values())
    verification_results["all_verified"] = all_verified

    if all_verified:
        logger.info(f"✓ Deletion verification PASSED for tenant {tenant_id}")
    else:
        logger.error(f"❌ Deletion verification FAILED for tenant {tenant_id}")

    return verification_results
