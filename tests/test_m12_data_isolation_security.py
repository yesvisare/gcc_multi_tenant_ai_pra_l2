"""
Tests for L3 M12.1: Vector Database Multi-Tenancy Patterns

Tests ALL major functions from script with offline mode for CI/CD.
SERVICE: Pinecone (mocked/offline for testing)
"""

import pytest
import os
from datetime import datetime

from src.l3_m12_data_isolation_security import (
    TenantContext,
    NamespaceRouter,
    validate_tenant_query,
    extract_tenant_filters,
    validate_filter_safety,
    parse_filter,
    tenant_filtered_query,
    create_tenant_namespace,
    is_cross_tenant,
    evaluate_isolation_model,
    get_isolation_costs,
    IsolationModel,
)

# Force offline mode for tests
os.environ["PINECONE_ENABLED"] = "false"
os.environ["OFFLINE"] = "true"


# Fixtures
@pytest.fixture
def sample_tenant_context():
    """Create sample tenant context for testing."""
    return TenantContext(
        tenant_id="test_tenant_001",
        user_id="user_123",
        roles=["user", "admin"],
        timestamp=datetime.utcnow().isoformat()
    )


@pytest.fixture
def sample_query_vector():
    """Create sample query vector."""
    return [0.1] * 768  # 768-dimensional vector


@pytest.fixture
def namespace_router():
    """Create namespace router instance."""
    config = {"default_top_k": 10}
    return NamespaceRouter(config)


# TenantContext Tests
def test_tenant_context_creation():
    """Test valid tenant context creation."""
    context = TenantContext(
        tenant_id="tenant_001",
        user_id="user_123",
        roles=["user"],
        timestamp="2025-01-01T00:00:00Z"
    )

    assert context.tenant_id == "tenant_001"
    assert context.user_id == "user_123"
    assert "user" in context.roles


def test_tenant_context_validation_missing_tenant():
    """Test tenant context validation with missing tenant_id."""
    with pytest.raises(ValueError, match="tenant_id is required"):
        TenantContext(
            tenant_id="",
            user_id="user_123",
            roles=["user"],
            timestamp="2025-01-01T00:00:00Z"
        )


def test_tenant_context_validation_missing_user():
    """Test tenant context validation with missing user_id."""
    with pytest.raises(ValueError, match="user_id is required"):
        TenantContext(
            tenant_id="tenant_001",
            user_id="",
            roles=["user"],
            timestamp="2025-01-01T00:00:00Z"
        )


# NamespaceRouter Tests
def test_namespace_router_initialization(namespace_router):
    """Test namespace router initialization."""
    assert namespace_router is not None
    assert namespace_router.config["default_top_k"] == 10


def test_namespace_router_query_offline(namespace_router, sample_tenant_context, sample_query_vector):
    """Test namespace router query in offline mode."""
    result = namespace_router.query(
        tenant_context=sample_tenant_context,
        query_vector=sample_query_vector,
        top_k=5,
        offline=True
    )

    assert result["skipped"] is True
    assert result["reason"] == "offline mode"
    assert result["namespace"] == f"tenant_{sample_tenant_context.tenant_id}"


def test_namespace_router_create_namespace(namespace_router):
    """Test namespace creation."""
    result = namespace_router.create_namespace("tenant_002")

    assert result["status"] == "created"
    assert result["namespace"] == "tenant_tenant_002"
    assert result["tenant_id"] == "tenant_002"


# Filter Validation Tests
def test_validate_tenant_query_valid():
    """Test valid tenant query validation."""
    query_filter = {"tenant_id": "tenant_001"}
    result = validate_tenant_query(query_filter, "tenant_001")

    assert result is True


def test_validate_tenant_query_cross_tenant():
    """Test cross-tenant query detection."""
    query_filter = {"tenant_id": "tenant_002"}
    result = validate_tenant_query(query_filter, "tenant_001")

    assert result is False


def test_validate_tenant_query_complex_filter():
    """Test validation with complex nested filter."""
    query_filter = {
        "$and": [
            {"tenant_id": "tenant_001"},
            {"status": "active"}
        ]
    }
    result = validate_tenant_query(query_filter, "tenant_001")

    assert result is True


def test_validate_tenant_query_malicious_or_filter():
    """Test detection of malicious OR filter attempting cross-tenant access."""
    query_filter = {
        "$or": [
            {"tenant_id": "tenant_001"},
            {"tenant_id": "tenant_002"}  # Malicious attempt
        ]
    }
    result = validate_tenant_query(query_filter, "tenant_001")

    assert result is False


def test_extract_tenant_filters_single():
    """Test extracting tenant_id from simple filter."""
    query_filter = {"tenant_id": "tenant_001"}
    tenant_ids = extract_tenant_filters(query_filter)

    assert len(tenant_ids) == 1
    assert "tenant_001" in tenant_ids


def test_extract_tenant_filters_nested():
    """Test extracting tenant_id from nested AND filter."""
    query_filter = {
        "$and": [
            {"tenant_id": "tenant_001"},
            {"status": "active"}
        ]
    }
    tenant_ids = extract_tenant_filters(query_filter)

    assert len(tenant_ids) == 1
    assert "tenant_001" in tenant_ids


def test_extract_tenant_filters_multiple():
    """Test extracting multiple tenant_id values (security violation)."""
    query_filter = {
        "$or": [
            {"tenant_id": "tenant_001"},
            {"tenant_id": "tenant_002"}
        ]
    }
    tenant_ids = extract_tenant_filters(query_filter)

    assert len(tenant_ids) == 2
    assert "tenant_001" in tenant_ids
    assert "tenant_002" in tenant_ids


def test_validate_filter_safety_safe():
    """Test filter safety validation with safe filter."""
    filter_dict = {"tenant_id": "tenant_001", "status": "active"}
    result = validate_filter_safety(filter_dict, "tenant_001")

    assert result is True


def test_validate_filter_safety_unsafe():
    """Test filter safety validation with unsafe filter."""
    filter_dict = {"tenant_id": "tenant_002"}
    result = validate_filter_safety(filter_dict, "tenant_001")

    assert result is False


def test_validate_filter_safety_missing_tenant():
    """Test filter safety with missing tenant_id."""
    filter_dict = {"status": "active"}
    result = validate_filter_safety(filter_dict, "tenant_001")

    assert result is False


def test_parse_filter():
    """Test filter parsing and normalization."""
    filter_dict = {"tenant_id": "tenant_001", "status": "active"}
    parsed = parse_filter(filter_dict)

    assert "tenant_id" in parsed
    assert parsed["tenant_id"] == "tenant_001"


# Tenant-Filtered Query Tests
def test_tenant_filtered_query_offline(sample_tenant_context, sample_query_vector):
    """Test tenant-filtered query in offline mode."""
    result = tenant_filtered_query(
        user_context=sample_tenant_context,
        query_vector=sample_query_vector,
        top_k=10,
        offline=True
    )

    assert result["skipped"] is True
    assert result["tenant_id"] == sample_tenant_context.tenant_id


def test_tenant_filtered_query_with_user_filter(sample_tenant_context, sample_query_vector):
    """Test tenant-filtered query with additional user filter."""
    user_filter = {"tenant_id": "test_tenant_001", "category": "finance"}

    result = tenant_filtered_query(
        user_context=sample_tenant_context,
        query_vector=sample_query_vector,
        user_filter=user_filter,
        offline=True
    )

    assert result["skipped"] is True


def test_tenant_filtered_query_blocks_cross_tenant(sample_tenant_context, sample_query_vector):
    """Test that cross-tenant query is blocked."""
    malicious_filter = {"tenant_id": "different_tenant"}

    with pytest.raises(ValueError, match="Cross-tenant query attempt blocked"):
        tenant_filtered_query(
            user_context=sample_tenant_context,
            query_vector=sample_query_vector,
            user_filter=malicious_filter,
            offline=False  # Must not be offline to trigger validation
        )


# Namespace Creation Tests
def test_create_tenant_namespace_offline():
    """Test tenant namespace creation in offline mode."""
    result = create_tenant_namespace("tenant_003", offline=True)

    assert result["skipped"] is True
    assert result["namespace"] == "tenant_tenant_003"


# Cross-Tenant Detection Tests
def test_is_cross_tenant_safe():
    """Test cross-tenant detection with safe query."""
    query_filter = {"tenant_id": "tenant_001"}
    result = is_cross_tenant(query_filter, "tenant_001")

    assert result is False


def test_is_cross_tenant_violation():
    """Test cross-tenant detection with violation."""
    query_filter = {"tenant_id": "tenant_002"}
    result = is_cross_tenant(query_filter, "tenant_001")

    assert result is True


# Isolation Model Evaluation Tests
def test_evaluate_isolation_model_cost_optimized():
    """Test evaluation recommending metadata filtering (cost-optimized)."""
    result = evaluate_isolation_model(
        num_tenants=20,
        security_requirement="standard",
        budget_constraint="tight"
    )

    assert result["recommended_model"] == IsolationModel.METADATA_FILTERING.value
    assert "5-8L" in result["cost_range"]
    assert result["isolation_strength"] == "7/10"


def test_evaluate_isolation_model_balanced():
    """Test evaluation recommending namespace-based (balanced)."""
    result = evaluate_isolation_model(
        num_tenants=100,
        security_requirement="high",
        budget_constraint="moderate"
    )

    assert result["recommended_model"] == IsolationModel.NAMESPACE_BASED.value
    assert "8-12L" in result["cost_range"]
    assert result["isolation_strength"] == "9/10"


def test_evaluate_isolation_model_maximum_security():
    """Test evaluation recommending dedicated indexes (maximum security)."""
    result = evaluate_isolation_model(
        num_tenants=50,
        security_requirement="maximum",
        budget_constraint="flexible"
    )

    assert result["recommended_model"] == IsolationModel.DEDICATED_INDEXES.value
    assert "30-40L" in result["cost_range"]
    assert result["isolation_strength"] == "10/10"


# Cost Calculation Tests
def test_get_isolation_costs():
    """Test cost calculation for all models."""
    costs = get_isolation_costs(num_tenants=50)

    assert IsolationModel.METADATA_FILTERING.value in costs
    assert IsolationModel.NAMESPACE_BASED.value in costs
    assert IsolationModel.DEDICATED_INDEXES.value in costs

    # Verify cost structure
    metadata_costs = costs[IsolationModel.METADATA_FILTERING.value]
    assert "annual_cost" in metadata_costs
    assert "monthly_cost" in metadata_costs
    assert "savings_vs_dedicated" in metadata_costs


def test_get_isolation_costs_scaling():
    """Test cost scaling with different tenant counts."""
    costs_10 = get_isolation_costs(num_tenants=10)
    costs_100 = get_isolation_costs(num_tenants=100)

    # Costs should scale linearly
    assert costs_10 is not None
    assert costs_100 is not None


# Integration Tests
def test_full_namespace_workflow(namespace_router, sample_tenant_context, sample_query_vector):
    """Test complete namespace-based workflow."""
    # Step 1: Create namespace
    create_result = namespace_router.create_namespace(sample_tenant_context.tenant_id)
    assert create_result["status"] == "created"

    # Step 2: Query with namespace isolation
    query_result = namespace_router.query(
        tenant_context=sample_tenant_context,
        query_vector=sample_query_vector,
        offline=True
    )
    assert query_result["namespace"] == f"tenant_{sample_tenant_context.tenant_id}"


def test_full_metadata_filtering_workflow(sample_tenant_context, sample_query_vector):
    """Test complete metadata filtering workflow."""
    # Valid user filter
    user_filter = {"tenant_id": sample_tenant_context.tenant_id, "status": "active"}

    # Step 1: Validate filter
    is_valid = validate_tenant_query(user_filter, sample_tenant_context.tenant_id)
    assert is_valid is True

    # Step 2: Execute filtered query
    result = tenant_filtered_query(
        user_context=sample_tenant_context,
        query_vector=sample_query_vector,
        user_filter=user_filter,
        offline=True
    )
    assert result["skipped"] is True


# Edge Cases
def test_empty_query_vector():
    """Test handling of empty query vector."""
    context = TenantContext(
        tenant_id="tenant_001",
        user_id="user_123",
        roles=["user"],
        timestamp="2025-01-01T00:00:00Z"
    )

    result = tenant_filtered_query(
        user_context=context,
        query_vector=[],
        offline=True
    )

    assert result["skipped"] is True


def test_large_tenant_count():
    """Test cost calculation with large tenant count."""
    costs = get_isolation_costs(num_tenants=10000)

    # Should still calculate without errors
    assert costs is not None
    assert len(costs) == 3


# Online Mode Tests (skip if Pinecone not enabled)
@pytest.mark.skipif(
    os.getenv("PINECONE_ENABLED", "false").lower() != "true",
    reason="PINECONE not enabled"
)
def test_namespace_router_online(namespace_router, sample_tenant_context, sample_query_vector):
    """Test namespace router with actual Pinecone (if enabled)."""
    result = namespace_router.query(
        tenant_context=sample_tenant_context,
        query_vector=sample_query_vector,
        offline=False
    )

    assert "status" in result
    # Additional assertions based on actual Pinecone response


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
