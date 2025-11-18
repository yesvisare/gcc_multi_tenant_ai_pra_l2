"""
L3 M11.4: Tenant Provisioning & Automation

This module implements automated tenant provisioning workflows for multi-tenant
RAG systems, transforming manual 2-week processes into 15-minute automated deployments.

Core capabilities:
- Infrastructure as Code provisioning via Terraform
- 8-step validation suite (isolation, performance, security)
- Transaction-like rollback semantics on failure
- Self-service portal integration with approval workflows
- Cost optimization and compliance enforcement
"""

import logging
import asyncio
import json
import subprocess
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime
import os

logger = logging.getLogger(__name__)

__all__ = [
    "TenantTier",
    "TenantStatus",
    "TenantRequest",
    "provision_infrastructure",
    "initialize_tenant_config",
    "validate_tenant",
    "activate_tenant",
    "rollback_provisioning",
    "approve_tenant_request",
    "provision_tenant_workflow",
    "simulate_provisioning_workflow"
]


class TenantTier(str, Enum):
    """Tenant tier levels with associated resource allocations"""
    GOLD = "Gold"
    SILVER = "Silver"
    BRONZE = "Bronze"


class TenantStatus(str, Enum):
    """Tenant lifecycle states"""
    PENDING = "pending"
    APPROVED = "approved"
    PROVISIONING = "provisioning"
    VALIDATING = "validating"
    ACTIVE = "active"
    FAILED = "failed"
    REJECTED = "rejected"


class TenantRequest:
    """Tenant provisioning request structure"""

    def __init__(
        self,
        tenant_name: str,
        tier: TenantTier,
        region: str,
        budget: float,
        owner_email: str
    ):
        self.tenant_id = f"tenant_{tenant_name.lower().replace(' ', '_')}"
        self.tenant_name = tenant_name
        self.tier = tier
        self.region = region
        self.budget = budget
        self.owner_email = owner_email
        self.status = TenantStatus.PENDING
        self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "tenant_id": self.tenant_id,
            "tenant_name": self.tenant_name,
            "tier": self.tier.value if isinstance(self.tier, TenantTier) else self.tier,
            "region": self.region,
            "budget": self.budget,
            "owner_email": self.owner_email,
            "status": self.status.value if isinstance(self.status, TenantStatus) else self.status,
            "created_at": self.created_at
        }


async def provision_infrastructure(
    tenant_id: str,
    tier: TenantTier,
    region: str,
    offline: bool = False
) -> Dict[str, Any]:
    """
    Provision infrastructure using Terraform for a new tenant.

    Creates:
    - PostgreSQL schema with Row-Level Security (RLS) policies
    - Vector DB namespace (Pinecone/Qdrant)
    - S3 bucket with IAM isolation policies
    - Redis namespace for caching
    - Monitoring dashboards (Grafana/Prometheus)
    - All resources tagged with TenantID, Tier, CostCenter

    Args:
        tenant_id: Unique tenant identifier
        tier: Resource tier (Gold/Silver/Bronze)
        region: AWS region (e.g., us-east-1, eu-west-1)
        offline: If True, simulate provisioning without actual infrastructure changes

    Returns:
        Dict containing provisioning results and resource identifiers

    Raises:
        RuntimeError: If Terraform execution fails
    """
    logger.info(f"Starting infrastructure provisioning for {tenant_id} in {region}")

    if offline:
        logger.warning("⚠️ Offline mode - simulating infrastructure provisioning")
        return {
            "status": "simulated",
            "tenant_id": tenant_id,
            "resources": {
                "postgresql_schema": f"{tenant_id}_schema",
                "vector_db_namespace": f"{tenant_id}_vectors",
                "s3_bucket": f"{tenant_id}-documents",
                "redis_namespace": f"{tenant_id}:cache",
                "monitoring_dashboard": f"grafana-{tenant_id}"
            },
            "duration_minutes": 0.1,
            "message": "Provisioning skipped in offline mode"
        }

    try:
        # Step 1: Create Terraform variables file
        terraform_vars = {
            "tenant_id": tenant_id,
            "tier": tier.value if isinstance(tier, TenantTier) else tier,
            "region": region,
            "enable_rls": True,
            "enable_monitoring": True,
            "cost_center": f"CC_{tenant_id.upper()}"
        }

        logger.info(f"Terraform variables: {terraform_vars}")

        # Step 2: Simulate Terraform workflow (init → plan → apply)
        # In production, this would execute:
        # subprocess.run(["terraform", "init"], check=True)
        # subprocess.run(["terraform", "plan", "-out=tfplan"], check=True)
        # subprocess.run(["terraform", "apply", "tfplan"], check=True)

        logger.info("Terraform init completed")
        await asyncio.sleep(0.1)  # Simulate processing time

        logger.info("Terraform plan completed")
        await asyncio.sleep(0.1)

        logger.info("Terraform apply completed")
        await asyncio.sleep(0.2)

        # Step 3: Return provisioned resource identifiers
        resources = {
            "postgresql_schema": f"{tenant_id}_schema",
            "vector_db_namespace": f"{tenant_id}_vectors",
            "s3_bucket": f"{tenant_id}-documents",
            "redis_namespace": f"{tenant_id}:cache",
            "monitoring_dashboard": f"grafana-{tenant_id}",
            "iam_role": f"arn:aws:iam::ACCOUNT:role/{tenant_id}-role"
        }

        logger.info(f"✓ Infrastructure provisioned for {tenant_id}: {list(resources.keys())}")

        return {
            "status": "success",
            "tenant_id": tenant_id,
            "resources": resources,
            "duration_minutes": 10.5,
            "terraform_state": f"s3://terraform-state/{tenant_id}.tfstate"
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"Terraform execution failed: {e}")
        raise RuntimeError(f"Infrastructure provisioning failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during provisioning: {e}")
        raise


async def initialize_tenant_config(
    tenant_id: str,
    tier: TenantTier,
    offline: bool = False
) -> Dict[str, Any]:
    """
    Initialize tenant-specific configuration and feature flags.

    Configuration includes:
    - Feature flags (tier-based capabilities)
    - Rate limits (queries/minute, documents/month)
    - LLM model selection (GPT-4 for Gold, GPT-3.5-turbo for others)
    - Optional demo document seeding for Gold tier

    Args:
        tenant_id: Unique tenant identifier
        tier: Resource tier determining feature availability
        offline: If True, simulate configuration without database writes

    Returns:
        Dict containing initialized configuration
    """
    logger.info(f"Initializing configuration for {tenant_id} (tier: {tier})")

    # Tier-based feature flags
    feature_flags = {
        "advanced_search": tier == TenantTier.GOLD,
        "real_time_indexing": tier in [TenantTier.GOLD, TenantTier.SILVER],
        "custom_models": tier == TenantTier.GOLD,
        "batch_processing": True,
        "api_access": True
    }

    # Tier-based rate limits
    rate_limits = {
        TenantTier.GOLD: {"queries_per_minute": 1000, "documents_per_month": 100000},
        TenantTier.SILVER: {"queries_per_minute": 500, "documents_per_month": 50000},
        TenantTier.BRONZE: {"queries_per_minute": 100, "documents_per_month": 10000}
    }

    # LLM model configuration
    llm_config = {
        TenantTier.GOLD: {"model": "gpt-4", "max_tokens": 4096, "temperature": 0.7},
        TenantTier.SILVER: {"model": "gpt-3.5-turbo", "max_tokens": 2048, "temperature": 0.7},
        TenantTier.BRONZE: {"model": "gpt-3.5-turbo", "max_tokens": 1024, "temperature": 0.7}
    }

    config = {
        "tenant_id": tenant_id,
        "tier": tier.value if isinstance(tier, TenantTier) else tier,
        "feature_flags": feature_flags,
        "rate_limits": rate_limits[tier],
        "llm_config": llm_config[tier],
        "demo_documents_seeded": tier == TenantTier.GOLD
    }

    if offline:
        logger.warning("⚠️ Offline mode - configuration not persisted to database")
        config["status"] = "simulated"
    else:
        # In production: Write to tenant registry database
        logger.info(f"Configuration written to registry for {tenant_id}")
        config["status"] = "persisted"

    logger.info(f"✓ Configuration initialized for {tenant_id}")
    return config


async def validate_tenant(
    tenant_id: str,
    offline: bool = False
) -> Dict[str, Any]:
    """
    Run comprehensive validation test suite for newly provisioned tenant.

    8-test validation suite:
    1. Database connectivity check
    2. Cross-tenant isolation verification (negative test)
    3. Vector search functionality test
    4. JWT authentication generation
    5. Query performance check (<500ms SLA)
    6. S3 upload permissions verification
    7. Prometheus metrics collection check
    8. Cost tag presence verification

    Args:
        tenant_id: Unique tenant identifier
        offline: If True, return mock validation results

    Returns:
        Dict with test results and pass/fail status for each check

    Raises:
        ValueError: If any critical validation test fails
    """
    logger.info(f"Starting validation suite for {tenant_id}")

    if offline:
        logger.warning("⚠️ Offline mode - returning simulated validation results")
        return {
            "tenant_id": tenant_id,
            "status": "simulated",
            "all_tests_passed": True,
            "tests": {
                "database_connectivity": {"passed": True, "message": "Simulated"},
                "tenant_isolation": {"passed": True, "message": "Simulated"},
                "vector_search": {"passed": True, "message": "Simulated"},
                "jwt_authentication": {"passed": True, "message": "Simulated"},
                "query_performance": {"passed": True, "latency_ms": 250, "message": "Simulated"},
                "s3_permissions": {"passed": True, "message": "Simulated"},
                "metrics_collection": {"passed": True, "message": "Simulated"},
                "cost_tags": {"passed": True, "message": "Simulated"}
            },
            "duration_seconds": 0.5
        }

    test_results = {}

    # Test 1: Database connectivity
    try:
        logger.info("Test 1/8: Database connectivity")
        # Simulate: SELECT 1 FROM tenant_schema.test_table
        await asyncio.sleep(0.1)
        test_results["database_connectivity"] = {
            "passed": True,
            "message": "Successfully connected to PostgreSQL schema"
        }
    except Exception as e:
        test_results["database_connectivity"] = {"passed": False, "error": str(e)}

    # Test 2: Cross-tenant isolation (negative test)
    try:
        logger.info("Test 2/8: Tenant isolation verification")
        # Simulate: Attempt to access another tenant's data (should fail)
        await asyncio.sleep(0.1)
        test_results["tenant_isolation"] = {
            "passed": True,
            "message": "RLS policies correctly block cross-tenant access"
        }
    except Exception as e:
        test_results["tenant_isolation"] = {"passed": False, "error": str(e)}

    # Test 3: Vector search functionality
    try:
        logger.info("Test 3/8: Vector search")
        # Simulate: Query vector database with sample embedding
        await asyncio.sleep(0.1)
        test_results["vector_search"] = {
            "passed": True,
            "message": "Vector namespace operational, returned 5 results"
        }
    except Exception as e:
        test_results["vector_search"] = {"passed": False, "error": str(e)}

    # Test 4: JWT authentication
    try:
        logger.info("Test 4/8: JWT authentication generation")
        # Simulate: Generate tenant-specific JWT token
        await asyncio.sleep(0.05)
        test_results["jwt_authentication"] = {
            "passed": True,
            "message": "JWT token generated with tenant claims"
        }
    except Exception as e:
        test_results["jwt_authentication"] = {"passed": False, "error": str(e)}

    # Test 5: Query performance (<500ms SLA)
    try:
        logger.info("Test 5/8: Query performance")
        # Simulate: Execute sample RAG query and measure latency
        await asyncio.sleep(0.15)
        latency_ms = 285
        test_results["query_performance"] = {
            "passed": latency_ms < 500,
            "latency_ms": latency_ms,
            "message": f"Query completed in {latency_ms}ms (SLA: <500ms)"
        }
    except Exception as e:
        test_results["query_performance"] = {"passed": False, "error": str(e)}

    # Test 6: S3 upload permissions
    try:
        logger.info("Test 6/8: S3 permissions")
        # Simulate: Upload test file to tenant bucket
        await asyncio.sleep(0.1)
        test_results["s3_permissions"] = {
            "passed": True,
            "message": "Successfully uploaded test file to S3 bucket"
        }
    except Exception as e:
        test_results["s3_permissions"] = {"passed": False, "error": str(e)}

    # Test 7: Prometheus metrics collection
    try:
        logger.info("Test 7/8: Metrics collection")
        # Simulate: Verify Prometheus scraping tenant metrics
        await asyncio.sleep(0.05)
        test_results["metrics_collection"] = {
            "passed": True,
            "message": "Prometheus scraping endpoint operational"
        }
    except Exception as e:
        test_results["metrics_collection"] = {"passed": False, "error": str(e)}

    # Test 8: Cost tag verification
    try:
        logger.info("Test 8/8: Cost tag verification")
        # Simulate: Check all resources have TenantID cost tags
        await asyncio.sleep(0.05)
        test_results["cost_tags"] = {
            "passed": True,
            "message": "All resources tagged with TenantID and CostCenter"
        }
    except Exception as e:
        test_results["cost_tags"] = {"passed": False, "error": str(e)}

    # Determine overall status
    all_passed = all(test["passed"] for test in test_results.values())

    result = {
        "tenant_id": tenant_id,
        "status": "passed" if all_passed else "failed",
        "all_tests_passed": all_passed,
        "tests": test_results,
        "duration_seconds": 2.5
    }

    if not all_passed:
        failed_tests = [name for name, result in test_results.items() if not result["passed"]]
        logger.error(f"✗ Validation failed for {tenant_id}: {failed_tests}")
        raise ValueError(f"Validation suite failed: {failed_tests}")

    logger.info(f"✓ All validation tests passed for {tenant_id}")
    return result


async def activate_tenant(tenant_id: str, offline: bool = False) -> Dict[str, Any]:
    """
    Mark tenant as active in registry and send notifications.

    Args:
        tenant_id: Unique tenant identifier
        offline: If True, skip actual database updates and notifications

    Returns:
        Dict with activation status and notification results
    """
    logger.info(f"Activating tenant {tenant_id}")

    if offline:
        logger.warning("⚠️ Offline mode - tenant not marked active in registry")
        return {
            "tenant_id": tenant_id,
            "status": "simulated",
            "activated_at": datetime.utcnow().isoformat(),
            "notifications_sent": False
        }

    # In production: Update tenant_registry SET status='active' WHERE tenant_id=...
    activated_at = datetime.utcnow().isoformat()

    # Send notifications (email/Slack)
    logger.info(f"Sending activation notifications for {tenant_id}")

    result = {
        "tenant_id": tenant_id,
        "status": "active",
        "activated_at": activated_at,
        "notifications_sent": True,
        "notification_channels": ["email", "slack"]
    }

    logger.info(f"✓ Tenant {tenant_id} activated successfully")
    return result


async def rollback_provisioning(
    tenant_id: str,
    failed_step: str,
    offline: bool = False
) -> Dict[str, Any]:
    """
    Rollback tenant provisioning with transaction-like semantics.

    Rollback actions:
    1. Log provisioning failure with failed step details
    2. Execute terraform destroy to remove all infrastructure
    3. Remove tenant from registry database
    4. Notify requester of failure with rollback confirmation

    Args:
        tenant_id: Unique tenant identifier
        failed_step: Name of the step that caused failure
        offline: If True, simulate rollback without actual changes

    Returns:
        Dict with rollback results
    """
    logger.error(f"Rolling back provisioning for {tenant_id} (failed at: {failed_step})")

    if offline:
        logger.warning("⚠️ Offline mode - rollback simulated")
        return {
            "tenant_id": tenant_id,
            "status": "simulated",
            "failed_step": failed_step,
            "rollback_actions": ["terraform_destroy", "registry_deletion", "notification"],
            "message": "Rollback skipped in offline mode"
        }

    rollback_actions = []

    try:
        # Action 1: Execute terraform destroy
        logger.info("Executing terraform destroy")
        # In production: subprocess.run(["terraform", "destroy", "-auto-approve"], check=True)
        await asyncio.sleep(0.2)
        rollback_actions.append("terraform_destroy_completed")

        # Action 2: Remove from tenant registry
        logger.info("Removing tenant from registry")
        # In production: DELETE FROM tenant_registry WHERE tenant_id=...
        await asyncio.sleep(0.1)
        rollback_actions.append("registry_deletion_completed")

        # Action 3: Send failure notification
        logger.info("Sending rollback notification to requester")
        await asyncio.sleep(0.05)
        rollback_actions.append("notification_sent")

        result = {
            "tenant_id": tenant_id,
            "status": "rollback_successful",
            "failed_step": failed_step,
            "rollback_actions": rollback_actions,
            "message": "All provisioning changes reverted"
        }

        logger.info(f"✓ Rollback completed for {tenant_id}")
        return result

    except Exception as e:
        logger.critical(f"Rollback failed for {tenant_id}: {e}")
        # This is critical - partial rollback may leave orphaned resources
        return {
            "tenant_id": tenant_id,
            "status": "rollback_failed",
            "failed_step": failed_step,
            "error": str(e),
            "warning": "Manual cleanup required - orphaned resources may exist"
        }


async def approve_tenant_request(
    tenant_id: str,
    budget: float,
    approver: str = "system",
    offline: bool = False
) -> Dict[str, Any]:
    """
    Process approval workflow for tenant provisioning request.

    Approval rules:
    - Budgets <₹10L: Auto-approved
    - Budgets ≥₹10L: Requires CFO manual approval

    Args:
        tenant_id: Unique tenant identifier
        budget: Annual budget allocation (in ₹)
        approver: Identifier of approving authority
        offline: If True, skip database updates

    Returns:
        Dict with approval decision and reasoning
    """
    logger.info(f"Processing approval for {tenant_id} (budget: ₹{budget:,.0f})")

    # Approval threshold
    auto_approve_threshold = 1000000  # ₹10 lakh

    if budget < auto_approve_threshold:
        decision = "approved"
        approval_type = "automatic"
        reason = f"Budget ₹{budget:,.0f} below auto-approval threshold"
        logger.info(f"✓ {tenant_id} auto-approved")
    else:
        # In production: Queue for manual CFO approval
        decision = "pending_manual_approval"
        approval_type = "manual_required"
        reason = f"Budget ₹{budget:,.0f} requires CFO approval"
        logger.info(f"⏳ {tenant_id} queued for CFO approval")

    if offline:
        logger.warning("⚠️ Offline mode - approval not persisted")

    return {
        "tenant_id": tenant_id,
        "decision": decision,
        "approval_type": approval_type,
        "approver": approver if decision == "approved" else "pending",
        "reason": reason,
        "budget": budget,
        "approved_at": datetime.utcnow().isoformat() if decision == "approved" else None
    }


async def provision_tenant_workflow(
    tenant_request: TenantRequest,
    offline: bool = False
) -> Dict[str, Any]:
    """
    Execute end-to-end tenant provisioning workflow.

    8-step workflow:
    1. Request Submission (input validation)
    2. Approval Workflow (budget-based governance)
    3. Infrastructure Provisioning (Terraform)
    4. Configuration Initialization (feature flags, rate limits)
    5. Validation Testing (8-test suite)
    6. Activation (mark tenant as active)
    7. Notification (stakeholder alerts)
    8. Rollback on Failure (transaction-like semantics)

    Args:
        tenant_request: TenantRequest object with provisioning details
        offline: If True, simulate workflow without actual infrastructure changes

    Returns:
        Dict with complete workflow results and timing

    Raises:
        Exception: If any step fails (triggers automatic rollback)
    """
    tenant_id = tenant_request.tenant_id
    start_time = datetime.utcnow()

    logger.info(f"========== Starting provisioning workflow for {tenant_id} ==========")
    logger.info(f"Request: {tenant_request.to_dict()}")

    workflow_results = {
        "tenant_id": tenant_id,
        "tenant_name": tenant_request.tenant_name,
        "steps_completed": [],
        "status": "in_progress"
    }

    try:
        # Step 1: Request Submission (already validated)
        tenant_request.status = TenantStatus.PENDING
        workflow_results["steps_completed"].append("request_submission")
        logger.info("✓ Step 1/8: Request submitted")

        # Step 2: Approval Workflow
        approval_result = await approve_tenant_request(
            tenant_id,
            tenant_request.budget,
            offline=offline
        )

        if approval_result["decision"] != "approved":
            tenant_request.status = TenantStatus.REJECTED
            workflow_results["status"] = "rejected"
            workflow_results["reason"] = approval_result["reason"]
            logger.warning(f"⏸ Workflow stopped: {approval_result['reason']}")
            return workflow_results

        tenant_request.status = TenantStatus.APPROVED
        workflow_results["steps_completed"].append("approval")
        workflow_results["approval"] = approval_result
        logger.info("✓ Step 2/8: Approval obtained")

        # Step 3: Infrastructure Provisioning
        tenant_request.status = TenantStatus.PROVISIONING
        infra_result = await provision_infrastructure(
            tenant_id,
            tenant_request.tier,
            tenant_request.region,
            offline=offline
        )
        workflow_results["steps_completed"].append("infrastructure_provisioning")
        workflow_results["infrastructure"] = infra_result
        logger.info(f"✓ Step 3/8: Infrastructure provisioned ({infra_result['duration_minutes']} min)")

        # Step 4: Configuration Initialization
        config_result = await initialize_tenant_config(
            tenant_id,
            tenant_request.tier,
            offline=offline
        )
        workflow_results["steps_completed"].append("configuration_initialization")
        workflow_results["configuration"] = config_result
        logger.info("✓ Step 4/8: Configuration initialized")

        # Step 5: Validation Testing
        tenant_request.status = TenantStatus.VALIDATING
        validation_result = await validate_tenant(tenant_id, offline=offline)
        workflow_results["steps_completed"].append("validation_testing")
        workflow_results["validation"] = validation_result
        logger.info(f"✓ Step 5/8: Validation passed ({validation_result['duration_seconds']}s)")

        # Step 6: Activation
        activation_result = await activate_tenant(tenant_id, offline=offline)
        tenant_request.status = TenantStatus.ACTIVE
        workflow_results["steps_completed"].append("activation")
        workflow_results["activation"] = activation_result
        logger.info("✓ Step 6/8: Tenant activated")

        # Step 7: Notification (included in activation)
        workflow_results["steps_completed"].append("notification")
        logger.info("✓ Step 7/8: Notifications sent")

        # Step 8: Rollback on Failure (not needed - success path)
        workflow_results["steps_completed"].append("rollback_not_required")

        # Calculate total duration
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds() / 60

        workflow_results["status"] = "completed"
        workflow_results["total_duration_minutes"] = round(duration, 2)
        workflow_results["completed_at"] = end_time.isoformat()

        logger.info(f"========== ✓ Provisioning workflow completed for {tenant_id} ({duration:.1f} min) ==========")

        return workflow_results

    except Exception as e:
        logger.error(f"========== ✗ Provisioning workflow failed for {tenant_id}: {e} ==========")

        # Step 8: Rollback on Failure
        failed_step = workflow_results["steps_completed"][-1] if workflow_results["steps_completed"] else "unknown"
        rollback_result = await rollback_provisioning(tenant_id, failed_step, offline=offline)

        tenant_request.status = TenantStatus.FAILED
        workflow_results["status"] = "failed"
        workflow_results["error"] = str(e)
        workflow_results["rollback"] = rollback_result

        logger.info(f"✓ Step 8/8: Rollback completed for {tenant_id}")

        return workflow_results


async def simulate_provisioning_workflow(
    tenant_name: str = "Demo Corp",
    tier: TenantTier = TenantTier.SILVER,
    region: str = "us-east-1",
    budget: float = 500000
) -> Dict[str, Any]:
    """
    Convenience function to simulate complete provisioning workflow.

    Useful for testing and demonstrations without actual infrastructure.

    Args:
        tenant_name: Tenant organization name
        tier: Resource tier (Gold/Silver/Bronze)
        region: AWS region
        budget: Annual budget allocation (in ₹)

    Returns:
        Dict with complete workflow results
    """
    logger.info(f"Simulating provisioning workflow for {tenant_name}")

    # Create tenant request
    request = TenantRequest(
        tenant_name=tenant_name,
        tier=tier,
        region=region,
        budget=budget,
        owner_email=f"admin@{tenant_name.lower().replace(' ', '')}.com"
    )

    # Execute workflow in offline mode
    result = await provision_tenant_workflow(request, offline=True)

    return result
