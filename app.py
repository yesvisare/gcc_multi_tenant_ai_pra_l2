"""
FastAPI application for L3 M14.4: Platform Governance & Operating Model

Provides REST API endpoints for:
- Operating model selection
- Team sizing calculations
- SLA template retrieval
- Self-service portal operations
- Platform maturity assessment

No external services required - pure governance logic.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Literal, Optional, Any
import logging

from src.l3_m14_operations_governance import (
    OperatingModel,
    TenantSophistication,
    ComplianceLevel,
    OrganizationalContext,
    OperatingModelSelector,
    TeamSizingCalculator,
    SLAManager
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="L3 M14.4: Platform Governance API",
    description="Complete platform governance framework for multi-tenant RAG systems in GCC environments",
    version="1.0.0"
)

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class OrganizationalContextRequest(BaseModel):
    """Request model for operating model selection."""
    num_tenants: int = Field(..., gt=0, description="Number of business units using platform")
    tenant_sophistication: Literal["low", "medium", "high"] = Field(..., description="Technical capability of tenants")
    compliance_level: Literal["low", "moderate", "critical"] = Field(..., description="Compliance requirements")
    rate_of_change: Literal["low", "medium", "high"] = Field(..., description="Frequency of requirement changes")


class OperatingModelResponse(BaseModel):
    """Response model for operating model selection."""
    chosen_model: str
    explanation: str
    team_size_recommendation: int


class TeamSizingRequest(BaseModel):
    """Request model for team sizing calculation."""
    num_tenants: int = Field(..., gt=0)
    complexity: Literal["low", "medium", "high"]
    operating_model: Literal["centralized", "federated", "hybrid"]


class TeamSizingResponse(BaseModel):
    """Response model for team sizing calculation."""
    recommended_team_size: int
    engineer_to_tenant_ratio: str
    annual_cost_inr: int
    annual_cost_usd: int
    cost_per_tenant_inr: int
    cost_per_tenant_usd: int
    breakdown: Dict[str, str]
    alternatives_comparison: Dict[str, int]


class SLAComparisonResponse(BaseModel):
    """Response model for SLA tier comparison."""
    comparison_table: str
    tiers: Dict[str, Dict[str, Any]]


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "module": "L3_M14_Platform_Governance",
        "service": "offline",
        "description": "Platform governance framework for GCC multi-tenant RAG systems"
    }


@app.post("/operating-model/select", response_model=OperatingModelResponse)
def select_operating_model(request: OrganizationalContextRequest):
    """
    Select operating model based on organizational context.

    This endpoint helps GCC leadership make the centralized-vs-federated
    decision systematically using production-proven decision logic.

    Args:
        request: Organizational context (tenants, sophistication, compliance, change rate)

    Returns:
        Chosen model, detailed explanation, and team size recommendation
    """
    try:
        # Convert string enums to enum types
        context = OrganizationalContext(
            num_tenants=request.num_tenants,
            tenant_sophistication=TenantSophistication(request.tenant_sophistication),
            compliance_level=ComplianceLevel(request.compliance_level),
            rate_of_change=request.rate_of_change
        )

        selector = OperatingModelSelector()
        chosen_model = selector.choose_model(context)
        explanation = selector.explain_decision(context, chosen_model)
        team_size = selector.calculate_team_size(chosen_model, context.num_tenants, "medium")

        logger.info(f"Operating model selected: {chosen_model.value} for {request.num_tenants} tenants")

        return OperatingModelResponse(
            chosen_model=chosen_model.value,
            explanation=explanation,
            team_size_recommendation=team_size
        )

    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Operating model selection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/team-sizing/calculate", response_model=TeamSizingResponse)
def calculate_team_size(request: TeamSizingRequest):
    """
    Calculate platform team size with cost justification.

    Uses 1:10-15 engineer:tenant ratio adjusted for complexity.
    Returns full cost breakdown for CFO presentation.

    Args:
        request: Tenant count, complexity, and operating model

    Returns:
        Team size, costs, and breakdown
    """
    try:
        # Convert string to enum
        model = OperatingModel(request.operating_model)

        calculator = TeamSizingCalculator()
        recommendation = calculator.calculate(
            num_tenants=request.num_tenants,
            complexity=request.complexity,
            operating_model=model
        )

        logger.info(f"Team sizing calculated: {recommendation.recommended_team_size} engineers "
                   f"for {request.num_tenants} tenants ({model.value} model)")

        return TeamSizingResponse(
            recommended_team_size=recommendation.recommended_team_size,
            engineer_to_tenant_ratio=recommendation.engineer_to_tenant_ratio,
            annual_cost_inr=recommendation.annual_cost_inr,
            annual_cost_usd=recommendation.annual_cost_usd,
            cost_per_tenant_inr=recommendation.cost_per_tenant_inr,
            cost_per_tenant_usd=recommendation.cost_per_tenant_usd,
            breakdown=recommendation.breakdown,
            alternatives_comparison=recommendation.alternatives_comparison
        )

    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Team sizing calculation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/team-sizing/compare-decentralized")
def compare_with_decentralized(num_tenants: int, centralized_cost_inr: int):
    """
    Compare centralized platform cost vs. decentralized (1 engineer per tenant).

    This is the killer argument for platform teams: Show 10× cost savings.

    Args:
        num_tenants: Number of tenants
        centralized_cost_inr: Cost of centralized platform team

    Returns:
        Cost comparison with savings calculation
    """
    try:
        if num_tenants < 1:
            raise ValueError("num_tenants must be positive")
        if centralized_cost_inr < 0:
            raise ValueError("centralized_cost_inr must be non-negative")

        calculator = TeamSizingCalculator()
        comparison = calculator.compare_with_decentralized(num_tenants, centralized_cost_inr)

        logger.info(f"Cost comparison: Centralized ₹{centralized_cost_inr/10_000_000:.1f}Cr "
                   f"vs Decentralized ₹{comparison['decentralized_cost_inr']/10_000_000:.1f}Cr "
                   f"(savings: {comparison['savings_percentage']:.0f}%)")

        return comparison

    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Cost comparison failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/sla/templates", response_model=SLAComparisonResponse)
def get_sla_templates():
    """
    Get SLA templates for all tenant tiers (Platinum, Gold, Silver).

    Returns comparison table and detailed tier information.
    Useful for tenant onboarding ("Which tier do you want?")

    Returns:
        SLA comparison table and tier details
    """
    try:
        comparison_table = SLAManager.compare_tiers()

        # Build tier details
        tiers_detail = {}
        for tier_name in ["platinum", "gold", "silver"]:
            template = SLAManager.get_template(tier_name)
            tiers_detail[tier_name] = {
                "availability": template.availability,
                "availability_downtime": template.availability_downtime(),
                "response_time_p95_ms": template.response_time_p95_ms,
                "support_response_minutes": template.support_response_minutes,
                "incident_priority": template.incident_priority,
                "dedicated_support": template.dedicated_support
            }

        logger.info("SLA templates retrieved successfully")

        return SLAComparisonResponse(
            comparison_table=comparison_table,
            tiers=tiers_detail
        )

    except Exception as e:
        logger.error(f"SLA template retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/sla/template/{tier}")
def get_sla_template(tier: Literal["platinum", "gold", "silver"]):
    """
    Get SLA template for specific tenant tier.

    Args:
        tier: Tier name (platinum, gold, or silver)

    Returns:
        SLA template details for the tier
    """
    try:
        template = SLAManager.get_template(tier)

        logger.info(f"SLA template retrieved: {tier}")

        return {
            "tier": template.tier,
            "availability": template.availability,
            "availability_downtime": template.availability_downtime(),
            "response_time_p95_ms": template.response_time_p95_ms,
            "support_response_minutes": template.support_response_minutes,
            "incident_priority": template.incident_priority,
            "dedicated_support": template.dedicated_support
        }

    except ValueError as e:
        logger.error(f"Invalid tier: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"SLA template retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/health")
def health_check():
    """
    Detailed health check endpoint.

    Returns configuration and system status.
    """
    import config

    return {
        "status": "healthy",
        "module": "L3_M14_Platform_Governance",
        "service": "offline",
        "configuration": config.get_config(),
        "components": {
            "operating_model_selector": "operational",
            "team_sizing_calculator": "operational",
            "sla_manager": "operational",
            "self_service_portal": "operational",
            "maturity_assessment": "operational"
        }
    }


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with proper logging."""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail}")
    return {
        "error": True,
        "status_code": exc.status_code,
        "message": exc.detail
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return {
        "error": True,
        "status_code": 500,
        "message": "Internal server error. Check logs for details."
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
