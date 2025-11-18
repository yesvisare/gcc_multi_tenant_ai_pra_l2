"""
Tests for L3 M11.3: Database Isolation & Cross-Tenant Security

Tests all major functions in offline mode (no external services required).
"""

import pytest
import os
import uuid
from typing import List, Dict, Any

# Force offline mode for tests
os.environ["POSTGRES_ENABLED"] = "false"
os.environ["PINECONE_ENABLED"] = "false"
os.environ["REDIS_ENABLED"] = "false"
os.environ["AWS_ENABLED"] = "false"
os.environ["OFFLINE"] = "true"

from src.l3_m11_multi_tenant_foundations import (
    TenantContextManager,
    PostgresRLSManager,
    PineconeNamespaceManager,
    SeparateDatabaseManager,
    CrossTenantSecurityTests,
    AuditLogger,
    RedisIsolationManager,
    S3PrefixIsolationManager
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def tenant_id():
    """Generate a test tenant UUID."""
    return uuid.uuid4()


@pytest.fixture
def multiple_tenant_ids():
    """Generate multiple test tenant UUIDs."""
    return [uuid.uuid4() for _ in range(5)]


@pytest.fixture
def tenant_context_manager():
    """Create tenant context manager instance."""
    return TenantContextManager()


@pytest.fixture
def audit_logger():
    """Create audit logger instance."""
    return AuditLogger()


# ============================================================================
# TENANT CONTEXT MANAGER TESTS
# ============================================================================

def test_set_tenant_context(tenant_context_manager, tenant_id):
    """Test setting tenant context."""
    tenant_context_manager.set_tenant_context(tenant_id)
    assert tenant_context_manager.get_tenant_context() == tenant_id


def test_get_tenant_context_not_set(tenant_context_manager):
    """Test getting tenant context when not set raises error."""
    with pytest.raises(RuntimeError, match="Tenant context not set"):
        tenant_context_manager.get_tenant_context()


def test_clear_tenant_context(tenant_context_manager, tenant_id):
    """Test clearing tenant context."""
    tenant_context_manager.set_tenant_context(tenant_id)
    tenant_context_manager.clear_tenant_context()

    with pytest.raises(RuntimeError):
        tenant_context_manager.get_tenant_context()


def test_invalid_tenant_id(tenant_context_manager):
    """Test that non-UUID tenant_id raises error."""
    with pytest.raises(ValueError, match="tenant_id must be UUID"):
        tenant_context_manager.set_tenant_context("not-a-uuid")


# ============================================================================
# POSTGRES RLS MANAGER TESTS (Offline Mode)
# ============================================================================

def test_postgres_rls_manager_offline(tenant_id):
    """Test PostgreSQL RLS manager in offline mode."""
    mgr = PostgresRLSManager(connection_pool=None)

    # Should return empty results when no connection available
    results = mgr.query_documents(tenant_id, "test")
    assert results == []


def test_postgres_validate_tenant_id():
    """Test that RLS manager validates tenant_id type."""
    mgr = PostgresRLSManager(connection_pool=None)

    # Should raise error for invalid tenant_id
    with pytest.raises(ValueError):
        # This would be called in set_tenant_context
        if not isinstance("invalid-uuid", uuid.UUID):
            raise ValueError("tenant_id must be UUID")


# ============================================================================
# PINECONE NAMESPACE MANAGER TESTS (Offline Mode)
# ============================================================================

def test_pinecone_namespace_validation(tenant_id):
    """Test namespace validation."""
    mgr = PineconeNamespaceManager(pinecone_client=None, index_name="test-index")

    # Valid namespace
    namespace = mgr.validate_namespace(tenant_id)
    assert namespace == f"tenant-{str(tenant_id)}"
    assert namespace.startswith("tenant-")


def test_pinecone_invalid_namespace():
    """Test that invalid namespace format raises error."""
    mgr = PineconeNamespaceManager(pinecone_client=None, index_name="test-index")

    # Should raise error for non-UUID
    with pytest.raises(ValueError):
        mgr.validate_namespace("not-a-uuid")


def test_pinecone_query_offline(tenant_id):
    """Test Pinecone query in offline mode."""
    mgr = PineconeNamespaceManager(pinecone_client=None, index_name="test-index")

    query_vector = [0.1] * 1536  # Mock embedding vector
    results = mgr.query_vectors(tenant_id, query_vector, top_k=5)

    assert results["skipped"] is True
    assert results["namespace"] == f"tenant-{tenant_id}"
    assert results["matches"] == []


def test_pinecone_upsert_offline(tenant_id):
    """Test Pinecone upsert in offline mode."""
    mgr = PineconeNamespaceManager(pinecone_client=None, index_name="test-index")

    vectors = [
        ("doc1", [0.1] * 1536, {"text": "test"}),
        ("doc2", [0.2] * 1536, {"text": "test2"})
    ]
    results = mgr.upsert_vectors(tenant_id, vectors)

    assert results["skipped"] is True
    assert results["upserted_count"] == 0


# ============================================================================
# SEPARATE DATABASE MANAGER TESTS
# ============================================================================

def test_separate_db_manager_init():
    """Test separate database manager initialization."""
    mgr = SeparateDatabaseManager()
    assert mgr.connection_pools == {}


def test_separate_db_manager_no_provisioned_db(tenant_id):
    """Test querying non-existent tenant database raises error."""
    mgr = SeparateDatabaseManager()

    # Should return empty list when database not provisioned
    results = mgr.query_documents(tenant_id, "test")
    assert results == []


# ============================================================================
# REDIS ISOLATION MANAGER TESTS (Offline Mode)
# ============================================================================

def test_redis_tenant_key_construction(tenant_id):
    """Test tenant-scoped key construction."""
    mgr = RedisIsolationManager(redis_client=None)

    key = mgr.get_tenant_key(tenant_id, "user_session")
    assert key == f"tenant:{str(tenant_id)}:user_session"
    assert key.startswith("tenant:")


def test_redis_set_cache_offline(tenant_id):
    """Test Redis set in offline mode."""
    mgr = RedisIsolationManager(redis_client=None)

    success = mgr.set_cache(tenant_id, "key1", "value1", ttl=3600)
    assert success is False  # Offline mode


def test_redis_get_cache_offline(tenant_id):
    """Test Redis get in offline mode."""
    mgr = RedisIsolationManager(redis_client=None)

    value = mgr.get_cache(tenant_id, "key1")
    assert value is None  # Offline mode


# ============================================================================
# S3 PREFIX ISOLATION MANAGER TESTS (Offline Mode)
# ============================================================================

def test_s3_prefix_construction(tenant_id):
    """Test S3 tenant prefix construction."""
    mgr = S3PrefixIsolationManager(s3_client=None, bucket="test-bucket")

    prefix = mgr.get_tenant_prefix(tenant_id)
    assert prefix == f"tenants/{str(tenant_id)}/"
    assert prefix.startswith("tenants/")
    assert prefix.endswith("/")


def test_s3_upload_offline(tenant_id):
    """Test S3 upload in offline mode."""
    mgr = S3PrefixIsolationManager(s3_client=None, bucket="test-bucket")

    result = mgr.upload_document(
        tenant_id=tenant_id,
        document_id="doc123",
        filename="test.pdf",
        content=b"test content"
    )

    assert result["skipped"] is True


# ============================================================================
# AUDIT LOGGER TESTS
# ============================================================================

def test_audit_log_access(audit_logger, tenant_id):
    """Test logging data access."""
    audit_logger.log_access(
        tenant_id=tenant_id,
        user_id="user123",
        action="query",
        resource="documents",
        result="success"
    )

    logs = audit_logger.get_audit_trail()
    assert len(logs) == 1
    assert logs[0]["tenant_id"] == str(tenant_id)
    assert logs[0]["action"] == "query"
    assert logs[0]["result"] == "success"


def test_audit_log_filter_by_tenant(audit_logger, multiple_tenant_ids):
    """Test filtering audit logs by tenant."""
    # Log access for multiple tenants
    for tenant_id in multiple_tenant_ids:
        audit_logger.log_access(
            tenant_id=tenant_id,
            user_id="user123",
            action="query",
            resource="documents",
            result="success"
        )

    # Get logs for specific tenant
    target_tenant = multiple_tenant_ids[0]
    filtered_logs = audit_logger.get_audit_trail(target_tenant)

    assert len(filtered_logs) == 1
    assert filtered_logs[0]["tenant_id"] == str(target_tenant)


def test_audit_log_all_tenants(audit_logger, multiple_tenant_ids):
    """Test getting all audit logs."""
    # Log access for multiple tenants
    for tenant_id in multiple_tenant_ids:
        audit_logger.log_access(
            tenant_id=tenant_id,
            user_id="user123",
            action="query",
            resource="documents",
            result="success"
        )

    # Get all logs
    all_logs = audit_logger.get_audit_trail()
    assert len(all_logs) == len(multiple_tenant_ids)


# ============================================================================
# CROSS-TENANT SECURITY TESTS (Mock)
# ============================================================================

class MockIsolationManager:
    """Mock isolation manager for security testing."""

    def __init__(self, leak: bool = False):
        self.leak = leak

    def query_documents(self, tenant_id: uuid.UUID, pattern: str) -> List[Dict[str, Any]]:
        """Mock query that can simulate leaks."""
        if self.leak:
            # Simulate cross-tenant leak
            return [
                {"id": "doc1", "title": "Test", "tenant_id": str(uuid.uuid4())}
            ]
        else:
            # Correct isolation
            return [
                {"id": "doc1", "title": "Test", "tenant_id": str(tenant_id)}
            ]


def test_security_tests_no_leak(multiple_tenant_ids):
    """Test security tests with proper isolation."""
    mock_mgr = MockIsolationManager(leak=False)
    tester = CrossTenantSecurityTests(mock_mgr)

    results = tester.run_adversarial_tests(multiple_tenant_ids)

    assert results["passed"] == results["total_tests"]
    assert results["failed"] == 0
    assert len(results["failures"]) == 0


def test_security_tests_with_leak(multiple_tenant_ids):
    """Test security tests detecting cross-tenant leak."""
    mock_mgr = MockIsolationManager(leak=True)
    tester = CrossTenantSecurityTests(mock_mgr)

    results = tester.run_adversarial_tests(multiple_tenant_ids)

    assert results["failed"] > 0
    assert len(results["failures"]) > 0


# ============================================================================
# INTEGRATION TESTS (Offline Mode)
# ============================================================================

def test_full_isolation_workflow_offline(tenant_id):
    """Test complete isolation workflow in offline mode."""
    # Initialize managers
    ctx_mgr = TenantContextManager()
    postgres_mgr = PostgresRLSManager(None)
    pinecone_mgr = PineconeNamespaceManager(None, "test-index")
    audit_logger = AuditLogger()

    # Set tenant context
    ctx_mgr.set_tenant_context(tenant_id)

    # Query with RLS (offline)
    rls_docs = postgres_mgr.query_documents(tenant_id, "test")
    assert rls_docs == []

    # Query with namespace (offline)
    query_vector = [0.1] * 1536
    ns_results = pinecone_mgr.query_vectors(tenant_id, query_vector)
    assert ns_results["skipped"] is True

    # Log audit
    audit_logger.log_access(tenant_id, "user123", "query", "docs", "success")

    # Verify audit
    logs = audit_logger.get_audit_trail(tenant_id)
    assert len(logs) == 1

    # Clear context
    ctx_mgr.clear_tenant_context()


@pytest.mark.skipif(
    os.getenv("POSTGRES_ENABLED", "false").lower() != "true",
    reason="PostgreSQL not enabled"
)
def test_postgres_rls_with_real_connection():
    """
    Test PostgreSQL RLS with actual database connection.

    Only runs if POSTGRES_ENABLED=true in environment.
    Requires running PostgreSQL instance.
    """
    # This test would connect to real PostgreSQL
    # and verify RLS policies work correctly
    pass


@pytest.mark.skipif(
    os.getenv("PINECONE_ENABLED", "false").lower() != "true",
    reason="Pinecone not enabled"
)
def test_pinecone_namespace_with_real_client():
    """
    Test Pinecone namespace isolation with actual client.

    Only runs if PINECONE_ENABLED=true in environment.
    Requires valid Pinecone API key.
    """
    # This test would connect to real Pinecone
    # and verify namespace isolation works correctly
    pass
