"""
FastAPI application for L3 M13.3: Cost Optimization Strategies

Provides REST API endpoints for multi-tenant cost attribution:
- Record usage metrics (queries, storage, compute, vector ops)
- Calculate tenant costs with volume discounts
- Generate chargeback reports and invoices
- Detect cost anomalies

This module runs entirely locally - no external AI services required.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.l3_m13_cost_optimization_strategies import (
    TenantUsageMetering,
    CostCalculationEngine,
    ChargebackReportGenerator,
    CostAnomalyDetector,
    UsageMetrics,
    validate_cost_attribution
)
from config import get_config_summary

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="L3 M13.3: Cost Optimization API",
    description="Multi-tenant cost attribution and optimization for RAG platforms",
    version="1.0.0"
)

# Initialize components
metering = TenantUsageMetering()
cost_engine = CostCalculationEngine()
report_generator = ChargebackReportGenerator(cost_engine)
anomaly_detector = CostAnomalyDetector()


# Request/Response Models
class RecordQueryRequest(BaseModel):
    """Request to record query usage"""
    tenant_id: str = Field(..., description="Unique tenant identifier")
    query_count: int = Field(1, ge=1, description="Number of queries executed")


class RecordStorageRequest(BaseModel):
    """Request to record storage usage"""
    tenant_id: str = Field(..., description="Unique tenant identifier")
    storage_gb: float = Field(..., ge=0, description="Storage in gigabytes")


class RecordComputeRequest(BaseModel):
    """Request to record compute usage"""
    tenant_id: str = Field(..., description="Unique tenant identifier")
    pod_hours: float = Field(..., ge=0, description="Compute time in pod-hours")


class RecordVectorRequest(BaseModel):
    """Request to record vector operations"""
    tenant_id: str = Field(..., description="Unique tenant identifier")
    operation_count: int = Field(1, ge=1, description="Number of vector operations")


class MigrationEstimateRequest(BaseModel):
    """Request to estimate migration cost"""
    num_documents: int = Field(..., ge=1, description="Number of documents to upload")
    avg_doc_size_mb: float = Field(..., ge=0.001, description="Average document size in MB")


class ValidateCostsRequest(BaseModel):
    """Request to validate cost attribution accuracy"""
    actual_cloud_bill: float = Field(..., ge=0, description="Actual cloud provider bill amount")
    tolerance: float = Field(0.10, ge=0, le=1, description="Acceptable variance (default: 0.10 = 10%)")


# Endpoints
@app.get("/")
def root():
    """Health check and configuration status"""
    config = get_config_summary()
    return {
        "status": "healthy",
        "module": "L3_M13_Cost_Optimization_Strategies",
        "description": "Multi-tenant cost attribution for RAG platforms",
        "mode": config["mode"],
        "infrastructure": config["infrastructure"],
        "endpoints": {
            "usage": "/usage/* (record metrics)",
            "costs": "/costs/* (calculate costs)",
            "reports": "/reports/* (generate invoices)",
            "anomalies": "/anomalies/* (detect spikes)",
            "utilities": "/estimate, /validate"
        }
    }


# Usage Recording Endpoints
@app.post("/usage/query")
def record_query(request: RecordQueryRequest):
    """
    Record query execution for a tenant.

    Used to track LLM API usage for cost attribution.
    """
    try:
        metering.record_query(request.tenant_id, request.query_count)
        return {
            "status": "recorded",
            "tenant_id": request.tenant_id,
            "query_count": request.query_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to record query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/usage/storage")
def record_storage(request: RecordStorageRequest):
    """
    Record storage usage for a tenant.

    Used to track document storage costs.
    """
    try:
        metering.record_storage(request.tenant_id, request.storage_gb)
        return {
            "status": "recorded",
            "tenant_id": request.tenant_id,
            "storage_gb": request.storage_gb,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to record storage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/usage/compute")
def record_compute(request: RecordComputeRequest):
    """
    Record compute usage for a tenant.

    Used to track pod-hours for cost attribution.
    """
    try:
        metering.record_compute(request.tenant_id, request.pod_hours)
        return {
            "status": "recorded",
            "tenant_id": request.tenant_id,
            "pod_hours": request.pod_hours,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to record compute: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/usage/vector")
def record_vector(request: RecordVectorRequest):
    """
    Record vector database operations for a tenant.

    Used to track vector search/insert costs.
    """
    try:
        metering.record_vector_operation(request.tenant_id, request.operation_count)
        return {
            "status": "recorded",
            "tenant_id": request.tenant_id,
            "operation_count": request.operation_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to record vector ops: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Cost Calculation Endpoints
@app.get("/costs/tenant/{tenant_id}")
def get_tenant_cost(tenant_id: str):
    """
    Get current cost breakdown for a tenant.

    Returns detailed cost components including volume discounts.
    """
    usage = metering.get_tenant_usage(tenant_id)

    if not usage:
        raise HTTPException(
            status_code=404,
            detail=f"No usage data found for tenant {tenant_id}"
        )

    try:
        cost_breakdown = cost_engine.calculate_tenant_cost(tenant_id, usage)
        return cost_breakdown.to_dict()
    except Exception as e:
        logger.error(f"Failed to calculate cost: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/costs/tenant/{tenant_id}/invoice")
def get_tenant_invoice(tenant_id: str):
    """
    Get CFO-ready invoice for a tenant.

    Returns formatted invoice with line items and totals.
    """
    usage = metering.get_tenant_usage(tenant_id)

    if not usage:
        raise HTTPException(
            status_code=404,
            detail=f"No usage data found for tenant {tenant_id}"
        )

    try:
        invoice = report_generator.generate_monthly_invoice(tenant_id, usage)
        return invoice
    except Exception as e:
        logger.error(f"Failed to generate invoice: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/costs/platform/summary")
def get_platform_summary():
    """
    Get platform-wide cost summary across all tenants.

    Returns aggregated costs, top tenants, and distribution metrics.
    """
    all_usage = metering.get_all_usage()

    if not all_usage:
        return {
            "report_type": "platform_summary",
            "tenant_count": 0,
            "total_cost_inr": 0,
            "message": "No usage data recorded yet"
        }

    try:
        summary = report_generator.generate_platform_summary(all_usage)
        return summary
    except Exception as e:
        logger.error(f"Failed to generate summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Anomaly Detection Endpoints
@app.get("/anomalies/tenant/{tenant_id}")
def check_tenant_anomaly(tenant_id: str):
    """
    Check for cost anomalies for a tenant.

    Alerts on >50% month-over-month cost increase.
    """
    usage = metering.get_tenant_usage(tenant_id)

    if not usage:
        raise HTTPException(
            status_code=404,
            detail=f"No usage data found for tenant {tenant_id}"
        )

    try:
        cost_breakdown = cost_engine.calculate_tenant_cost(tenant_id, usage)
        anomaly = anomaly_detector.check_anomaly(
            tenant_id,
            cost_breakdown.final_cost,
            usage
        )

        if anomaly:
            return {
                "anomaly_detected": True,
                "alert": anomaly
            }
        else:
            return {
                "anomaly_detected": False,
                "message": "No cost anomalies detected",
                "current_cost": cost_breakdown.final_cost
            }
    except Exception as e:
        logger.error(f"Failed to check anomaly: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/anomalies/tenant/{tenant_id}/trend")
def get_cost_trend(tenant_id: str):
    """
    Get historical cost trend for a tenant.

    Returns up to 12 months of historical costs.
    """
    trend = anomaly_detector.get_cost_trend(tenant_id)

    return {
        "tenant_id": tenant_id,
        "historical_costs": trend,
        "data_points": len(trend)
    }


# Utility Endpoints
@app.post("/estimate/migration")
def estimate_migration(request: MigrationEstimateRequest):
    """
    Estimate cost for bulk document migration.

    Helps tenants understand storage cost impact before uploading.
    """
    try:
        estimate = cost_engine.estimate_migration_cost(
            request.num_documents,
            request.avg_doc_size_mb
        )
        return estimate
    except Exception as e:
        logger.error(f"Failed to estimate migration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/validate/attribution")
def validate_attribution(request: ValidateCostsRequest):
    """
    Validate cost attribution accuracy vs. actual cloud bill.

    Monthly reconciliation to ensure all cost components are tracked.
    """
    all_usage = metering.get_all_usage()

    if not all_usage:
        raise HTTPException(
            status_code=400,
            detail="No usage data available for validation"
        )

    try:
        # Calculate total attributed costs
        total_attributed = 0.0
        for tenant_id, usage in all_usage.items():
            breakdown = cost_engine.calculate_tenant_cost(tenant_id, usage)
            total_attributed += breakdown.final_cost

        # Validate against actual bill
        validation_result = validate_cost_attribution(
            total_attributed,
            request.actual_cloud_bill,
            request.tolerance
        )

        return validation_result
    except Exception as e:
        logger.error(f"Failed to validate attribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Admin Endpoints
@app.post("/admin/reset/{tenant_id}")
def reset_tenant_usage(tenant_id: str):
    """
    Reset usage metrics for a tenant (e.g., start of new billing period).

    Admin only - use with caution.
    """
    try:
        metering.reset_tenant_usage(tenant_id)
        return {
            "status": "reset",
            "tenant_id": tenant_id,
            "message": "Usage metrics reset to zero"
        }
    except Exception as e:
        logger.error(f"Failed to reset tenant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/tenants")
def list_tenants():
    """
    List all tenants with current usage.

    Returns summary of all tracked tenants.
    """
    all_usage = metering.get_all_usage()

    tenant_list = [
        {
            "tenant_id": tenant_id,
            "query_count": usage.query_count,
            "storage_gb": usage.storage_gb,
            "compute_pod_hours": usage.compute_pod_hours,
            "vector_operations": usage.vector_operations
        }
        for tenant_id, usage in all_usage.items()
    ]

    return {
        "tenant_count": len(tenant_list),
        "tenants": tenant_list
    }
