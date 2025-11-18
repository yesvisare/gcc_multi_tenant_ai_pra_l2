"""
Tests for L3 M11.2: Tenant Metadata & Registry Design

Comprehensive test suite covering:
- Tenant CRUD operations
- Feature flag hierarchical evaluation
- Lifecycle state machine transitions
- Cascading operations
- Health monitoring
"""

import pytest
from datetime import datetime
from src.l3_m11_multi_tenant_foundations import (
    TenantRegistry,
    TenantStatus,
    Tenant,
    LifecycleManager,
    FeatureFlagService,
    FeatureFlag,
    CascadingOperations,
    HealthMonitor,
)


# Tenant CRUD Tests

def test_create_tenant():
    """Test tenant creation with valid data."""
    registry = TenantRegistry()
    tenant = registry.create_tenant({
        "tenant_id": "test_tenant",
        "tenant_name": "Test Tenant",
        "tier": "gold",
        "max_users": 50
    })

    assert tenant.tenant_id == "test_tenant"
    assert tenant.tenant_name == "Test Tenant"
    assert tenant.tier == "gold"
    assert tenant.status == TenantStatus.ACTIVE
    assert tenant.max_users == 50
    assert tenant.health_score == 100


def test_create_tenant_invalid_tier():
    """Test tenant creation fails with invalid tier."""
    registry = TenantRegistry()

    with pytest.raises(ValueError, match="Invalid tier"):
        registry.create_tenant({
            "tenant_id": "test_tenant",
            "tenant_name": "Test Tenant",
            "tier": "invalid_tier"
        })


def test_create_duplicate_tenant():
    """Test creating duplicate tenant fails."""
    registry = TenantRegistry()
    registry.create_tenant({
        "tenant_id": "test_tenant",
        "tenant_name": "Test Tenant",
        "tier": "gold"
    })

    with pytest.raises(ValueError, match="already exists"):
        registry.create_tenant({
            "tenant_id": "test_tenant",
            "tenant_name": "Another Tenant",
            "tier": "silver"
        })


def test_get_tenant():
    """Test tenant retrieval by ID."""
    registry = TenantRegistry()
    registry.create_tenant({
        "tenant_id": "test_tenant",
        "tenant_name": "Test Tenant",
        "tier": "gold"
    })

    tenant = registry.get_tenant("test_tenant")
    assert tenant is not None
    assert tenant.tenant_name == "Test Tenant"


def test_get_nonexistent_tenant():
    """Test retrieving non-existent tenant returns None."""
    registry = TenantRegistry()
    tenant = registry.get_tenant("nonexistent")
    assert tenant is None


def test_list_tenants():
    """Test listing all tenants."""
    registry = TenantRegistry()
    registry.create_tenant({"tenant_id": "t1", "tenant_name": "T1", "tier": "gold"})
    registry.create_tenant({"tenant_id": "t2", "tenant_name": "T2", "tier": "silver"})

    tenants = registry.list_tenants()
    assert len(tenants) == 2


def test_list_tenants_by_status():
    """Test listing tenants filtered by status."""
    registry = TenantRegistry()
    t1 = registry.create_tenant({"tenant_id": "t1", "tenant_name": "T1", "tier": "gold"})
    t2 = registry.create_tenant({"tenant_id": "t2", "tenant_name": "T2", "tier": "silver"})

    # Suspend one tenant
    registry.lifecycle_manager.transition(t2, TenantStatus.SUSPENDED)

    active_tenants = registry.list_tenants(status=TenantStatus.ACTIVE)
    assert len(active_tenants) == 1
    assert active_tenants[0].tenant_id == "t1"

    suspended_tenants = registry.list_tenants(status=TenantStatus.SUSPENDED)
    assert len(suspended_tenants) == 1
    assert suspended_tenants[0].tenant_id == "t2"


def test_list_tenants_by_tier():
    """Test listing tenants filtered by tier."""
    registry = TenantRegistry()
    registry.create_tenant({"tenant_id": "t1", "tenant_name": "T1", "tier": "platinum"})
    registry.create_tenant({"tenant_id": "t2", "tenant_name": "T2", "tier": "gold"})
    registry.create_tenant({"tenant_id": "t3", "tenant_name": "T3", "tier": "gold"})

    gold_tenants = registry.list_tenants(tier="gold")
    assert len(gold_tenants) == 2


def test_list_tenants_by_health_score():
    """Test listing tenants filtered by minimum health score."""
    registry = TenantRegistry()
    t1 = registry.create_tenant({"tenant_id": "t1", "tenant_name": "T1", "tier": "gold"})
    t2 = registry.create_tenant({"tenant_id": "t2", "tenant_name": "T2", "tier": "silver"})

    # Update health scores
    t1.update_health_score(90)
    t2.update_health_score(60)

    healthy_tenants = registry.list_tenants(min_health_score=80)
    assert len(healthy_tenants) == 1
    assert healthy_tenants[0].tenant_id == "t1"


def test_update_tenant():
    """Test updating tenant attributes."""
    registry = TenantRegistry()
    registry.create_tenant({
        "tenant_id": "test_tenant",
        "tenant_name": "Original Name",
        "tier": "silver"
    })

    updated = registry.update_tenant("test_tenant", {
        "tenant_name": "Updated Name",
        "tier": "gold",
        "max_users": 100
    })

    assert updated.tenant_name == "Updated Name"
    assert updated.tier == "gold"
    assert updated.max_users == 100


def test_update_nonexistent_tenant():
    """Test updating non-existent tenant fails."""
    registry = TenantRegistry()

    with pytest.raises(ValueError, match="Tenant not found"):
        registry.update_tenant("nonexistent", {"tenant_name": "New Name"})


def test_delete_tenant():
    """Test deleting tenant in DELETED status."""
    registry = TenantRegistry()
    tenant = registry.create_tenant({
        "tenant_id": "test_tenant",
        "tenant_name": "Test Tenant",
        "tier": "gold"
    })

    # Transition to DELETED status
    registry.lifecycle_manager.transition(tenant, TenantStatus.SUSPENDED)
    registry.lifecycle_manager.transition(tenant, TenantStatus.ARCHIVED)
    registry.lifecycle_manager.transition(tenant, TenantStatus.DELETED)

    # Now delete
    result = registry.delete_tenant("test_tenant")
    assert result is True
    assert registry.get_tenant("test_tenant") is None


def test_delete_tenant_not_in_deleted_status():
    """Test deleting tenant not in DELETED status fails."""
    registry = TenantRegistry()
    registry.create_tenant({
        "tenant_id": "test_tenant",
        "tenant_name": "Test Tenant",
        "tier": "gold"
    })

    with pytest.raises(ValueError, match="must be in DELETED status"):
        registry.delete_tenant("test_tenant")


# Lifecycle State Machine Tests

def test_lifecycle_valid_transition_active_to_suspended():
    """Test valid transition: ACTIVE -> SUSPENDED."""
    manager = LifecycleManager()
    tenant = Tenant("t1", "T1", "gold")

    result = manager.transition(tenant, TenantStatus.SUSPENDED)
    assert result is True
    assert tenant.status == TenantStatus.SUSPENDED


def test_lifecycle_valid_transition_suspended_to_active():
    """Test valid transition: SUSPENDED -> ACTIVE."""
    manager = LifecycleManager()
    tenant = Tenant("t1", "T1", "gold", status=TenantStatus.SUSPENDED)

    result = manager.transition(tenant, TenantStatus.ACTIVE)
    assert result is True
    assert tenant.status == TenantStatus.ACTIVE


def test_lifecycle_valid_transition_active_to_migrating():
    """Test valid transition: ACTIVE -> MIGRATING."""
    manager = LifecycleManager()
    tenant = Tenant("t1", "T1", "gold")

    result = manager.transition(tenant, TenantStatus.MIGRATING)
    assert result is True
    assert tenant.status == TenantStatus.MIGRATING


def test_lifecycle_valid_transition_suspended_to_archived():
    """Test valid transition: SUSPENDED -> ARCHIVED."""
    manager = LifecycleManager()
    tenant = Tenant("t1", "T1", "gold", status=TenantStatus.SUSPENDED)

    result = manager.transition(tenant, TenantStatus.ARCHIVED)
    assert result is True
    assert tenant.status == TenantStatus.ARCHIVED


def test_lifecycle_valid_transition_archived_to_deleted():
    """Test valid transition: ARCHIVED -> DELETED."""
    manager = LifecycleManager()
    tenant = Tenant("t1", "T1", "gold", status=TenantStatus.ARCHIVED)

    result = manager.transition(tenant, TenantStatus.DELETED)
    assert result is True
    assert tenant.status == TenantStatus.DELETED


def test_lifecycle_invalid_transition_active_to_deleted():
    """Test invalid transition: ACTIVE -> DELETED (must go through SUSPENDED -> ARCHIVED)."""
    manager = LifecycleManager()
    tenant = Tenant("t1", "T1", "gold")

    with pytest.raises(ValueError, match="Invalid lifecycle transition"):
        manager.transition(tenant, TenantStatus.DELETED)


def test_lifecycle_invalid_transition_active_to_archived():
    """Test invalid transition: ACTIVE -> ARCHIVED."""
    manager = LifecycleManager()
    tenant = Tenant("t1", "T1", "gold")

    with pytest.raises(ValueError, match="Invalid lifecycle transition"):
        manager.transition(tenant, TenantStatus.ARCHIVED)


def test_lifecycle_invalid_transition_from_deleted():
    """Test no transitions allowed from DELETED (terminal state)."""
    manager = LifecycleManager()
    tenant = Tenant("t1", "T1", "gold", status=TenantStatus.DELETED)

    with pytest.raises(ValueError, match="Invalid lifecycle transition"):
        manager.transition(tenant, TenantStatus.ACTIVE)


def test_lifecycle_can_transition():
    """Test can_transition method."""
    manager = LifecycleManager()

    assert manager.can_transition(TenantStatus.ACTIVE, TenantStatus.SUSPENDED) is True
    assert manager.can_transition(TenantStatus.ACTIVE, TenantStatus.DELETED) is False
    assert manager.can_transition(TenantStatus.ARCHIVED, TenantStatus.DELETED) is True


def test_lifecycle_get_valid_transitions():
    """Test getting valid transitions for current state."""
    manager = LifecycleManager()

    valid = manager.get_valid_transitions(TenantStatus.ACTIVE)
    assert "suspended" in valid
    assert "migrating" in valid
    assert "deleted" not in valid


# Feature Flag Tests

def test_feature_flag_set_global():
    """Test setting global feature flag."""
    service = FeatureFlagService()
    flag = FeatureFlag("new_feature", True, "global")
    service.set_flag(flag)

    assert service.global_defaults["new_feature"] is True


def test_feature_flag_set_tier():
    """Test setting tier-level feature flag."""
    service = FeatureFlagService()
    flag = FeatureFlag("analytics", True, "tier", "platinum")
    service.set_flag(flag)

    assert service.tier_defaults["platinum"]["analytics"] is True


def test_feature_flag_set_tenant():
    """Test setting tenant-level feature flag."""
    service = FeatureFlagService()
    flag = FeatureFlag("beta_feature", True, "tenant", "tenant1")
    service.set_flag(flag)

    assert service.tenant_flags["tenant1"]["beta_feature"] is True


def test_feature_flag_evaluation_global_default():
    """Test feature flag evaluation falls back to global default."""
    service = FeatureFlagService()
    service.global_defaults["feature1"] = False

    result = service.evaluate("tenant1", "feature1")
    assert result is False


def test_feature_flag_evaluation_tier_override():
    """Test feature flag tier default overrides global."""
    service = FeatureFlagService()
    service.global_defaults["feature1"] = False
    service.tier_defaults["platinum"] = {"feature1": True}

    result = service.evaluate("tenant1", "feature1", tenant_tier="platinum")
    assert result is True


def test_feature_flag_evaluation_tenant_override():
    """Test feature flag tenant override wins hierarchy."""
    service = FeatureFlagService()
    service.global_defaults["feature1"] = False
    service.tier_defaults["platinum"] = {"feature1": True}
    service.tenant_flags["tenant1"] = {"feature1": False}

    # Tenant override should win (even if it's False)
    result = service.evaluate("tenant1", "feature1", tenant_tier="platinum")
    assert result is False


def test_feature_flag_evaluation_hierarchy_complete():
    """Test complete feature flag hierarchy."""
    service = FeatureFlagService()

    # Set global default
    service.global_defaults["analytics"] = False

    # Set tier defaults
    service.tier_defaults["platinum"] = {"analytics": True}
    service.tier_defaults["silver"] = {"analytics": False}

    # Set tenant override
    service.tenant_flags["marketing"] = {"analytics": True}

    # Platinum tenant without override: gets tier default
    assert service.evaluate("finance", "analytics", "platinum") is True

    # Silver tenant without override: gets tier default
    assert service.evaluate("ops", "analytics", "silver") is False

    # Silver tenant WITH override: gets tenant override
    assert service.evaluate("marketing", "analytics", "silver") is True

    # Unknown feature: defaults to False
    assert service.evaluate("finance", "unknown_feature", "platinum") is False


def test_feature_flag_list_all():
    """Test listing all feature flags."""
    service = FeatureFlagService()

    service.set_flag(FeatureFlag("f1", True, "global"))
    service.set_flag(FeatureFlag("f2", True, "tier", "gold"))
    service.set_flag(FeatureFlag("f3", False, "tenant", "t1"))

    flags = service.list_flags()
    assert len(flags) == 3


def test_feature_flag_list_filtered_by_scope():
    """Test listing feature flags filtered by scope."""
    service = FeatureFlagService()

    service.set_flag(FeatureFlag("f1", True, "global"))
    service.set_flag(FeatureFlag("f2", True, "tier", "gold"))
    service.set_flag(FeatureFlag("f3", False, "tenant", "t1"))

    tenant_flags = service.list_flags(scope="tenant")
    assert len(tenant_flags) == 1
    assert tenant_flags[0]["scope"] == "tenant"


# Cascading Operations Tests

def test_cascading_suspend_tenant():
    """Test cascading tenant suspension."""
    ops = CascadingOperations()
    result = ops.suspend_tenant("tenant1")

    assert "postgresql" in result
    assert "vector_db" in result
    assert "s3" in result
    assert "redis" in result
    assert "monitoring" in result

    assert result["postgresql"]["status"] == "suspended"
    assert result["vector_db"]["status"] == "suspended"


def test_cascading_activate_tenant():
    """Test cascading tenant activation."""
    ops = CascadingOperations()
    result = ops.activate_tenant("tenant1")

    assert "postgresql" in result
    assert result["postgresql"]["status"] == "active"


def test_cascading_audit_log():
    """Test cascading operations create audit log entries."""
    ops = CascadingOperations()

    ops.suspend_tenant("tenant1")
    ops.activate_tenant("tenant2")

    log = ops.get_audit_log()
    assert len(log) == 2

    assert log[0]["operation"] == "suspend_tenant"
    assert log[0]["tenant_id"] == "tenant1"

    assert log[1]["operation"] == "activate_tenant"
    assert log[1]["tenant_id"] == "tenant2"


def test_cascading_audit_log_filtered():
    """Test filtering audit log by tenant ID."""
    ops = CascadingOperations()

    ops.suspend_tenant("tenant1")
    ops.activate_tenant("tenant2")

    log = ops.get_audit_log(tenant_id="tenant1")
    assert len(log) == 1
    assert log[0]["tenant_id"] == "tenant1"


# Health Monitor Tests

def test_health_score_perfect():
    """Test health score calculation with perfect metrics."""
    monitor = HealthMonitor()

    score = monitor.calculate_health_score(
        tenant_id="tenant1",
        latency_p95=200.0,  # Under 500ms
        error_rate=0.0,  # No errors
        query_success_rate=1.0,  # 100% success
        storage_utilization=0.5  # 50% storage
    )

    assert score == 100


def test_health_score_high_latency():
    """Test health score penalty for high latency."""
    monitor = HealthMonitor()

    score = monitor.calculate_health_score(
        tenant_id="tenant1",
        latency_p95=700.0,  # 200ms over threshold
        error_rate=0.0,
        query_success_rate=1.0,
        storage_utilization=0.5
    )

    assert score < 100  # Should be penalized


def test_health_score_high_error_rate():
    """Test health score penalty for high error rate."""
    monitor = HealthMonitor()

    score = monitor.calculate_health_score(
        tenant_id="tenant1",
        latency_p95=200.0,
        error_rate=0.05,  # 5% error rate
        query_success_rate=1.0,
        storage_utilization=0.5
    )

    assert score < 100  # Should be penalized


def test_health_score_low_query_success():
    """Test health score penalty for low query success rate."""
    monitor = HealthMonitor()

    score = monitor.calculate_health_score(
        tenant_id="tenant1",
        latency_p95=200.0,
        error_rate=0.0,
        query_success_rate=0.8,  # 80% success (below 95% threshold)
        storage_utilization=0.5
    )

    assert score < 100  # Should be penalized


def test_health_score_high_storage():
    """Test health score penalty for high storage utilization."""
    monitor = HealthMonitor()

    score = monitor.calculate_health_score(
        tenant_id="tenant1",
        latency_p95=200.0,
        error_rate=0.0,
        query_success_rate=1.0,
        storage_utilization=0.95  # 95% storage
    )

    assert score < 100  # Should be penalized


def test_health_score_multiple_issues():
    """Test health score with multiple issues compounds penalties."""
    monitor = HealthMonitor()

    score = monitor.calculate_health_score(
        tenant_id="tenant1",
        latency_p95=800.0,  # High latency
        error_rate=0.1,  # 10% errors
        query_success_rate=0.85,  # Low success rate
        storage_utilization=0.95  # High storage
    )

    assert score < 50  # Multiple penalties should result in low score


def test_health_score_clamped_to_zero():
    """Test health score is clamped to 0 (not negative)."""
    monitor = HealthMonitor()

    score = monitor.calculate_health_score(
        tenant_id="tenant1",
        latency_p95=5000.0,  # Extremely high latency
        error_rate=0.5,  # 50% errors
        query_success_rate=0.5,  # 50% success
        storage_utilization=0.99  # Nearly full storage
    )

    assert score >= 0  # Should not go negative


def test_health_metrics_cached():
    """Test health metrics are cached and retrievable."""
    monitor = HealthMonitor()

    monitor.calculate_health_score(
        tenant_id="tenant1",
        latency_p95=300.0,
        error_rate=0.01,
        query_success_rate=0.98,
        storage_utilization=0.7
    )

    metrics = monitor.get_metrics("tenant1")
    assert metrics is not None
    assert metrics["health_score"] == 100
    assert metrics["latency_p95"] == 300.0
    assert metrics["error_rate"] == 0.01


# Integration Tests

def test_registry_suspend_tenant_integration():
    """Test complete tenant suspension flow."""
    registry = TenantRegistry()
    tenant = registry.create_tenant({
        "tenant_id": "test_tenant",
        "tenant_name": "Test Tenant",
        "tier": "gold"
    })

    result = registry.suspend_tenant("test_tenant")

    # Check status updated
    assert tenant.status == TenantStatus.SUSPENDED

    # Check cascading operations executed
    assert result["status"] == "suspended"
    assert "operations" in result
    assert result["operations"]["postgresql"]["status"] == "suspended"


def test_registry_activate_tenant_integration():
    """Test complete tenant activation flow."""
    registry = TenantRegistry()
    tenant = registry.create_tenant({
        "tenant_id": "test_tenant",
        "tenant_name": "Test Tenant",
        "tier": "gold"
    })

    # First suspend
    registry.suspend_tenant("test_tenant")

    # Then activate
    result = registry.activate_tenant("test_tenant")

    assert tenant.status == TenantStatus.ACTIVE
    assert result["status"] == "active"


def test_registry_statistics():
    """Test registry statistics calculation."""
    registry = TenantRegistry()

    registry.create_tenant({"tenant_id": "t1", "tenant_name": "T1", "tier": "platinum"})
    registry.create_tenant({"tenant_id": "t2", "tenant_name": "T2", "tier": "gold"})
    registry.create_tenant({"tenant_id": "t3", "tenant_name": "T3", "tier": "gold"})

    # Suspend one
    registry.suspend_tenant("t3")

    stats = registry.get_statistics()

    assert stats["total_tenants"] == 3
    assert stats["by_status"]["active"] == 2
    assert stats["by_status"]["suspended"] == 1
    assert stats["by_tier"]["platinum"] == 1
    assert stats["by_tier"]["gold"] == 2
    assert stats["average_health_score"] == 100.0


def test_tenant_to_dict():
    """Test tenant serialization to dictionary."""
    tenant = Tenant(
        tenant_id="t1",
        tenant_name="Test Tenant",
        tier="platinum",
        max_users=100,
        health_score=95
    )

    data = tenant.to_dict()

    assert data["tenant_id"] == "t1"
    assert data["tenant_name"] == "Test Tenant"
    assert data["tier"] == "platinum"
    assert data["status"] == "active"
    assert data["health_score"] == 95
    assert "created_at" in data
    assert "updated_at" in data


def test_tenant_update_health_score():
    """Test updating tenant health score."""
    tenant = Tenant("t1", "Test Tenant", "gold")

    tenant.update_health_score(85)
    assert tenant.health_score == 85


def test_tenant_update_health_score_invalid():
    """Test updating tenant health score with invalid value fails."""
    tenant = Tenant("t1", "Test Tenant", "gold")

    with pytest.raises(ValueError, match="Health score must be 0-100"):
        tenant.update_health_score(150)

    with pytest.raises(ValueError, match="Health score must be 0-100"):
        tenant.update_health_score(-10)
