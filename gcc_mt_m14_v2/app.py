"""
FastAPI application for L3 M14.2: Incident Management & Blast Radius

Provides REST API endpoints for incident management operations including
blast radius detection, circuit breaker status, and incident tracking.

SERVICE: PROMETHEUS (monitoring/metrics system)
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.l3_m14_operations_governance import (
    BlastRadiusDetector,
    TenantTier,
    IncidentPriority,
    TenantMetrics,
    Incident,
    create_incident,
    send_notifications,
    generate_postmortem_template,
)
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="L3 M14.2: Incident Management API",
    description="Incident management system with blast radius detection, circuit breaker isolation, and automated notifications for multi-tenant RAG platforms",
    version="1.0.0"
)

# Global state
incidents: List[Incident] = []
detector_instance: Optional[BlastRadiusDetector] = None

# ============================================================================
# Request/Response Models
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    module: str
    prometheus_enabled: bool
    prometheus_url: Optional[str]
    notification_config: Dict[str, bool]


class TenantConfigRequest(BaseModel):
    """Request to configure tenant tier."""
    tenant_id: str = Field(..., description="Tenant identifier")
    tier: str = Field(..., description="Tenant tier: platinum, gold, silver, bronze")


class TenantHealthResponse(BaseModel):
    """Response for tenant health check."""
    tenant_id: str
    is_failing: bool
    metrics: Optional[Dict[str, Any]]
    circuit_breaker_state: Optional[str]


class BlastRadiusResponse(BaseModel):
    """Response for blast radius scan."""
    scan_time: str
    failing_tenants_count: int
    failing_tenants: List[Dict[str, Any]]
    circuit_breaker_status: Dict[str, Dict[str, Any]]


class IncidentResponse(BaseModel):
    """Response for incident operations."""
    incident_id: str
    priority: str
    tenant_ids: List[str]
    created_at: str
    resolved_at: Optional[str]
    affected_tier: Optional[str]
    cost_impact_inr: Optional[float]


class PostmortemResponse(BaseModel):
    """Response with postmortem template."""
    incident_id: str
    postmortem: str


# ============================================================================
# Startup/Shutdown
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize detector on startup."""
    global detector_instance

    if config.PROMETHEUS_ENABLED:
        try:
            detector_instance = BlastRadiusDetector(
                prometheus_url=config.PROMETHEUS_URL,
                error_threshold=config.ERROR_THRESHOLD,
                check_interval_seconds=config.CHECK_INTERVAL,
                check_window=config.CHECK_WINDOW
            )
            logger.info(f"✓ Detector initialized: {config.PROMETHEUS_URL}")
        except Exception as e:
            logger.error(f"Failed to initialize detector: {e}")
    else:
        logger.warning("⚠️ Prometheus disabled - detector unavailable")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down incident management API")


# ============================================================================
# Endpoints
# ============================================================================

@app.get("/", response_model=HealthResponse)
def root():
    """
    Health check endpoint.

    Returns system status and configuration.
    """
    return HealthResponse(
        status="healthy",
        module="L3_M14_Operations_Governance",
        prometheus_enabled=config.PROMETHEUS_ENABLED,
        prometheus_url=config.PROMETHEUS_URL if config.PROMETHEUS_ENABLED else None,
        notification_config=config.get_notification_config()
    )


@app.post("/tenants/configure")
def configure_tenant(request: TenantConfigRequest):
    """
    Configure tenant tier for priority calculation.

    **Args:**
    - **tenant_id**: Tenant identifier
    - **tier**: Tenant tier (platinum, gold, silver, bronze)

    **Returns:**
    - Configuration status
    """
    if not detector_instance:
        raise HTTPException(
            status_code=503,
            detail="Detector unavailable - set PROMETHEUS_ENABLED=true"
        )

    try:
        tier = TenantTier(request.tier.lower())
        detector_instance.set_tenant_tier(request.tenant_id, tier)

        logger.info(f"Configured tenant {request.tenant_id} as {tier.value}")

        return {
            "status": "success",
            "tenant_id": request.tenant_id,
            "tier": tier.value
        }

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tier: {request.tier}. Must be: platinum, gold, silver, bronze"
        )


@app.get("/tenants/{tenant_id}/health", response_model=TenantHealthResponse)
def check_tenant_health(tenant_id: str):
    """
    Check health status of a specific tenant.

    **Args:**
    - **tenant_id**: Tenant identifier

    **Returns:**
    - Tenant health status with metrics and circuit breaker state
    """
    if not detector_instance:
        raise HTTPException(
            status_code=503,
            detail="Detector unavailable - set PROMETHEUS_ENABLED=true"
        )

    try:
        is_failing, metrics = detector_instance.check_tenant_health(tenant_id)

        breaker = detector_instance.circuit_breakers.get(tenant_id)
        breaker_state = breaker.state.value if breaker else None

        return TenantHealthResponse(
            tenant_id=tenant_id,
            is_failing=is_failing,
            metrics={
                "total_queries": metrics.total_queries,
                "error_queries": metrics.error_queries,
                "error_rate": metrics.error_rate,
                "timestamp": metrics.timestamp.isoformat(),
                "tier": metrics.tier.value
            } if metrics else None,
            circuit_breaker_state=breaker_state
        )

    except Exception as e:
        logger.error(f"Health check failed for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/blast-radius/scan", response_model=BlastRadiusResponse)
def scan_blast_radius():
    """
    Scan all tenants and detect blast radius.

    Queries Prometheus for all active tenants and identifies failing ones
    based on error rate threshold (default 50%).

    **Returns:**
    - List of failing tenants with metrics
    - Circuit breaker status for all tenants
    """
    if not detector_instance:
        raise HTTPException(
            status_code=503,
            detail="Detector unavailable - set PROMETHEUS_ENABLED=true"
        )

    try:
        scan_time = datetime.now()
        failing_tenants = detector_instance.detect_blast_radius()

        failing_tenants_data = [
            {
                "tenant_id": t.tenant_id,
                "error_rate": t.error_rate,
                "total_queries": t.total_queries,
                "error_queries": t.error_queries,
                "tier": t.tier.value,
                "timestamp": t.timestamp.isoformat()
            }
            for t in failing_tenants
        ]

        breaker_status = detector_instance.get_circuit_breaker_status()

        return BlastRadiusResponse(
            scan_time=scan_time.isoformat(),
            failing_tenants_count=len(failing_tenants),
            failing_tenants=failing_tenants_data,
            circuit_breaker_status=breaker_status
        )

    except Exception as e:
        logger.error(f"Blast radius scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/incidents/create", response_model=IncidentResponse)
def create_incident_endpoint(background_tasks: BackgroundTasks):
    """
    Create incident from current blast radius scan.

    Scans for failing tenants, calculates priority, and creates incident record.
    Sends notifications in background.

    **Returns:**
    - Incident details with priority and affected tenants
    """
    if not detector_instance:
        raise HTTPException(
            status_code=503,
            detail="Detector unavailable - set PROMETHEUS_ENABLED=true"
        )

    try:
        # Scan for failing tenants
        failing_tenants = detector_instance.detect_blast_radius()

        if not failing_tenants:
            raise HTTPException(
                status_code=404,
                detail="No failing tenants detected"
            )

        # Create incident
        incident = create_incident(failing_tenants, detector_instance)
        incidents.append(incident)

        # Send notifications in background
        notification_config = config.get_notification_config()
        background_tasks.add_task(
            send_notifications,
            incident,
            notification_config.get("pagerduty_enabled", False),
            notification_config.get("slack_enabled", False)
        )

        return IncidentResponse(
            incident_id=incident.incident_id,
            priority=incident.priority.value,
            tenant_ids=incident.tenant_ids,
            created_at=incident.created_at.isoformat(),
            resolved_at=incident.resolved_at.isoformat() if incident.resolved_at else None,
            affected_tier=incident.affected_tier.value if incident.affected_tier else None,
            cost_impact_inr=incident.cost_impact_inr
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Incident creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/incidents", response_model=List[IncidentResponse])
def list_incidents():
    """
    List all incidents.

    **Returns:**
    - List of all incident records
    """
    return [
        IncidentResponse(
            incident_id=inc.incident_id,
            priority=inc.priority.value,
            tenant_ids=inc.tenant_ids,
            created_at=inc.created_at.isoformat(),
            resolved_at=inc.resolved_at.isoformat() if inc.resolved_at else None,
            affected_tier=inc.affected_tier.value if inc.affected_tier else None,
            cost_impact_inr=inc.cost_impact_inr
        )
        for inc in incidents
    ]


@app.get("/incidents/{incident_id}", response_model=IncidentResponse)
def get_incident(incident_id: str):
    """
    Get details of a specific incident.

    **Args:**
    - **incident_id**: Incident identifier

    **Returns:**
    - Incident details
    """
    incident = next((inc for inc in incidents if inc.incident_id == incident_id), None)

    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    return IncidentResponse(
        incident_id=incident.incident_id,
        priority=incident.priority.value,
        tenant_ids=incident.tenant_ids,
        created_at=incident.created_at.isoformat(),
        resolved_at=incident.resolved_at.isoformat() if incident.resolved_at else None,
        affected_tier=incident.affected_tier.value if incident.affected_tier else None,
        cost_impact_inr=incident.cost_impact_inr
    )


@app.post("/incidents/{incident_id}/resolve")
def resolve_incident(incident_id: str, root_cause: Optional[str] = None):
    """
    Mark incident as resolved.

    **Args:**
    - **incident_id**: Incident identifier
    - **root_cause**: Optional root cause description

    **Returns:**
    - Updated incident details
    """
    incident = next((inc for inc in incidents if inc.incident_id == incident_id), None)

    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    incident.resolved_at = datetime.now()
    if root_cause:
        incident.root_cause = root_cause

    logger.info(f"Incident {incident_id} resolved")

    return {
        "status": "resolved",
        "incident_id": incident_id,
        "resolved_at": incident.resolved_at.isoformat(),
        "duration_minutes": (incident.resolved_at - incident.created_at).total_seconds() / 60
    }


@app.get("/incidents/{incident_id}/postmortem", response_model=PostmortemResponse)
def get_postmortem(incident_id: str):
    """
    Generate blameless postmortem template for incident.

    **Args:**
    - **incident_id**: Incident identifier

    **Returns:**
    - Markdown-formatted postmortem template
    """
    incident = next((inc for inc in incidents if inc.incident_id == incident_id), None)

    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    postmortem = generate_postmortem_template(incident)

    return PostmortemResponse(
        incident_id=incident_id,
        postmortem=postmortem
    )


@app.get("/circuit-breakers", response_model=Dict[str, Dict[str, Any]])
def get_circuit_breaker_status():
    """
    Get status of all circuit breakers.

    **Returns:**
    - Dict mapping tenant_id to breaker status
    """
    if not detector_instance:
        raise HTTPException(
            status_code=503,
            detail="Detector unavailable - set PROMETHEUS_ENABLED=true"
        )

    return detector_instance.get_circuit_breaker_status()
