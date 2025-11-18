"""
L3 M14.4: Platform Governance & Operating Model

This module implements a complete platform governance framework for multi-tenant
RAG systems in GCC environments. It provides tools for:

- Operating model selection (Centralized, Federated, Hybrid)
- Team sizing calculations (1:10-15 engineer:tenant ratio)
- Self-service portal architecture (80% tier 1 auto-approval)
- SLA templates by tenant tier (Platinum, Gold, Silver)
- Platform maturity assessment (5 levels across 6 dimensions)

Based on production GCC experience with 20-100 tenant platforms.
"""

import logging
import math
from enum import Enum, IntEnum
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Tuple, Any, Optional
from datetime import datetime
import re

# Configure logging
logger = logging.getLogger(__name__)

# Export public API
__all__ = [
    "OperatingModel",
    "TenantSophistication",
    "ComplianceLevel",
    "MaturityLevel",
    "OrganizationalContext",
    "OperatingModelSelector",
    "TeamSizingCalculator",
    "TeamSizingRecommendation",
    "SLATemplate",
    "SLAManager",
    "SelfServicePortal",
    "TenantRequest",
    "PlatformMaturityAssessment",
    "MaturityDimension"
]


# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class OperatingModel(Enum):
    """
    Three operating model types for multi-tenant platforms.

    - CENTRALIZED: Single platform team controls all tenant operations
    - FEDERATED: Tenant teams self-manage, platform provides infrastructure only
    - HYBRID: Platform core + tenant champions (most common for GCC)
    """
    CENTRALIZED = "centralized"
    FEDERATED = "federated"
    HYBRID = "hybrid"


class TenantSophistication(Enum):
    """
    Technical capability level of tenant teams.

    - LOW: Business users with no technical staff
    - MEDIUM: 1-2 technical people, not platform experts
    - HIGH: Dedicated engineering teams
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ComplianceLevel(Enum):
    """
    Compliance requirements for the platform.

    - LOW: Internal tools, non-sensitive data
    - MODERATE: Standard corporate compliance (data privacy, security)
    - CRITICAL: Finance/Legal/Healthcare audit requirements (SOX, HIPAA)
    """
    LOW = "low"
    MODERATE = "moderate"
    CRITICAL = "critical"


class MaturityLevel(IntEnum):
    """
    Platform governance maturity levels (CMMI-adapted).

    Each level builds on previous - you can't skip levels.
    """
    AD_HOC = 1          # No governance, everything ad-hoc
    REPEATABLE = 2      # Some processes documented
    DEFINED = 3         # Standard processes across all tenants
    MANAGED = 4         # Processes measured and controlled
    OPTIMIZED = 5       # Continuous improvement culture


@dataclass
class OrganizationalContext:
    """
    Context for operating model decision.

    Attributes:
        num_tenants: Current number of business units using platform
        tenant_sophistication: Technical capability of most tenants
        compliance_level: Regulatory/compliance requirements
        rate_of_change: How frequently platform requirements change
    """
    num_tenants: int
    tenant_sophistication: TenantSophistication
    compliance_level: ComplianceLevel
    rate_of_change: Literal["low", "medium", "high"]


@dataclass
class TeamSizingRecommendation:
    """
    Team sizing output with cost justification.

    CFOs need to see not just headcount, but cost and ROI.
    """
    recommended_team_size: int
    engineer_to_tenant_ratio: str  # e.g., "1:12"
    annual_cost_inr: int  # Total cost in rupees
    annual_cost_usd: int  # Total cost in USD
    cost_per_tenant_inr: int  # Cost per tenant in rupees
    cost_per_tenant_usd: int  # Cost per tenant in USD
    breakdown: Dict[str, str]  # Detailed explanation
    alternatives_comparison: Dict[str, int]  # Cost of other models


@dataclass
class SLATemplate:
    """
    Service Level Agreement template by tenant tier.

    Different tiers get different SLAs - platinum pays more, gets better service.
    """
    tier: str
    availability: float  # 0.999 = 99.9%
    response_time_p95_ms: int  # 95th percentile latency
    support_response_minutes: int  # How fast support responds
    incident_priority: str  # P0/P1/P2
    dedicated_support: bool  # Does tenant get dedicated support engineer?

    def availability_downtime(self) -> str:
        """
        Convert availability percentage to human-readable downtime.

        CFOs understand "4 hours/year" better than "99.95%"
        """
        downtime_fraction = 1 - self.availability
        downtime_minutes_per_year = downtime_fraction * 365 * 24 * 60

        if downtime_minutes_per_year < 60:
            return f"{downtime_minutes_per_year:.0f} minutes/year"
        elif downtime_minutes_per_year < 24 * 60:
            return f"{downtime_minutes_per_year/60:.1f} hours/year"
        else:
            return f"{downtime_minutes_per_year/(24*60):.1f} days/year"


@dataclass
class TenantRequest:
    """
    Represents a tenant request in self-service portal.

    In production, this would be stored in PostgreSQL with audit trail.
    """
    request_id: str
    tenant_id: str
    request_type: Literal["quota_increase", "access_grant", "feature_request", "support_ticket"]
    description: str
    status: Literal["pending", "approved", "rejected", "completed"]
    created_at: datetime = field(default_factory=datetime.now)
    approved_by: Optional[str] = None
    completed_at: Optional[datetime] = None


@dataclass
class MaturityDimension:
    """
    One dimension of platform maturity.

    Platform maturity is multi-dimensional. You might be Level 4 in onboarding
    but Level 2 in incident response.
    """
    name: str
    description: str
    current_level: MaturityLevel
    evidence: List[str]  # What practices exist today
    gaps: List[str]      # What's missing for next level
    next_actions: List[str]  # Concrete steps to improve


# ============================================================================
# OPERATING MODEL SELECTOR
# ============================================================================

class OperatingModelSelector:
    """
    Decision framework for choosing operating model.

    Based on production GCC experience with 10-100 tenant platforms.
    Key insight: No single model fits all - must consider org context.
    """

    def choose_model(self, context: OrganizationalContext) -> OperatingModel:
        """
        Select operating model based on organizational context.

        Decision logic:
        1. Small scale (< 10 tenants): Default to centralized (simple to manage)
        2. Large scale (> 50 tenants) + high sophistication: Federated (tenants can self-manage)
        3. Critical compliance regardless of scale: Centralized (need control)
        4. Most other cases: Hybrid (balance control and velocity)

        Args:
            context: Organizational context for decision

        Returns:
            OperatingModel enum value

        Raises:
            ValueError: If context is invalid
        """
        # Validate context
        if context.num_tenants < 1:
            logger.error("Invalid num_tenants: must be positive")
            raise ValueError("num_tenants must be positive")

        logger.info(f"Choosing operating model for {context.num_tenants} tenants, "
                   f"sophistication={context.tenant_sophistication.value}, "
                   f"compliance={context.compliance_level.value}")

        # Rule 1: Small scale → Centralized
        # Rationale: At < 10 tenants, manual ops are viable and provide best control
        if context.num_tenants < 10:
            if context.compliance_level == ComplianceLevel.CRITICAL:
                logger.info("Decision: CENTRALIZED (small scale + critical compliance)")
                return OperatingModel.CENTRALIZED
            else:
                logger.info("Decision: CENTRALIZED (small scale)")
                return OperatingModel.CENTRALIZED

        # Rule 2: Large scale + sophisticated tenants → Federated
        # Rationale: Tenants can self-manage, platform team provides infrastructure only
        elif context.num_tenants > 50 and context.tenant_sophistication == TenantSophistication.HIGH:
            if context.compliance_level == ComplianceLevel.CRITICAL:
                # Even with sophistication, critical compliance needs control
                # Fall through to Hybrid
                pass
            else:
                logger.info("Decision: FEDERATED (large scale + high sophistication)")
                return OperatingModel.FEDERATED

        # Rule 3: Critical compliance → Centralized (even at medium scale)
        # Rationale: Audit requirements demand centralized control and oversight
        elif context.compliance_level == ComplianceLevel.CRITICAL:
            logger.info("Decision: CENTRALIZED (critical compliance)")
            return OperatingModel.CENTRALIZED

        # Rule 4: Default to Hybrid for 10-50 tenants
        # Rationale: Most GCCs land here - need balance between control and velocity
        logger.info("Decision: HYBRID (default for 10-50 tenants)")
        return OperatingModel.HYBRID

    def calculate_team_size(
        self,
        model: OperatingModel,
        num_tenants: int,
        complexity: Literal["low", "medium", "high"]
    ) -> int:
        """
        Calculate platform team size based on operating model.

        Formula: team_size = num_tenants / (base_ratio × complexity_multiplier)

        Base ratios by model:
        - Centralized: 1:5 (more hands-on support needed)
        - Federated: 1:20 (infrastructure only, tenants self-manage)
        - Hybrid: 1:12 (tenant champions handle tier 2, platform does tier 3)

        Complexity multipliers:
        - Low: 1.5× (simple tenants, less support needed)
        - Medium: 1.0× (standard complexity)
        - High: 0.75× (complex tenants, more support needed)

        Args:
            model: Operating model choice
            num_tenants: Number of tenants to support
            complexity: Complexity level of tenant requirements

        Returns:
            Recommended team size (minimum 2 for redundancy)
        """
        # Base ratio depends on operating model (from production GCC data)
        base_ratios = {
            OperatingModel.CENTRALIZED: 5,   # 1:5 ratio (hands-on)
            OperatingModel.FEDERATED: 20,    # 1:20 ratio (infrastructure only)
            OperatingModel.HYBRID: 12        # 1:12 ratio (champions help)
        }

        # Complexity multiplier adjusts for tenant sophistication
        complexity_multipliers = {
            "low": 1.5,     # Simple tenants need less support (1:18 for hybrid)
            "medium": 1.0,  # Standard complexity (1:12 for hybrid)
            "high": 0.75    # Complex tenants need more support (1:9 for hybrid)
        }

        base_ratio = base_ratios[model]
        multiplier = complexity_multipliers[complexity]

        # Calculate team size
        adjusted_ratio = base_ratio * multiplier
        team_size = num_tenants / adjusted_ratio

        # Always round up (can't have fractional engineers)
        team_size = math.ceil(team_size)

        # Minimum team size is 2 (need redundancy for on-call, vacations)
        final_team_size = max(team_size, 2)

        logger.info(f"Team sizing: {num_tenants} tenants / {adjusted_ratio:.1f} "
                   f"(base {base_ratio} × {multiplier}) = {final_team_size} engineers")

        return final_team_size

    def explain_decision(
        self,
        context: OrganizationalContext,
        chosen_model: OperatingModel
    ) -> str:
        """
        Generate human-readable explanation for operating model choice.

        This is crucial for stakeholder communication (CFO, CTO, BU heads).
        They need to understand WHY this model was chosen and what it means.

        Args:
            context: The organizational context used for decision
            chosen_model: The selected operating model

        Returns:
            Multi-paragraph explanation suitable for presentation to leadership
        """
        explanations = {
            OperatingModel.CENTRALIZED: f"""
CENTRALIZED OPERATING MODEL SELECTED

Why this model:
- Your GCC has {context.num_tenants} tenants (small-to-medium scale)
- Compliance level is {context.compliance_level.value} (requires strong control)
- Tenant sophistication is {context.tenant_sophistication.value} (may lack self-service capability)

What this means:
- Platform team manages ALL tenant operations (onboarding, configuration, support)
- Tenants submit requests via tickets, platform team implements
- Strong governance and audit trails
- Consistent experience across all tenants

Trade-offs:
- Pros: Maximum control, best for compliance, simple accountability
- Cons: Platform team can become bottleneck, slower iteration for tenants

Team sizing:
- Recommended ratio: 1 engineer per 5-7 tenants (hands-on support)
- For {context.num_tenants} tenants: ~{self.calculate_team_size(chosen_model, context.num_tenants, "medium")} engineers

When to revisit:
- If tenant count exceeds 20 (centralized bottleneck becomes severe)
- If tenants gain technical capability (could move to hybrid)
- If compliance requirements relax (could enable more self-service)
""",
            OperatingModel.FEDERATED: f"""
FEDERATED OPERATING MODEL SELECTED

Why this model:
- Your GCC has {context.num_tenants} tenants (large scale)
- Tenant sophistication is {context.tenant_sophistication.value} (can self-manage)
- Compliance level is {context.compliance_level.value} (allows distributed control)

What this means:
- Each tenant team manages their own RAG instance
- Platform team provides: Infrastructure, monitoring, security baselines
- Platform team does NOT provide: Configuration, feature implementation, support
- Tenants iterate at their own pace (no central bottleneck)

Trade-offs:
- Pros: Scales to 100+ tenants, fast innovation, no bottleneck
- Cons: Inconsistent experience across tenants, higher compliance risk

Team sizing:
- Recommended ratio: 1 engineer per 15-20 tenants (infrastructure only)
- For {context.num_tenants} tenants: ~{self.calculate_team_size(chosen_model, context.num_tenants, "medium")} engineers

When to revisit:
- If compliance requirements increase (need more control)
- If tenants request more platform-provided features (moving toward hybrid)
- If inconsistency becomes problem (standardization needed)
""",
            OperatingModel.HYBRID: f"""
HYBRID OPERATING MODEL SELECTED

Why this model:
- Your GCC has {context.num_tenants} tenants (sweet spot for hybrid: 10-100)
- Tenant sophistication is {context.tenant_sophistication.value} (mixed capabilities)
- Compliance level is {context.compliance_level.value} (need balance of control and velocity)

What this means:
- Tier 1 issues (80%): Self-service portal (documentation, automation)
- Tier 2 issues (15%): Tenant champions (designated BU representative, 2 hours/week)
- Tier 3 issues (5%): Platform team (platform-level bugs, features)

Tenant Champions:
- Each BU designates 1-2 champions (2-4 hours/week commitment)
- Champions get admin permissions for their tenant
- Champions handle: Access grants, quota increases, configuration changes
- Champions escalate to platform team only for platform-level issues

Trade-offs:
- Pros: Scales to 50-100 tenants, balance of control and velocity, champions understand BU needs
- Cons: Requires identifying and training champions, more complex communication structure

Team sizing:
- Platform team ratio: 1 engineer per 10-15 tenants (tier 3 only)
- For {context.num_tenants} tenants: ~{self.calculate_team_size(chosen_model, context.num_tenants, "medium")} platform engineers
- Plus: {context.num_tenants} tenant champions (2-4 hours/week each)

When to revisit:
- If champions are overwhelmed (need more self-service automation)
- If tenant count exceeds 100 (consider federated for sophisticated tenants)
- If compliance increases dramatically (move toward centralized)
"""
        }

        return explanations[chosen_model]


# ============================================================================
# TEAM SIZING CALCULATOR
# ============================================================================

class TeamSizingCalculator:
    """
    Calculate platform team size based on operating model and complexity.

    Uses production GCC ratios from 20+ real deployments.
    Key insight: Team size grows sublinearly with tenant count IF you have self-service.
    """

    # Average engineer salary in GCC (senior platform engineer)
    AVG_SALARY_INR = 30_00_000  # ₹30 lakhs per year
    INR_TO_USD = 82  # Current exchange rate (approximate)

    def calculate(
        self,
        num_tenants: int,
        complexity: Literal["low", "medium", "high"],
        operating_model: OperatingModel
    ) -> TeamSizingRecommendation:
        """
        Calculate team size with full cost justification.

        Args:
            num_tenants: Number of business units using platform
            complexity: Tenant complexity level
            operating_model: Chosen operating model

        Returns:
            TeamSizingRecommendation with headcount and costs
        """
        logger.info(f"Calculating team size for {num_tenants} tenants, "
                   f"complexity={complexity}, model={operating_model.value}")

        # Base ratio by operating model
        base_ratios = {
            OperatingModel.CENTRALIZED: 5,   # 1:5 (hands-on)
            OperatingModel.FEDERATED: 20,    # 1:20 (infrastructure only)
            OperatingModel.HYBRID: 12        # 1:12 (champions help)
        }

        # Complexity adjustment
        complexity_multipliers = {
            "low": 1.5,     # Simpler tenants need less support
            "medium": 1.0,  # Standard complexity
            "high": 0.75    # Complex tenants need more support
        }

        base_ratio = base_ratios[operating_model]
        multiplier = complexity_multipliers[complexity]
        adjusted_ratio = base_ratio * multiplier

        # Calculate team size
        team_size = math.ceil(num_tenants / adjusted_ratio)
        team_size = max(team_size, 2)  # Minimum 2 for redundancy

        # Calculate costs
        annual_cost_inr = team_size * self.AVG_SALARY_INR
        annual_cost_usd = annual_cost_inr // self.INR_TO_USD
        cost_per_tenant_inr = annual_cost_inr // num_tenants
        cost_per_tenant_usd = cost_per_tenant_inr // self.INR_TO_USD

        # Build detailed breakdown for CFO presentation
        breakdown = {
            "formula": f"team_size = {num_tenants} tenants / ({base_ratio} × {multiplier}) = {num_tenants / adjusted_ratio:.1f} → {team_size} engineers",
            "base_ratio": f"1:{base_ratio} ({operating_model.value} model)",
            "complexity_adjustment": f"{multiplier}× ({complexity} complexity)",
            "adjusted_ratio": f"1:{adjusted_ratio:.0f}",
            "minimum_team": "2 engineers (redundancy for on-call, vacations)",
            "salary_assumption": f"₹{self.AVG_SALARY_INR/100_000:.0f}L per engineer (senior platform engineer in India)"
        }

        # Compare with other operating models
        alternatives_comparison = {}
        for model in OperatingModel:
            if model != operating_model:
                alt_ratio = base_ratios[model] * multiplier
                alt_team_size = max(math.ceil(num_tenants / alt_ratio), 2)
                alt_cost = alt_team_size * self.AVG_SALARY_INR
                alternatives_comparison[model.value] = alt_cost

        logger.info(f"Team size recommendation: {team_size} engineers, "
                   f"₹{annual_cost_inr/10_000_000:.2f}Cr/year")

        return TeamSizingRecommendation(
            recommended_team_size=team_size,
            engineer_to_tenant_ratio=f"1:{adjusted_ratio:.0f}",
            annual_cost_inr=annual_cost_inr,
            annual_cost_usd=annual_cost_usd,
            cost_per_tenant_inr=cost_per_tenant_inr,
            cost_per_tenant_usd=cost_per_tenant_usd,
            breakdown=breakdown,
            alternatives_comparison=alternatives_comparison
        )

    def compare_with_decentralized(
        self,
        num_tenants: int,
        centralized_cost: int
    ) -> Dict[str, Any]:
        """
        Compare centralized platform cost vs. decentralized (1 engineer per tenant).

        This is the killer argument for platform teams: Show 10× cost savings.

        Args:
            num_tenants: Number of tenants
            centralized_cost: Cost of centralized platform team

        Returns:
            Dict with comparison metrics
        """
        # Decentralized model: Each tenant has 1 dedicated engineer
        decentralized_cost = num_tenants * self.AVG_SALARY_INR

        # Calculate savings
        savings_inr = decentralized_cost - centralized_cost
        savings_usd = savings_inr // self.INR_TO_USD
        savings_percentage = (savings_inr / decentralized_cost) * 100
        roi_multiple = decentralized_cost / centralized_cost

        logger.info(f"Cost comparison: Centralized ₹{centralized_cost/10_000_000:.1f}Cr "
                   f"vs Decentralized ₹{decentralized_cost/10_000_000:.1f}Cr "
                   f"(savings: {savings_percentage:.0f}%)")

        return {
            "decentralized_cost_inr": decentralized_cost,
            "decentralized_cost_usd": decentralized_cost // self.INR_TO_USD,
            "centralized_cost_inr": centralized_cost,
            "centralized_cost_usd": centralized_cost // self.INR_TO_USD,
            "savings_inr": savings_inr,
            "savings_usd": savings_usd,
            "savings_percentage": savings_percentage,
            "roi_multiple": roi_multiple,
            "narrative": f"Centralized platform saves ₹{savings_inr/10_000_000:.1f} Cr/year ({savings_percentage:.0f}% reduction), providing {roi_multiple:.1f}× ROI."
        }


# ============================================================================
# SLA MANAGER
# ============================================================================

class SLAManager:
    """
    Manage SLA templates for different tenant tiers.

    In production, these would be stored in database and customizable.
    Here we show standard templates from real GCC deployments.
    """

    # Standard SLA templates from production GCC platforms
    TEMPLATES = {
        "platinum": SLATemplate(
            tier="platinum",
            availability=0.9999,  # 99.99% = 52 minutes/year downtime
            response_time_p95_ms=200,  # 200ms P95
            support_response_minutes=15,  # 15 minute response
            incident_priority="P0",
            dedicated_support=True  # Platinum gets dedicated support engineer
        ),
        "gold": SLATemplate(
            tier="gold",
            availability=0.999,  # 99.9% = 8.7 hours/year downtime
            response_time_p95_ms=500,  # 500ms P95
            support_response_minutes=60,  # 1 hour response
            incident_priority="P1",
            dedicated_support=False
        ),
        "silver": SLATemplate(
            tier="silver",
            availability=0.99,  # 99% = 3.65 days/year downtime
            response_time_p95_ms=1000,  # 1 second P95
            support_response_minutes=240,  # 4 hour response
            incident_priority="P2",
            dedicated_support=False
        )
    }

    @classmethod
    def get_template(cls, tier: str) -> SLATemplate:
        """Get SLA template for tenant tier."""
        if tier not in cls.TEMPLATES:
            logger.error(f"Unknown SLA tier: {tier}")
            raise ValueError(f"Unknown tier: {tier}. Valid: {list(cls.TEMPLATES.keys())}")
        return cls.TEMPLATES[tier]

    @classmethod
    def compare_tiers(cls) -> str:
        """
        Generate comparison table of all tiers.

        Useful for tenant onboarding ("Which tier do you want?")
        """
        comparison = "SLA TIER COMPARISON:\n\n"
        comparison += f"{'Tier':<10} {'Availability':<12} {'Downtime':<15} {'Response Time':<15} {'Support Response':<20}\n"
        comparison += "=" * 80 + "\n"

        for tier_name, template in cls.TEMPLATES.items():
            comparison += f"{tier_name.capitalize():<10} "
            comparison += f"{template.availability*100:.2f}%{' ':<5} "
            comparison += f"{template.availability_downtime():<15} "
            comparison += f"{template.response_time_p95_ms}ms P95{' ':<6} "
            comparison += f"{template.support_response_minutes} min{' ':<12}\n"

        return comparison


# ============================================================================
# SELF-SERVICE PORTAL
# ============================================================================

class SelfServicePortal:
    """
    Self-service portal for tenant requests.

    This is the KEY to scaling governance. 80% of requests are handled here
    without human involvement (tier 1) or with champion involvement (tier 2).

    In production, this would be a React frontend + FastAPI backend.
    Here we show the business logic only.
    """

    def __init__(self):
        """Initialize portal with empty request queue."""
        self.requests: Dict[str, TenantRequest] = {}
        self.auto_approval_rules = self._init_auto_approval_rules()
        logger.info("Self-service portal initialized")

    def _init_auto_approval_rules(self) -> Dict[str, callable]:
        """
        Define which requests can be auto-approved (no human needed).

        These rules encode the 80% of tier 1 requests that are safe to automate.
        In production, these would be configurable via Open Policy Agent (OPA).
        """
        return {
            "quota_increase": lambda req: self._auto_approve_quota(req),
            "access_grant": lambda req: self._auto_approve_access(req),
            "feature_request": lambda req: False,  # Always needs human review
            "support_ticket": lambda req: self._auto_resolve_support(req)
        }

    def _auto_approve_quota(self, request: TenantRequest) -> bool:
        """
        Auto-approve quota increases if under threshold.

        Business rule: Quota increases <10GB are auto-approved (low cost, low risk).
        Larger increases need champion or CFO approval.
        """
        # Parse quota increase from description
        match = re.search(r'(\d+)\s*GB', request.description)
        if match:
            increase_gb = int(match.group(1))
            if increase_gb <= 10:
                logger.info(f"Auto-approving quota increase: {increase_gb}GB <= 10GB threshold")
                return True
        logger.info(f"Quota increase requires manual approval (>10GB or invalid format)")
        return False

    def _auto_approve_access(self, request: TenantRequest) -> bool:
        """
        Auto-approve access grants if user is in same organization.

        Business rule: Access grants to users in same BU are auto-approved.
        Cross-BU access requires champion approval (compliance risk).
        """
        if "same-org" in request.description.lower():
            logger.info("Auto-approving access grant (same-org user)")
            return True
        logger.info("Access grant requires manual approval (cross-org or unverified)")
        return False

    def _auto_resolve_support(self, request: TenantRequest) -> bool:
        """
        Auto-resolve support tickets if answer is in knowledge base.

        Business rule: If question matches FAQ, return canned response.
        This is 50% of support tickets ("How do I...?" questions).
        """
        # Common questions that can be auto-resolved
        faq_keywords = ["how do i", "where is", "what is", "can i"]
        desc_lower = request.description.lower()

        for keyword in faq_keywords:
            if keyword in desc_lower:
                logger.info(f"Auto-resolving support ticket (FAQ match: {keyword})")
                return True
        logger.info("Support ticket requires manual review (no FAQ match)")
        return False

    def submit_request(
        self,
        tenant_id: str,
        request_type: str,
        description: str
    ) -> TenantRequest:
        """
        Submit a new request to self-service portal.

        This is the tenant-facing API. Tenant submits request, portal decides:
        - Can this be auto-approved? (tier 1, self-service)
        - Does this need champion? (tier 2, human review)
        - Does this need platform team? (tier 3, escalation)

        Args:
            tenant_id: Which tenant is making request
            request_type: Type of request
            description: Details of what they want

        Returns:
            TenantRequest object with initial status
        """
        # Create request
        request_id = f"REQ-{len(self.requests)+1:04d}"
        request = TenantRequest(
            request_id=request_id,
            tenant_id=tenant_id,
            request_type=request_type,  # type: ignore
            description=description,
            status="pending"
        )

        logger.info(f"New request submitted: {request_id} from {tenant_id}, type={request_type}")

        # Try auto-approval
        if request_type in self.auto_approval_rules:
            auto_approve_fn = self.auto_approval_rules[request_type]
            if auto_approve_fn(request):
                # Auto-approved! No human involvement needed.
                request.status = "approved"
                request.approved_by = "AUTO"
                request.completed_at = datetime.now()
                logger.info(f"✅ Request {request_id} AUTO-APPROVED (tier 1, self-service)")
            else:
                # Needs human review (champion or platform team)
                logger.info(f"⏳ Request {request_id} PENDING REVIEW (tier 2/3, escalation needed)")
        else:
            logger.warning(f"⏳ Request {request_id} PENDING REVIEW (unknown type: {request_type})")

        self.requests[request_id] = request
        return request

    def get_tenant_dashboard(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get self-service dashboard for a tenant.

        This is what tenant sees when they log into portal.
        Shows: Current configuration, usage metrics, pending requests.
        """
        tenant_requests = [r for r in self.requests.values() if r.tenant_id == tenant_id]

        auto_approved = [r for r in tenant_requests if r.approved_by == "AUTO"]
        pending = [r for r in tenant_requests if r.status == "pending"]

        auto_approved_pct = len(auto_approved) / max(len(tenant_requests), 1) * 100

        logger.info(f"Dashboard for {tenant_id}: {len(tenant_requests)} total, "
                   f"{len(pending)} pending, {auto_approved_pct:.0f}% auto-approved")

        return {
            "tenant_id": tenant_id,
            "total_requests": len(tenant_requests),
            "pending_requests": len(pending),
            "auto_approved_percentage": auto_approved_pct,
            "recent_requests": sorted(tenant_requests, key=lambda x: x.created_at, reverse=True)[:5]
        }


# ============================================================================
# PLATFORM MATURITY ASSESSMENT
# ============================================================================

class PlatformMaturityAssessment:
    """
    Assess platform governance maturity across multiple dimensions.

    This tool is used in quarterly reviews with GCC leadership to:
    1. Understand current maturity
    2. Identify gaps
    3. Prioritize improvements
    """

    # Dimensions of platform maturity
    DIMENSIONS = [
        "onboarding",      # How tenants are onboarded
        "self_service",   # Self-service capabilities
        "incident_mgmt",  # How incidents are handled
        "change_mgmt",    # How changes are deployed
        "monitoring",     # Observability and alerting
        "governance",     # Operating model and processes
    ]

    def __init__(self):
        """Initialize assessment with empty dimensions."""
        self.dimensions: Dict[str, MaturityDimension] = {}
        logger.info("Platform maturity assessment initialized")

    def assess_dimension(
        self,
        dimension: str,
        questions: List[Tuple[str, MaturityLevel]]
    ) -> MaturityDimension:
        """
        Assess maturity for one dimension.

        Process:
        1. Ask series of questions ("Do you have X?")
        2. Each yes/no maps to a maturity level
        3. Lowest "no" answer determines current level

        Args:
            dimension: Which dimension to assess
            questions: List of (question, level) tuples

        Returns:
            MaturityDimension with assessment results
        """
        logger.info(f"Assessing maturity for dimension: {dimension}")

        # Sort questions by maturity level
        questions_sorted = sorted(questions, key=lambda x: x[1])

        # Find highest level where all questions are answered "yes"
        current_level = MaturityLevel.AD_HOC
        evidence = []
        gaps = []

        for question, required_level in questions_sorted:
            # In production, prompt user "Do you have this? (y/n)"
            # Here we simulate answers for demo
            has_capability = self._simulate_capability_check(dimension, required_level)

            if has_capability:
                current_level = required_level
                evidence.append(question)
            else:
                gaps.append(question)

        # Generate next actions based on gaps
        next_actions = self._generate_next_actions(dimension, current_level, gaps)

        dimension_obj = MaturityDimension(
            name=dimension,
            description=self._get_dimension_description(dimension),
            current_level=current_level,
            evidence=evidence,
            gaps=gaps,
            next_actions=next_actions
        )

        self.dimensions[dimension] = dimension_obj
        logger.info(f"Dimension {dimension} assessed at Level {current_level.value} ({current_level.name})")
        return dimension_obj

    def _simulate_capability_check(
        self,
        dimension: str,
        required_level: MaturityLevel
    ) -> bool:
        """
        Simulate capability check for demo.

        In production, this would prompt user or query platform configuration.
        Here we return reasonable defaults for a Level 2-3 platform.
        """
        # Simulate a platform that's Level 2-3 in most dimensions
        if required_level <= MaturityLevel.REPEATABLE:
            return True  # Has Level 1-2 capabilities
        elif required_level == MaturityLevel.DEFINED:
            return dimension in ["onboarding", "monitoring"]  # Level 3 only in some dimensions
        else:
            return False  # Doesn't have Level 4-5 capabilities yet

    def _get_dimension_description(self, dimension: str) -> str:
        """Get human-readable description of dimension."""
        descriptions = {
            "onboarding": "How new tenants are added to platform",
            "self_service": "Tenant self-service capabilities",
            "incident_mgmt": "How platform incidents are detected and resolved",
            "change_mgmt": "How changes are deployed safely",
            "monitoring": "Observability and alerting",
            "governance": "Operating model and decision processes"
        }
        return descriptions.get(dimension, "Unknown dimension")

    def _generate_next_actions(
        self,
        dimension: str,
        current_level: MaturityLevel,
        gaps: List[str]
    ) -> List[str]:
        """
        Generate concrete next actions to improve maturity.

        These are actionable recommendations, not vague "get better"
        """
        # Map each gap to specific action
        action_templates = {
            "onboarding": {
                MaturityLevel.AD_HOC: [
                    "Document onboarding process in runbook",
                    "Create onboarding checklist",
                    "Assign onboarding owner"
                ],
                MaturityLevel.REPEATABLE: [
                    "Automate onboarding (Terraform/API)",
                    "Create self-service onboarding form",
                    "Track onboarding time (SLA: <1 day)"
                ],
                MaturityLevel.DEFINED: [
                    "Measure onboarding errors (target: <5%)",
                    "Implement onboarding rollback",
                    "A/B test onboarding UX"
                ],
                MaturityLevel.MANAGED: [
                    "Predict onboarding volume (capacity planning)",
                    "Optimize onboarding for different tenant types",
                    "Continuously improve based on metrics"
                ]
            },
            "self_service": {
                MaturityLevel.AD_HOC: [
                    "Build self-service portal (basic UI)",
                    "Document common tasks",
                    "Enable tenants to view their config"
                ],
                MaturityLevel.REPEATABLE: [
                    "Add auto-approval for tier 1 requests",
                    "Implement tenant champions",
                    "Track self-service adoption (target: 80%)"
                ],
                MaturityLevel.DEFINED: [
                    "Measure self-service success rate",
                    "Add ML-powered assistance (chatbot)",
                    "Optimize workflows based on metrics"
                ],
                MaturityLevel.MANAGED: [
                    "Predict support load",
                    "Personalize self-service for tenant type",
                    "Continuously improve UX"
                ]
            }
        }

        # Get actions for this dimension at next level
        next_level_value = current_level.value + 1
        if next_level_value > MaturityLevel.OPTIMIZED:
            return ["You've reached maximum maturity! Focus on maintaining excellence."]

        next_level = MaturityLevel(next_level_value)

        return action_templates.get(dimension, {}).get(current_level, [
            f"Improve {dimension} from level {current_level.name} to {next_level.name}",
            "Consult platform maturity framework for specific recommendations"
        ])

    def generate_report(self) -> str:
        """
        Generate maturity assessment report for leadership.

        This report goes to CTO/CFO to justify improvement investments.
        Format: Executive summary + dimension breakdown + prioritized next actions.
        """
        report = []
        report.append("=" * 80)
        report.append("PLATFORM GOVERNANCE MATURITY ASSESSMENT")
        report.append("=" * 80 + "\n")

        if not self.dimensions:
            report.append("No dimensions assessed yet.")
            return "\n".join(report)

        # Executive summary
        avg_level = sum(d.current_level for d in self.dimensions.values()) / len(self.dimensions)
        highest = max(self.dimensions.items(), key=lambda x: x[1].current_level)
        lowest = min(self.dimensions.items(), key=lambda x: x[1].current_level)

        report.append("EXECUTIVE SUMMARY:")
        report.append(f"Overall Maturity: Level {avg_level:.1f} ({self._level_name(avg_level)})")
        report.append(f"Dimensions Assessed: {len(self.dimensions)}")
        report.append(f"Highest Maturity: {highest[0]} (Level {highest[1].current_level.value})")
        report.append(f"Lowest Maturity: {lowest[0]} (Level {lowest[1].current_level.value})\n")

        # Dimension breakdown
        report.append("MATURITY BY DIMENSION:\n")
        for dim_name, dim in sorted(self.dimensions.items(), key=lambda x: x[1].current_level, reverse=True):
            report.append(f"{dim_name.upper().replace('_', ' ')}:")
            report.append(f"  Current Level: {dim.current_level.value} - {dim.current_level.name}")
            report.append(f"  Description: {dim.description}")
            report.append(f"  Evidence ({len(dim.evidence)} capabilities):")
            for e in dim.evidence[:3]:  # Show top 3
                report.append(f"    ✓ {e}")
            if len(dim.evidence) > 3:
                report.append(f"    ... and {len(dim.evidence)-3} more")
            report.append(f"  Gaps ({len(dim.gaps)} missing):")
            for g in dim.gaps[:3]:  # Show top 3
                report.append(f"    ✗ {g}")
            if len(dim.gaps) > 3:
                report.append(f"    ... and {len(dim.gaps)-3} more")
            report.append("")

        # Prioritized next actions
        report.append("\nPRIORITIZED NEXT ACTIONS:")
        report.append("Focus on lowest-maturity dimensions first for maximum ROI.\n")

        # Sort dimensions by maturity (lowest first)
        sorted_dims = sorted(self.dimensions.values(), key=lambda x: x.current_level)

        for i, dim in enumerate(sorted_dims[:3], 1):  # Top 3 priorities
            next_level = dim.current_level.value + 1
            if next_level <= MaturityLevel.OPTIMIZED:
                report.append(f"Priority {i}: {dim.name.upper().replace('_', ' ')} (Level {dim.current_level.value} → {next_level})")
                for action in dim.next_actions:
                    report.append(f"  • {action}")
                report.append("")

        return "\n".join(report)

    def _level_name(self, level_float: float) -> str:
        """Convert numeric level to name."""
        level_int = round(level_float)
        return MaturityLevel(level_int).name
