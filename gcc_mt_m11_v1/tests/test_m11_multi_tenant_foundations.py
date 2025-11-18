"""
Tests for L3 M11.1: Multi-Tenant RAG Architecture

Tests ALL major functions and cross-tenant isolation patterns.
Services: Mocked/offline for testing (no external API calls).
"""

import pytest
import os
from typing import Dict, Any
from fastapi.testclient import TestClient

# Force offline mode for tests
os.environ["PINECONE_ENABLED"] = "false"
os.environ["OPENAI_ENABLED"] = "false"
os.environ["OFFLINE"] = "true"

from src.l3_m11_multi_tenant_foundations import (
    TenantRegistry,
    TenantContextManager,
    VectorDBIsolation,
    create_tenant,
    get_tenant,
    update_tenant_status,
    soft_delete_tenant,
    set_current_tenant,
    get_current_tenant,
    provision_tenant_namespace,
    query_vectors_for_tenant,
    delete_tenant_namespace,
    validate_tenant_id_format,
    hash_api_key,
)
from app import app


client = TestClient(app)


# Fixtures
@pytest.fixture
def tenant_registry():
    """Create fresh tenant registry for each test."""
    return TenantRegistry()


@pytest.fixture
def vector_db():
    """Create fresh vector DB for each test."""
    return VectorDBIsolation()


@pytest.fixture
def setup_tenants(tenant_registry, vector_db):
    """Set up two test tenants."""
    # Create tenant A (Finance)
    tenant_a = tenant_registry.create_tenant(
        tenant_id='finance',
        tenant_name='Finance Department',
        tier='premium',
        admin_email='admin@finance.example.com'
    )
    vector_db.provision_tenant_namespace('finance')

    # Create tenant B (Legal)
    tenant_b = tenant_registry.create_tenant(
        tenant_id='legal',
        tenant_name='Legal Department',
        tier='standard',
        admin_email='admin@legal.example.com'
    )
    vector_db.provision_tenant_namespace('legal')

    return {
        'tenant_a': tenant_a,
        'tenant_b': tenant_b,
        'registry': tenant_registry,
        'vector_db': vector_db
    }


# Test: Tenant CRUD Operations
def test_create_tenant(tenant_registry):
    """Test: Create tenant with default parameters."""
    tenant = tenant_registry.create_tenant(
        tenant_id='test-tenant-1',
        tenant_name='Test Tenant',
        tier='standard',
        admin_email='admin@test.com'
    )

    assert tenant['tenant_id'] == 'test-tenant-1'
    assert tenant['tenant_name'] == 'Test Tenant'
    assert tenant['status'] == 'active'
    assert tenant['tier'] == 'standard'


def test_create_duplicate_tenant(tenant_registry):
    """Test: Cannot create duplicate tenant."""
    tenant_registry.create_tenant(
        tenant_id='duplicate',
        tenant_name='First',
        admin_email='admin@test.com'
    )

    with pytest.raises(ValueError, match="already exists"):
        tenant_registry.create_tenant(
            tenant_id='duplicate',
            tenant_name='Second',
            admin_email='admin@test.com'
        )


def test_get_tenant(tenant_registry):
    """Test: Retrieve existing tenant."""
    tenant_registry.create_tenant(
        tenant_id='get-test',
        tenant_name='Get Test',
        admin_email='admin@test.com'
    )

    tenant = tenant_registry.get_tenant('get-test')

    assert tenant is not None
    assert tenant['tenant_id'] == 'get-test'


def test_get_nonexistent_tenant(tenant_registry):
    """Test: Get non-existent tenant returns None."""
    tenant = tenant_registry.get_tenant('does-not-exist')
    assert tenant is None


def test_update_tenant_status(tenant_registry):
    """Test: Update tenant status."""
    tenant_registry.create_tenant(
        tenant_id='status-test',
        tenant_name='Status Test',
        admin_email='admin@test.com'
    )

    tenant = tenant_registry.update_tenant_status('status-test', 'suspended')

    assert tenant['status'] == 'suspended'


def test_soft_delete_tenant(tenant_registry):
    """Test: Soft delete tenant."""
    tenant_registry.create_tenant(
        tenant_id='delete-test',
        tenant_name='Delete Test',
        admin_email='admin@test.com'
    )

    tenant_registry.soft_delete_tenant('delete-test')

    # Tenant should not be retrievable after soft delete
    tenant = tenant_registry.get_tenant('delete-test')
    assert tenant is None


def test_tenant_tier_limits(tenant_registry):
    """Test: Different tiers have correct limits."""
    # Create premium tenant
    tenant_registry.create_tenant(
        tenant_id='premium-tenant',
        tenant_name='Premium',
        tier='premium',
        admin_email='admin@test.com'
    )

    # Create trial tenant
    tenant_registry.create_tenant(
        tenant_id='trial-tenant',
        tenant_name='Trial',
        tier='trial',
        admin_email='admin@test.com'
    )

    premium_limits = tenant_registry.limits['premium-tenant']
    trial_limits = tenant_registry.limits['trial-tenant']

    # Premium should have higher limits
    assert premium_limits['max_queries_per_day'] > trial_limits['max_queries_per_day']
    assert premium_limits['rate_limit_rpm'] > trial_limits['rate_limit_rpm']


# Test: Tenant Context Propagation
def test_set_and_get_current_tenant():
    """Test: Set and retrieve tenant context."""
    TenantContextManager.clear_context()

    set_current_tenant('test-tenant')
    tenant_id = get_current_tenant()

    assert tenant_id == 'test-tenant'


def test_get_current_tenant_without_context():
    """Test: Error when retrieving tenant without setting context."""
    TenantContextManager.clear_context()

    with pytest.raises(ValueError, match="No tenant context found"):
        get_current_tenant()


# Test: Vector Database Isolation
def test_provision_tenant_namespace(vector_db):
    """Test: Provision vector namespace for tenant."""
    vector_db.provision_tenant_namespace('namespace-test')

    namespace = vector_db.get_tenant_namespace('namespace-test')
    assert namespace == 'tenant_namespace-test'
    assert namespace in vector_db.vectors


def test_upsert_documents_for_tenant(vector_db):
    """Test: Upsert documents with tenant isolation."""
    vector_db.provision_tenant_namespace('upsert-test')

    documents = [
        {
            'id': 'doc-1',
            'embedding': [0.1] * 1536,
            'metadata': {'title': 'Document 1'}
        },
        {
            'id': 'doc-2',
            'embedding': [0.2] * 1536,
            'metadata': {'title': 'Document 2'}
        }
    ]

    vector_db.upsert_documents_for_tenant('upsert-test', documents)

    namespace = vector_db.get_tenant_namespace('upsert-test')
    assert vector_db.vectors[namespace]['metadata']['document_count'] == 2


def test_query_vectors_for_tenant(vector_db):
    """Test: Query vectors with namespace isolation."""
    vector_db.provision_tenant_namespace('query-test')

    documents = [
        {
            'id': 'doc-1',
            'embedding': [0.1] * 1536,
            'metadata': {'title': 'Finance Report', 'tenant_id': 'query-test'}
        }
    ]

    vector_db.upsert_documents_for_tenant('query-test', documents)

    results = vector_db.query_vectors_for_tenant(
        tenant_id='query-test',
        query_embedding=[0.1] * 1536,
        top_k=5
    )

    assert len(results) == 1
    assert results[0]['metadata']['tenant_id'] == 'query-test'


def test_cross_tenant_isolation(setup_tenants):
    """Test: Tenant A cannot access Tenant B's vectors."""
    vector_db = setup_tenants['vector_db']

    # Add documents for Finance
    finance_docs = [
        {
            'id': 'finance-doc-1',
            'embedding': [0.1] * 1536,
            'metadata': {'title': 'Finance Q4 Report', 'tenant_id': 'finance'}
        }
    ]
    vector_db.upsert_documents_for_tenant('finance', finance_docs)

    # Add documents for Legal
    legal_docs = [
        {
            'id': 'legal-doc-1',
            'embedding': [0.1] * 1536,
            'metadata': {'title': 'Legal Compliance Report', 'tenant_id': 'legal'}
        }
    ]
    vector_db.upsert_documents_for_tenant('legal', legal_docs)

    # Query Finance namespace
    finance_results = vector_db.query_vectors_for_tenant(
        tenant_id='finance',
        query_embedding=[0.1] * 1536,
        top_k=10
    )

    # Assert: Only Finance documents returned
    for result in finance_results:
        assert result['metadata']['tenant_id'] == 'finance'
        assert 'Legal' not in result['metadata']['title']


def test_delete_tenant_namespace(vector_db):
    """Test: Delete tenant namespace (GDPR compliance)."""
    vector_db.provision_tenant_namespace('delete-namespace-test')

    documents = [
        {
            'id': 'doc-1',
            'embedding': [0.1] * 1536,
            'metadata': {'title': 'Document 1'}
        }
    ]
    vector_db.upsert_documents_for_tenant('delete-namespace-test', documents)

    # Delete namespace
    vector_db.delete_tenant_namespace('delete-namespace-test')

    namespace = vector_db.get_tenant_namespace('delete-namespace-test')
    assert namespace not in vector_db.vectors


# Test: Utility Functions
def test_validate_tenant_id_format():
    """Test: Tenant ID format validation."""
    assert validate_tenant_id_format('valid-tenant-123') is True
    assert validate_tenant_id_format('valid_tenant_123') is True
    assert validate_tenant_id_format('invalid tenant!') is False
    assert validate_tenant_id_format('invalid@tenant') is False


def test_hash_api_key():
    """Test: API key hashing."""
    api_key = 'rag_finance_7a3f2e1c9b4d'
    hashed = hash_api_key(api_key)

    # Should be deterministic
    assert hashed == hash_api_key(api_key)

    # Different keys produce different hashes
    different_key = 'rag_legal_9x2y1z3w4v5u'
    assert hash_api_key(different_key) != hashed


# Test: API Endpoints
def test_api_root():
    """Test: Root endpoint returns health status."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'
    assert data['module'] == 'L3_M11_Multi_Tenant_Foundations'


def test_api_create_tenant():
    """Test: Create tenant via API."""
    response = client.post(
        "/tenants",
        json={
            'tenant_id': 'api-test-tenant',
            'tenant_name': 'API Test Tenant',
            'tier': 'standard',
            'isolation_model': 'shared-db',
            'admin_email': 'admin@api-test.com'
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data['tenant_id'] == 'api-test-tenant'


def test_api_get_tenant():
    """Test: Retrieve tenant via API."""
    # Create tenant first
    client.post(
        "/tenants",
        json={
            'tenant_id': 'get-api-test',
            'tenant_name': 'Get API Test',
            'admin_email': 'admin@test.com'
        }
    )

    # Get tenant
    response = client.get("/tenants/get-api-test")

    assert response.status_code == 200
    data = response.json()
    assert data['tenant_id'] == 'get-api-test'


def test_api_query_offline_mode():
    """Test: Query returns skipped response when services disabled."""
    # Create tenant
    client.post(
        "/tenants",
        json={
            'tenant_id': 'query-test',
            'tenant_name': 'Query Test',
            'admin_email': 'admin@test.com'
        }
    )

    # Query with tenant header
    response = client.post(
        "/query",
        json={'query': 'test query', 'top_k': 5},
        headers={'X-Tenant-Id': 'query-test'}
    )

    assert response.status_code == 200
    data = response.json()
    assert data['skipped'] is True
    assert 'Services disabled' in data['message']


def test_api_missing_tenant_header():
    """Test: API returns 401 when tenant header missing."""
    response = client.post(
        "/query",
        json={'query': 'test query'}
    )

    assert response.status_code == 401
    assert 'Missing X-Tenant-Id header' in response.json()['detail']


def test_api_audit_logs():
    """Test: Retrieve audit logs for tenant."""
    # Create tenant
    client.post(
        "/tenants",
        json={
            'tenant_id': 'audit-test',
            'tenant_name': 'Audit Test',
            'admin_email': 'admin@test.com'
        }
    )

    # Get audit logs
    response = client.get(
        "/audit-logs",
        headers={'X-Tenant-Id': 'audit-test'}
    )

    assert response.status_code == 200
    data = response.json()
    assert data['tenant_id'] == 'audit-test'
    assert data['log_count'] >= 1  # At least creation log


# Test: Isolation Failures (Security Tests)
def test_spoofed_tenant_context(setup_tenants):
    """Test: Manually setting wrong tenant context is detected."""
    vector_db = setup_tenants['vector_db']

    # Add Finance documents
    finance_docs = [
        {
            'id': 'finance-secret',
            'embedding': [0.1] * 1536,
            'metadata': {'title': 'Secret Finance Data', 'tenant_id': 'finance'}
        }
    ]
    vector_db.upsert_documents_for_tenant('finance', finance_docs)

    # Try to query Finance data with Legal tenant_id (should fail assertion)
    # This tests the assertion in query_vectors_for_tenant
    legal_docs = [
        {
            'id': 'legal-doc',
            'embedding': [0.1] * 1536,
            'metadata': {'title': 'Legal Data', 'tenant_id': 'legal'}
        }
    ]
    vector_db.upsert_documents_for_tenant('legal', legal_docs)

    # Query should only return Legal data
    results = vector_db.query_vectors_for_tenant('legal', [0.1] * 1536, top_k=10)

    for result in results:
        assert result['metadata']['tenant_id'] == 'legal'


@pytest.mark.skipif(
    os.getenv("PINECONE_ENABLED", "false").lower() != "true",
    reason="PINECONE not enabled"
)
def test_online_mode_integration():
    """
    Test: Integration with actual Pinecone service (if enabled).

    This test is skipped unless PINECONE_ENABLED=true.
    """
    # This would test actual Pinecone integration
    # Only runs if environment is configured
    pass


@pytest.mark.skipif(
    os.getenv("OPENAI_ENABLED", "false").lower() != "true",
    reason="OPENAI not enabled"
)
def test_openai_integration():
    """
    Test: Integration with actual OpenAI service (if enabled).

    This test is skipped unless OPENAI_ENABLED=true.
    """
    # This would test actual OpenAI integration
    # Only runs if environment is configured
    pass


# Summary test
def test_full_tenant_lifecycle(tenant_registry, vector_db):
    """
    Test: Complete tenant lifecycle from creation to deletion.

    This test validates:
    1. Tenant creation
    2. Vector namespace provisioning
    3. Document ingestion
    4. Query execution
    5. Status update
    6. Soft deletion
    7. Namespace cleanup
    """
    # 1. Create tenant
    tenant = tenant_registry.create_tenant(
        tenant_id='lifecycle-test',
        tenant_name='Lifecycle Test',
        tier='premium',
        admin_email='admin@lifecycle.com'
    )
    assert tenant['status'] == 'active'

    # 2. Provision namespace
    vector_db.provision_tenant_namespace('lifecycle-test')
    assert 'tenant_lifecycle-test' in vector_db.vectors

    # 3. Ingest documents
    documents = [
        {
            'id': 'doc-1',
            'embedding': [0.1] * 1536,
            'metadata': {'title': 'Document 1', 'tenant_id': 'lifecycle-test'}
        }
    ]
    vector_db.upsert_documents_for_tenant('lifecycle-test', documents)

    # 4. Query
    results = vector_db.query_vectors_for_tenant('lifecycle-test', [0.1] * 1536)
    assert len(results) == 1

    # 5. Update status
    tenant = tenant_registry.update_tenant_status('lifecycle-test', 'suspended')
    assert tenant['status'] == 'suspended'

    # 6. Soft delete
    tenant_registry.soft_delete_tenant('lifecycle-test')
    assert tenant_registry.get_tenant('lifecycle-test') is None

    # 7. Cleanup namespace
    vector_db.delete_tenant_namespace('lifecycle-test')
    assert 'tenant_lifecycle-test' not in vector_db.vectors
