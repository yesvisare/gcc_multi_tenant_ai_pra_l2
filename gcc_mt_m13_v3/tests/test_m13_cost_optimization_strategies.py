"""
Tests for L3 M13.3: Cost Optimization Strategies

Tests all major functions:
- Usage metering (queries, storage, compute, vector ops)
- Cost calculation with volume discounts
- Chargeback report generation
- Cost anomaly detection
- Validation utilities
"""

import pytest
from datetime import datetime, timedelta

from src.l3_m13_cost_optimization_strategies import (
    TenantUsageMetering,
    CostCalculationEngine,
    ChargebackReportGenerator,
    CostAnomalyDetector,
    UsageMetrics,
    VolumeDiscountTier,
    validate_cost_attribution
)


# Fixtures
@pytest.fixture
def metering():
    """Create fresh metering instance"""
    return TenantUsageMetering()


@pytest.fixture
def cost_engine():
    """Create fresh cost calculation engine"""
    return CostCalculationEngine()


@pytest.fixture
def report_generator(cost_engine):
    """Create fresh report generator"""
    return ChargebackReportGenerator(cost_engine)


@pytest.fixture
def anomaly_detector():
    """Create fresh anomaly detector"""
    return CostAnomalyDetector()


@pytest.fixture
def sample_usage():
    """Create sample usage metrics"""
    now = datetime.utcnow()
    return UsageMetrics(
        tenant_id="finance",
        query_count=100_000,
        storage_gb=200.0,
        compute_pod_hours=500.0,
        vector_operations=500_000,
        period_start=now.isoformat(),
        period_end=(now + timedelta(days=30)).isoformat()
    )


# Test Usage Metering
def test_record_query(metering):
    """Test recording query usage"""
    metering.record_query("finance", 100)

    usage = metering.get_tenant_usage("finance")
    assert usage is not None
    assert usage.query_count == 100
    assert usage.tenant_id == "finance"


def test_record_storage(metering):
    """Test recording storage usage"""
    metering.record_storage("finance", 250.5)

    usage = metering.get_tenant_usage("finance")
    assert usage is not None
    assert usage.storage_gb == 250.5


def test_record_compute(metering):
    """Test recording compute usage"""
    metering.record_compute("finance", 100.0)

    usage = metering.get_tenant_usage("finance")
    assert usage is not None
    assert usage.compute_pod_hours == 100.0


def test_record_vector_operation(metering):
    """Test recording vector operations"""
    metering.record_vector_operation("finance", 1000)

    usage = metering.get_tenant_usage("finance")
    assert usage is not None
    assert usage.vector_operations == 1000


def test_multiple_tenants(metering):
    """Test tracking multiple tenants"""
    metering.record_query("finance", 100)
    metering.record_query("legal", 50)
    metering.record_query("hr", 25)

    all_usage = metering.get_all_usage()
    assert len(all_usage) == 3
    assert all_usage["finance"].query_count == 100
    assert all_usage["legal"].query_count == 50
    assert all_usage["hr"].query_count == 25


def test_reset_tenant_usage(metering):
    """Test resetting tenant usage"""
    metering.record_query("finance", 100)
    metering.reset_tenant_usage("finance")

    usage = metering.get_tenant_usage("finance")
    assert usage.query_count == 0


# Test Cost Calculation
def test_calculate_basic_cost(cost_engine, sample_usage):
    """Test basic cost calculation"""
    breakdown = cost_engine.calculate_tenant_cost("finance", sample_usage)

    assert breakdown.tenant_id == "finance"
    assert breakdown.query_count == 100_000
    assert breakdown.final_cost > 0
    assert breakdown.cost_per_query > 0


def test_volume_discount_tier_0(cost_engine):
    """Test no discount for <10K queries"""
    now = datetime.utcnow()
    usage = UsageMetrics(
        tenant_id="hr",
        query_count=5_000,
        storage_gb=10.0,
        compute_pod_hours=50.0,
        vector_operations=10_000,
        period_start=now.isoformat(),
        period_end=(now + timedelta(days=30)).isoformat()
    )

    breakdown = cost_engine.calculate_tenant_cost("hr", usage)
    assert breakdown.volume_discount_rate == 0.0


def test_volume_discount_tier_1(cost_engine):
    """Test 15% discount for 10K-100K queries"""
    now = datetime.utcnow()
    usage = UsageMetrics(
        tenant_id="finance",
        query_count=50_000,
        storage_gb=100.0,
        compute_pod_hours=200.0,
        vector_operations=200_000,
        period_start=now.isoformat(),
        period_end=(now + timedelta(days=30)).isoformat()
    )

    breakdown = cost_engine.calculate_tenant_cost("finance", usage)
    assert breakdown.volume_discount_rate == 0.15


def test_volume_discount_tier_2(cost_engine):
    """Test 30% discount for 100K-1M queries"""
    now = datetime.utcnow()
    usage = UsageMetrics(
        tenant_id="legal",
        query_count=500_000,
        storage_gb=500.0,
        compute_pod_hours=1000.0,
        vector_operations=2_000_000,
        period_start=now.isoformat(),
        period_end=(now + timedelta(days=30)).isoformat()
    )

    breakdown = cost_engine.calculate_tenant_cost("legal", usage)
    assert breakdown.volume_discount_rate == 0.30


def test_volume_discount_tier_3(cost_engine):
    """Test 40% discount for >1M queries"""
    now = datetime.utcnow()
    usage = UsageMetrics(
        tenant_id="operations",
        query_count=2_000_000,
        storage_gb=1000.0,
        compute_pod_hours=2000.0,
        vector_operations=10_000_000,
        period_start=now.isoformat(),
        period_end=(now + timedelta(days=30)).isoformat()
    )

    breakdown = cost_engine.calculate_tenant_cost("operations", usage)
    assert breakdown.volume_discount_rate == 0.40


def test_overhead_allocation(cost_engine, sample_usage):
    """Test overhead allocation (20%)"""
    breakdown = cost_engine.calculate_tenant_cost("finance", sample_usage)

    assert breakdown.overhead_rate == 0.20
    assert breakdown.overhead_cost == breakdown.direct_total * 0.20


def test_cost_breakdown_components(cost_engine, sample_usage):
    """Test all cost components are calculated"""
    breakdown = cost_engine.calculate_tenant_cost("finance", sample_usage)

    assert breakdown.llm_cost > 0
    assert breakdown.storage_cost > 0
    assert breakdown.compute_cost > 0
    assert breakdown.vector_cost > 0
    assert breakdown.direct_total > 0
    assert breakdown.overhead_cost > 0
    assert breakdown.final_cost > 0


def test_migration_cost_estimate(cost_engine):
    """Test migration cost estimation"""
    estimate = cost_engine.estimate_migration_cost(
        num_documents=5000,
        avg_doc_size_mb=2.0
    )

    assert "num_documents" in estimate
    assert "total_size_gb" in estimate
    assert "monthly_storage_cost_inr" in estimate
    assert estimate["num_documents"] == 5000
    assert estimate["total_size_gb"] > 0


def test_migration_cost_warning(cost_engine):
    """Test migration cost warning for large uploads"""
    estimate = cost_engine.estimate_migration_cost(
        num_documents=50_000,
        avg_doc_size_mb=5.0
    )

    assert estimate["warning"] is not None
    assert "High cost migration" in estimate["warning"]


# Test Chargeback Reports
def test_generate_monthly_invoice(report_generator, sample_usage):
    """Test monthly invoice generation"""
    invoice = report_generator.generate_monthly_invoice("finance", sample_usage)

    assert "invoice_id" in invoice
    assert "tenant_id" in invoice
    assert "billing_period" in invoice
    assert "line_items" in invoice
    assert "total" in invoice
    assert invoice["tenant_id"] == "finance"
    assert len(invoice["line_items"]) == 4  # LLM, Storage, Compute, Vector


def test_generate_platform_summary(report_generator, metering):
    """Test platform summary generation"""
    # Add usage for multiple tenants
    now = datetime.utcnow()
    for tenant_id in ["finance", "legal", "hr"]:
        usage = UsageMetrics(
            tenant_id=tenant_id,
            query_count=10_000,
            storage_gb=50.0,
            compute_pod_hours=100.0,
            vector_operations=50_000,
            period_start=now.isoformat(),
            period_end=(now + timedelta(days=30)).isoformat()
        )
        metering._usage_data[tenant_id] = usage

    summary = report_generator.generate_platform_summary(metering.get_all_usage())

    assert summary["tenant_count"] == 3
    assert summary["total_cost_inr"] > 0
    assert summary["total_queries"] == 30_000
    assert len(summary["top_tenants"]) == 3


# Test Anomaly Detection
def test_no_anomaly_first_month(anomaly_detector):
    """Test no anomaly on first month (no history)"""
    now = datetime.utcnow()
    usage = UsageMetrics(
        tenant_id="finance",
        query_count=10_000,
        storage_gb=50.0,
        compute_pod_hours=100.0,
        vector_operations=50_000,
        period_start=now.isoformat(),
        period_end=(now + timedelta(days=30)).isoformat()
    )

    anomaly = anomaly_detector.check_anomaly("finance", 10000.0, usage)
    assert anomaly is None  # No history yet


def test_anomaly_detection_spike(anomaly_detector):
    """Test anomaly detection on cost spike >50%"""
    now = datetime.utcnow()
    usage = UsageMetrics(
        tenant_id="finance",
        query_count=10_000,
        storage_gb=50.0,
        compute_pod_hours=100.0,
        vector_operations=50_000,
        period_start=now.isoformat(),
        period_end=(now + timedelta(days=30)).isoformat()
    )

    # First month: 10K
    anomaly_detector.check_anomaly("finance", 10000.0, usage)

    # Second month: 20K (100% increase - should trigger)
    usage.query_count = 20_000
    anomaly = anomaly_detector.check_anomaly("finance", 20000.0, usage)

    assert anomaly is not None
    assert anomaly["alert_type"] == "cost_spike"
    assert anomaly["change_percent"] == 100.0


def test_no_anomaly_small_increase(anomaly_detector):
    """Test no anomaly on small cost increase <50%"""
    now = datetime.utcnow()
    usage = UsageMetrics(
        tenant_id="finance",
        query_count=10_000,
        storage_gb=50.0,
        compute_pod_hours=100.0,
        vector_operations=50_000,
        period_start=now.isoformat(),
        period_end=(now + timedelta(days=30)).isoformat()
    )

    # First month: 10K
    anomaly_detector.check_anomaly("finance", 10000.0, usage)

    # Second month: 14K (40% increase - should not trigger)
    anomaly = anomaly_detector.check_anomaly("finance", 14000.0, usage)

    assert anomaly is None


def test_cost_trend_tracking(anomaly_detector):
    """Test cost trend history tracking"""
    now = datetime.utcnow()
    usage = UsageMetrics(
        tenant_id="finance",
        query_count=10_000,
        storage_gb=50.0,
        compute_pod_hours=100.0,
        vector_operations=50_000,
        period_start=now.isoformat(),
        period_end=(now + timedelta(days=30)).isoformat()
    )

    # Record 3 months
    anomaly_detector.check_anomaly("finance", 10000.0, usage)
    anomaly_detector.check_anomaly("finance", 12000.0, usage)
    anomaly_detector.check_anomaly("finance", 15000.0, usage)

    trend = anomaly_detector.get_cost_trend("finance")
    assert len(trend) == 3
    assert trend == [10000.0, 12000.0, 15000.0]


# Test Validation
def test_validate_cost_attribution_pass():
    """Test cost attribution validation passes"""
    result = validate_cost_attribution(
        total_attributed_cost=100000.0,
        actual_cloud_bill=105000.0,
        tolerance=0.10
    )

    assert result["status"] == "PASS"
    assert result["variance_percent"] < 10


def test_validate_cost_attribution_fail():
    """Test cost attribution validation fails on high variance"""
    result = validate_cost_attribution(
        total_attributed_cost=100000.0,
        actual_cloud_bill=150000.0,
        tolerance=0.10
    )

    assert result["status"] == "FAIL"
    assert result["variance_percent"] > 10
    assert "investigate" in result["message"].lower()


# Test Edge Cases
def test_zero_query_cost_per_query(cost_engine):
    """Test cost per query when query count is zero"""
    now = datetime.utcnow()
    usage = UsageMetrics(
        tenant_id="test",
        query_count=0,
        storage_gb=100.0,
        compute_pod_hours=50.0,
        vector_operations=0,
        period_start=now.isoformat(),
        period_end=(now + timedelta(days=30)).isoformat()
    )

    breakdown = cost_engine.calculate_tenant_cost("test", usage)
    assert breakdown.cost_per_query == 0.0


def test_invoice_format(report_generator, sample_usage):
    """Test invoice is properly formatted for CFO"""
    invoice = report_generator.generate_monthly_invoice("finance", sample_usage)

    # Check required fields
    assert "invoice_id" in invoice
    assert "billing_period" in invoice
    assert "line_items" in invoice
    assert "subtotal" in invoice
    assert "overhead" in invoice
    assert "discount" in invoice
    assert "total" in invoice

    # Check line items
    assert len(invoice["line_items"]) == 4
    for item in invoice["line_items"]:
        assert "description" in item
        assert "quantity" in item
        assert "cost" in item


def test_cost_breakdown_to_dict(cost_engine, sample_usage):
    """Test cost breakdown converts to dict"""
    breakdown = cost_engine.calculate_tenant_cost("finance", sample_usage)
    data = breakdown.to_dict()

    assert isinstance(data, dict)
    assert "tenant_id" in data
    assert "final_cost" in data
    assert "llm_cost" in data
