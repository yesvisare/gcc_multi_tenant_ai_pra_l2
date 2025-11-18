"""
L3 M13.2: Auto-Scaling Multi-Tenant Infrastructure

This module implements intelligent Kubernetes auto-scaling for multi-tenant RAG platforms,
using per-tenant queue depth metrics to drive HPA scaling decisions while enforcing
resource quotas and maintaining SLA compliance.

Key Capabilities:
- Per-tenant queue depth tracking for HPA metrics
- Tier-based scaling policies (Premium, Standard, Free)
- Resource quota enforcement preventing tenant monopoly
- Graceful scale-down with connection draining
- Prometheus metrics export for custom HPA metrics
"""

import logging
import asyncio
import math
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

__all__ = [
    "TenantTier",
    "ScalingConfig",
    "GCCAutoScalingPolicy",
    "TenantQueueManager",
    "calculate_target_replicas",
    "validate_resource_quota",
    "log_scale_event",
    "generate_cost_report"
]


class TenantTier(Enum):
    """Tenant tier classifications for scaling policy differentiation"""
    PREMIUM = "premium"
    STANDARD = "standard"
    FREE = "free"


@dataclass
class ScalingConfig:
    """
    Tier-specific scaling configuration.

    Attributes:
        min_replicas: Minimum pods (baseline capacity)
        max_replicas: Maximum pods (budget ceiling)
        scale_up_cooldown: Seconds to wait before scaling up
        scale_down_cooldown: Seconds to wait before scaling down
        resource_quota_percent: Maximum cluster resources (%)
        sla_target: Target uptime (0.999 = 99.9%)
    """
    min_replicas: int
    max_replicas: int
    scale_up_cooldown: int
    scale_down_cooldown: int
    resource_quota_percent: float
    sla_target: float


class GCCAutoScalingPolicy:
    """
    Enterprise-grade auto-scaling policy for GCC multi-tenant RAG platform.

    Manages tier-based scaling configurations ensuring fair resource allocation
    across 50+ tenants with different SLAs and cost sensitivities.

    Example:
        >>> policy = GCCAutoScalingPolicy(TenantTier.PREMIUM)
        >>> config = policy.get_scaling_config()
        >>> print(config.min_replicas)  # 5 for premium
    """

    TIER_CONFIGS = {
        TenantTier.PREMIUM: ScalingConfig(
            min_replicas=5,
            max_replicas=30,
            scale_up_cooldown=60,
            scale_down_cooldown=600,
            resource_quota_percent=40.0,
            sla_target=0.9995
        ),
        TenantTier.STANDARD: ScalingConfig(
            min_replicas=3,
            max_replicas=15,
            scale_up_cooldown=120,
            scale_down_cooldown=300,
            resource_quota_percent=20.0,
            sla_target=0.999
        ),
        TenantTier.FREE: ScalingConfig(
            min_replicas=1,
            max_replicas=5,
            scale_up_cooldown=300,
            scale_down_cooldown=60,
            resource_quota_percent=10.0,
            sla_target=0.99
        )
    }

    def __init__(self, tenant_tier: TenantTier):
        """
        Initialize auto-scaling policy for specified tenant tier.

        Args:
            tenant_tier: Tier classification (Premium, Standard, or Free)
        """
        if not isinstance(tenant_tier, TenantTier):
            raise ValueError(f"tenant_tier must be TenantTier enum, got {type(tenant_tier)}")

        self.tenant_tier = tenant_tier
        logger.info(f"Initialized auto-scaling policy for {tenant_tier.value} tier")

    def get_scaling_config(self) -> ScalingConfig:
        """
        Returns scaling configuration for this tenant tier.

        Platform team can adjust these values per tenant without
        changing code (stored in ConfigMap or database).

        Returns:
            ScalingConfig with tier-specific parameters
        """
        return self.TIER_CONFIGS[self.tenant_tier]

    def calculate_target_replicas(self, current_queue_depth: int) -> int:
        """
        Calculate how many replicas this tenant needs based on queue depth.

        Formula: ceil(queue_depth / target_queue_per_pod)
        Constrained by: min_replicas <= result <= max_replicas

        Args:
            current_queue_depth: Number of queries currently queued

        Returns:
            Target replica count (constrained by min/max)

        Example:
            >>> policy = GCCAutoScalingPolicy(TenantTier.PREMIUM)
            >>> policy.calculate_target_replicas(100)
            10  # 100 queries / 10 per pod = 10 pods
        """
        config = self.get_scaling_config()
        target_queue_per_pod = 10  # Target: max 10 queries per pod

        # Calculate ideal replica count
        target = math.ceil(current_queue_depth / target_queue_per_pod) if current_queue_depth > 0 else config.min_replicas

        # Apply min/max constraints
        constrained_target = max(
            config.min_replicas,
            min(target, config.max_replicas)
        )

        logger.debug(
            f"Calculated target replicas: queue_depth={current_queue_depth}, "
            f"target={target}, constrained={constrained_target}"
        )

        return constrained_target


@dataclass
class TenantQueue:
    """Represents a tenant's query queue"""
    tenant_id: str
    queries: asyncio.Queue = field(default_factory=asyncio.Queue)

    def depth(self) -> int:
        """Return current queue depth"""
        return self.queries.qsize()


class TenantQueueManager:
    """
    Manages per-tenant query queues with depth tracking for HPA metrics.

    This is the core component that exports `tenant_queue_depth` metric
    to Prometheus, which drives HPA scaling decisions.

    Example:
        >>> manager = TenantQueueManager()
        >>> await manager.enqueue("tenant_a", {"query": "test"})
        >>> depth = manager.get_queue_depth("tenant_a")
        >>> print(depth)  # 1
    """

    def __init__(self, max_queue_size: int = 100):
        """
        Initialize tenant queue manager.

        Args:
            max_queue_size: Maximum queries per tenant (backpressure limit)
        """
        self.queues: Dict[str, TenantQueue] = {}
        self.max_queue_size = max_queue_size
        logger.info(f"Initialized TenantQueueManager with max_queue_size={max_queue_size}")

    def _get_or_create_queue(self, tenant_id: str) -> TenantQueue:
        """Get existing queue or create new one for tenant"""
        if tenant_id not in self.queues:
            self.queues[tenant_id] = TenantQueue(tenant_id=tenant_id)
            logger.info(f"Created new queue for tenant {tenant_id}")
        return self.queues[tenant_id]

    async def enqueue(self, tenant_id: str, query: Dict[str, Any]) -> bool:
        """
        Add query to tenant's queue.

        Args:
            tenant_id: Tenant identifier
            query: Query data to enqueue

        Returns:
            True if enqueued, False if queue is full (backpressure)

        Raises:
            ValueError: If tenant_id is empty or query is None
        """
        if not tenant_id:
            raise ValueError("tenant_id cannot be empty")
        if query is None:
            raise ValueError("query cannot be None")

        queue = self._get_or_create_queue(tenant_id)

        # Check if queue is full (backpressure mechanism)
        if queue.depth() >= self.max_queue_size:
            logger.warning(
                f"Queue full for tenant {tenant_id}: "
                f"{queue.depth()}/{self.max_queue_size}"
            )
            return False

        await queue.queries.put(query)
        logger.debug(f"Enqueued query for tenant {tenant_id}, depth={queue.depth()}")
        return True

    async def dequeue(self, tenant_id: str, timeout: float = 0.1) -> Optional[Dict[str, Any]]:
        """
        Remove query from tenant's queue.

        Args:
            tenant_id: Tenant identifier
            timeout: Seconds to wait for query (0 = non-blocking)

        Returns:
            Query data if available, None if queue empty or timeout
        """
        queue = self._get_or_create_queue(tenant_id)

        try:
            query = await asyncio.wait_for(queue.queries.get(), timeout=timeout)
            logger.debug(f"Dequeued query for tenant {tenant_id}, remaining={queue.depth()}")
            return query
        except asyncio.TimeoutError:
            return None

    def get_queue_depth(self, tenant_id: str) -> int:
        """
        Get current queue depth for tenant.

        This is the metric exported to Prometheus for HPA scaling.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Number of queries in queue (0 if tenant has no queue)
        """
        if tenant_id not in self.queues:
            return 0
        return self.queues[tenant_id].depth()

    def get_all_queue_depths(self) -> Dict[str, int]:
        """
        Get queue depths for all tenants.

        Returns:
            Dict mapping tenant_id to queue depth
        """
        return {
            tenant_id: queue.depth()
            for tenant_id, queue in self.queues.items()
        }


def calculate_target_replicas(
    queue_depth: int,
    target_queue_per_pod: int = 10,
    min_replicas: int = 1,
    max_replicas: int = 20
) -> int:
    """
    Calculate target replica count based on queue depth.

    This is a simplified version for testing/validation outside of
    the full GCCAutoScalingPolicy class.

    Args:
        queue_depth: Current number of queued queries
        target_queue_per_pod: Desired queries per pod
        min_replicas: Minimum replicas to maintain
        max_replicas: Maximum replicas allowed

    Returns:
        Constrained target replica count

    Example:
        >>> calculate_target_replicas(queue_depth=50, target_queue_per_pod=10)
        5  # 50 / 10 = 5 pods needed
    """
    if queue_depth <= 0:
        return min_replicas

    target = math.ceil(queue_depth / target_queue_per_pod)
    return max(min_replicas, min(target, max_replicas))


def validate_resource_quota(
    tenant_tier: TenantTier,
    requested_replicas: int,
    total_cluster_capacity: int
) -> Tuple[bool, str]:
    """
    Validate if requested replicas exceed tenant's resource quota.

    Args:
        tenant_tier: Tenant's tier classification
        requested_replicas: Number of replicas requested
        total_cluster_capacity: Total cluster pod capacity

    Returns:
        Tuple of (is_valid, message)

    Example:
        >>> valid, msg = validate_resource_quota(
        ...     TenantTier.PREMIUM,
        ...     requested_replicas=30,
        ...     total_cluster_capacity=100
        ... )
        >>> print(valid)  # True (30/100 = 30% < 40% quota)
    """
    policy = GCCAutoScalingPolicy(tenant_tier)
    config = policy.get_scaling_config()

    # Calculate percentage of cluster requested
    requested_percent = (requested_replicas / total_cluster_capacity) * 100

    # Check if within quota
    if requested_percent > config.resource_quota_percent:
        message = (
            f"Quota exceeded: {tenant_tier.value} tier limited to "
            f"{config.resource_quota_percent}% of cluster, "
            f"but requesting {requested_percent:.1f}%"
        )
        logger.warning(message)
        return False, message

    message = f"Quota valid: {requested_percent:.1f}% <= {config.resource_quota_percent}%"
    return True, message


def log_scale_event(
    tenant_id: str,
    old_replicas: int,
    new_replicas: int,
    reason: str,
    audit_logger: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Log scaling event for SOX/DPDPA compliance audit trail.

    All scale events must be logged immutably for regulatory compliance.
    Auditors need to verify no unauthorized resource allocation.

    Args:
        tenant_id: Tenant identifier
        old_replicas: Previous replica count
        new_replicas: New replica count
        reason: Reason for scaling (e.g., "queue_depth_high")
        audit_logger: Optional external audit logging system

    Returns:
        Dict containing audit trail entry

    Example:
        >>> event = log_scale_event(
        ...     tenant_id="finance_corp",
        ...     old_replicas=5,
        ...     new_replicas=15,
        ...     reason="queue_depth_exceeded_threshold"
        ... )
    """
    audit_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'tenant_id': tenant_id,
        'event_type': 'auto_scale',
        'old_replicas': old_replicas,
        'new_replicas': new_replicas,
        'reason': reason,
        'triggering_user': 'HPA',
        'approval': 'automated_policy',
        'immutable': True
    }

    logger.info(
        f"AUDIT: Scale event for {tenant_id}: "
        f"{old_replicas} -> {new_replicas} ({reason})"
    )

    # If external audit logger provided, use it
    if audit_logger:
        try:
            audit_logger.log(audit_entry)
        except Exception as e:
            logger.error(f"Failed to write to external audit log: {e}")

    return audit_entry


def generate_cost_report(
    tenant_id: str,
    avg_replicas: float,
    peak_replicas: int,
    pod_cost_per_month: float = 2000.0,
    budget: Optional[float] = None
) -> Dict[str, Any]:
    """
    Generate per-tenant cost report for CFO chargeback.

    Provides transparency on infrastructure costs per tenant,
    supporting fair cost attribution across business units.

    Args:
        tenant_id: Tenant identifier
        avg_replicas: Average replicas over reporting period
        peak_replicas: Peak replica count reached
        pod_cost_per_month: Cost per pod per month (default: ₹2000)
        budget: Optional budget for comparison

    Returns:
        Dict containing cost breakdown

    Example:
        >>> report = generate_cost_report(
        ...     tenant_id="media_agency",
        ...     avg_replicas=6.5,
        ...     peak_replicas=14,
        ...     budget=15000.0
        ... )
        >>> print(report['actual_cost'])  # 13000.0
    """
    actual_cost = avg_replicas * pod_cost_per_month
    peak_cost = peak_replicas * pod_cost_per_month

    report = {
        'tenant_id': tenant_id,
        'reporting_period': datetime.utcnow().strftime('%Y-%m'),
        'avg_replicas': round(avg_replicas, 2),
        'peak_replicas': peak_replicas,
        'pod_cost_per_month': pod_cost_per_month,
        'actual_cost': round(actual_cost, 2),
        'peak_cost': round(peak_cost, 2),
        'currency': 'INR'
    }

    if budget:
        report['budget'] = budget
        report['variance'] = round(actual_cost - budget, 2)
        report['variance_percent'] = round(((actual_cost - budget) / budget) * 100, 2)
        report['under_budget'] = actual_cost <= budget

    logger.info(
        f"Cost report for {tenant_id}: "
        f"avg={avg_replicas:.1f} pods, cost=₹{actual_cost:,.0f}"
    )

    return report
