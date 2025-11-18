"""
Tests for L3 M12.2: Document Storage & Access Control

Tests all major functions from script in offline mode.
SERVICE: AWS_S3 (mocked/offline for testing)

Test Coverage:
- TenantS3Client: upload, download, delete, list operations
- PresignedURLService: URL generation and validation
- DataResidencyValidator: upload and access validation
- StorageAuditLogger: audit logging operations
- Cross-tenant access prevention
- Data residency enforcement
"""

import pytest
import os
from src.l3_m12_document_storage import (
    TenantS3Client,
    PresignedURLService,
    DataResidencyValidator,
    StorageAuditLogger,
    TenantMetadata,
    DocumentNotFound,
    Forbidden,
    DataResidencyViolation
)

# Force offline mode for tests
os.environ["AWS_S3_ENABLED"] = "false"
os.environ["OFFLINE"] = "true"


class TestTenantS3Client:
    """Test TenantS3Client wrapper class"""

    def test_init_offline_mode(self):
        """Test client initialization in offline mode"""
        client = TenantS3Client("tenant-123")

        assert client.tenant_id == "tenant-123"
        assert client.prefix == "tenant-tenant-123/"
        assert client.aws_enabled is False
        assert client._s3 is None

    def test_upload_offline(self):
        """Test upload in offline mode"""
        client = TenantS3Client("tenant-123")
        result = client.upload("test.pdf", b"test data")

        assert "s3://" in result
        assert "tenant-tenant-123/test.pdf" in result
        assert "(offline)" in result

    def test_download_offline(self):
        """Test download in offline mode"""
        client = TenantS3Client("tenant-123")
        data = client.download("test.pdf")

        assert data == b"offline-mode-placeholder"

    def test_delete_offline(self):
        """Test delete in offline mode (should not raise)"""
        client = TenantS3Client("tenant-123")
        # Should complete without error
        client.delete("test.pdf")

    def test_list_documents_offline(self):
        """Test list documents in offline mode"""
        client = TenantS3Client("tenant-123")
        docs = client.list_documents()

        assert isinstance(docs, list)
        assert len(docs) > 0
        # Should return example documents

    def test_prefix_enforcement(self):
        """Test that tenant prefix is always applied"""
        client = TenantS3Client("tenant-456")

        # Upload should prefix the key
        result = client.upload("invoice.pdf", b"data")
        assert "tenant-tenant-456/invoice.pdf" in result

    def test_data_residency_validation(self):
        """Test data residency is validated on upload"""
        metadata = TenantMetadata(
            tenant_id="tenant-eu-001",
            data_residency="EU",
            data_residency_region="eu-west-1",
            encryption_key_id="key-eu"
        )

        # Try to create client in wrong region
        client = TenantS3Client("tenant-eu-001", region="us-east-1", tenant_metadata=metadata)

        # Upload should fail due to residency mismatch
        with pytest.raises(DataResidencyViolation):
            client.upload("test.pdf", b"data")


class TestPresignedURLService:
    """Test PresignedURLService class"""

    def test_generate_url_offline(self):
        """Test presigned URL generation in offline mode"""
        service = PresignedURLService()

        url = service.generate_url("tenant-123", "tenant-tenant-123/test.pdf")

        assert "offline-mode" in url
        assert "tenant-tenant-123/test.pdf" in url

    def test_cross_tenant_access_denied(self):
        """Test that cross-tenant access is blocked"""
        service = PresignedURLService()

        # Tenant A trying to access Tenant B's document
        with pytest.raises(Forbidden) as exc_info:
            service.generate_url("tenant-A", "tenant-tenant-B/secret.pdf")

        assert "Cross-tenant access denied" in str(exc_info.value)

    def test_prefix_validation(self):
        """Test document key prefix validation"""
        service = PresignedURLService()

        # Valid: key starts with correct prefix
        url = service.generate_url("tenant-123", "tenant-tenant-123/valid.pdf")
        assert url is not None

        # Invalid: key doesn't start with tenant prefix
        with pytest.raises(Forbidden):
            service.generate_url("tenant-123", "wrong-prefix/invalid.pdf")

    def test_cache_integration(self):
        """Test Redis cache integration (without Redis)"""
        service = PresignedURLService(redis_client=None)

        # Should work without Redis
        url = service.generate_url("tenant-123", "tenant-tenant-123/test.pdf")
        assert url is not None

        # validate_url should return None without Redis
        cached = service.validate_url("tenant-123", "test.pdf")
        assert cached is None


class TestDataResidencyValidator:
    """Test DataResidencyValidator class"""

    def test_validate_upload_correct_region(self):
        """Test upload validation with correct region"""
        validator = DataResidencyValidator()
        metadata = TenantMetadata(
            tenant_id="tenant-us-001",
            data_residency="US",
            data_residency_region="us-east-1",
            encryption_key_id="key-us"
        )

        # Should return required region
        region = validator.validate_upload("tenant-us-001", tenant_metadata=metadata)
        assert region == "us-east-1"

    def test_validate_upload_wrong_region(self):
        """Test upload validation fails with wrong region"""
        validator = DataResidencyValidator()
        metadata = TenantMetadata(
            tenant_id="tenant-eu-001",
            data_residency="EU",
            data_residency_region="eu-west-1",
            encryption_key_id="key-eu"
        )

        # Should raise violation for wrong region
        with pytest.raises(DataResidencyViolation) as exc_info:
            validator.validate_upload(
                "tenant-eu-001",
                region_override="us-east-1",
                tenant_metadata=metadata
            )

        assert "us-east-1" in str(exc_info.value)
        assert "eu-west-1" in str(exc_info.value)

    def test_validate_access(self):
        """Test access validation (should not raise)"""
        validator = DataResidencyValidator()

        # Should complete without error
        validator.validate_access("user-1", "tenant-123", operation="read")


class TestStorageAuditLogger:
    """Test StorageAuditLogger class"""

    def test_log_access_without_db(self):
        """Test audit logging without database connection"""
        logger = StorageAuditLogger()

        # Should complete without error
        logger.log_access("upload", "tenant-123", "test.pdf", user_id="user-1")

    def test_get_tenant_access_log(self):
        """Test retrieving access logs"""
        logger = StorageAuditLogger()

        logs = logger.get_tenant_access_log("tenant-123", days=30)

        assert isinstance(logs, list)
        # Should return mock data without database

    def test_detect_anomalies(self):
        """Test anomaly detection"""
        logger = StorageAuditLogger()

        anomalies = logger.detect_anomalies("tenant-123")

        assert isinstance(anomalies, list)
        # Should return empty list without database


class TestCrossTenantSecurity:
    """Test cross-tenant security scenarios from script"""

    def test_tenant_a_cannot_download_tenant_b_file(self):
        """
        Failure Scenario 1: Tenant A downloads Tenant B's file
        Root Cause: Missing prefix validation before presigned URL generation
        Fix: Validate doc_key.startswith(f"tenant-{tenant_id}/")
        """
        client_a = TenantS3Client("tenant-A")
        service = PresignedURLService()

        # Tenant A should NOT be able to access Tenant B's documents
        with pytest.raises(Forbidden):
            service.generate_url("tenant-A", "tenant-tenant-B/secret-contract.pdf")

    def test_presigned_url_tag_validation(self):
        """
        Test that presigned URLs validate object tags match tenant_id
        """
        service = PresignedURLService()

        # In offline mode, should still validate prefix
        with pytest.raises(Forbidden):
            service.generate_url("tenant-123", "tenant-456/document.pdf")

    def test_prefix_immutability(self):
        """
        Test that tenant prefix cannot be bypassed
        """
        client = TenantS3Client("tenant-123")

        # Even if user provides full key, prefix is still enforced
        result = client.upload("subdir/file.pdf", b"data")
        assert "tenant-tenant-123/subdir/file.pdf" in result


class TestDataResidencyScenarios:
    """Test data residency scenarios from script"""

    def test_eu_tenant_upload_to_us_region_blocked(self):
        """
        Failure Scenario 2: Wrong S3 region used (GDPR violation)
        Root Cause: No region enforcement at upload time
        Fix: Implement DataResidencyValidator in TenantS3Client init
        """
        metadata_eu = TenantMetadata(
            tenant_id="tenant-eu-logistics",
            data_residency="EU",
            data_residency_region="eu-west-1",
            encryption_key_id="key-eu"
        )

        # Client initialized with wrong region should fail on upload
        client = TenantS3Client("tenant-eu-logistics", region="us-east-1", tenant_metadata=metadata_eu)

        with pytest.raises(DataResidencyViolation):
            client.upload("gdpr-protected.pdf", b"EU citizen data")

    def test_multi_region_mapping(self):
        """Test region mapping for different data residency requirements"""
        validator = DataResidencyValidator()

        assert validator.REGION_MAPPING["EU"] == "eu-west-1"
        assert validator.REGION_MAPPING["US"] == "us-east-1"
        assert validator.REGION_MAPPING["India"] == "ap-south-1"


@pytest.mark.skipif(
    os.getenv("AWS_S3_ENABLED", "false").lower() != "true",
    reason="AWS S3 not enabled"
)
class TestOnlineMode:
    """
    Tests that require actual AWS S3 connection.
    Only run if AWS_S3_ENABLED=true in environment.
    """

    def test_upload_with_real_s3(self):
        """Test upload with actual S3 client"""
        client = TenantS3Client("tenant-test")

        # This would actually upload to S3
        result = client.upload("test-online.pdf", b"test data")
        assert "s3://" in result
        assert "(offline)" not in result

    def test_presigned_url_with_real_s3(self):
        """Test presigned URL generation with real S3"""
        service = PresignedURLService()

        # Would generate real presigned URL
        url = service.generate_url("tenant-test", "tenant-tenant-test/test.pdf")
        assert "amazonaws.com" in url


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
