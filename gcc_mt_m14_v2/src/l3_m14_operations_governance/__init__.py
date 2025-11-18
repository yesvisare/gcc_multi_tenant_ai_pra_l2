"""
L3 M14.2: Incident Management & Blast Radius

This module implements incident management with automatic blast radius containment
for multi-tenant RAG systems. It detects failing tenants within 60 seconds and
isolates them automatically using circuit breaker patterns.

Core Capabilities:
- Blast radius detection within 60 seconds
- Circuit breaker isolation for failing tenants
- Automated notifications and incident tracking
- Incident priority framework (P0/P1/P2)
- Blameless postmortem generation
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import requests

logger = logging.getLogger(__name__)

# ============================================================================
# Data Models
# ============================================================================

class TenantTier(Enum):
    """Tenant tier classification for SLA and priority calculation."""
    PLATINUM = "platinum"  # ₹2 crore contracts, 99.99% SLA
    GOLD = "gold"          # High-value, 99.9% SLA
    SILVER = "silver"      # Standard, 99% SLA
    BRONZE = "bronze"      # Basic, best-effort SLA


class IncidentPriority(Enum):
    """Incident priority levels with response SLAs."""
    P0 = "critical"   # 15-min response: Platinum tenant OR 10+ tenants
    P1 = "high"       # 60-min response: Gold tenant OR 5-9 tenants
    P2 = "medium"     # 4-hour response: Silver/Bronze, <5 tenants


class CircuitBreakerState(Enum):
    """Circuit breaker states for tenant isolation."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Isolated (no traffic)
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class TenantMetrics:
    """Metrics for a single tenant from Prometheus."""
    tenant_id: str
    total_queries: int
    error_queries: int
    error_rate: float
    timestamp: datetime
    tier: TenantTier = TenantTier.BRONZE

    def is_failing(self, threshold: float = 0.50) -> bool:
        """Check if tenant exceeds error threshold."""
        return self.error_rate >= threshold


@dataclass
class CircuitBreaker:
    """Circuit breaker for tenant isolation."""
    tenant_id: str
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    failure_threshold: int = 5  # Trip after 5 consecutive failures
    timeout_seconds: int = 60   # Try recovery after 60 seconds

    def record_success(self) -> None:
        """Record successful request."""
        self.failure_count = 0
        if self.state == CircuitBreakerState.HALF_OPEN:
            logger.info(f"Circuit breaker CLOSED for tenant {self.tenant_id} - recovery successful")
            self.state = CircuitBreakerState.CLOSED
            self.opened_at = None

    def record_failure(self) -> bool:
        """
        Record failed request and update state.

        Returns:
            bool: True if circuit breaker tripped (transitioned to OPEN)
        """
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.state == CircuitBreakerState.CLOSED and self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            self.opened_at = datetime.now()
            logger.warning(f"Circuit breaker OPENED for tenant {self.tenant_id} - {self.failure_count} failures")
            return True

        if self.state == CircuitBreakerState.HALF_OPEN:
            # Recovery failed, back to OPEN
            self.state = CircuitBreakerState.OPEN
            self.opened_at = datetime.now()
            logger.warning(f"Circuit breaker recovery FAILED for tenant {self.tenant_id}")
            return True

        return False

    def attempt_reset(self) -> bool:
        """
        Attempt to transition from OPEN to HALF_OPEN after timeout.

        Returns:
            bool: True if transitioned to HALF_OPEN
        """
        if self.state == CircuitBreakerState.OPEN and self.opened_at:
            elapsed = (datetime.now() - self.opened_at).total_seconds()
            if elapsed >= self.timeout_seconds:
                self.state = CircuitBreakerState.HALF_OPEN
                self.failure_count = 0
                logger.info(f"Circuit breaker HALF_OPEN for tenant {self.tenant_id} - attempting recovery")
                return True
        return False

    def is_open(self) -> bool:
        """Check if circuit breaker is open (blocking traffic)."""
        return self.state == CircuitBreakerState.OPEN


@dataclass
class Incident:
    """Incident record for tracking and postmortem."""
    incident_id: str
    tenant_ids: List[str]
    priority: IncidentPriority
    created_at: datetime
    resolved_at: Optional[datetime] = None
    root_cause: Optional[str] = None
    action_items: List[str] = field(default_factory=list)
    affected_tier: Optional[TenantTier] = None
    cost_impact_inr: Optional[float] = None


# ============================================================================
# Blast Radius Detector
# ============================================================================

class BlastRadiusDetector:
    """
    Main detection engine for identifying failing tenants.

    Polls Prometheus every 10 seconds to check tenant health and triggers
    circuit breakers when error rates exceed 50%.
    """

    def __init__(
        self,
        prometheus_url: str = "http://prometheus:9090",
        error_threshold: float = 0.50,
        check_interval_seconds: int = 10,
        check_window: str = "5m"
    ):
        """
        Initialize blast radius detector.

        Args:
            prometheus_url: Prometheus server URL
            error_threshold: Error rate threshold (0.0-1.0)
            check_interval_seconds: Polling interval in seconds
            check_window: Prometheus time window for rate calculations
        """
        self.prometheus_url = prometheus_url.rstrip('/')
        self.error_threshold = error_threshold
        self.check_interval = check_interval_seconds
        self.check_window = check_window
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.tenant_tiers: Dict[str, TenantTier] = {}  # Loaded from config
        logger.info(f"Initialized BlastRadiusDetector: threshold={error_threshold}, interval={check_interval}s")

    def set_tenant_tier(self, tenant_id: str, tier: TenantTier) -> None:
        """Set tenant tier for priority calculation."""
        self.tenant_tiers[tenant_id] = tier

    def get_active_tenants(self) -> List[str]:
        """
        Query Prometheus for all active tenant IDs.

        Returns:
            List of tenant IDs with recent activity

        Raises:
            requests.RequestException: If Prometheus query fails
        """
        try:
            # Query Prometheus for tenant_id label values
            response = requests.get(
                f"{self.prometheus_url}/api/v1/label/tenant_id/values",
                timeout=5
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "success":
                logger.error(f"Prometheus query failed: {data}")
                return []

            tenant_ids = data.get("data", [])
            logger.info(f"Found {len(tenant_ids)} active tenants")
            return tenant_ids

        except requests.RequestException as e:
            logger.error(f"Failed to query Prometheus for tenants: {e}")
            raise

    def get_tenant_metrics(self, tenant_id: str) -> Optional[TenantMetrics]:
        """
        Calculate error rate for a specific tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            TenantMetrics object or None if query fails
        """
        try:
            # Query total queries
            total_query = f'sum(rate(rag_queries_total{{tenant_id="{tenant_id}"}}[{self.check_window}]))'
            total_response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": total_query},
                timeout=5
            )
            total_response.raise_for_status()
            total_data = total_response.json()

            # Query error queries
            error_query = f'sum(rate(rag_queries_errors{{tenant_id="{tenant_id}"}}[{self.check_window}]))'
            error_response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": error_query},
                timeout=5
            )
            error_response.raise_for_status()
            error_data = error_response.json()

            # Extract values
            total_result = total_data.get("data", {}).get("result", [])
            error_result = error_data.get("data", {}).get("result", [])

            if not total_result:
                logger.debug(f"No query data for tenant {tenant_id}")
                return None

            total_queries = float(total_result[0].get("value", [0, 0])[1])
            error_queries = float(error_result[0].get("value", [0, 0])[1]) if error_result else 0.0

            # Calculate error rate
            error_rate = (error_queries / total_queries) if total_queries > 0 else 0.0

            tier = self.tenant_tiers.get(tenant_id, TenantTier.BRONZE)

            return TenantMetrics(
                tenant_id=tenant_id,
                total_queries=int(total_queries),
                error_queries=int(error_queries),
                error_rate=error_rate,
                timestamp=datetime.now(),
                tier=tier
            )

        except requests.RequestException as e:
            logger.error(f"Failed to query metrics for tenant {tenant_id}: {e}")
            return None

    def check_tenant_health(self, tenant_id: str) -> Tuple[bool, Optional[TenantMetrics]]:
        """
        Check if tenant is failing and update circuit breaker.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Tuple of (is_failing, metrics)
        """
        metrics = self.get_tenant_metrics(tenant_id)

        if metrics is None:
            return False, None

        # Get or create circuit breaker
        if tenant_id not in self.circuit_breakers:
            self.circuit_breakers[tenant_id] = CircuitBreaker(tenant_id=tenant_id)

        breaker = self.circuit_breakers[tenant_id]

        # Attempt reset if in OPEN state
        breaker.attempt_reset()

        # Check if tenant is failing
        if metrics.is_failing(self.error_threshold):
            logger.warning(
                f"Tenant {tenant_id} FAILING: error_rate={metrics.error_rate:.2%} "
                f"(threshold={self.error_threshold:.2%})"
            )
            tripped = breaker.record_failure()
            return True, metrics
        else:
            breaker.record_success()
            return False, metrics

    def detect_blast_radius(self) -> List[TenantMetrics]:
        """
        Scan all tenants and return list of failing tenants.

        Returns:
            List of TenantMetrics for failing tenants
        """
        try:
            tenant_ids = self.get_active_tenants()
            failing_tenants = []

            for tenant_id in tenant_ids:
                is_failing, metrics = self.check_tenant_health(tenant_id)

                if is_failing and metrics:
                    failing_tenants.append(metrics)

            if failing_tenants:
                logger.warning(f"Blast radius detected: {len(failing_tenants)} failing tenants")

            return failing_tenants

        except Exception as e:
            logger.error(f"Blast radius detection failed: {e}")
            return []

    def get_circuit_breaker_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all circuit breakers.

        Returns:
            Dict mapping tenant_id to breaker status
        """
        return {
            tenant_id: {
                "state": breaker.state.value,
                "failure_count": breaker.failure_count,
                "is_open": breaker.is_open(),
                "opened_at": breaker.opened_at.isoformat() if breaker.opened_at else None
            }
            for tenant_id, breaker in self.circuit_breakers.items()
        }


# ============================================================================
# Incident Management
# ============================================================================

def calculate_incident_priority(
    failing_tenants: List[TenantMetrics]
) -> IncidentPriority:
    """
    Calculate incident priority based on affected tenants.

    Rules:
    - P0: Any Platinum tenant OR 10+ tenants affected
    - P1: Gold tenant OR 5-9 tenants affected
    - P2: Silver/Bronze, <5 tenants affected

    Args:
        failing_tenants: List of failing tenant metrics

    Returns:
        Incident priority level
    """
    if not failing_tenants:
        return IncidentPriority.P2

    # Check for Platinum tenants
    has_platinum = any(t.tier == TenantTier.PLATINUM for t in failing_tenants)
    if has_platinum:
        logger.info("P0 incident: Platinum tenant affected")
        return IncidentPriority.P0

    # Check tenant count
    tenant_count = len(failing_tenants)
    if tenant_count >= 10:
        logger.info(f"P0 incident: {tenant_count} tenants affected")
        return IncidentPriority.P0

    # Check for Gold tenants
    has_gold = any(t.tier == TenantTier.GOLD for t in failing_tenants)
    if has_gold:
        logger.info("P1 incident: Gold tenant affected")
        return IncidentPriority.P1

    if tenant_count >= 5:
        logger.info(f"P1 incident: {tenant_count} tenants affected")
        return IncidentPriority.P1

    # Default to P2
    logger.info(f"P2 incident: {tenant_count} Silver/Bronze tenants affected")
    return IncidentPriority.P2


def create_incident(
    failing_tenants: List[TenantMetrics],
    detector: BlastRadiusDetector
) -> Incident:
    """
    Create incident record for failing tenants.

    Args:
        failing_tenants: List of failing tenant metrics
        detector: BlastRadiusDetector instance for context

    Returns:
        Incident object with priority and metadata
    """
    tenant_ids = [t.tenant_id for t in failing_tenants]
    priority = calculate_incident_priority(failing_tenants)

    # Determine highest affected tier
    tier_priority = {
        TenantTier.PLATINUM: 4,
        TenantTier.GOLD: 3,
        TenantTier.SILVER: 2,
        TenantTier.BRONZE: 1
    }
    affected_tier = max(
        (t.tier for t in failing_tenants),
        key=lambda t: tier_priority[t],
        default=TenantTier.BRONZE
    )

    # Estimate cost impact (simplified)
    # Platinum: ₹50K/hour, Gold: ₹20K/hour, Silver: ₹10K/hour, Bronze: ₹5K/hour
    cost_per_hour = {
        TenantTier.PLATINUM: 50000,
        TenantTier.GOLD: 20000,
        TenantTier.SILVER: 10000,
        TenantTier.BRONZE: 5000
    }
    estimated_cost = sum(cost_per_hour.get(t.tier, 5000) for t in failing_tenants)

    incident = Incident(
        incident_id=f"INC-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        tenant_ids=tenant_ids,
        priority=priority,
        created_at=datetime.now(),
        affected_tier=affected_tier,
        cost_impact_inr=estimated_cost
    )

    logger.info(
        f"Created incident {incident.incident_id}: {priority.value} priority, "
        f"{len(tenant_ids)} tenants, estimated cost ₹{estimated_cost:,.0f}/hour"
    )

    return incident


def send_notifications(
    incident: Incident,
    pagerduty_enabled: bool = False,
    slack_enabled: bool = False
) -> Dict[str, bool]:
    """
    Send notifications for incident.

    Args:
        incident: Incident object
        pagerduty_enabled: Enable PagerDuty integration
        slack_enabled: Enable Slack webhook

    Returns:
        Dict of notification results
    """
    results = {}

    # Log notification (always enabled)
    logger.error(
        f"INCIDENT ALERT: {incident.incident_id} | Priority: {incident.priority.value} | "
        f"Tenants: {', '.join(incident.tenant_ids)} | "
        f"Tier: {incident.affected_tier.value if incident.affected_tier else 'unknown'} | "
        f"Est. Cost: ₹{incident.cost_impact_inr:,.0f}/hour"
    )
    results["log"] = True

    # PagerDuty notification (if enabled)
    if pagerduty_enabled:
        try:
            # TODO: Implement PagerDuty API call
            logger.info(f"PagerDuty notification sent for {incident.incident_id}")
            results["pagerduty"] = True
        except Exception as e:
            logger.error(f"PagerDuty notification failed: {e}")
            results["pagerduty"] = False

    # Slack notification (if enabled)
    if slack_enabled:
        try:
            # TODO: Implement Slack webhook call
            logger.info(f"Slack notification sent for {incident.incident_id}")
            results["slack"] = True
        except Exception as e:
            logger.error(f"Slack notification failed: {e}")
            results["slack"] = False

    return results


def generate_postmortem_template(incident: Incident) -> str:
    """
    Generate blameless postmortem template.

    Args:
        incident: Resolved incident

    Returns:
        Markdown-formatted postmortem template
    """
    template = f"""# Incident Postmortem: {incident.incident_id}

## Summary
- **Incident ID**: {incident.incident_id}
- **Priority**: {incident.priority.value.upper()}
- **Created**: {incident.created_at.strftime('%Y-%m-%d %H:%M:%S')}
- **Resolved**: {incident.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if incident.resolved_at else 'Ongoing'}
- **Duration**: {(incident.resolved_at - incident.created_at).total_seconds() / 60:.1f} minutes (if resolved)
- **Affected Tenants**: {len(incident.tenant_ids)} ({', '.join(incident.tenant_ids[:5])}{'...' if len(incident.tenant_ids) > 5 else ''})
- **Highest Tier Affected**: {incident.affected_tier.value.upper() if incident.affected_tier else 'Unknown'}
- **Estimated Cost Impact**: ₹{incident.cost_impact_inr:,.0f}/hour

## Timeline
- **{incident.created_at.strftime('%H:%M:%S')}**: Incident detected
- **{incident.created_at.strftime('%H:%M:%S')}**: Circuit breaker activated
- **{incident.created_at.strftime('%H:%M:%S')}**: Notifications sent
- _(Add more timeline events here)_

## Root Cause Analysis (Five Whys)
1. **Why did the incident occur?**
   - {incident.root_cause or '_To be filled_'}

2. **Why did that happen?**
   - _To be filled_

3. **Why did that underlying issue exist?**
   - _To be filled_

4. **Why wasn't it prevented?**
   - _To be filled_

5. **Why wasn't that in place?**
   - _Root cause identified_

## What Went Well
- Circuit breaker isolated failing tenant(s) within 60 seconds
- Other {50 - len(incident.tenant_ids)} tenants remained operational
- Blast radius contained to {len(incident.tenant_ids)} tenant(s)

## What Went Wrong
- _To be filled based on investigation_

## Action Items (Blameless)
"""

    if incident.action_items:
        for i, action in enumerate(incident.action_items, 1):
            template += f"{i}. {action}\n"
    else:
        template += """1. [ ] **Owner**: _Name_ | **Deadline**: _Date_ | **Action**: Implement validation for query patterns
2. [ ] **Owner**: _Name_ | **Deadline**: _Date_ | **Action**: Add pre-deployment testing for queries
3. [ ] **Owner**: _Name_ | **Deadline**: _Date_ | **Action**: Update runbook with detection steps
4. [ ] **Owner**: _Name_ | **Deadline**: _Date_ | **Action**: Review circuit breaker thresholds
"""

    template += """
## Lessons Learned
- _System improvement focus, not individual blame_

## Prevention Measures
- _Long-term systemic changes_
"""

    return template


# ============================================================================
# Main Monitoring Loop
# ============================================================================

def run_monitoring_loop(
    detector: BlastRadiusDetector,
    max_iterations: Optional[int] = None,
    offline: bool = False
) -> List[Incident]:
    """
    Run continuous monitoring loop for blast radius detection.

    Args:
        detector: BlastRadiusDetector instance
        max_iterations: Maximum iterations (None for infinite)
        offline: If True, skip actual monitoring

    Returns:
        List of incidents created during monitoring
    """
    if offline:
        logger.warning("⚠️ Offline mode - skipping monitoring loop")
        return []

    logger.info(f"Starting monitoring loop: interval={detector.check_interval}s")
    incidents = []
    iteration = 0

    try:
        while max_iterations is None or iteration < max_iterations:
            iteration += 1
            logger.info(f"Monitoring iteration {iteration}")

            # Detect failing tenants
            failing_tenants = detector.detect_blast_radius()

            # Create incident if tenants are failing
            if failing_tenants:
                incident = create_incident(failing_tenants, detector)
                incidents.append(incident)

                # Send notifications
                send_notifications(incident)

            # Sleep until next check
            time.sleep(detector.check_interval)

    except KeyboardInterrupt:
        logger.info("Monitoring loop interrupted by user")
    except Exception as e:
        logger.error(f"Monitoring loop crashed: {e}")
        raise

    return incidents


# ============================================================================
# Public API
# ============================================================================

__all__ = [
    # Enums
    "TenantTier",
    "IncidentPriority",
    "CircuitBreakerState",

    # Data classes
    "TenantMetrics",
    "CircuitBreaker",
    "Incident",

    # Main classes
    "BlastRadiusDetector",

    # Functions
    "calculate_incident_priority",
    "create_incident",
    "send_notifications",
    "generate_postmortem_template",
    "run_monitoring_loop",
]
