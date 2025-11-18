"""
Tests for L3 M12.4: Compliance Boundaries & Data Governance

Tests ALL major functions from script with offline mode (no external services required).
Validates:
- Tenant compliance configuration creation
- Legal hold checking
- Scheduled deletion workflow
- Multi-system cascade deletion
- Verification testing
- GDPR Article 17 compliance

Services: Mocked/offline for testing
"""

import pytest
import os
from datetime import datetime, timedelta
from typing import Dict, Any

# Force offline mode for tests
os.environ["PINECONE_ENABLED"] = "false"
os.environ["AWS_ENABLED"] = "false"
os.environ["OFFLINE"] = "true"

from src.l3_m12_compliance_boundaries import (
    TenantComplianceConfig,
    ComplianceDeletionService,
    DeletionRequest,
    ComplianceAuditTrail,
    RegulationType,
    DataResidency,
    create_compliance_config,
    execute_scheduled_deletion,
    check_legal_hold,
    verify_deletion,
)


# ===== TENANT COMPLIANCE CONFIG TESTS =====

def test_create_compliance_config_gdpr():
    """Test creating GDPR compliance config with 90-day retention"""
    config = create_compliance_config(
        tenant_id="test_tenant_eu",
        tenant_name="Test GDPR Tenant",
        tenant_email="dpo@test.eu",
        regulations=["GDPR", "SOX"],
        retention_days=90,
        data_residency="EU",
    )

    assert config.tenant_id == "test_tenant_eu"
    assert RegulationType.GDPR in config.regulations
    assert config.retention_days == 90
    assert config.data_residency == DataResidency.EU
    assert config.auto_delete_enabled == True
    assert config.legal_hold_active == False


def test_create_compliance_config_ccpa():
    """Test creating CCPA compliance config with 7-year retention (SOX)"""
    config = create_compliance_config(
        tenant_id="test_tenant_us",
        tenant_name="Test CCPA Tenant",
        tenant_email="privacy@test.com",
        regulations=["CCPA", "SOX"],
        retention_days=2555,  # 7 years
        data_residency="US",
    )

    assert config.tenant_id == "test_tenant_us"
    assert RegulationType.CCPA in config.regulations
    assert RegulationType.SOX in config.regulations
    assert config.retention_days == 2555
    assert config.data_residency == DataResidency.US


def test_create_compliance_config_dpdpa():
    """Test creating DPDPA compliance config with India data localization"""
    config = create_compliance_config(
        tenant_id="test_tenant_in",
        tenant_name="Test DPDPA Tenant",
        tenant_email="legal@test.in",
        regulations=["DPDPA", "PCI-DSS"],
        retention_days=180,
        data_residency="IN",
    )

    assert config.tenant_id == "test_tenant_in"
    assert RegulationType.DPDPA in config.regulations
    assert config.retention_days == 180
    assert config.data_residency == DataResidency.IN


def test_create_compliance_config_validation_retention_too_low():
    """Test validation fails for retention_days < 1"""
    with pytest.raises(ValueError, match="retention_days must be between 1 and 3650"):
        create_compliance_config(
            tenant_id="test",
            tenant_name="Test",
            tenant_email="test@test.com",
            regulations=["GDPR"],
            retention_days=0,  # Invalid: must be >= 1
            data_residency="EU",
        )


def test_create_compliance_config_validation_retention_too_high():
    """Test validation fails for retention_days > 3650 (10 years)"""
    with pytest.raises(ValueError, match="retention_days must be between 1 and 3650"):
        create_compliance_config(
            tenant_id="test",
            tenant_name="Test",
            tenant_email="test@test.com",
            regulations=["GDPR"],
            retention_days=4000,  # Invalid: > 10 years
            data_residency="EU",
        )


def test_compliance_config_to_dict():
    """Test compliance config serialization"""
    config = create_compliance_config(
        tenant_id="test",
        tenant_name="Test",
        tenant_email="test@test.com",
        regulations=["GDPR"],
        retention_days=90,
        data_residency="EU",
    )

    config_dict = config.to_dict()

    assert config_dict["tenant_id"] == "test"
    assert "GDPR" in config_dict["regulations"]
    assert config_dict["retention_days"] == 90
    assert config_dict["data_residency"] == "EU"
    assert "created_at" in config_dict
    assert "updated_at" in config_dict


# ===== LEGAL HOLD TESTS =====

def test_check_legal_hold_not_active():
    """Test legal hold check when not active"""
    config = create_compliance_config(
        tenant_id="test",
        tenant_name="Test",
        tenant_email="test@test.com",
        regulations=["GDPR"],
        retention_days=90,
        data_residency="EU",
    )

    legal_hold_active, reason = check_legal_hold("test", config)

    assert legal_hold_active == False
    assert reason is None


def test_check_legal_hold_active():
    """Test legal hold check when active (prevents deletion)"""
    config = create_compliance_config(
        tenant_id="test",
        tenant_name="Test",
        tenant_email="test@test.com",
        regulations=["GDPR"],
        retention_days=90,
        data_residency="EU",
        legal_hold_active=True,
        legal_hold_reason="SEC Investigation Case #2024-SEC-98765",
    )

    legal_hold_active, reason = check_legal_hold("test", config)

    assert legal_hold_active == True
    assert "SEC Investigation" in reason


# ===== DELETION SERVICE TESTS =====

def test_deletion_service_offline_mode():
    """Test deletion service in offline mode (no external clients)"""
    service = ComplianceDeletionService(
        pinecone_client=None,
        s3_client=None,
        redis_client=None,
        db_session=None,
        cloudfront_client=None,
        offline_mode=True,
    )

    cutoff_date = datetime.utcnow() - timedelta(days=90)
    success, count, error = service.delete_from_vector_db("test_tenant", cutoff_date)

    # In offline mode, deletion is skipped
    assert success == True
    assert count == 0
    assert "offline" in error.lower()


def test_cascade_delete_offline():
    """Test cascade deletion across 7 systems in offline mode"""
    service = ComplianceDeletionService(offline_mode=True)

    cutoff_date = datetime.utcnow() - timedelta(days=90)
    config = {"s3_bucket": "test-bucket", "cloudfront_distribution_id": None}

    results = service.cascade_delete("test_tenant", cutoff_date, config)

    # All systems should be present in results
    assert "vector_db" in results
    assert "s3" in results
    assert "redis" in results
    assert "cdn" in results
    assert "postgresql" in results
    assert "logs" in results
    assert "backups" in results

    # In offline mode, most operations are skipped
    assert results["vector_db"]["success"] == True
    assert results["s3"]["success"] == True
    assert results["redis"]["success"] == True


def test_scheduled_deletion_legal_hold_blocks():
    """Test scheduled deletion is blocked when legal hold is active"""
    config = create_compliance_config(
        tenant_id="test",
        tenant_name="Test",
        tenant_email="test@test.com",
        regulations=["GDPR"],
        retention_days=90,
        data_residency="EU",
        legal_hold_active=True,
        legal_hold_reason="Litigation pending",
    )

    service = ComplianceDeletionService(offline_mode=True)
    system_config = {"s3_bucket": "test-bucket"}

    result = execute_scheduled_deletion(
        tenant_id="test",
        compliance_config=config,
        deletion_service=service,
        config=system_config,
    )

    # Deletion should be skipped due to legal hold
    assert result["skipped"] == True
    assert "Litigation" in result["reason"]


def test_scheduled_deletion_auto_delete_disabled():
    """Test scheduled deletion is skipped when auto_delete_enabled=False"""
    config = create_compliance_config(
        tenant_id="test",
        tenant_name="Test",
        tenant_email="test@test.com",
        regulations=["GDPR"],
        retention_days=90,
        data_residency="EU",
        auto_delete_enabled=False,  # Manual approval required
    )

    service = ComplianceDeletionService(offline_mode=True)
    system_config = {"s3_bucket": "test-bucket"}

    result = execute_scheduled_deletion(
        tenant_id="test",
        compliance_config=config,
        deletion_service=service,
        config=system_config,
    )

    # Deletion should be skipped - requires manual approval
    assert result["skipped"] == True
    assert "auto_delete" in result["reason"].lower()


def test_scheduled_deletion_success():
    """Test successful scheduled deletion with offline mode"""
    config = create_compliance_config(
        tenant_id="test",
        tenant_name="Test",
        tenant_email="test@test.com",
        regulations=["GDPR"],
        retention_days=90,
        data_residency="EU",
    )

    service = ComplianceDeletionService(offline_mode=True)
    system_config = {"s3_bucket": "test-bucket"}

    result = execute_scheduled_deletion(
        tenant_id="test",
        compliance_config=config,
        deletion_service=service,
        config=system_config,
    )

    # In offline mode, deletion succeeds (skipped operations)
    assert "tenant_id" in result
    assert "cutoff_date" in result
    assert "results" in result
    assert result["all_systems_succeeded"] == True
    assert "audit_trail_id" in result


# ===== DELETION REQUEST TESTS =====

def test_deletion_request_creation():
    """Test creating a deletion request"""
    request = DeletionRequest(
        request_id="test_req_001",
        tenant_id="test_tenant",
        user_id="user_123",
        request_type="gdpr_article_17",
    )

    assert request.request_id == "test_req_001"
    assert request.tenant_id == "test_tenant"
    assert request.user_id == "user_123"
    assert request.request_type == "gdpr_article_17"
    assert request.completed_at is None


def test_deletion_request_to_dict():
    """Test deletion request serialization"""
    request = DeletionRequest(
        request_id="test_req_001",
        tenant_id="test_tenant",
        user_id="user_123",
    )

    request_dict = request.to_dict()

    assert request_dict["request_id"] == "test_req_001"
    assert request_dict["tenant_id"] == "test_tenant"
    assert request_dict["user_id"] == "user_123"
    assert "requested_at" in request_dict


# ===== AUDIT TRAIL TESTS =====

def test_audit_trail_creation():
    """Test creating immutable audit trail entry"""
    audit_entry = ComplianceAuditTrail(
        tenant_id="test_tenant",
        event_type="scheduled_deletion_executed",
        event_data={
            "cutoff_date": "2024-08-20T00:00:00Z",
            "retention_days": 90,
            "deleted_count": 523,
        },
    )

    assert audit_entry.tenant_id == "test_tenant"
    assert audit_entry.event_type == "scheduled_deletion_executed"
    assert audit_entry.event_data["deleted_count"] == 523
    assert audit_entry.id is not None
    assert audit_entry.created_at is not None


def test_audit_trail_to_dict():
    """Test audit trail serialization"""
    audit_entry = ComplianceAuditTrail(
        tenant_id="test_tenant",
        event_type="data_deletion",
        event_data={"system": "vector_db", "count": 100},
    )

    audit_dict = audit_entry.to_dict()

    assert audit_dict["tenant_id"] == "test_tenant"
    assert audit_dict["event_type"] == "data_deletion"
    assert audit_dict["event_data"]["count"] == 100
    assert "id" in audit_dict
    assert "created_at" in audit_dict


# ===== VERIFICATION TESTS =====

def test_verify_deletion_offline():
    """Test deletion verification in offline mode"""
    service = ComplianceDeletionService(offline_mode=True)
    system_config = {"s3_bucket": "test-bucket"}

    result = verify_deletion(
        tenant_id="test_tenant",
        deletion_request_id="test_req_001",
        deletion_service=service,
        config=system_config,
    )

    assert result["tenant_id"] == "test_tenant"
    assert result["deletion_request_id"] == "test_req_001"
    assert "verified_at" in result
    assert "systems" in result
    assert result["all_verified"] == True  # Offline mode verification passes


# ===== MULTI-REGULATION TESTS =====

def test_multi_regulation_config():
    """Test tenant with multiple regulations (GDPR + CCPA + DPDPA)"""
    config = create_compliance_config(
        tenant_id="test_multi",
        tenant_name="Multi-Regulation Tenant",
        tenant_email="compliance@test.com",
        regulations=["GDPR", "CCPA", "DPDPA"],
        retention_days=90,  # Most restrictive (GDPR/DPDPA)
        data_residency="GLOBAL",
    )

    assert len(config.regulations) == 3
    assert RegulationType.GDPR in config.regulations
    assert RegulationType.CCPA in config.regulations
    assert RegulationType.DPDPA in config.regulations


def test_financial_regulations():
    """Test financial tenant with SOX + FINRA"""
    config = create_compliance_config(
        tenant_id="test_financial",
        tenant_name="Financial Services",
        tenant_email="compliance@finance.com",
        regulations=["SOX", "FINRA"],
        retention_days=2555,  # 7 years (SEC Rule 17a-4)
        data_residency="US",
        encryption_standard="RSA-4096",  # Enhanced for financial data
        auto_delete_enabled=False,  # Manual approval required
    )

    assert RegulationType.SOX in config.regulations
    assert RegulationType.FINRA in config.regulations
    assert config.retention_days == 2555
    assert config.encryption_standard == "RSA-4096"
    assert config.auto_delete_enabled == False


def test_healthcare_hipaa():
    """Test healthcare tenant with HIPAA + GDPR"""
    config = create_compliance_config(
        tenant_id="test_healthcare",
        tenant_name="Healthcare Global",
        tenant_email="hipaa@health.com",
        regulations=["HIPAA", "GDPR"],
        retention_days=2190,  # 6 years (HIPAA medical records)
        data_residency="US",
        auto_delete_enabled=False,  # Manual approval for PHI
    )

    assert RegulationType.HIPAA in config.regulations
    assert RegulationType.GDPR in config.regulations
    assert config.retention_days == 2190
    assert config.auto_delete_enabled == False


# ===== INTEGRATION TESTS =====

@pytest.mark.skipif(
    os.getenv("PINECONE_ENABLED", "false").lower() != "true",
    reason="Pinecone not enabled - skipping online test",
)
def test_scheduled_deletion_with_pinecone():
    """Test scheduled deletion with actual Pinecone client (if enabled)"""
    # This test only runs if PINECONE_ENABLED=true and API key is set
    from config import get_clients

    clients = get_clients()

    if not clients.get("pinecone"):
        pytest.skip("Pinecone client not available")

    config = create_compliance_config(
        tenant_id="test_online",
        tenant_name="Test Online",
        tenant_email="test@test.com",
        regulations=["GDPR"],
        retention_days=90,
        data_residency="EU",
    )

    service = ComplianceDeletionService(
        pinecone_client=clients.get("pinecone"),
        offline_mode=False,
    )

    system_config = {"s3_bucket": "test-bucket"}

    result = execute_scheduled_deletion(
        tenant_id="test_online",
        compliance_config=config,
        deletion_service=service,
        config=system_config,
    )

    assert "tenant_id" in result
    assert "results" in result


# ===== EDGE CASE TESTS =====

def test_zero_retention_days_validation():
    """Test that retention_days=0 is rejected"""
    with pytest.raises(ValueError):
        create_compliance_config(
            tenant_id="test",
            tenant_name="Test",
            tenant_email="test@test.com",
            regulations=["GDPR"],
            retention_days=0,
            data_residency="EU",
        )


def test_negative_retention_days_validation():
    """Test that negative retention_days is rejected"""
    with pytest.raises(ValueError):
        create_compliance_config(
            tenant_id="test",
            tenant_name="Test",
            tenant_email="test@test.com",
            regulations=["GDPR"],
            retention_days=-10,
            data_residency="EU",
        )


def test_audit_retention_less_than_7_years():
    """Test that audit_retention_days < 2555 (7 years) is rejected"""
    with pytest.raises(ValueError, match="audit_retention_days must be >= 2555"):
        create_compliance_config(
            tenant_id="test",
            tenant_name="Test",
            tenant_email="test@test.com",
            regulations=["GDPR"],
            retention_days=90,
            data_residency="EU",
            audit_retention_days=365,  # Invalid: < 7 years
        )


# ===== RUN TESTS =====

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
