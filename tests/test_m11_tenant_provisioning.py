"""
Tests for L3 M11.4: Tenant Provisioning & Automation

Tests ALL major functions from the provisioning workflow.
SERVICE: PROVISIONING (mocked/offline for testing)
"""

import pytest
import asyncio
import os
from src.l3_m11_tenant_provisioning import (
    TenantTier,
    TenantStatus,
    TenantRequest,
    provision_infrastructure,
    initialize_tenant_config,
    validate_tenant,
    activate_tenant,
    rollback_provisioning,
    approve_tenant_request,
    provision_tenant_workflow,
    simulate_provisioning_workflow
)

# Force offline mode for tests
os.environ["PROVISIONING_ENABLED"] = "false"
os.environ["OFFLINE"] = "true"


# ========== TenantRequest Tests ==========

def test_tenant_request_creation():
    """Test TenantRequest object creation"""
    request = TenantRequest(
        tenant_name="Test Corp",
        tier=TenantTier.SILVER,
        region="us-east-1",
        budget=500000,
        owner_email="admin@testcorp.com"
    )

    assert request.tenant_id == "tenant_test_corp"
    assert request.tenant_name == "Test Corp"
    assert request.tier == TenantTier.SILVER
    assert request.region == "us-east-1"
    assert request.budget == 500000
    assert request.owner_email == "admin@testcorp.com"
    assert request.status == TenantStatus.PENDING


def test_tenant_request_to_dict():
    """Test TenantRequest serialization"""
    request = TenantRequest(
        tenant_name="Demo Inc",
        tier=TenantTier.GOLD,
        region="eu-west-1",
        budget=2000000,
        owner_email="cto@demoinc.com"
    )

    data = request.to_dict()

    assert data["tenant_id"] == "tenant_demo_inc"
    assert data["tier"] == "Gold"
    assert data["status"] == "pending"
    assert "created_at" in data


# ========== Infrastructure Provisioning Tests ==========

@pytest.mark.asyncio
async def test_provision_infrastructure_offline():
    """Test infrastructure provisioning in offline mode"""
    result = await provision_infrastructure(
        tenant_id="tenant_test1",
        tier=TenantTier.SILVER,
        region="us-east-1",
        offline=True
    )

    assert result["status"] == "simulated"
    assert result["tenant_id"] == "tenant_test1"
    assert "resources" in result
    assert "postgresql_schema" in result["resources"]
    assert "vector_db_namespace" in result["resources"]
    assert "s3_bucket" in result["resources"]
    assert "redis_namespace" in result["resources"]
    assert "monitoring_dashboard" in result["resources"]


@pytest.mark.asyncio
async def test_provision_infrastructure_resources():
    """Test infrastructure provisioning returns correct resource structure"""
    result = await provision_infrastructure(
        tenant_id="tenant_acme",
        tier=TenantTier.GOLD,
        region="us-west-2",
        offline=True
    )

    resources = result["resources"]
    assert resources["postgresql_schema"] == "tenant_acme_schema"
    assert resources["vector_db_namespace"] == "tenant_acme_vectors"
    assert resources["s3_bucket"] == "tenant_acme-documents"
    assert resources["redis_namespace"] == "tenant_acme:cache"
    assert resources["monitoring_dashboard"] == "grafana-tenant_acme"


# ========== Configuration Initialization Tests ==========

@pytest.mark.asyncio
async def test_initialize_tenant_config_gold():
    """Test configuration initialization for Gold tier"""
    result = await initialize_tenant_config(
        tenant_id="tenant_premium",
        tier=TenantTier.GOLD,
        offline=True
    )

    assert result["tier"] == "Gold"
    assert result["feature_flags"]["advanced_search"] is True
    assert result["feature_flags"]["real_time_indexing"] is True
    assert result["feature_flags"]["custom_models"] is True
    assert result["rate_limits"]["queries_per_minute"] == 1000
    assert result["rate_limits"]["documents_per_month"] == 100000
    assert result["llm_config"]["model"] == "gpt-4"
    assert result["demo_documents_seeded"] is True


@pytest.mark.asyncio
async def test_initialize_tenant_config_silver():
    """Test configuration initialization for Silver tier"""
    result = await initialize_tenant_config(
        tenant_id="tenant_standard",
        tier=TenantTier.SILVER,
        offline=True
    )

    assert result["tier"] == "Silver"
    assert result["feature_flags"]["advanced_search"] is False
    assert result["feature_flags"]["real_time_indexing"] is True
    assert result["feature_flags"]["custom_models"] is False
    assert result["rate_limits"]["queries_per_minute"] == 500
    assert result["rate_limits"]["documents_per_month"] == 50000
    assert result["llm_config"]["model"] == "gpt-3.5-turbo"
    assert result["demo_documents_seeded"] is False


@pytest.mark.asyncio
async def test_initialize_tenant_config_bronze():
    """Test configuration initialization for Bronze tier"""
    result = await initialize_tenant_config(
        tenant_id="tenant_basic",
        tier=TenantTier.BRONZE,
        offline=True
    )

    assert result["tier"] == "Bronze"
    assert result["feature_flags"]["advanced_search"] is False
    assert result["feature_flags"]["real_time_indexing"] is False
    assert result["rate_limits"]["queries_per_minute"] == 100
    assert result["rate_limits"]["documents_per_month"] == 10000
    assert result["llm_config"]["model"] == "gpt-3.5-turbo"


# ========== Validation Tests ==========

@pytest.mark.asyncio
async def test_validate_tenant_offline():
    """Test tenant validation in offline mode"""
    result = await validate_tenant("tenant_test2", offline=True)

    assert result["status"] == "simulated"
    assert result["all_tests_passed"] is True
    assert len(result["tests"]) == 8

    # Verify all 8 tests are present
    expected_tests = [
        "database_connectivity",
        "tenant_isolation",
        "vector_search",
        "jwt_authentication",
        "query_performance",
        "s3_permissions",
        "metrics_collection",
        "cost_tags"
    ]

    for test_name in expected_tests:
        assert test_name in result["tests"]
        assert result["tests"][test_name]["passed"] is True


@pytest.mark.asyncio
async def test_validate_tenant_test_structure():
    """Test validation returns correct test structure"""
    result = await validate_tenant("tenant_validate", offline=True)

    # Check query performance test has latency metric
    perf_test = result["tests"]["query_performance"]
    assert "latency_ms" in perf_test
    assert perf_test["latency_ms"] == 250
    assert perf_test["passed"] is True


# ========== Activation Tests ==========

@pytest.mark.asyncio
async def test_activate_tenant_offline():
    """Test tenant activation in offline mode"""
    result = await activate_tenant("tenant_test3", offline=True)

    assert result["status"] == "simulated"
    assert result["tenant_id"] == "tenant_test3"
    assert result["notifications_sent"] is False
    assert "activated_at" in result


@pytest.mark.asyncio
async def test_activate_tenant_online_simulation():
    """Test tenant activation (simulated online mode)"""
    result = await activate_tenant("tenant_activate", offline=False)

    assert result["status"] == "active"
    assert result["tenant_id"] == "tenant_activate"
    assert result["notifications_sent"] is True
    assert "notification_channels" in result
    assert "email" in result["notification_channels"]
    assert "slack" in result["notification_channels"]


# ========== Rollback Tests ==========

@pytest.mark.asyncio
async def test_rollback_provisioning_offline():
    """Test rollback in offline mode"""
    result = await rollback_provisioning(
        tenant_id="tenant_test4",
        failed_step="validation_testing",
        offline=True
    )

    assert result["status"] == "simulated"
    assert result["tenant_id"] == "tenant_test4"
    assert result["failed_step"] == "validation_testing"
    assert "rollback_actions" in result


@pytest.mark.asyncio
async def test_rollback_provisioning_actions():
    """Test rollback executes correct actions"""
    result = await rollback_provisioning(
        tenant_id="tenant_rollback",
        failed_step="infrastructure_provisioning",
        offline=False
    )

    assert result["status"] == "rollback_successful"
    assert len(result["rollback_actions"]) == 3
    assert "terraform_destroy_completed" in result["rollback_actions"]
    assert "registry_deletion_completed" in result["rollback_actions"]
    assert "notification_sent" in result["rollback_actions"]


# ========== Approval Workflow Tests ==========

@pytest.mark.asyncio
async def test_approve_tenant_auto_approval():
    """Test auto-approval for budgets below threshold"""
    result = await approve_tenant_request(
        tenant_id="tenant_test5",
        budget=500000,  # ₹5 lakh (below ₹10L threshold)
        offline=True
    )

    assert result["decision"] == "approved"
    assert result["approval_type"] == "automatic"
    assert "auto-approval" in result["reason"]


@pytest.mark.asyncio
async def test_approve_tenant_manual_required():
    """Test manual approval required for high budgets"""
    result = await approve_tenant_request(
        tenant_id="tenant_test6",
        budget=15000000,  # ₹1.5 crore (above ₹10L threshold)
        offline=True
    )

    assert result["decision"] == "pending_manual_approval"
    assert result["approval_type"] == "manual_required"
    assert "CFO approval" in result["reason"]


@pytest.mark.asyncio
async def test_approve_tenant_threshold_boundary():
    """Test approval at exact threshold boundary"""
    # Exactly at threshold
    result1 = await approve_tenant_request(
        tenant_id="tenant_boundary1",
        budget=1000000,  # Exactly ₹10L
        offline=True
    )
    assert result1["decision"] == "pending_manual_approval"  # >= threshold requires approval

    # Just below threshold
    result2 = await approve_tenant_request(
        tenant_id="tenant_boundary2",
        budget=999999,  # ₹9.99L
        offline=True
    )
    assert result2["decision"] == "approved"  # < threshold auto-approves


# ========== End-to-End Workflow Tests ==========

@pytest.mark.asyncio
async def test_provision_tenant_workflow_success():
    """Test complete provisioning workflow (success path)"""
    request = TenantRequest(
        tenant_name="Workflow Test Corp",
        tier=TenantTier.SILVER,
        region="us-east-1",
        budget=500000,
        owner_email="admin@workflowtest.com"
    )

    result = await provision_tenant_workflow(request, offline=True)

    assert result["status"] == "completed"
    assert result["tenant_id"] == "tenant_workflow_test_corp"
    assert "total_duration_minutes" in result
    assert len(result["steps_completed"]) >= 7  # All steps except rollback

    # Verify key steps were completed
    assert "request_submission" in result["steps_completed"]
    assert "approval" in result["steps_completed"]
    assert "infrastructure_provisioning" in result["steps_completed"]
    assert "configuration_initialization" in result["steps_completed"]
    assert "validation_testing" in result["steps_completed"]
    assert "activation" in result["steps_completed"]
    assert "notification" in result["steps_completed"]


@pytest.mark.asyncio
async def test_provision_tenant_workflow_high_budget_rejection():
    """Test workflow handles high-budget manual approval requirement"""
    request = TenantRequest(
        tenant_name="Enterprise Corp",
        tier=TenantTier.GOLD,
        region="us-east-1",
        budget=20000000,  # ₹2 crore
        owner_email="cfo@enterprise.com"
    )

    result = await provision_tenant_workflow(request, offline=True)

    # Should stop at approval step
    assert result["status"] == "rejected"  # Pending manual approval treated as rejection in workflow
    assert "steps_completed" in result
    assert "approval" in result["steps_completed"]


@pytest.mark.asyncio
async def test_simulate_provisioning_workflow():
    """Test simulation convenience function"""
    result = await simulate_provisioning_workflow(
        tenant_name="Simulation Test",
        tier=TenantTier.SILVER,
        region="us-east-1",
        budget=500000
    )

    assert result["status"] == "completed"
    assert result["tenant_id"] == "tenant_simulation_test"
    assert "approval" in result
    assert "infrastructure" in result
    assert "configuration" in result
    assert "validation" in result
    assert "activation" in result


@pytest.mark.asyncio
async def test_simulate_provisioning_workflow_all_tiers():
    """Test simulation for all three tiers"""
    tiers = [TenantTier.GOLD, TenantTier.SILVER, TenantTier.BRONZE]

    for tier in tiers:
        result = await simulate_provisioning_workflow(
            tenant_name=f"Test {tier.value}",
            tier=tier,
            region="us-east-1",
            budget=500000
        )

        assert result["status"] == "completed"
        assert result["configuration"]["tier"] == tier.value

        # Verify tier-specific configuration
        if tier == TenantTier.GOLD:
            assert result["configuration"]["feature_flags"]["advanced_search"] is True
            assert result["configuration"]["llm_config"]["model"] == "gpt-4"
        elif tier == TenantTier.SILVER:
            assert result["configuration"]["feature_flags"]["real_time_indexing"] is True
            assert result["configuration"]["llm_config"]["model"] == "gpt-3.5-turbo"
        elif tier == TenantTier.BRONZE:
            assert result["configuration"]["rate_limits"]["queries_per_minute"] == 100


# ========== Performance and Edge Case Tests ==========

@pytest.mark.asyncio
async def test_workflow_timing():
    """Test workflow completes within expected timeframe (offline mode)"""
    import time

    request = TenantRequest(
        tenant_name="Performance Test",
        tier=TenantTier.SILVER,
        region="us-east-1",
        budget=500000,
        owner_email="perf@test.com"
    )

    start = time.time()
    result = await provision_tenant_workflow(request, offline=True)
    duration = time.time() - start

    # Offline mode should complete in <2 seconds
    assert duration < 2.0
    assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_concurrent_provisioning():
    """Test multiple tenants can be provisioned concurrently"""
    requests = [
        TenantRequest(
            tenant_name=f"Concurrent Test {i}",
            tier=TenantTier.SILVER,
            region="us-east-1",
            budget=500000,
            owner_email=f"tenant{i}@test.com"
        )
        for i in range(3)
    ]

    # Provision concurrently
    results = await asyncio.gather(*[
        provision_tenant_workflow(req, offline=True)
        for req in requests
    ])

    # Verify all succeeded
    assert len(results) == 3
    for result in results:
        assert result["status"] == "completed"


# ========== Pytest Configuration ==========

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
