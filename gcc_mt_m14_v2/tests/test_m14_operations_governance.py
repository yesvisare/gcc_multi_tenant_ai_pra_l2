"""
Tests for L3 M14.2: Incident Management & Blast Radius

Comprehensive test suite covering blast radius detection, circuit breakers,
incident priority calculation, and notification systems.

SERVICE: Mocked for testing (no Prometheus required)
"""

import pytest
import os
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Force offline mode for tests
os.environ["PROMETHEUS_ENABLED"] = "false"
os.environ["OFFLINE"] = "true"

from src.l3_m14_operations_governance import (
    TenantTier,
    IncidentPriority,
    CircuitBreakerState,
    TenantMetrics,
    CircuitBreaker,
    Incident,
    BlastRadiusDetector,
    calculate_incident_priority,
    create_incident,
    send_notifications,
    generate_postmortem_template,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_tenant_metrics():
    """Create sample tenant metrics."""
    return TenantMetrics(
        tenant_id="tenant-A",
        total_queries=1000,
        error_queries=600,
        error_rate=0.60,
        timestamp=datetime.now(),
        tier=TenantTier.GOLD
    )


@pytest.fixture
def failing_tenants():
    """Create list of failing tenants."""
    return [
        TenantMetrics("tenant-A", 1000, 600, 0.60, datetime.now(), TenantTier.PLATINUM),
        TenantMetrics("tenant-B", 800, 500, 0.625, datetime.now(), TenantTier.GOLD),
        TenantMetrics("tenant-C", 500, 300, 0.60, datetime.now(), TenantTier.SILVER),
    ]


@pytest.fixture
def circuit_breaker():
    """Create circuit breaker instance."""
    return CircuitBreaker(tenant_id="tenant-A")


@pytest.fixture
def mock_detector():
    """Create mock BlastRadiusDetector."""
    with patch('requests.get') as mock_get:
        # Mock Prometheus responses
        mock_get.return_value.json.return_value = {
            "status": "success",
            "data": ["tenant-A", "tenant-B"]
        }
        detector = BlastRadiusDetector(
            prometheus_url="http://mock-prometheus:9090",
            error_threshold=0.50
        )
        yield detector


# ============================================================================
# TenantMetrics Tests
# ============================================================================

def test_tenant_metrics_creation(sample_tenant_metrics):
    """Test TenantMetrics dataclass creation."""
    assert sample_tenant_metrics.tenant_id == "tenant-A"
    assert sample_tenant_metrics.total_queries == 1000
    assert sample_tenant_metrics.error_queries == 600
    assert sample_tenant_metrics.error_rate == 0.60
    assert sample_tenant_metrics.tier == TenantTier.GOLD


def test_tenant_metrics_is_failing_above_threshold(sample_tenant_metrics):
    """Test failing detection when above threshold."""
    assert sample_tenant_metrics.is_failing(threshold=0.50) is True


def test_tenant_metrics_is_failing_below_threshold(sample_tenant_metrics):
    """Test passing detection when below threshold."""
    assert sample_tenant_metrics.is_failing(threshold=0.70) is False


def test_tenant_metrics_is_failing_at_threshold():
    """Test failing detection at exact threshold."""
    metrics = TenantMetrics("tenant-X", 100, 50, 0.50, datetime.now())
    assert metrics.is_failing(threshold=0.50) is True


# ============================================================================
# CircuitBreaker Tests
# ============================================================================

def test_circuit_breaker_initial_state(circuit_breaker):
    """Test circuit breaker starts in CLOSED state."""
    assert circuit_breaker.state == CircuitBreakerState.CLOSED
    assert circuit_breaker.failure_count == 0
    assert circuit_breaker.is_open() is False


def test_circuit_breaker_record_success(circuit_breaker):
    """Test recording successful requests."""
    circuit_breaker.failure_count = 3
    circuit_breaker.record_success()
    assert circuit_breaker.failure_count == 0


def test_circuit_breaker_record_failure_below_threshold(circuit_breaker):
    """Test recording failures below threshold."""
    for i in range(4):
        tripped = circuit_breaker.record_failure()
        assert tripped is False
        assert circuit_breaker.state == CircuitBreakerState.CLOSED


def test_circuit_breaker_trips_at_threshold(circuit_breaker):
    """Test circuit breaker trips at failure threshold."""
    # Record 4 failures (below threshold)
    for i in range(4):
        circuit_breaker.record_failure()

    # 5th failure should trip
    tripped = circuit_breaker.record_failure()
    assert tripped is True
    assert circuit_breaker.state == CircuitBreakerState.OPEN
    assert circuit_breaker.is_open() is True


def test_circuit_breaker_attempt_reset_before_timeout(circuit_breaker):
    """Test reset attempt before timeout expires."""
    # Trip the breaker
    for i in range(5):
        circuit_breaker.record_failure()

    # Immediately attempt reset (should fail)
    reset = circuit_breaker.attempt_reset()
    assert reset is False
    assert circuit_breaker.state == CircuitBreakerState.OPEN


def test_circuit_breaker_attempt_reset_after_timeout():
    """Test reset attempt after timeout expires."""
    breaker = CircuitBreaker(tenant_id="tenant-X", timeout_seconds=0)

    # Trip the breaker
    for i in range(5):
        breaker.record_failure()

    # Attempt reset (should succeed with 0-second timeout)
    reset = breaker.attempt_reset()
    assert reset is True
    assert breaker.state == CircuitBreakerState.HALF_OPEN


def test_circuit_breaker_recovery_success():
    """Test successful recovery from HALF_OPEN."""
    breaker = CircuitBreaker(tenant_id="tenant-X", timeout_seconds=0)

    # Trip and transition to HALF_OPEN
    for i in range(5):
        breaker.record_failure()
    breaker.attempt_reset()

    # Successful request should close breaker
    breaker.record_success()
    assert breaker.state == CircuitBreakerState.CLOSED


def test_circuit_breaker_recovery_failure():
    """Test failed recovery from HALF_OPEN."""
    breaker = CircuitBreaker(tenant_id="tenant-X", timeout_seconds=0)

    # Trip and transition to HALF_OPEN
    for i in range(5):
        breaker.record_failure()
    breaker.attempt_reset()

    # Failed request should reopen breaker
    tripped = breaker.record_failure()
    assert tripped is True
    assert breaker.state == CircuitBreakerState.OPEN


# ============================================================================
# Incident Priority Tests
# ============================================================================

def test_calculate_priority_platinum_tenant():
    """Test P0 priority for Platinum tenant."""
    tenants = [
        TenantMetrics("tenant-A", 100, 60, 0.60, datetime.now(), TenantTier.PLATINUM)
    ]
    priority = calculate_incident_priority(tenants)
    assert priority == IncidentPriority.P0


def test_calculate_priority_10_plus_tenants():
    """Test P0 priority for 10+ affected tenants."""
    tenants = [
        TenantMetrics(f"tenant-{i}", 100, 60, 0.60, datetime.now(), TenantTier.BRONZE)
        for i in range(10)
    ]
    priority = calculate_incident_priority(tenants)
    assert priority == IncidentPriority.P0


def test_calculate_priority_gold_tenant():
    """Test P1 priority for Gold tenant."""
    tenants = [
        TenantMetrics("tenant-A", 100, 60, 0.60, datetime.now(), TenantTier.GOLD)
    ]
    priority = calculate_incident_priority(tenants)
    assert priority == IncidentPriority.P1


def test_calculate_priority_5_to_9_tenants():
    """Test P1 priority for 5-9 affected tenants."""
    tenants = [
        TenantMetrics(f"tenant-{i}", 100, 60, 0.60, datetime.now(), TenantTier.SILVER)
        for i in range(7)
    ]
    priority = calculate_incident_priority(tenants)
    assert priority == IncidentPriority.P1


def test_calculate_priority_silver_bronze_few_tenants():
    """Test P2 priority for Silver/Bronze with <5 tenants."""
    tenants = [
        TenantMetrics("tenant-A", 100, 60, 0.60, datetime.now(), TenantTier.SILVER),
        TenantMetrics("tenant-B", 100, 60, 0.60, datetime.now(), TenantTier.BRONZE),
    ]
    priority = calculate_incident_priority(tenants)
    assert priority == IncidentPriority.P2


def test_calculate_priority_empty_list():
    """Test P2 priority for empty tenant list."""
    priority = calculate_incident_priority([])
    assert priority == IncidentPriority.P2


# ============================================================================
# Incident Creation Tests
# ============================================================================

def test_create_incident_basic(failing_tenants, mock_detector):
    """Test basic incident creation."""
    incident = create_incident(failing_tenants, mock_detector)

    assert incident.incident_id.startswith("INC-")
    assert incident.priority == IncidentPriority.P0  # Platinum tenant
    assert len(incident.tenant_ids) == 3
    assert incident.affected_tier == TenantTier.PLATINUM
    assert incident.cost_impact_inr > 0


def test_create_incident_cost_calculation(failing_tenants, mock_detector):
    """Test cost impact calculation in incident."""
    incident = create_incident(failing_tenants, mock_detector)

    # Platinum (50K) + Gold (20K) + Silver (10K) = 80K per hour
    expected_cost = 50000 + 20000 + 10000
    assert incident.cost_impact_inr == expected_cost


def test_create_incident_single_tenant(mock_detector):
    """Test incident creation for single tenant."""
    tenants = [
        TenantMetrics("tenant-X", 100, 60, 0.60, datetime.now(), TenantTier.SILVER)
    ]
    incident = create_incident(tenants, mock_detector)

    assert len(incident.tenant_ids) == 1
    assert incident.tenant_ids[0] == "tenant-X"
    assert incident.priority == IncidentPriority.P2


# ============================================================================
# Notification Tests
# ============================================================================

def test_send_notifications_log_only():
    """Test notifications with only logging enabled."""
    incident = Incident(
        incident_id="INC-TEST-001",
        tenant_ids=["tenant-A"],
        priority=IncidentPriority.P1,
        created_at=datetime.now(),
        cost_impact_inr=20000
    )

    results = send_notifications(incident, pagerduty_enabled=False, slack_enabled=False)

    assert results["log"] is True
    assert "pagerduty" not in results
    assert "slack" not in results


def test_send_notifications_pagerduty_enabled():
    """Test notifications with PagerDuty enabled."""
    incident = Incident(
        incident_id="INC-TEST-002",
        tenant_ids=["tenant-A"],
        priority=IncidentPriority.P0,
        created_at=datetime.now(),
        cost_impact_inr=50000
    )

    results = send_notifications(incident, pagerduty_enabled=True, slack_enabled=False)

    assert results["log"] is True
    # PagerDuty will fail without actual API implementation
    assert "pagerduty" in results


def test_send_notifications_all_enabled():
    """Test notifications with all systems enabled."""
    incident = Incident(
        incident_id="INC-TEST-003",
        tenant_ids=["tenant-A", "tenant-B"],
        priority=IncidentPriority.P0,
        created_at=datetime.now(),
        cost_impact_inr=70000
    )

    results = send_notifications(incident, pagerduty_enabled=True, slack_enabled=True)

    assert results["log"] is True
    assert "pagerduty" in results
    assert "slack" in results


# ============================================================================
# Postmortem Tests
# ============================================================================

def test_generate_postmortem_basic():
    """Test postmortem generation."""
    incident = Incident(
        incident_id="INC-TEST-001",
        tenant_ids=["tenant-A", "tenant-B"],
        priority=IncidentPriority.P1,
        created_at=datetime.now(),
        resolved_at=datetime.now(),
        affected_tier=TenantTier.GOLD,
        cost_impact_inr=40000,
        root_cause="Bad query deployment"
    )

    postmortem = generate_postmortem_template(incident)

    assert "INC-TEST-001" in postmortem
    assert "P1" in postmortem
    assert "tenant-A" in postmortem
    assert "GOLD" in postmortem
    assert "₹40,000" in postmortem
    assert "Bad query deployment" in postmortem
    assert "Five Whys" in postmortem
    assert "Action Items" in postmortem


def test_generate_postmortem_unresolved():
    """Test postmortem for unresolved incident."""
    incident = Incident(
        incident_id="INC-TEST-002",
        tenant_ids=["tenant-X"],
        priority=IncidentPriority.P2,
        created_at=datetime.now(),
        cost_impact_inr=10000
    )

    postmortem = generate_postmortem_template(incident)

    assert "INC-TEST-002" in postmortem
    assert "Ongoing" in postmortem or "To be filled" in postmortem


# ============================================================================
# BlastRadiusDetector Tests (Mocked)
# ============================================================================

@patch('requests.get')
def test_detector_get_active_tenants(mock_get):
    """Test fetching active tenants from Prometheus."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "status": "success",
        "data": ["tenant-A", "tenant-B", "tenant-C"]
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    detector = BlastRadiusDetector()
    tenants = detector.get_active_tenants()

    assert len(tenants) == 3
    assert "tenant-A" in tenants
    assert "tenant-B" in tenants


@patch('requests.get')
def test_detector_get_tenant_metrics(mock_get):
    """Test fetching tenant metrics from Prometheus."""
    # Mock total queries response
    total_response = Mock()
    total_response.json.return_value = {
        "status": "success",
        "data": {
            "result": [{"value": [0, "1000"]}]
        }
    }
    total_response.raise_for_status = Mock()

    # Mock error queries response
    error_response = Mock()
    error_response.json.return_value = {
        "status": "success",
        "data": {
            "result": [{"value": [0, "600"]}]
        }
    }
    error_response.raise_for_status = Mock()

    mock_get.side_effect = [total_response, error_response]

    detector = BlastRadiusDetector()
    metrics = detector.get_tenant_metrics("tenant-A")

    assert metrics is not None
    assert metrics.tenant_id == "tenant-A"
    assert metrics.total_queries == 1000
    assert metrics.error_queries == 600
    assert metrics.error_rate == 0.60


def test_detector_set_tenant_tier(mock_detector):
    """Test setting tenant tier."""
    mock_detector.set_tenant_tier("tenant-A", TenantTier.PLATINUM)

    assert mock_detector.tenant_tiers["tenant-A"] == TenantTier.PLATINUM


@patch('requests.get')
def test_detector_check_tenant_health_failing(mock_get):
    """Test tenant health check for failing tenant."""
    # Mock responses
    total_response = Mock()
    total_response.json.return_value = {
        "status": "success",
        "data": {"result": [{"value": [0, "1000"]}]}
    }
    total_response.raise_for_status = Mock()

    error_response = Mock()
    error_response.json.return_value = {
        "status": "success",
        "data": {"result": [{"value": [0, "700"]}]}
    }
    error_response.raise_for_status = Mock()

    mock_get.side_effect = [total_response, error_response]

    detector = BlastRadiusDetector(error_threshold=0.50)
    is_failing, metrics = detector.check_tenant_health("tenant-A")

    assert is_failing is True
    assert metrics.error_rate == 0.70


def test_detector_get_circuit_breaker_status(mock_detector):
    """Test getting circuit breaker status."""
    # Create some circuit breakers
    mock_detector.circuit_breakers["tenant-A"] = CircuitBreaker("tenant-A")
    mock_detector.circuit_breakers["tenant-B"] = CircuitBreaker("tenant-B")

    # Trip one breaker
    for i in range(5):
        mock_detector.circuit_breakers["tenant-A"].record_failure()

    status = mock_detector.get_circuit_breaker_status()

    assert "tenant-A" in status
    assert "tenant-B" in status
    assert status["tenant-A"]["state"] == "open"
    assert status["tenant-A"]["is_open"] is True
    assert status["tenant-B"]["state"] == "closed"
    assert status["tenant-B"]["is_open"] is False


# ============================================================================
# Integration Tests
# ============================================================================

@patch('requests.get')
def test_full_blast_radius_detection_workflow(mock_get):
    """Test complete blast radius detection workflow."""
    # Mock active tenants
    tenants_response = Mock()
    tenants_response.json.return_value = {
        "status": "success",
        "data": ["tenant-A", "tenant-B"]
    }
    tenants_response.raise_for_status = Mock()

    # Mock metrics for tenant-A (failing)
    total_A = Mock()
    total_A.json.return_value = {"status": "success", "data": {"result": [{"value": [0, "1000"]}]}}
    total_A.raise_for_status = Mock()

    error_A = Mock()
    error_A.json.return_value = {"status": "success", "data": {"result": [{"value": [0, "600"]}]}}
    error_A.raise_for_status = Mock()

    # Mock metrics for tenant-B (healthy)
    total_B = Mock()
    total_B.json.return_value = {"status": "success", "data": {"result": [{"value": [0, "1000"]}]}}
    total_B.raise_for_status = Mock()

    error_B = Mock()
    error_B.json.return_value = {"status": "success", "data": {"result": [{"value": [0, "100"]}]}}
    error_B.raise_for_status = Mock()

    mock_get.side_effect = [tenants_response, total_A, error_A, total_B, error_B]

    detector = BlastRadiusDetector(error_threshold=0.50)
    detector.set_tenant_tier("tenant-A", TenantTier.PLATINUM)

    failing = detector.detect_blast_radius()

    assert len(failing) == 1
    assert failing[0].tenant_id == "tenant-A"
    assert failing[0].error_rate == 0.60


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
