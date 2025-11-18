"""
Tests for L3 M14.1: Multi-Tenant Monitoring & Observability

Tests all major functions:
- start_query_tracking / end_query_tracking
- track_query (unified tracking)
- update_quota_usage
- TenantMetricsCollector class
- In-memory fallback behavior

Prometheus is mocked/disabled for testing to ensure tests run without dependencies.
"""

import pytest
import os
import time
from unittest.mock import patch, MagicMock

# Force offline mode for tests
os.environ["PROMETHEUS_ENABLED"] = "false"
os.environ["OFFLINE"] = "true"

from src.l3_m14_monitoring_observability import (
    start_query_tracking,
    end_query_tracking,
    track_query,
    update_quota_usage,
    get_tenant_metrics,
    TenantMetricsCollector
)

# ============================================================================
# TEST: START/END QUERY TRACKING
# ============================================================================

def test_start_query_tracking():
    """Test starting query tracking returns valid context"""
    context = start_query_tracking("test-tenant-1")

    assert context is not None
    assert 'tenant_id' in context
    assert context['tenant_id'] == "test-tenant-1"
    assert 'start_time' in context
    assert 'timestamp' in context
    assert isinstance(context['start_time'], float)


def test_end_query_tracking_success():
    """Test ending query tracking with success status"""
    context = start_query_tracking("test-tenant-2")
    time.sleep(0.1)  # Simulate query duration

    # Should not raise exception
    end_query_tracking(context, "success", docs_retrieved=5, llm_tokens=1200)


def test_end_query_tracking_error():
    """Test ending query tracking with error status"""
    context = start_query_tracking("test-tenant-3")

    end_query_tracking(context, "error", docs_retrieved=0, llm_tokens=0)


def test_end_query_tracking_invalid_context():
    """Test ending tracking with invalid context raises ValueError"""
    invalid_context = {'foo': 'bar'}

    with pytest.raises(ValueError, match="Invalid context"):
        end_query_tracking(invalid_context, "success")


# ============================================================================
# TEST: UNIFIED TRACK_QUERY
# ============================================================================

def test_track_query_basic():
    """Test unified query tracking"""
    track_query(
        tenant_id="test-tenant-4",
        status="success",
        duration=1.5,
        docs_retrieved=3,
        llm_tokens=800
    )
    # Should complete without error


def test_track_query_defaults():
    """Test track_query with default parameters"""
    track_query(tenant_id="test-tenant-5")
    # Should use defaults: status="success", duration=0.0, etc.


# ============================================================================
# TEST: QUOTA USAGE
# ============================================================================

def test_update_quota_usage():
    """Test updating tenant quota usage"""
    update_quota_usage("test-tenant-6", "queries", 75.0)
    update_quota_usage("test-tenant-6", "tokens", 50.0)
    update_quota_usage("test-tenant-6", "storage", 90.0)
    # Should complete without error


# ============================================================================
# TEST: TENANTMETRICSCOLLECTOR CLASS
# ============================================================================

def test_tenant_metrics_collector_init():
    """Test TenantMetricsCollector initialization"""
    collector = TenantMetricsCollector(
        tenant_id="test-tenant-7",
        tier="premium",
        name="Test Tenant"
    )

    assert collector.tenant_id == "test-tenant-7"
    assert collector.tier == "premium"
    assert collector.name == "Test Tenant"


def test_tenant_metrics_collector_tracking():
    """Test full tracking lifecycle with TenantMetricsCollector"""
    collector = TenantMetricsCollector("test-tenant-8")

    context = collector.start_tracking()
    assert 'tenant_id' in context
    assert context['tenant_id'] == "test-tenant-8"

    time.sleep(0.05)
    collector.end_tracking(context, "success", docs_count=10, token_count=2000)


# ============================================================================
# TEST: GET METRICS (IN-MEMORY MODE)
# ============================================================================

def test_get_tenant_metrics_no_data():
    """Test getting metrics for tenant with no recorded queries"""
    metrics = get_tenant_metrics("test-tenant-new")

    assert metrics is not None
    assert 'tenant_id' in metrics
    assert metrics['total_queries'] == 0


def test_get_tenant_metrics_with_data():
    """Test getting metrics after recording queries"""
    tenant_id = "test-tenant-9"

    # Record some queries
    track_query(tenant_id, "success", 1.0, 5, 1000)
    track_query(tenant_id, "success", 2.0, 3, 800)
    track_query(tenant_id, "error", 0.5, 0, 0)

    metrics = get_tenant_metrics(tenant_id)

    assert metrics['tenant_id'] == tenant_id
    assert metrics['total_queries'] >= 3
    assert metrics['success_count'] >= 2
    assert metrics['error_count'] >= 1


# ============================================================================
# TEST: MULTI-TENANT ISOLATION
# ============================================================================

def test_multi_tenant_isolation():
    """Test that metrics are isolated per tenant"""
    tenant_a = "tenant-a"
    tenant_b = "tenant-b"

    # Record different queries for each tenant
    track_query(tenant_a, "success", 1.0, 5, 1000)
    track_query(tenant_a, "success", 1.5, 3, 800)

    track_query(tenant_b, "error", 0.5, 0, 0)

    metrics_a = get_tenant_metrics(tenant_a)
    metrics_b = get_tenant_metrics(tenant_b)

    # Tenant A should have 2 queries (both success)
    assert metrics_a['total_queries'] >= 2

    # Tenant B should have 1 query (error)
    assert metrics_b['total_queries'] >= 1


# ============================================================================
# TEST: PROMETHEUS AVAILABILITY HANDLING
# ============================================================================

def test_prometheus_unavailable_graceful_fallback():
    """Test that module works gracefully when Prometheus is unavailable"""
    # This test validates the in-memory fallback works
    context = start_query_tracking("fallback-tenant")
    end_query_tracking(context, "success", 5, 1000)

    metrics = get_tenant_metrics("fallback-tenant")
    assert metrics is not None


# ============================================================================
# TEST: EDGE CASES
# ============================================================================

def test_zero_duration_query():
    """Test tracking query with zero duration"""
    track_query("edge-tenant-1", "success", 0.0, 1, 100)


def test_large_values():
    """Test tracking with large values"""
    track_query(
        "edge-tenant-2",
        "success",
        duration=30.0,
        docs_retrieved=100,
        llm_tokens=50000
    )


def test_quota_boundary_values():
    """Test quota usage at boundary values"""
    update_quota_usage("edge-tenant-3", "queries", 0.0)
    update_quota_usage("edge-tenant-3", "queries", 100.0)


# ============================================================================
# TEST: PROMETHEUS METRICS (WHEN ENABLED)
# ============================================================================

@pytest.mark.skipif(
    os.getenv("PROMETHEUS_ENABLED", "false").lower() != "true",
    reason="Prometheus not enabled"
)
def test_prometheus_metrics_server():
    """Test Prometheus metrics server startup (only if enabled)"""
    from src.l3_m14_monitoring_observability import start_metrics_server

    # This test only runs when PROMETHEUS_ENABLED=true
    # It validates the server can start
    try:
        start_metrics_server(port=9090)
    except Exception as e:
        pytest.fail(f"Metrics server failed to start: {e}")


# ============================================================================
# FIXTURE: CLEANUP
# ============================================================================

@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables before each test"""
    os.environ["PROMETHEUS_ENABLED"] = "false"
    os.environ["OFFLINE"] = "true"
    yield
    # Cleanup after test if needed
