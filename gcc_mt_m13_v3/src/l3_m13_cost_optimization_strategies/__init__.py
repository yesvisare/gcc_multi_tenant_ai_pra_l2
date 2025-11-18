"""
L3 M13.3: Cost Optimization Strategies

This module implements cost attribution and optimization for multi-tenant RAG systems.
It provides usage metering, cost calculation with volume discounts, chargeback report
generation, and anomaly detection for GCC enterprise platforms.

Key capabilities:
- Track per-tenant usage (queries, storage, compute, vector operations)
- Calculate costs with multi-component formula and overhead allocation
- Apply volume discounts (15% @ 10K, 30% @ 100K, 40% @ 1M queries)
- Generate CFO-ready monthly invoices
- Detect cost anomalies (>50% spikes with root cause analysis)
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
from enum import Enum

logger = logging.getLogger(__name__)

__all__ = [
    "TenantUsageMetering",
    "CostCalculationEngine",
    "ChargebackReportGenerator",
    "CostAnomalyDetector",
    "UsageMetrics",
    "CostBreakdown",
    "VolumeDiscountTier"
]


class VolumeDiscountTier(Enum):
    """Volume discount tiers based on monthly query count"""
    TIER_0 = (0, 10_000, 0.00)          # < 10K: 0% discount
    TIER_1 = (10_000, 100_000, 0.15)    # 10K-100K: 15% discount
    TIER_2 = (100_000, 1_000_000, 0.30) # 100K-1M: 30% discount
    TIER_3 = (1_000_000, float('inf'), 0.40)  # >1M: 40% discount


@dataclass
class UsageMetrics:
    """Container for tenant usage metrics"""
    tenant_id: str
    query_count: int
    storage_gb: float
    compute_pod_hours: float
    vector_operations: int
    period_start: str
    period_end: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class CostBreakdown:
    """Detailed cost breakdown for a tenant"""
    tenant_id: str
    period: str

    # Direct costs
    llm_cost: float
    storage_cost: float
    compute_cost: float
    vector_cost: float
    direct_total: float

    # Overhead and discounts
    overhead_rate: float
    overhead_cost: float
    volume_discount_rate: float
    volume_discount_amount: float

    # Final costs
    final_cost: float
    cost_per_query: float

    # Usage metrics
    query_count: int
    storage_gb: float
    compute_pod_hours: float
    vector_operations: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    def to_invoice_format(self) -> Dict[str, Any]:
        """Format for CFO-ready invoice"""
        return {
            "tenant_id": self.tenant_id,
            "billing_period": self.period,
            "line_items": [
                {"description": "LLM API Calls", "quantity": self.query_count, "cost": f"₹{self.llm_cost:.2f}"},
                {"description": "Storage", "quantity": f"{self.storage_gb:.1f} GB", "cost": f"₹{self.storage_cost:.2f}"},
                {"description": "Compute", "quantity": f"{self.compute_pod_hours:.1f} pod-hours", "cost": f"₹{self.compute_cost:.2f}"},
                {"description": "Vector Operations", "quantity": self.vector_operations, "cost": f"₹{self.vector_cost:.2f}"},
            ],
            "subtotal": f"₹{self.direct_total:.2f}",
            "overhead": f"₹{self.overhead_cost:.2f} ({self.overhead_rate*100:.0f}%)",
            "discount": f"-₹{self.volume_discount_amount:.2f} ({self.volume_discount_rate*100:.0f}%)",
            "total": f"₹{self.final_cost:.2f}",
            "cost_per_query": f"₹{self.cost_per_query:.2f}"
        }


class TenantUsageMetering:
    """
    Tracks per-tenant usage metrics for multi-tenant RAG platform.

    This class provides methods to record usage events (queries, storage, compute, vector ops)
    with minimal latency overhead (<5ms). Uses singleton pattern for shared metering.

    Cost constants (as of 2025):
    - LLM API: $0.002 per 1K tokens (~1 query)
    - Storage: $0.023 per GB/month
    - Compute: $0.05 per pod-hour
    - Vector Operations: $0.0001 per operation
    """

    # Cost constants (USD)
    LLM_COST_PER_QUERY = 0.002
    STORAGE_COST_PER_GB = 0.023
    COMPUTE_COST_PER_POD_HOUR = 0.05
    VECTOR_COST_PER_OP = 0.0001
    USD_TO_INR = 83.0

    def __init__(self):
        """Initialize usage tracking storage"""
        self._usage_data: Dict[str, UsageMetrics] = {}
        logger.info("Initialized TenantUsageMetering")

    def record_query(self, tenant_id: str, query_count: int = 1) -> None:
        """
        Record query execution for tenant.

        Args:
            tenant_id: Unique tenant identifier
            query_count: Number of queries (default: 1)
        """
        logger.debug(f"Recording {query_count} queries for tenant {tenant_id}")

        if tenant_id not in self._usage_data:
            self._init_tenant_metrics(tenant_id)

        self._usage_data[tenant_id].query_count += query_count

    def record_storage(self, tenant_id: str, storage_gb: float) -> None:
        """
        Record storage usage for tenant.

        Args:
            tenant_id: Unique tenant identifier
            storage_gb: Storage in gigabytes
        """
        logger.debug(f"Recording {storage_gb:.2f} GB storage for tenant {tenant_id}")

        if tenant_id not in self._usage_data:
            self._init_tenant_metrics(tenant_id)

        self._usage_data[tenant_id].storage_gb = storage_gb

    def record_compute(self, tenant_id: str, pod_hours: float) -> None:
        """
        Record compute usage for tenant.

        Args:
            tenant_id: Unique tenant identifier
            pod_hours: Compute time in pod-hours
        """
        logger.debug(f"Recording {pod_hours:.2f} pod-hours for tenant {tenant_id}")

        if tenant_id not in self._usage_data:
            self._init_tenant_metrics(tenant_id)

        self._usage_data[tenant_id].compute_pod_hours += pod_hours

    def record_vector_operation(self, tenant_id: str, operation_count: int = 1) -> None:
        """
        Record vector database operations for tenant.

        Args:
            tenant_id: Unique tenant identifier
            operation_count: Number of vector operations
        """
        logger.debug(f"Recording {operation_count} vector ops for tenant {tenant_id}")

        if tenant_id not in self._usage_data:
            self._init_tenant_metrics(tenant_id)

        self._usage_data[tenant_id].vector_operations += operation_count

    def get_tenant_usage(self, tenant_id: str) -> Optional[UsageMetrics]:
        """
        Get usage metrics for a specific tenant.

        Args:
            tenant_id: Unique tenant identifier

        Returns:
            UsageMetrics if found, None otherwise
        """
        return self._usage_data.get(tenant_id)

    def get_all_usage(self) -> Dict[str, UsageMetrics]:
        """
        Get usage metrics for all tenants.

        Returns:
            Dictionary mapping tenant_id to UsageMetrics
        """
        return self._usage_data.copy()

    def reset_tenant_usage(self, tenant_id: str) -> None:
        """
        Reset usage metrics for a tenant (e.g., start of new billing period).

        Args:
            tenant_id: Unique tenant identifier
        """
        if tenant_id in self._usage_data:
            self._init_tenant_metrics(tenant_id)
            logger.info(f"Reset usage metrics for tenant {tenant_id}")

    def _init_tenant_metrics(self, tenant_id: str) -> None:
        """Initialize empty metrics for a tenant"""
        now = datetime.utcnow()
        self._usage_data[tenant_id] = UsageMetrics(
            tenant_id=tenant_id,
            query_count=0,
            storage_gb=0.0,
            compute_pod_hours=0.0,
            vector_operations=0,
            period_start=now.isoformat(),
            period_end=(now + timedelta(days=30)).isoformat()
        )


class CostCalculationEngine:
    """
    Calculates tenant costs with multi-component formula.

    Formula: Direct Costs + (20% Overhead) - Volume Discounts = Final Cost

    Direct costs include:
    - LLM API calls
    - Storage
    - Compute
    - Vector operations

    Overhead rate: 20% (covers platform team salaries, monitoring, tooling)
    Volume discounts: 0%, 15%, 30%, 40% based on query volume
    """

    DEFAULT_OVERHEAD_RATE = 0.20  # 20% overhead

    def __init__(self, overhead_rate: float = DEFAULT_OVERHEAD_RATE):
        """
        Initialize cost calculation engine.

        Args:
            overhead_rate: Overhead allocation rate (default: 0.20)
        """
        self.overhead_rate = overhead_rate
        self.metering = TenantUsageMetering()
        logger.info(f"Initialized CostCalculationEngine with {overhead_rate*100:.0f}% overhead")

    def calculate_tenant_cost(
        self,
        tenant_id: str,
        usage: UsageMetrics
    ) -> CostBreakdown:
        """
        Calculate complete cost breakdown for a tenant.

        Args:
            tenant_id: Unique tenant identifier
            usage: Usage metrics for the billing period

        Returns:
            CostBreakdown with detailed cost components
        """
        logger.info(f"Calculating costs for tenant {tenant_id}")

        # Calculate direct costs (in USD)
        llm_cost_usd = usage.query_count * TenantUsageMetering.LLM_COST_PER_QUERY
        storage_cost_usd = usage.storage_gb * TenantUsageMetering.STORAGE_COST_PER_GB
        compute_cost_usd = usage.compute_pod_hours * TenantUsageMetering.COMPUTE_COST_PER_POD_HOUR
        vector_cost_usd = usage.vector_operations * TenantUsageMetering.VECTOR_COST_PER_OP

        direct_total_usd = llm_cost_usd + storage_cost_usd + compute_cost_usd + vector_cost_usd

        # Convert to INR
        llm_cost = llm_cost_usd * TenantUsageMetering.USD_TO_INR
        storage_cost = storage_cost_usd * TenantUsageMetering.USD_TO_INR
        compute_cost = compute_cost_usd * TenantUsageMetering.USD_TO_INR
        vector_cost = vector_cost_usd * TenantUsageMetering.USD_TO_INR
        direct_total = direct_total_usd * TenantUsageMetering.USD_TO_INR

        # Calculate overhead
        overhead_cost = direct_total * self.overhead_rate

        # Determine volume discount
        discount_rate = self._get_volume_discount_rate(usage.query_count)
        discount_amount = (direct_total + overhead_cost) * discount_rate

        # Calculate final cost
        final_cost = direct_total + overhead_cost - discount_amount

        # Cost per query
        cost_per_query = final_cost / usage.query_count if usage.query_count > 0 else 0.0

        breakdown = CostBreakdown(
            tenant_id=tenant_id,
            period=f"{usage.period_start[:10]} to {usage.period_end[:10]}",
            llm_cost=llm_cost,
            storage_cost=storage_cost,
            compute_cost=compute_cost,
            vector_cost=vector_cost,
            direct_total=direct_total,
            overhead_rate=self.overhead_rate,
            overhead_cost=overhead_cost,
            volume_discount_rate=discount_rate,
            volume_discount_amount=discount_amount,
            final_cost=final_cost,
            cost_per_query=cost_per_query,
            query_count=usage.query_count,
            storage_gb=usage.storage_gb,
            compute_pod_hours=usage.compute_pod_hours,
            vector_operations=usage.vector_operations
        )

        logger.info(
            f"Tenant {tenant_id}: Direct=₹{direct_total:.2f}, "
            f"Overhead=₹{overhead_cost:.2f}, Discount=₹{discount_amount:.2f}, "
            f"Final=₹{final_cost:.2f}"
        )

        return breakdown

    def _get_volume_discount_rate(self, query_count: int) -> float:
        """
        Determine volume discount rate based on query count.

        Args:
            query_count: Total queries in billing period

        Returns:
            Discount rate (0.00 to 0.40)
        """
        for tier in VolumeDiscountTier:
            min_queries, max_queries, discount = tier.value
            if min_queries <= query_count < max_queries:
                logger.debug(f"Query count {query_count} → {discount*100:.0f}% discount ({tier.name})")
                return discount

        return 0.0

    def estimate_migration_cost(
        self,
        num_documents: int,
        avg_doc_size_mb: float
    ) -> Dict[str, Any]:
        """
        Estimate cost for bulk document migration.

        Helps tenants understand cost impact before uploading large document sets.

        Args:
            num_documents: Number of documents to upload
            avg_doc_size_mb: Average document size in MB

        Returns:
            Dict with cost estimate and warnings
        """
        total_size_gb = (num_documents * avg_doc_size_mb) / 1024
        storage_cost_usd = total_size_gb * TenantUsageMetering.STORAGE_COST_PER_GB
        storage_cost_inr = storage_cost_usd * TenantUsageMetering.USD_TO_INR

        estimate = {
            "num_documents": num_documents,
            "total_size_gb": round(total_size_gb, 2),
            "monthly_storage_cost_usd": round(storage_cost_usd, 2),
            "monthly_storage_cost_inr": round(storage_cost_inr, 2),
            "warning": None
        }

        # Add warning for large migrations
        if storage_cost_inr > 50000:  # ₹50K threshold
            estimate["warning"] = f"High cost migration: ₹{storage_cost_inr:.0f}/month storage"
            logger.warning(f"Large migration detected: {num_documents} docs, ₹{storage_cost_inr:.0f}/month")

        return estimate


class ChargebackReportGenerator:
    """
    Generates CFO-ready chargeback reports and invoices.

    Supports:
    - Monthly invoices with detailed cost breakdowns
    - Multi-tenant summary reports
    - Historical cost trends
    - Export to JSON (can be extended to PDF with ReportLab)
    """

    def __init__(self, cost_engine: CostCalculationEngine):
        """
        Initialize report generator.

        Args:
            cost_engine: Cost calculation engine instance
        """
        self.cost_engine = cost_engine
        logger.info("Initialized ChargebackReportGenerator")

    def generate_monthly_invoice(
        self,
        tenant_id: str,
        usage: UsageMetrics
    ) -> Dict[str, Any]:
        """
        Generate monthly invoice for a tenant.

        Args:
            tenant_id: Unique tenant identifier
            usage: Usage metrics for the month

        Returns:
            Invoice dictionary (CFO-ready format)
        """
        logger.info(f"Generating invoice for tenant {tenant_id}")

        cost_breakdown = self.cost_engine.calculate_tenant_cost(tenant_id, usage)
        invoice = cost_breakdown.to_invoice_format()

        invoice["invoice_id"] = f"INV-{tenant_id}-{datetime.utcnow().strftime('%Y%m')}"
        invoice["generated_at"] = datetime.utcnow().isoformat()

        return invoice

    def generate_platform_summary(
        self,
        all_usage: Dict[str, UsageMetrics]
    ) -> Dict[str, Any]:
        """
        Generate platform-wide cost summary across all tenants.

        Args:
            all_usage: Dictionary of all tenant usage metrics

        Returns:
            Platform summary with aggregated costs
        """
        logger.info(f"Generating platform summary for {len(all_usage)} tenants")

        tenant_costs = []
        total_cost = 0.0
        total_queries = 0

        for tenant_id, usage in all_usage.items():
            breakdown = self.cost_engine.calculate_tenant_cost(tenant_id, usage)
            tenant_costs.append({
                "tenant_id": tenant_id,
                "cost": breakdown.final_cost,
                "queries": usage.query_count,
                "cost_per_query": breakdown.cost_per_query
            })
            total_cost += breakdown.final_cost
            total_queries += usage.query_count

        # Sort by cost (descending)
        tenant_costs.sort(key=lambda x: x["cost"], reverse=True)

        summary = {
            "report_type": "platform_summary",
            "generated_at": datetime.utcnow().isoformat(),
            "tenant_count": len(all_usage),
            "total_cost_inr": round(total_cost, 2),
            "total_queries": total_queries,
            "avg_cost_per_query": round(total_cost / total_queries, 4) if total_queries > 0 else 0,
            "top_tenants": tenant_costs[:10],  # Top 10 by cost
            "cost_distribution": {
                "top_10_percent": sum(t["cost"] for t in tenant_costs[:max(1, len(tenant_costs)//10)]),
                "top_50_percent": sum(t["cost"] for t in tenant_costs[:max(1, len(tenant_costs)//2)])
            }
        }

        logger.info(
            f"Platform summary: {len(all_usage)} tenants, "
            f"₹{total_cost:.0f} total, {total_queries} queries"
        )

        return summary

    def export_invoice_json(self, invoice: Dict[str, Any], filepath: str) -> None:
        """
        Export invoice to JSON file.

        Args:
            invoice: Invoice dictionary
            filepath: Output file path
        """
        with open(filepath, 'w') as f:
            json.dump(invoice, f, indent=2)
        logger.info(f"Exported invoice to {filepath}")


class CostAnomalyDetector:
    """
    Detects cost anomalies and spikes in tenant usage.

    Alerts on:
    - >50% month-over-month cost increase
    - Unusual usage patterns (query surge, storage spike)
    - Provides root cause hints for investigation
    """

    SPIKE_THRESHOLD = 0.50  # 50% increase triggers alert

    def __init__(self):
        """Initialize anomaly detector with historical data storage"""
        self._historical_costs: Dict[str, List[float]] = {}
        logger.info("Initialized CostAnomalyDetector")

    def check_anomaly(
        self,
        tenant_id: str,
        current_cost: float,
        current_usage: UsageMetrics
    ) -> Optional[Dict[str, Any]]:
        """
        Check for cost anomalies for a tenant.

        Args:
            tenant_id: Unique tenant identifier
            current_cost: Current month cost
            current_usage: Current month usage metrics

        Returns:
            Anomaly alert dict if detected, None otherwise
        """
        logger.debug(f"Checking anomaly for tenant {tenant_id}, cost=₹{current_cost:.2f}")

        # Get historical costs
        if tenant_id not in self._historical_costs:
            self._historical_costs[tenant_id] = []

        history = self._historical_costs[tenant_id]

        # Need at least 1 historical data point
        if len(history) == 0:
            history.append(current_cost)
            return None

        # Calculate month-over-month change
        previous_cost = history[-1]

        if previous_cost == 0:
            # Avoid division by zero
            history.append(current_cost)
            return None

        change_rate = (current_cost - previous_cost) / previous_cost

        # Update history
        history.append(current_cost)

        # Keep only last 12 months
        if len(history) > 12:
            history.pop(0)

        # Check if spike exceeds threshold
        if change_rate > self.SPIKE_THRESHOLD:
            logger.warning(
                f"ANOMALY DETECTED: Tenant {tenant_id} cost spike "
                f"{change_rate*100:.1f}% (₹{previous_cost:.0f} → ₹{current_cost:.0f})"
            )

            # Determine root cause hints
            root_causes = self._analyze_root_cause(current_usage)

            alert = {
                "alert_type": "cost_spike",
                "tenant_id": tenant_id,
                "previous_cost": round(previous_cost, 2),
                "current_cost": round(current_cost, 2),
                "change_percent": round(change_rate * 100, 1),
                "threshold_percent": self.SPIKE_THRESHOLD * 100,
                "detected_at": datetime.utcnow().isoformat(),
                "root_cause_hints": root_causes,
                "action_required": "Contact tenant owner to verify usage pattern"
            }

            return alert

        return None

    def _analyze_root_cause(self, usage: UsageMetrics) -> List[str]:
        """
        Analyze usage metrics to provide root cause hints.

        Args:
            usage: Current usage metrics

        Returns:
            List of possible root causes
        """
        hints = []

        if usage.query_count > 100000:
            hints.append(f"High query volume: {usage.query_count:,} queries")

        if usage.storage_gb > 1000:
            hints.append(f"Large storage usage: {usage.storage_gb:.1f} GB")

        if usage.compute_pod_hours > 500:
            hints.append(f"High compute usage: {usage.compute_pod_hours:.1f} pod-hours")

        if usage.vector_operations > 1000000:
            hints.append(f"High vector ops: {usage.vector_operations:,} operations")

        if not hints:
            hints.append("Usage within normal ranges - investigate cost formula changes")

        return hints

    def get_cost_trend(self, tenant_id: str) -> List[float]:
        """
        Get historical cost trend for a tenant.

        Args:
            tenant_id: Unique tenant identifier

        Returns:
            List of historical costs (up to 12 months)
        """
        return self._historical_costs.get(tenant_id, []).copy()


# Validation utility
def validate_cost_attribution(
    total_attributed_cost: float,
    actual_cloud_bill: float,
    tolerance: float = 0.10
) -> Dict[str, Any]:
    """
    Validate cost attribution accuracy by comparing to actual cloud bill.

    Monthly reconciliation check to ensure metering captures all cost components.

    Args:
        total_attributed_cost: Sum of all tenant costs
        actual_cloud_bill: Actual cloud provider bill
        tolerance: Acceptable variance (default: 10%)

    Returns:
        Validation result with variance and status
    """
    variance = abs(total_attributed_cost - actual_cloud_bill) / actual_cloud_bill
    variance_percent = variance * 100

    status = "PASS" if variance <= tolerance else "FAIL"

    result = {
        "status": status,
        "total_attributed_cost": round(total_attributed_cost, 2),
        "actual_cloud_bill": round(actual_cloud_bill, 2),
        "variance_percent": round(variance_percent, 2),
        "tolerance_percent": tolerance * 100,
        "message": None
    }

    if status == "FAIL":
        result["message"] = (
            f"Cost attribution variance {variance_percent:.1f}% exceeds "
            f"{tolerance*100:.0f}% tolerance. Investigate missing cost components."
        )
        logger.error(result["message"])
    else:
        result["message"] = f"Cost attribution accurate: {variance_percent:.1f}% variance"
        logger.info(result["message"])

    return result
