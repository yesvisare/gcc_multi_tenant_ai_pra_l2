"""
FastAPI application for L3 M11.4: Tenant Provisioning & Automation

Provides REST API endpoints for automated tenant provisioning workflows.

SERVICE: PROVISIONING (Terraform-based infrastructure automation)
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import logging
from typing import Dict, Any, Optional
import os

from src.l3_m11_tenant_provisioning import (
    TenantTier,
    TenantStatus,
    TenantRequest,
    provision_tenant_workflow,
    simulate_provisioning_workflow,
    approve_tenant_request,
    validate_tenant,
    rollback_provisioning
)
from config import CLIENTS, get_config_summary, PROVISIONING_ENABLED

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="L3 M11.4: Tenant Provisioning API",
    description="""
    Automated tenant provisioning for multi-tenant RAG systems.

    Transforms manual 2-week onboarding into 15-minute automated deployments.

    Features:
    - Infrastructure as Code provisioning (Terraform)
    - 8-step validation suite
    - Transaction-like rollback semantics
    - Budget-based approval workflows
    - Cost optimization and compliance
    """,
    version="1.0.0"
)


# ========== Pydantic Models ==========

class ProvisionRequest(BaseModel):
    """Request model for tenant provisioning"""
    tenant_name: str = Field(..., description="Organization name", min_length=3, max_length=100)
    tier: str = Field(..., description="Resource tier: Gold, Silver, or Bronze")
    region: str = Field(default="us-east-1", description="AWS region for deployment")
    budget: float = Field(..., description="Annual budget allocation (₹)", gt=0)
    owner_email: str = Field(..., description="Tenant administrator email")

    @validator("tier")
    def validate_tier(cls, v):
        """Validate tier is valid"""
        valid_tiers = ["Gold", "Silver", "Bronze"]
        if v not in valid_tiers:
            raise ValueError(f"Tier must be one of: {valid_tiers}")
        return v

    @validator("region")
    def validate_region(cls, v):
        """Validate AWS region format"""
        valid_regions = [
            "us-east-1", "us-west-2", "eu-west-1", "eu-central-1",
            "ap-south-1", "ap-southeast-1", "ap-northeast-1"
        ]
        if v not in valid_regions:
            raise ValueError(f"Region must be one of: {valid_regions}")
        return v


class ProvisionResponse(BaseModel):
    """Response model for provisioning operations"""
    tenant_id: str
    status: str
    message: str
    workflow_results: Optional[Dict[str, Any]] = None


class ApprovalRequest(BaseModel):
    """Request model for manual approval"""
    tenant_id: str = Field(..., description="Tenant identifier")
    approver: str = Field(..., description="Approver identifier (e.g., CFO email)")
    decision: str = Field(..., description="Approval decision: approved or rejected")

    @validator("decision")
    def validate_decision(cls, v):
        """Validate decision is valid"""
        valid_decisions = ["approved", "rejected"]
        if v not in valid_decisions:
            raise ValueError(f"Decision must be one of: {valid_decisions}")
        return v


class ValidationRequest(BaseModel):
    """Request model for tenant validation"""
    tenant_id: str = Field(..., description="Tenant identifier")


class RollbackRequest(BaseModel):
    """Request model for manual rollback"""
    tenant_id: str = Field(..., description="Tenant identifier")
    failed_step: str = Field(..., description="Step that failed")
    reason: str = Field(..., description="Reason for rollback")


# ========== API Endpoints ==========

@app.get("/")
def root():
    """
    Health check and service information endpoint.

    Returns service status and configuration summary.
    """
    config = get_config_summary()

    return {
        "service": "L3 M11.4: Tenant Provisioning API",
        "status": "healthy",
        "module": "multi_tenant_foundations",
        "provisioning_enabled": PROVISIONING_ENABLED,
        "mode": "production" if PROVISIONING_ENABLED else "simulation",
        "configuration": config,
        "endpoints": [
            "POST /provision - Create new tenant",
            "POST /simulate - Simulate provisioning workflow",
            "POST /approve - Manual approval decision",
            "POST /validate - Run validation suite",
            "POST /rollback - Rollback provisioning",
            "GET /config - Configuration details"
        ]
    }


@app.get("/config")
def get_config():
    """
    Get detailed configuration information.

    Useful for debugging and verifying environment setup.
    """
    return {
        "configuration": get_config_summary(),
        "provisioning_enabled": PROVISIONING_ENABLED,
        "clients_available": list(CLIENTS.keys()),
        "mode": "production" if PROVISIONING_ENABLED else "simulation"
    }


@app.post("/provision", response_model=ProvisionResponse)
async def provision_tenant(request: ProvisionRequest):
    """
    Provision a new tenant with full infrastructure setup.

    Executes 8-step workflow:
    1. Request Submission
    2. Approval Workflow (auto or manual based on budget)
    3. Infrastructure Provisioning (Terraform)
    4. Configuration Initialization
    5. Validation Testing (8-test suite)
    6. Activation
    7. Notification
    8. Rollback on Failure

    **Timeline:** 12-15 minutes for complete provisioning

    **Approval Rules:**
    - Budgets <₹10L: Auto-approved
    - Budgets ≥₹10L: Requires CFO approval (returns pending status)
    """
    if not PROVISIONING_ENABLED:
        return ProvisionResponse(
            tenant_id=f"tenant_{request.tenant_name.lower().replace(' ', '_')}",
            status="simulation_mode",
            message="PROVISIONING_ENABLED is false. Set to true in .env for actual infrastructure provisioning.",
            workflow_results=None
        )

    try:
        # Create TenantRequest object
        tenant_request = TenantRequest(
            tenant_name=request.tenant_name,
            tier=TenantTier(request.tier),
            region=request.region,
            budget=request.budget,
            owner_email=request.owner_email
        )

        logger.info(f"Received provisioning request for {tenant_request.tenant_id}")

        # Execute provisioning workflow
        workflow_results = await provision_tenant_workflow(tenant_request, offline=False)

        # Determine response based on workflow status
        if workflow_results["status"] == "rejected":
            return ProvisionResponse(
                tenant_id=tenant_request.tenant_id,
                status="rejected",
                message=workflow_results["reason"],
                workflow_results=workflow_results
            )

        elif workflow_results["status"] == "completed":
            return ProvisionResponse(
                tenant_id=tenant_request.tenant_id,
                status="active",
                message=f"Tenant provisioned successfully in {workflow_results['total_duration_minutes']} minutes",
                workflow_results=workflow_results
            )

        elif workflow_results["status"] == "failed":
            return ProvisionResponse(
                tenant_id=tenant_request.tenant_id,
                status="failed",
                message=f"Provisioning failed: {workflow_results['error']}. Rollback completed.",
                workflow_results=workflow_results
            )

        else:
            return ProvisionResponse(
                tenant_id=tenant_request.tenant_id,
                status=workflow_results["status"],
                message="Provisioning in progress",
                workflow_results=workflow_results
            )

    except Exception as e:
        logger.error(f"Provisioning request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/simulate", response_model=ProvisionResponse)
async def simulate_provision(request: ProvisionRequest):
    """
    Simulate tenant provisioning workflow without actual infrastructure changes.

    Useful for:
    - Testing provisioning logic
    - Demonstrations
    - Estimating timelines
    - Validating configurations

    **Timeline:** <1 second (simulation mode)
    """
    try:
        logger.info(f"Simulating provisioning for {request.tenant_name}")

        # Execute simulation
        workflow_results = await simulate_provisioning_workflow(
            tenant_name=request.tenant_name,
            tier=TenantTier(request.tier),
            region=request.region,
            budget=request.budget
        )

        return ProvisionResponse(
            tenant_id=workflow_results["tenant_id"],
            status="simulated",
            message="Provisioning workflow simulated successfully (no infrastructure changes)",
            workflow_results=workflow_results
        )

    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/approve")
async def approve_tenant(request: ApprovalRequest):
    """
    Process manual approval decision for tenant request.

    Used when budget exceeds auto-approval threshold (₹10L).

    **Required for:**
    - High-budget tenants (≥₹10L)
    - Special compliance requirements
    - Multi-stakeholder approvals
    """
    try:
        logger.info(f"Processing approval for {request.tenant_id}: {request.decision}")

        if request.decision == "rejected":
            return {
                "tenant_id": request.tenant_id,
                "status": "rejected",
                "approver": request.approver,
                "message": "Tenant request rejected by approver"
            }

        # In production: Update tenant status and trigger provisioning
        return {
            "tenant_id": request.tenant_id,
            "status": "approved",
            "approver": request.approver,
            "message": "Approval recorded. Provisioning will commence.",
            "next_steps": "Provisioning workflow will be triggered automatically"
        }

    except Exception as e:
        logger.error(f"Approval processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/validate")
async def validate_tenant_endpoint(request: ValidationRequest):
    """
    Run 8-test validation suite for a tenant.

    Tests:
    1. Database connectivity
    2. Cross-tenant isolation (negative test)
    3. Vector search functionality
    4. JWT authentication generation
    5. Query performance (<500ms SLA)
    6. S3 upload permissions
    7. Prometheus metrics collection
    8. Cost tag verification

    **Timeline:** 2-3 minutes
    """
    try:
        logger.info(f"Running validation suite for {request.tenant_id}")

        # Run validation
        validation_results = await validate_tenant(
            request.tenant_id,
            offline=not PROVISIONING_ENABLED
        )

        return {
            "tenant_id": request.tenant_id,
            "validation_status": validation_results["status"],
            "all_tests_passed": validation_results["all_tests_passed"],
            "test_results": validation_results["tests"],
            "duration_seconds": validation_results["duration_seconds"]
        }

    except ValueError as e:
        # Validation failed
        logger.error(f"Validation failed for {request.tenant_id}: {e}")
        raise HTTPException(status_code=422, detail=str(e))

    except Exception as e:
        logger.error(f"Validation request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rollback")
async def rollback_tenant(request: RollbackRequest):
    """
    Manually trigger rollback for a tenant.

    Rollback actions:
    1. Execute terraform destroy
    2. Remove tenant from registry
    3. Send failure notifications

    **Use cases:**
    - Failed provisioning recovery
    - Tenant decommissioning
    - Error correction

    **Warning:** This operation cannot be undone.
    """
    try:
        logger.info(f"Initiating rollback for {request.tenant_id}")

        # Execute rollback
        rollback_results = await rollback_provisioning(
            request.tenant_id,
            request.failed_step,
            offline=not PROVISIONING_ENABLED
        )

        return {
            "tenant_id": request.tenant_id,
            "rollback_status": rollback_results["status"],
            "failed_step": request.failed_step,
            "reason": request.reason,
            "rollback_actions": rollback_results.get("rollback_actions", []),
            "message": rollback_results.get("message", "Rollback completed")
        }

    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health_check():
    """
    Detailed health check endpoint.

    Checks:
    - Service availability
    - Client connectivity
    - Configuration validity
    """
    health_status = {
        "service": "healthy",
        "provisioning_enabled": PROVISIONING_ENABLED,
        "clients_initialized": len(CLIENTS) > 0,
        "clients": list(CLIENTS.keys())
    }

    # Check critical dependencies
    if PROVISIONING_ENABLED and len(CLIENTS) == 0:
        health_status["service"] = "degraded"
        health_status["warning"] = "Provisioning enabled but no clients initialized"

    return health_status


# ========== Exception Handlers ==========

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle validation errors"""
    return JSONResponse(
        status_code=422,
        content={"error": "Validation Error", "detail": str(exc)}
    )


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request, exc):
    """Handle runtime errors"""
    return JSONResponse(
        status_code=500,
        content={"error": "Runtime Error", "detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
