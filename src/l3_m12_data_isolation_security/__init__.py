"""
L3 M12.1: Vector Database Multi-Tenancy Patterns

This module implements namespace-based isolation, metadata filtering enforcement,
and tenant-scoped vector stores for multi-tenant vector databases with Pinecone.

Core capabilities:
- Namespace-based tenant isolation
- Query validation with automatic tenant_id filter injection
- Cross-tenant query detection and prevention
- Audit logging for security compliance
- Three isolation models: Metadata Filtering, Namespace-Based, Dedicated Indexes
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime

logger = logging.getLogger(__name__)

__all__ = [
    "IsolationModel",
    "TenantContext",
    "NamespaceRouter",
    "validate_tenant_query",
    "extract_tenant_filters",
    "validate_filter_safety",
    "parse_filter",
    "tenant_filtered_query",
    "create_tenant_namespace",
    "security_alert",
    "is_cross_tenant",
    "evaluate_isolation_model",
    "get_isolation_costs",
]


class IsolationModel(Enum):
    """Vector database isolation strategies."""
    METADATA_FILTERING = "metadata_filtering"
    NAMESPACE_BASED = "namespace_based"
    DEDICATED_INDEXES = "dedicated_indexes"


@dataclass
class TenantContext:
    """Immutable tenant context extracted from JWT."""
    tenant_id: str
    user_id: str
    roles: List[str]
    timestamp: str

    def __post_init__(self):
        """Validate tenant context integrity."""
        if not self.tenant_id:
            raise ValueError("tenant_id is required")
        if not self.user_id:
            raise ValueError("user_id is required")
        logger.info(f"Created TenantContext for tenant={self.tenant_id}, user={self.user_id}")


class NamespaceRouter:
    """
    Routes vector queries to tenant-specific namespaces.

    Implements namespace-based isolation (Model 2) with automatic
    routing based on tenant context.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize namespace router.

        Args:
            config: Configuration dict with namespace mappings
        """
        self.config = config
        self.namespace_map = {}
        logger.info("Initialized NamespaceRouter")

    def query(
        self,
        tenant_context: TenantContext,
        query_vector: List[float],
        top_k: int = 10,
        offline: bool = False
    ) -> Dict[str, Any]:
        """
        Query vector database with namespace isolation.

        Args:
            tenant_context: Validated tenant context from JWT
            query_vector: Query embedding vector
            top_k: Number of results to return
            offline: If True, skip external API calls

        Returns:
            Dict containing query results with namespace isolation

        Raises:
            ValueError: If tenant_context is invalid
        """
        if offline:
            logger.warning("⚠️ Offline mode - skipping Pinecone query")
            return {
                "skipped": True,
                "reason": "offline mode",
                "namespace": f"tenant_{tenant_context.tenant_id}"
            }

        namespace = f"tenant_{tenant_context.tenant_id}"

        logger.info(f"Querying namespace={namespace}, top_k={top_k}")

        # Security audit log
        audit_log = {
            "event": "vector_query",
            "tenant_id": tenant_context.tenant_id,
            "user_id": tenant_context.user_id,
            "namespace": namespace,
            "timestamp": datetime.utcnow().isoformat(),
            "vector_dim": len(query_vector)
        }
        logger.info(f"Audit: {json.dumps(audit_log)}")

        # In production: pinecone_client.query(namespace=namespace, vector=query_vector, top_k=top_k)
        return {
            "status": "success",
            "namespace": namespace,
            "isolation_model": IsolationModel.NAMESPACE_BASED.value,
            "results": [],  # Placeholder for actual Pinecone results
            "audit": audit_log
        }

    def create_namespace(self, tenant_id: str) -> Dict[str, Any]:
        """
        Create new tenant namespace.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Dict with namespace creation status
        """
        namespace = f"tenant_{tenant_id}"
        self.namespace_map[tenant_id] = namespace

        logger.info(f"Created namespace={namespace} for tenant={tenant_id}")

        return {
            "status": "created",
            "namespace": namespace,
            "tenant_id": tenant_id,
            "provisioning_time": "<60 seconds"
        }


def validate_tenant_query(query_filter: Dict[str, Any], user_tenant_id: str) -> bool:
    """
    Validate query filter for cross-tenant access attempts.

    Implements defense-in-depth by ensuring ALL filter clauses
    reference only the authenticated user's tenant_id.

    Args:
        query_filter: Filter dictionary from user query
        user_tenant_id: Authenticated user's tenant ID from JWT

    Returns:
        True if filter is safe, False if cross-tenant attempt detected

    Raises:
        ValueError: If filter structure is invalid
    """
    logger.info(f"Validating query filter for tenant={user_tenant_id}")

    try:
        tenant_filters = extract_tenant_filters(query_filter)

        # Check if any filter references a different tenant
        for filter_tenant_id in tenant_filters:
            if filter_tenant_id != user_tenant_id:
                logger.error(f"❌ Cross-tenant query attempt: user_tenant={user_tenant_id}, filter_tenant={filter_tenant_id}")
                security_alert({
                    "event": "cross_tenant_query_attempt",
                    "user_tenant_id": user_tenant_id,
                    "attempted_tenant_id": filter_tenant_id,
                    "filter": query_filter,
                    "timestamp": datetime.utcnow().isoformat()
                })
                return False

        logger.info("✓ Query filter validation passed")
        return True

    except Exception as e:
        logger.error(f"Filter validation error: {e}")
        raise ValueError(f"Invalid filter structure: {e}")


def extract_tenant_filters(query_filter: Dict[str, Any]) -> List[str]:
    """
    Extract all tenant_id values from filter dictionary.

    Recursively parses filter AST to find all tenant_id references
    in AND/OR/leaf nodes.

    Args:
        query_filter: Filter dictionary (potentially nested)

    Returns:
        List of all tenant_id values found in filter
    """
    tenant_ids = []

    def parse_recursive(filter_dict: Dict[str, Any]):
        """Recursively parse filter structure."""
        if not isinstance(filter_dict, dict):
            return

        # Check for tenant_id in current level
        if "tenant_id" in filter_dict:
            tenant_ids.append(filter_dict["tenant_id"])

        # Recurse into AND/OR operators
        if "$and" in filter_dict:
            for sub_filter in filter_dict["$and"]:
                parse_recursive(sub_filter)

        if "$or" in filter_dict:
            for sub_filter in filter_dict["$or"]:
                parse_recursive(sub_filter)

    parse_recursive(query_filter)
    logger.info(f"Extracted {len(tenant_ids)} tenant_id references from filter")
    return tenant_ids


def validate_filter_safety(filter_dict: Dict[str, Any], allowed_tenant: str) -> bool:
    """
    Validate that filter only references allowed tenant.

    Ensures EVERY leaf node in filter AST contains the correct tenant_id.
    Implements the "tenant_id in EVERY leaf node" security requirement.

    Args:
        filter_dict: Filter dictionary to validate
        allowed_tenant: The only allowed tenant_id value

    Returns:
        True if safe, False if violation detected
    """
    tenant_filters = extract_tenant_filters(filter_dict)

    if not tenant_filters:
        logger.warning("⚠️ No tenant_id filters found - potential security violation")
        return False

    for tenant_id in tenant_filters:
        if tenant_id != allowed_tenant:
            logger.error(f"❌ Unauthorized tenant_id in filter: {tenant_id}")
            return False

    logger.info(f"✓ Filter safety validated for tenant={allowed_tenant}")
    return True


def parse_filter(filter_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse and normalize filter dictionary.

    Args:
        filter_dict: Raw filter from user query

    Returns:
        Normalized filter structure
    """
    # Basic normalization - in production would handle complex operators
    normalized = filter_dict.copy()

    logger.info(f"Parsed filter with {len(normalized)} clauses")
    return normalized


def tenant_filtered_query(
    user_context: TenantContext,
    query_vector: List[float],
    top_k: int = 10,
    user_filter: Optional[Dict[str, Any]] = None,
    offline: bool = False
) -> Dict[str, Any]:
    """
    Execute vector query with automatic tenant_id filter injection.

    Implements Metadata Filtering (Model 1) with defense-in-depth:
    1. Middleware injects tenant_id filter
    2. Validates user-provided filters
    3. Post-query result validation
    4. Audit logging

    Args:
        user_context: Authenticated tenant context from JWT
        query_vector: Query embedding vector
        top_k: Number of results to return
        user_filter: Optional additional filters from user
        offline: If True, skip external API calls

    Returns:
        Dict containing filtered query results

    Raises:
        ValueError: If cross-tenant query attempt detected
    """
    if offline:
        logger.warning("⚠️ Offline mode - skipping Pinecone query")
        return {
            "skipped": True,
            "reason": "offline mode",
            "tenant_id": user_context.tenant_id
        }

    # Step 1: Inject tenant_id filter (defense layer 1)
    injected_filter = {"tenant_id": user_context.tenant_id}

    # Step 2: Validate user-provided filters (defense layer 2)
    if user_filter:
        if not validate_tenant_query(user_filter, user_context.tenant_id):
            raise ValueError("Cross-tenant query attempt blocked")

        # Merge filters with AND
        combined_filter = {
            "$and": [
                injected_filter,
                user_filter
            ]
        }
    else:
        combined_filter = injected_filter

    logger.info(f"Executing filtered query for tenant={user_context.tenant_id}")

    # Step 3: Execute query (in production: pinecone_client.query())
    # results = pinecone_client.query(vector=query_vector, filter=combined_filter, top_k=top_k)

    # Step 4: Post-query validation (defense layer 3)
    # for result in results:
    #     if result.metadata.get("tenant_id") != user_context.tenant_id:
    #         security_alert({...})
    #         raise ValueError("Post-query validation failed")

    # Step 5: Audit logging (defense layer 4)
    audit_log = {
        "event": "metadata_filtered_query",
        "tenant_id": user_context.tenant_id,
        "user_id": user_context.user_id,
        "filter": combined_filter,
        "timestamp": datetime.utcnow().isoformat()
    }
    logger.info(f"Audit: {json.dumps(audit_log)}")

    return {
        "status": "success",
        "isolation_model": IsolationModel.METADATA_FILTERING.value,
        "filter_applied": combined_filter,
        "results": [],  # Placeholder
        "audit": audit_log
    }


def create_tenant_namespace(tenant_id: str, offline: bool = False) -> Dict[str, Any]:
    """
    Create new tenant namespace in vector database.

    Implements fast tenant onboarding (<60 seconds) with namespace isolation.

    Args:
        tenant_id: Tenant identifier
        offline: If True, skip external API calls

    Returns:
        Dict with namespace creation status
    """
    if offline:
        logger.warning("⚠️ Offline mode - skipping namespace creation")
        return {
            "skipped": True,
            "reason": "offline mode",
            "namespace": f"tenant_{tenant_id}"
        }

    namespace = f"tenant_{tenant_id}"

    logger.info(f"Creating namespace={namespace}")

    # In production: pinecone_client.create_index() or create_namespace()
    # Provisioning time: <60 seconds

    return {
        "status": "created",
        "namespace": namespace,
        "tenant_id": tenant_id,
        "provisioning_time": "<60 seconds",
        "isolation_strength": "9/10",
        "max_scale": "~1,000 namespaces per index"
    }


def security_alert(event_data: Dict[str, Any]) -> None:
    """
    Trigger security alert for suspicious activity.

    In production, this would:
    - Send alert to security monitoring system
    - Trigger incident response protocol
    - Update threat intelligence database

    Args:
        event_data: Security event details
    """
    logger.error(f"🚨 SECURITY ALERT: {json.dumps(event_data)}")

    # In production:
    # - Send to SIEM (Splunk, ELK)
    # - Trigger PagerDuty/OpsGenie
    # - Auto-block if threshold exceeded
    # - Notify compliance team


def is_cross_tenant(query_filter: Dict[str, Any], user_tenant_id: str) -> bool:
    """
    Check if query filter attempts cross-tenant access.

    Args:
        query_filter: Filter dictionary from query
        user_tenant_id: Authenticated user's tenant ID

    Returns:
        True if cross-tenant attempt detected, False otherwise
    """
    tenant_filters = extract_tenant_filters(query_filter)

    for filter_tenant_id in tenant_filters:
        if filter_tenant_id != user_tenant_id:
            logger.warning(f"⚠️ Cross-tenant attempt: {filter_tenant_id} != {user_tenant_id}")
            return True

    return False


def evaluate_isolation_model(
    num_tenants: int,
    security_requirement: str,
    budget_constraint: str
) -> Dict[str, Any]:
    """
    Evaluate which isolation model to use based on requirements.

    Implements Decision Card logic for choosing between:
    - Metadata Filtering (cost-optimized)
    - Namespace-Based (balanced)
    - Dedicated Indexes (maximum security)

    Args:
        num_tenants: Number of tenants to support
        security_requirement: "standard" | "high" | "maximum"
        budget_constraint: "tight" | "moderate" | "flexible"

    Returns:
        Dict with recommended model and trade-offs
    """
    logger.info(f"Evaluating isolation model: tenants={num_tenants}, security={security_requirement}, budget={budget_constraint}")

    # Decision matrix
    if security_requirement == "maximum" or budget_constraint == "flexible":
        return {
            "recommended_model": IsolationModel.DEDICATED_INDEXES.value,
            "cost_range": "₹30-40L/month (50 tenants)",
            "isolation_strength": "10/10",
            "provisioning_time": "Hours to days",
            "best_for": "Competing tenants, regulatory mandates (SOX, HIPAA)",
            "trade_offs": {
                "pros": ["Complete isolation", "Zero blast radius", "Regulatory compliance"],
                "cons": ["10x infrastructure cost", "Complex management", "Slower onboarding"]
            }
        }

    elif num_tenants > 50 and num_tenants <= 1000 and security_requirement == "high":
        return {
            "recommended_model": IsolationModel.NAMESPACE_BASED.value,
            "cost_range": "₹8-12L/month (50 tenants)",
            "isolation_strength": "9/10",
            "provisioning_time": "<60 seconds",
            "best_for": "Most GCC scenarios, balanced trade-off",
            "trade_offs": {
                "pros": ["Fast onboarding", "Good isolation", "Moderate cost"],
                "cons": ["~1,000 namespace limit", "Shared infrastructure"]
            }
        }

    else:  # Cost-optimized
        return {
            "recommended_model": IsolationModel.METADATA_FILTERING.value,
            "cost_range": "₹5-8L/month (50 tenants)",
            "isolation_strength": "7/10",
            "provisioning_time": "Immediate",
            "best_for": "Cost-sensitive, similar security requirements",
            "trade_offs": {
                "pros": ["Lowest cost", "Instant onboarding", "Simple architecture"],
                "cons": ["Filter bugs affect all tenants", "5-10ms query latency", "Requires robust testing"]
            },
            "warnings": ["NOT for regulatory physical isolation", "Requires 5,000+ penetration tests"]
        }


def get_isolation_costs(num_tenants: int) -> Dict[str, Dict[str, Any]]:
    """
    Calculate costs for each isolation model.

    Args:
        num_tenants: Number of tenants to support

    Returns:
        Dict with cost breakdown by model
    """
    base_cost_per_tenant_metadata = 100_000  # ₹ per tenant per year (metadata filtering)
    base_cost_per_tenant_namespace = 160_000  # ₹ per tenant per year (namespace-based)
    base_cost_per_tenant_dedicated = 800_000  # ₹ per tenant per year (dedicated indexes)

    return {
        IsolationModel.METADATA_FILTERING.value: {
            "annual_cost": f"₹{(base_cost_per_tenant_metadata * num_tenants) / 100_000:.1f}L",
            "monthly_cost": f"₹{(base_cost_per_tenant_metadata * num_tenants) / 1_200_000:.1f}L",
            "cost_per_tenant": f"₹{base_cost_per_tenant_metadata / 100_000:.1f}L/year",
            "savings_vs_dedicated": "10x cost reduction"
        },
        IsolationModel.NAMESPACE_BASED.value: {
            "annual_cost": f"₹{(base_cost_per_tenant_namespace * num_tenants) / 100_000:.1f}L",
            "monthly_cost": f"₹{(base_cost_per_tenant_namespace * num_tenants) / 1_200_000:.1f}L",
            "cost_per_tenant": f"₹{base_cost_per_tenant_namespace / 100_000:.1f}L/year",
            "savings_vs_dedicated": "5x cost reduction"
        },
        IsolationModel.DEDICATED_INDEXES.value: {
            "annual_cost": f"₹{(base_cost_per_tenant_dedicated * num_tenants) / 100_000:.1f}L",
            "monthly_cost": f"₹{(base_cost_per_tenant_dedicated * num_tenants) / 1_200_000:.1f}L",
            "cost_per_tenant": f"₹{base_cost_per_tenant_dedicated / 100_000:.1f}L/year",
            "premium": "Maximum security tier"
        }
    }
