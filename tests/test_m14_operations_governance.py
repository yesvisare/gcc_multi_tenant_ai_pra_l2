"""
Tests for L3 M14.4: Platform Governance & Operating Model

Tests ALL major functions from the governance framework.
All tests run in offline mode (no external services needed).
"""

import pytest
import os
from datetime import datetime

from src.l3_m14_operations_governance import (
    OperatingModel,
    TenantSophistication,
    ComplianceLevel,
    MaturityLevel,
    OrganizationalContext,
    OperatingModelSelector,
    TeamSizingCalculator,
    SLAManager,
    SelfServicePortal,
    PlatformMaturityAssessment
)

# Force offline mode for all tests
os.environ["OFFLINE"] = "true"


# ============================================================================
# OPERATING MODEL SELECTOR TESTS
# ============================================================================

class TestOperatingModelSelector:
    """Tests for operating model selection logic."""

    def test_small_scale_centralized(self):
        """Test that < 10 tenants defaults to centralized."""
        selector = OperatingModelSelector()
        context = OrganizationalContext(
            num_tenants=8,
            tenant_sophistication=TenantSophistication.MEDIUM,
            compliance_level=ComplianceLevel.MODERATE,
            rate_of_change="medium"
        )

        model = selector.choose_model(context)
        assert model == OperatingModel.CENTRALIZED

    def test_large_scale_high_sophistication_federated(self):
        """Test that > 50 tenants with high sophistication selects federated."""
        selector = OperatingModelSelector()
        context = OrganizationalContext(
            num_tenants=75,
            tenant_sophistication=TenantSophistication.HIGH,
            compliance_level=ComplianceLevel.MODERATE,
            rate_of_change="high"
        )

        model = selector.choose_model(context)
        assert model == OperatingModel.FEDERATED

    def test_medium_scale_hybrid(self):
        """Test that 10-50 tenants with mixed sophistication selects hybrid."""
        selector = OperatingModelSelector()
        context = OrganizationalContext(
            num_tenants=45,
            tenant_sophistication=TenantSophistication.MEDIUM,
            compliance_level=ComplianceLevel.MODERATE,
            rate_of_change="medium"
        )

        model = selector.choose_model(context)
        assert model == OperatingModel.HYBRID

    def test_critical_compliance_centralized(self):
        """Test that critical compliance forces centralized regardless of scale."""
        selector = OperatingModelSelector()
        context = OrganizationalContext(
            num_tenants=30,  # Medium scale
            tenant_sophistication=TenantSophistication.HIGH,
            compliance_level=ComplianceLevel.CRITICAL,  # Critical compliance
            rate_of_change="medium"
        )

        model = selector.choose_model(context)
        assert model == OperatingModel.CENTRALIZED

    def test_invalid_tenant_count(self):
        """Test that invalid tenant count raises ValueError."""
        selector = OperatingModelSelector()
        context = OrganizationalContext(
            num_tenants=0,  # Invalid
            tenant_sophistication=TenantSophistication.MEDIUM,
            compliance_level=ComplianceLevel.MODERATE,
            rate_of_change="medium"
        )

        with pytest.raises(ValueError, match="num_tenants must be positive"):
            selector.choose_model(context)

    def test_team_sizing_centralized(self):
        """Test team sizing for centralized model (1:5 ratio)."""
        selector = OperatingModelSelector()
        team_size = selector.calculate_team_size(
            model=OperatingModel.CENTRALIZED,
            num_tenants=20,
            complexity="medium"
        )

        # 20 tenants / (5 * 1.0) = 4 engineers
        assert team_size == 4

    def test_team_sizing_hybrid(self):
        """Test team sizing for hybrid model (1:12 ratio)."""
        selector = OperatingModelSelector()
        team_size = selector.calculate_team_size(
            model=OperatingModel.HYBRID,
            num_tenants=50,
            complexity="medium"
        )

        # 50 tenants / (12 * 1.0) = 4.17 → ceil(4.17) = 5 engineers
        assert team_size == 5

    def test_team_sizing_minimum(self):
        """Test that team size never goes below 2 (redundancy)."""
        selector = OperatingModelSelector()
        team_size = selector.calculate_team_size(
            model=OperatingModel.HYBRID,
            num_tenants=5,  # Very small
            complexity="low"  # 1.5× multiplier
        )

        # 5 / (12 * 1.5) = 5 / 18 = 0.28 → max(ceil(0.28), 2) = 2
        assert team_size == 2

    def test_explain_decision_contains_rationale(self):
        """Test that explanation contains key decision rationale."""
        selector = OperatingModelSelector()
        context = OrganizationalContext(
            num_tenants=45,
            tenant_sophistication=TenantSophistication.MEDIUM,
            compliance_level=ComplianceLevel.MODERATE,
            rate_of_change="medium"
        )

        model = selector.choose_model(context)
        explanation = selector.explain_decision(context, model)

        # Check that explanation contains expected content
        assert "HYBRID" in explanation
        assert str(context.num_tenants) in explanation
        assert "Tier 1" in explanation  # Hybrid explanation mentions tiers
        assert "Tier 2" in explanation
        assert "Tier 3" in explanation


# ============================================================================
# TEAM SIZING CALCULATOR TESTS
# ============================================================================

class TestTeamSizingCalculator:
    """Tests for team sizing and cost calculations."""

    def test_calculate_hybrid_medium_complexity(self):
        """Test team sizing calculation for hybrid model."""
        calculator = TeamSizingCalculator()
        recommendation = calculator.calculate(
            num_tenants=50,
            complexity="medium",
            operating_model=OperatingModel.HYBRID
        )

        # 50 / (12 * 1.0) = 4.17 → 5 engineers
        assert recommendation.recommended_team_size == 5
        assert recommendation.engineer_to_tenant_ratio == "1:12"
        assert recommendation.annual_cost_inr == 5 * calculator.AVG_SALARY_INR
        assert recommendation.cost_per_tenant_inr == (5 * calculator.AVG_SALARY_INR) // 50

    def test_calculate_low_complexity_adjustment(self):
        """Test that low complexity increases ratio (fewer engineers needed)."""
        calculator = TeamSizingCalculator()
        recommendation = calculator.calculate(
            num_tenants=20,
            complexity="low",  # 1.5× multiplier
            operating_model=OperatingModel.HYBRID
        )

        # 20 / (12 * 1.5) = 20 / 18 = 1.11 → max(ceil(1.11), 2) = 2 engineers
        assert recommendation.recommended_team_size == 2

    def test_calculate_high_complexity_adjustment(self):
        """Test that high complexity decreases ratio (more engineers needed)."""
        calculator = TeamSizingCalculator()
        recommendation = calculator.calculate(
            num_tenants=100,
            complexity="high",  # 0.75× multiplier
            operating_model=OperatingModel.HYBRID
        )

        # 100 / (12 * 0.75) = 100 / 9 = 11.11 → ceil(11.11) = 12 engineers
        assert recommendation.recommended_team_size == 12

    def test_calculate_includes_breakdown(self):
        """Test that calculation includes detailed breakdown for CFO."""
        calculator = TeamSizingCalculator()
        recommendation = calculator.calculate(
            num_tenants=45,
            complexity="medium",
            operating_model=OperatingModel.HYBRID
        )

        # Check breakdown contains expected keys
        assert "formula" in recommendation.breakdown
        assert "base_ratio" in recommendation.breakdown
        assert "complexity_adjustment" in recommendation.breakdown
        assert "adjusted_ratio" in recommendation.breakdown
        assert "minimum_team" in recommendation.breakdown
        assert "salary_assumption" in recommendation.breakdown

    def test_calculate_includes_alternatives(self):
        """Test that calculation includes cost of alternative models."""
        calculator = TeamSizingCalculator()
        recommendation = calculator.calculate(
            num_tenants=45,
            complexity="medium",
            operating_model=OperatingModel.HYBRID
        )

        # Should have costs for centralized and federated (not hybrid)
        assert "centralized" in recommendation.alternatives_comparison
        assert "federated" in recommendation.alternatives_comparison
        assert "hybrid" not in recommendation.alternatives_comparison

    def test_compare_with_decentralized(self):
        """Test centralized vs decentralized cost comparison."""
        calculator = TeamSizingCalculator()

        # 50 tenants, hybrid model with 5 engineers
        centralized_cost = 5 * calculator.AVG_SALARY_INR

        comparison = calculator.compare_with_decentralized(
            num_tenants=50,
            centralized_cost=centralized_cost
        )

        # Decentralized: 50 * 30L = 15Cr
        # Centralized: 5 * 30L = 1.5Cr
        # Savings: 13.5Cr (90%)
        assert comparison["decentralized_cost_inr"] == 50 * calculator.AVG_SALARY_INR
        assert comparison["centralized_cost_inr"] == centralized_cost
        assert comparison["savings_inr"] == (50 - 5) * calculator.AVG_SALARY_INR
        assert 85 < comparison["savings_percentage"] < 95  # ~90%
        assert 9 < comparison["roi_multiple"] < 11  # ~10×


# ============================================================================
# SLA MANAGER TESTS
# ============================================================================

class TestSLAManager:
    """Tests for SLA template management."""

    def test_get_platinum_template(self):
        """Test retrieving platinum SLA template."""
        template = SLAManager.get_template("platinum")

        assert template.tier == "platinum"
        assert template.availability == 0.9999  # 99.99%
        assert template.response_time_p95_ms == 200
        assert template.support_response_minutes == 15
        assert template.dedicated_support is True

    def test_get_gold_template(self):
        """Test retrieving gold SLA template."""
        template = SLAManager.get_template("gold")

        assert template.tier == "gold"
        assert template.availability == 0.999  # 99.9%
        assert template.response_time_p95_ms == 500
        assert template.support_response_minutes == 60

    def test_get_silver_template(self):
        """Test retrieving silver SLA template."""
        template = SLAManager.get_template("silver")

        assert template.tier == "silver"
        assert template.availability == 0.99  # 99%
        assert template.response_time_p95_ms == 1000
        assert template.support_response_minutes == 240

    def test_get_invalid_tier(self):
        """Test that invalid tier raises ValueError."""
        with pytest.raises(ValueError, match="Unknown tier"):
            SLAManager.get_template("invalid")

    def test_availability_downtime_calculation(self):
        """Test downtime calculation from availability percentage."""
        template = SLAManager.get_template("platinum")

        downtime_str = template.availability_downtime()

        # 99.99% = 0.01% downtime = 52.56 minutes/year
        assert "minutes/year" in downtime_str

    def test_compare_tiers_returns_table(self):
        """Test that tier comparison returns formatted table."""
        comparison = SLAManager.compare_tiers()

        # Check table contains all tiers
        assert "Platinum" in comparison or "platinum" in comparison
        assert "Gold" in comparison or "gold" in comparison
        assert "Silver" in comparison or "silver" in comparison
        assert "Availability" in comparison
        assert "Downtime" in comparison


# ============================================================================
# SELF-SERVICE PORTAL TESTS
# ============================================================================

class TestSelfServicePortal:
    """Tests for self-service portal functionality."""

    def test_auto_approve_small_quota_increase(self):
        """Test that small quota increases (<10GB) are auto-approved."""
        portal = SelfServicePortal()

        request = portal.submit_request(
            tenant_id="finance-analytics",
            request_type="quota_increase",
            description="Increase quota by 5GB for Q4 reports"
        )

        assert request.status == "approved"
        assert request.approved_by == "AUTO"

    def test_manual_approve_large_quota_increase(self):
        """Test that large quota increases (>10GB) require manual approval."""
        portal = SelfServicePortal()

        request = portal.submit_request(
            tenant_id="finance-analytics",
            request_type="quota_increase",
            description="Increase quota by 50GB for year-end processing"
        )

        assert request.status == "pending"  # Not auto-approved
        assert request.approved_by is None

    def test_auto_approve_same_org_access(self):
        """Test that same-org access grants are auto-approved."""
        portal = SelfServicePortal()

        request = portal.submit_request(
            tenant_id="finance-analytics",
            request_type="access_grant",
            description="Grant access to john.doe@company.com (same-org)"
        )

        assert request.status == "approved"
        assert request.approved_by == "AUTO"

    def test_manual_approve_cross_org_access(self):
        """Test that cross-org access grants require manual approval."""
        portal = SelfServicePortal()

        request = portal.submit_request(
            tenant_id="finance-analytics",
            request_type="access_grant",
            description="Grant access to jane.smith@external.com"
        )

        assert request.status == "pending"
        assert request.approved_by is None

    def test_auto_resolve_faq_question(self):
        """Test that FAQ questions are auto-resolved."""
        portal = SelfServicePortal()

        request = portal.submit_request(
            tenant_id="finance-analytics",
            request_type="support_ticket",
            description="How do I optimize my queries for better performance?"
        )

        assert request.status == "approved"  # Auto-resolved
        assert request.approved_by == "AUTO"

    def test_feature_request_always_manual(self):
        """Test that feature requests always require manual review."""
        portal = SelfServicePortal()

        request = portal.submit_request(
            tenant_id="finance-analytics",
            request_type="feature_request",
            description="Add support for Chinese language documents"
        )

        assert request.status == "pending"
        assert request.approved_by is None

    def test_get_tenant_dashboard(self):
        """Test tenant dashboard aggregates requests correctly."""
        portal = SelfServicePortal()

        # Submit multiple requests
        portal.submit_request("tenant1", "quota_increase", "Increase quota by 3GB")  # Auto-approved
        portal.submit_request("tenant1", "quota_increase", "Increase quota by 50GB")  # Pending
        portal.submit_request("tenant1", "feature_request", "Add new feature")  # Pending

        dashboard = portal.get_tenant_dashboard("tenant1")

        assert dashboard["tenant_id"] == "tenant1"
        assert dashboard["total_requests"] == 3
        assert dashboard["pending_requests"] == 2
        assert 30 < dashboard["auto_approved_percentage"] < 40  # 1/3 ≈ 33%


# ============================================================================
# PLATFORM MATURITY ASSESSMENT TESTS
# ============================================================================

class TestPlatformMaturityAssessment:
    """Tests for platform maturity assessment."""

    def test_assess_onboarding_dimension(self):
        """Test assessing onboarding maturity dimension."""
        assessment = PlatformMaturityAssessment()

        questions = [
            ("Onboarding process is documented", MaturityLevel.REPEATABLE),
            ("Onboarding is partially automated", MaturityLevel.REPEATABLE),
            ("Onboarding is fully automated", MaturityLevel.DEFINED),
            ("Onboarding time is measured and tracked", MaturityLevel.DEFINED),
        ]

        dimension = assessment.assess_dimension("onboarding", questions)

        assert dimension.name == "onboarding"
        assert dimension.current_level in [MaturityLevel.REPEATABLE, MaturityLevel.DEFINED]
        assert len(dimension.evidence) > 0
        assert len(dimension.next_actions) > 0

    def test_assess_self_service_dimension(self):
        """Test assessing self-service maturity dimension."""
        assessment = PlatformMaturityAssessment()

        questions = [
            ("Self-service portal exists", MaturityLevel.REPEATABLE),
            ("80% of tier 1 requests are self-service", MaturityLevel.DEFINED),
            ("Self-service success rate is measured", MaturityLevel.MANAGED),
        ]

        dimension = assessment.assess_dimension("self_service", questions)

        assert dimension.name == "self_service"
        assert isinstance(dimension.current_level, MaturityLevel)
        assert dimension.description == "Tenant self-service capabilities"

    def test_generate_report(self):
        """Test generating maturity assessment report."""
        assessment = PlatformMaturityAssessment()

        # Assess multiple dimensions
        assessment.assess_dimension("onboarding", [
            ("Onboarding process documented", MaturityLevel.REPEATABLE)
        ])
        assessment.assess_dimension("monitoring", [
            ("Basic monitoring exists", MaturityLevel.REPEATABLE),
            ("Per-tenant metrics available", MaturityLevel.DEFINED)
        ])

        report = assessment.generate_report()

        # Check report contains expected sections
        assert "PLATFORM GOVERNANCE MATURITY ASSESSMENT" in report
        assert "EXECUTIVE SUMMARY" in report
        assert "MATURITY BY DIMENSION" in report
        assert "PRIORITIZED NEXT ACTIONS" in report
        assert "onboarding" in report.lower()
        assert "monitoring" in report.lower()

    def test_empty_assessment_report(self):
        """Test generating report with no dimensions assessed."""
        assessment = PlatformMaturityAssessment()

        report = assessment.generate_report()

        assert "No dimensions assessed yet" in report


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests across multiple components."""

    def test_full_governance_workflow(self):
        """Test complete governance decision workflow."""
        # Step 1: Select operating model
        context = OrganizationalContext(
            num_tenants=45,
            tenant_sophistication=TenantSophistication.MEDIUM,
            compliance_level=ComplianceLevel.MODERATE,
            rate_of_change="medium"
        )

        selector = OperatingModelSelector()
        model = selector.choose_model(context)

        assert model == OperatingModel.HYBRID

        # Step 2: Calculate team size
        calculator = TeamSizingCalculator()
        recommendation = calculator.calculate(
            num_tenants=45,
            complexity="medium",
            operating_model=model
        )

        assert recommendation.recommended_team_size == 4  # 45 / 12 = 3.75 → 4

        # Step 3: Get SLA template
        sla = SLAManager.get_template("gold")

        assert sla.availability == 0.999

        # Step 4: Test self-service portal
        portal = SelfServicePortal()
        request = portal.submit_request(
            "finance",
            "quota_increase",
            "Increase quota by 8GB"
        )

        assert request.status == "approved"  # Auto-approved (<10GB)

        # All components work together
        assert True


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
