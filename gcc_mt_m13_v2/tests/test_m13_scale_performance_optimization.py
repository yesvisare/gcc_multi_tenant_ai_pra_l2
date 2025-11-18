"""
Tests for L3 M13.2: Auto-Scaling Multi-Tenant Infrastructure

Tests all major functions from the auto-scaling module using offline mode
(no external services required).
"""

import pytest
import asyncio
import os
from src.l3_m13_scale_performance_optimization import (
    TenantTier,
    ScalingConfig,
    GCCAutoScalingPolicy,
    TenantQueueManager,
    calculate_target_replicas,
    validate_resource_quota,
    log_scale_event,
    generate_cost_report
)

# Force offline mode for tests
os.environ["REDIS_ENABLED"] = "false"
os.environ["PROMETHEUS_ENABLED"] = "false"
os.environ["OFFLINE"] = "true"


class TestScalingConfig:
    """Test ScalingConfig dataclass"""

    def test_scaling_config_creation(self):
        """Test creating a ScalingConfig instance"""
        config = ScalingConfig(
            min_replicas=3,
            max_replicas=20,
            scale_up_cooldown=60,
            scale_down_cooldown=300,
            resource_quota_percent=40.0,
            sla_target=0.9995
        )

        assert config.min_replicas == 3
        assert config.max_replicas == 20
        assert config.scale_up_cooldown == 60
        assert config.resource_quota_percent == 40.0


class TestGCCAutoScalingPolicy:
    """Test GCCAutoScalingPolicy class"""

    def test_premium_tier_config(self):
        """Test premium tier scaling configuration"""
        policy = GCCAutoScalingPolicy(TenantTier.PREMIUM)
        config = policy.get_scaling_config()

        assert config.min_replicas == 5
        assert config.max_replicas == 30
        assert config.resource_quota_percent == 40.0
        assert config.sla_target == 0.9995

    def test_standard_tier_config(self):
        """Test standard tier scaling configuration"""
        policy = GCCAutoScalingPolicy(TenantTier.STANDARD)
        config = policy.get_scaling_config()

        assert config.min_replicas == 3
        assert config.max_replicas == 15
        assert config.resource_quota_percent == 20.0
        assert config.sla_target == 0.999

    def test_free_tier_config(self):
        """Test free tier scaling configuration"""
        policy = GCCAutoScalingPolicy(TenantTier.FREE)
        config = policy.get_scaling_config()

        assert config.min_replicas == 1
        assert config.max_replicas == 5
        assert config.resource_quota_percent == 10.0
        assert config.sla_target == 0.99

    def test_calculate_target_replicas_low_queue(self):
        """Test replica calculation with low queue depth"""
        policy = GCCAutoScalingPolicy(TenantTier.PREMIUM)
        target = policy.calculate_target_replicas(queue_depth=20)

        # 20 queries / 10 per pod = 2 pods, but min is 5 for premium
        assert target == 5

    def test_calculate_target_replicas_high_queue(self):
        """Test replica calculation with high queue depth"""
        policy = GCCAutoScalingPolicy(TenantTier.PREMIUM)
        target = policy.calculate_target_replicas(queue_depth=250)

        # 250 queries / 10 per pod = 25 pods
        assert target == 25

    def test_calculate_target_replicas_exceeds_max(self):
        """Test replica calculation when exceeding max"""
        policy = GCCAutoScalingPolicy(TenantTier.FREE)
        target = policy.calculate_target_replicas(queue_depth=100)

        # 100 / 10 = 10 pods, but free tier max is 5
        assert target == 5

    def test_invalid_tenant_tier(self):
        """Test error handling for invalid tenant tier"""
        with pytest.raises(ValueError):
            GCCAutoScalingPolicy("invalid_tier")


class TestTenantQueueManager:
    """Test TenantQueueManager class"""

    @pytest.mark.asyncio
    async def test_enqueue_query(self):
        """Test enqueueing a query"""
        manager = TenantQueueManager()
        query = {"query": "test query", "metadata": {}}

        success = await manager.enqueue("tenant_a", query)
        assert success is True

        depth = manager.get_queue_depth("tenant_a")
        assert depth == 1

    @pytest.mark.asyncio
    async def test_dequeue_query(self):
        """Test dequeueing a query"""
        manager = TenantQueueManager()
        query = {"query": "test query"}

        await manager.enqueue("tenant_a", query)
        dequeued = await manager.dequeue("tenant_a")

        assert dequeued == query
        assert manager.get_queue_depth("tenant_a") == 0

    @pytest.mark.asyncio
    async def test_dequeue_empty_queue(self):
        """Test dequeueing from empty queue"""
        manager = TenantQueueManager()
        dequeued = await manager.dequeue("tenant_a", timeout=0.01)

        assert dequeued is None

    @pytest.mark.asyncio
    async def test_queue_full_backpressure(self):
        """Test backpressure when queue is full"""
        manager = TenantQueueManager(max_queue_size=5)

        # Fill queue to capacity
        for i in range(5):
            await manager.enqueue("tenant_a", {"query": f"query_{i}"})

        # Try to add one more (should fail)
        success = await manager.enqueue("tenant_a", {"query": "overflow"})
        assert success is False

        depth = manager.get_queue_depth("tenant_a")
        assert depth == 5

    @pytest.mark.asyncio
    async def test_get_all_queue_depths(self):
        """Test getting queue depths for all tenants"""
        manager = TenantQueueManager()

        await manager.enqueue("tenant_a", {"query": "a1"})
        await manager.enqueue("tenant_a", {"query": "a2"})
        await manager.enqueue("tenant_b", {"query": "b1"})

        depths = manager.get_all_queue_depths()

        assert depths["tenant_a"] == 2
        assert depths["tenant_b"] == 1

    @pytest.mark.asyncio
    async def test_invalid_enqueue_params(self):
        """Test error handling for invalid enqueue parameters"""
        manager = TenantQueueManager()

        with pytest.raises(ValueError):
            await manager.enqueue("", {"query": "test"})

        with pytest.raises(ValueError):
            await manager.enqueue("tenant_a", None)


class TestCalculateTargetReplicas:
    """Test calculate_target_replicas helper function"""

    def test_basic_calculation(self):
        """Test basic replica calculation"""
        target = calculate_target_replicas(
            queue_depth=50,
            target_queue_per_pod=10
        )
        assert target == 5  # 50 / 10 = 5

    def test_minimum_constraint(self):
        """Test minimum replica constraint"""
        target = calculate_target_replicas(
            queue_depth=5,
            target_queue_per_pod=10,
            min_replicas=3
        )
        assert target == 3  # Would be 1, but min is 3

    def test_maximum_constraint(self):
        """Test maximum replica constraint"""
        target = calculate_target_replicas(
            queue_depth=500,
            target_queue_per_pod=10,
            max_replicas=20
        )
        assert target == 20  # Would be 50, but max is 20

    def test_zero_queue_depth(self):
        """Test with zero queue depth"""
        target = calculate_target_replicas(
            queue_depth=0,
            min_replicas=3
        )
        assert target == 3  # Returns min replicas


class TestValidateResourceQuota:
    """Test validate_resource_quota function"""

    def test_premium_within_quota(self):
        """Test premium tenant within 40% quota"""
        valid, message = validate_resource_quota(
            TenantTier.PREMIUM,
            requested_replicas=30,
            total_cluster_capacity=100
        )
        assert valid is True
        assert "30.0%" in message

    def test_premium_exceeds_quota(self):
        """Test premium tenant exceeding 40% quota"""
        valid, message = validate_resource_quota(
            TenantTier.PREMIUM,
            requested_replicas=50,
            total_cluster_capacity=100
        )
        assert valid is False
        assert "exceeded" in message.lower()

    def test_standard_within_quota(self):
        """Test standard tenant within 20% quota"""
        valid, message = validate_resource_quota(
            TenantTier.STANDARD,
            requested_replicas=15,
            total_cluster_capacity=100
        )
        assert valid is True

    def test_free_within_quota(self):
        """Test free tenant within 10% quota"""
        valid, message = validate_resource_quota(
            TenantTier.FREE,
            requested_replicas=8,
            total_cluster_capacity=100
        )
        assert valid is True


class TestLogScaleEvent:
    """Test log_scale_event function"""

    def test_scale_up_event(self):
        """Test logging a scale-up event"""
        event = log_scale_event(
            tenant_id="finance_corp",
            old_replicas=5,
            new_replicas=15,
            reason="queue_depth_high"
        )

        assert event["tenant_id"] == "finance_corp"
        assert event["old_replicas"] == 5
        assert event["new_replicas"] == 15
        assert event["reason"] == "queue_depth_high"
        assert event["event_type"] == "auto_scale"
        assert event["immutable"] is True

    def test_scale_down_event(self):
        """Test logging a scale-down event"""
        event = log_scale_event(
            tenant_id="media_agency",
            old_replicas=20,
            new_replicas=10,
            reason="load_decreased"
        )

        assert event["old_replicas"] == 20
        assert event["new_replicas"] == 10
        assert "timestamp" in event


class TestGenerateCostReport:
    """Test generate_cost_report function"""

    def test_basic_cost_report(self):
        """Test basic cost report generation"""
        report = generate_cost_report(
            tenant_id="retail_chain",
            avg_replicas=8.5,
            peak_replicas=18
        )

        assert report["tenant_id"] == "retail_chain"
        assert report["avg_replicas"] == 8.5
        assert report["peak_replicas"] == 18
        assert report["actual_cost"] == 17000.0  # 8.5 * 2000
        assert report["peak_cost"] == 36000.0  # 18 * 2000
        assert report["currency"] == "INR"

    def test_cost_report_with_budget(self):
        """Test cost report with budget comparison"""
        report = generate_cost_report(
            tenant_id="legal_firm",
            avg_replicas=6.0,
            peak_replicas=12,
            budget=15000.0
        )

        assert report["budget"] == 15000.0
        assert report["actual_cost"] == 12000.0  # 6 * 2000
        assert report["variance"] == -3000.0  # Under budget
        assert report["under_budget"] is True

    def test_cost_report_over_budget(self):
        """Test cost report when over budget"""
        report = generate_cost_report(
            tenant_id="startup",
            avg_replicas=10.0,
            peak_replicas=15,
            budget=15000.0
        )

        assert report["actual_cost"] == 20000.0  # 10 * 2000
        assert report["variance"] == 5000.0  # Over budget
        assert report["under_budget"] is False
        assert report["variance_percent"] > 0


# Integration tests

@pytest.mark.asyncio
async def test_full_scaling_workflow():
    """Test complete scaling workflow from queue to replica calculation"""
    # Create tenant queue manager
    manager = TenantQueueManager()

    # Enqueue 50 queries for premium tenant
    for i in range(50):
        await manager.enqueue("finance_corp", {"query": f"query_{i}"})

    # Get queue depth
    depth = manager.get_queue_depth("finance_corp")
    assert depth == 50

    # Calculate target replicas
    policy = GCCAutoScalingPolicy(TenantTier.PREMIUM)
    target = policy.calculate_target_replicas(depth)

    # 50 / 10 = 5 pods, but min is 5 for premium
    assert target == 5

    # Validate quota
    valid, _ = validate_resource_quota(
        TenantTier.PREMIUM,
        requested_replicas=target,
        total_cluster_capacity=100
    )
    assert valid is True

    # Log scale event
    event = log_scale_event(
        tenant_id="finance_corp",
        old_replicas=5,
        new_replicas=target,
        reason="queue_depth_50"
    )
    assert event["new_replicas"] == target


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
