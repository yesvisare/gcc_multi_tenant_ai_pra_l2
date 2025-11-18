# L3 M14.4: Platform Governance & Operating Model

Complete platform governance framework for multi-tenant RAG systems in GCC environments. This module provides systematic tools for operating model selection, team sizing, self-service capabilities, SLA management, and maturity assessment based on production GCC experience with 20-100 tenant platforms.

**Part of:** TechVoyageHub L3 Production RAG Engineering Track
**Prerequisites:** M11-M14.3 (Tenant Registry, Data Isolation, Scale Optimization, Monitoring)
**SERVICE:** OFFLINE (Pure Python governance framework - no external APIs)

## What You'll Build

This module implements a complete platform operating model that determines HOW your multi-tenant RAG platform operates at scale. The framework enables GCC platforms to scale from 10 to 100+ tenants without linearly increasing platform team size through systematic governance, self-service, and escalation workflows.

**Key Capabilities:**
- **Operating Model Selector**: Choose the right model (centralized vs. federated vs. hybrid) based on organizational context
- **Team Sizing Calculator**: Calculate platform team size using 1:10-15 engineer:tenant ratio adjusted for complexity
- **Self-Service Portal**: Enable tenants to self-configure without tickets for 80% of tier 1 issues
- **Escalation Workflow**: Route complex issues through tenant champions to platform team only when necessary
- **SLA Templates**: Define service levels by tenant tier (Platinum/Gold/Silver)
- **Maturity Assessment**: Evaluate platform governance maturity across 6 dimensions (5 levels)

**Success Criteria:**
- Operating model chosen and documented with stakeholder approval (CFO, CTO, Compliance)
- Team size scales sublinearly with tenant count (1:12 ratio vs. 1:5 without governance)
- Self-service portal handles 80% of tier 1 requests without human intervention
- Escalation workflow routes requests efficiently (tier 1 → tier 2 → tier 3)
- Platform maturity assessed and improvement roadmap defined

## How It Works

```
┌───────────────────────────────────────────────────────────────────┐
│                   GCC PLATFORM GOVERNANCE FRAMEWORK                │
├───────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. Operating Model Decision                                      │
│     ┌─────────────┐   ┌───────────┐   ┌──────────────┐          │
│     │ Centralized │   │ Federated │   │ Hybrid       │          │
│     │ (1:5 ratio) │   │(1:20 ratio)│   │(1:12 ratio)  │          │
│     └─────────────┘   └───────────┘   └──────────────┘          │
│            ↓                 ↓                ↓                    │
│       Input: num_tenants, sophistication, compliance              │
│       Output: Chosen model + team size + explanation              │
│                                                                     │
│  2. Self-Service Portal (80% Tier 1 Auto-Approval)               │
│     ┌──────────────────────────────────────────────┐             │
│     │  Tenant Request                              │             │
│     │    ↓                                          │             │
│     │  Auto-Approval Rules (Policy Engine)         │             │
│     │    ├─ Quota <10GB → Approve                  │             │
│     │    ├─ Same-org access → Approve              │             │
│     │    ├─ FAQ question → Resolve                 │             │
│     │    └─ Else → Escalate to Tier 2              │             │
│     └──────────────────────────────────────────────┘             │
│                                                                     │
│  3. Escalation Workflow (3 Tiers)                                 │
│     Tier 1 (80%): Self-Service → Auto-resolved                   │
│     Tier 2 (15%): Tenant Champions → Human review                │
│     Tier 3 (5%): Platform Team → Expert handling                 │
│                                                                     │
│  4. SLA Tiers (Platinum/Gold/Silver)                              │
│     - Platinum: 99.99%, 15-min response, dedicated support       │
│     - Gold: 99.9%, 1-hour response, shared support               │
│     - Silver: 99%, 4-hour response, best-effort                   │
│                                                                     │
│  5. Maturity Assessment (5 Levels × 6 Dimensions)                 │
│     Dimensions: Onboarding, Self-Service, Incident Mgmt,         │
│                 Change Mgmt, Monitoring, Governance              │
│     Levels: Ad-hoc → Repeatable → Defined → Managed → Optimized │
└───────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Clone and Setup
```bash
git clone <repo_url>
cd gcc_mt_m14_v3
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env if you want to override defaults (optional)
# OFFLINE=true (default - no external services needed)
```

### 4. Run Tests
```bash
# Windows PowerShell
$env:PYTHONPATH=$PWD; pytest -q

# Or use script
./scripts/run_tests.ps1
```

### 5. Start API
```bash
# Windows PowerShell
$env:PYTHONPATH=$PWD; uvicorn app:app --reload

# Or use script
./scripts/run_api.ps1
```

API will be available at http://localhost:8000
- Swagger docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### 6. Explore Notebook
```bash
jupyter lab notebooks/L3_M14_Operations_Governance.ipynb
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OFFLINE` | No | `true` | Operating mode (always true - no external services) |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) |
| `AVG_ENGINEER_SALARY_INR` | No | `3000000` | Average platform engineer salary in INR (₹30L) |
| `CHAMPION_COST_PER_HOUR_INR` | No | `2000` | Champion time cost in INR (₹2000/hour) |
| `SMALL_SCALE_THRESHOLD` | No | `10` | Tenant count threshold for small scale (<10) |
| `LARGE_SCALE_THRESHOLD` | No | `50` | Tenant count threshold for large scale (>50) |
| `SELF_SERVICE_TARGET_PERCENTAGE` | No | `80` | Target percentage for tier 1 self-service (80%) |

## Common Failures & Fixes

| Failure | Cause | Fix |
|---------|-------|-----|
| **Centralized Bottleneck** | 25+ tenants with centralized model, no self-service | Build self-service portal (80% reduction in support load), invest ₹15L for 4-month payback |
| **Federated Chaos** | 60 tenants with inconsistent configs, 12 security issues | Move to Hybrid with guardrails (OPA policies, cost limits), standardize on 3 approved configurations |
| **Hybrid Without Champions** | Champions are VPs with no time (15 min/week vs. 2-4 hours needed) | Re-scope to senior engineers with 10% time allocation + training + quarterly recognition |
| **Self-Service Plateau** | Adoption stuck at 60-70%, won't reach 80% | Accept 65-70% is realistic (Type 1: "Just fix it" 10%, Type 2: Edge cases 10%, Type 3: Compliance paranoid 5%) |
| **No Operating Model Decision** | Ad-hoc chaos, tenants don't know how to get help | Document operating model (1-3 pages), communicate to all tenants, publish RACI matrix |
| **Understaffed Platform Team** | 50 tenants with 3 engineers (should be 5), ticket backlog 3 weeks | Hire to 1:12 ratio, build self-service (60% reduction), or reduce tenant count |
| **No Self-Service** | 400 tickets/month × 60% could be automated = 120 hours/month wasted | Build portal (3-month project, ₹15L), payback in 4 months, ₹48L/year savings |
| **Unclear Escalation** | 40% of tickets bounced between champion and platform team | Create escalation decision tree (tier 1: <10GB quota, tier 2: 10-50GB, tier 3: >50GB + bugs) |
| **SLA Mismatch** | Promised 99.99% / 15-min response, delivering 99% / 4-hour | Introduce tiered SLAs (Platinum/Gold/Silver), set based on actual capacity not aspirations |

## Decision Card

### When to Use Platform Governance Framework

**✓ Implement Formal Governance:**
- 10+ tenants with growth expected
- Multiple business units with different requirements
- Long-term platform (multi-year roadmap)
- Compliance requirements exist (audit trail needed)
- Platform team experiencing bottleneck or burnout

**✗ Skip Formal Governance:**
- Fewer than 10 tenants (manual ops acceptable)
- All tenants same business unit (no isolation needs)
- Platform lifespan < 12 months (temporary solution)
- No compliance requirements (internal tools only)
- Manual operations not causing pain

### Operating Model Selection

**Centralized Model (1:5 ratio):**
- ✓ 5-20 tenants
- ✓ High compliance (SOX, HIPAA, finance/legal)
- ✓ Non-technical tenants (business users)
- ✓ Consistency more important than velocity
- **Cost:** 20 tenants = 4 engineers = ₹1.2Cr/year

**Federated Model (1:20 ratio):**
- ✓ 50+ tenants
- ✓ Tenants have dedicated engineering teams
- ✓ Low to moderate compliance
- ✓ Innovation speed critical
- **Cost:** 75 tenants = 3 engineers = ₹90L/year (platform only, tenants self-manage)

**Hybrid Model (1:12 ratio) - Most Common for GCC:**
- ✓ 10-100 tenants
- ✓ Mixed technical sophistication
- ✓ Moderate compliance requirements
- ✓ Need balance of control and velocity
- ✓ Can identify tenant champions (1 per BU, 2-4 hours/week)
- **Cost:** 50 tenants = 5 engineers + 50 champions = ₹1.5Cr + ₹50L = ₹2Cr/year

### Example Deployments

**Small GCC (20 tenants, low complexity, hybrid):**
- Platform team: 2 engineers (₹60L/year)
- Champions: 20 × ₹50K/year = ₹10L/year
- **Total:** ₹70L/year (₹3.5L per tenant)
- Comparison: Centralized would be 3 engineers = ₹90L (28% more)

**Medium GCC (50 tenants, medium complexity, hybrid):**
- Platform team: 5 engineers (₹1.5Cr/year)
- Champions: 50 × ₹1L/year = ₹50L/year
- **Total:** ₹2Cr/year (₹4L per tenant)
- Comparison: Centralized would be 10 engineers = ₹3Cr (50% more)

**Large GCC (100 tenants, high complexity, hybrid):**
- Platform team: 12 engineers (₹3.6Cr/year)
- Champions: 100 × ₹1L/year = ₹1Cr/year
- **Total:** ₹4.6Cr/year (₹4.6L per tenant)
- Comparison: Decentralized would be 100 engineers = ₹30Cr (6.5× more)

## Troubleshooting

### Service Disabled Mode
This module runs entirely offline (no external services required). All functionality is pure Python governance logic. If you see any errors about missing API keys, they can be safely ignored - this module doesn't need them.

### Import Errors
If you see `ModuleNotFoundError: No module named 'src.l3_m14_operations_governance'`, ensure:
```bash
$env:PYTHONPATH=$PWD  # Windows PowerShell
export PYTHONPATH=.   # Linux/Mac
```

### Tests Failing
Run tests with verbose output:
```bash
pytest -v tests/
```

All tests should pass (20+ test cases covering all major functions).

### API Not Starting
Check that port 8000 is not in use:
```bash
# Windows PowerShell
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess
```

### Notebook Kernel Issues
Ensure Jupyter kernel is installed:
```bash
python -m ipykernel install --user --name gcc_governance --display-name "GCC Governance"
```

## API Endpoints

### Operating Model Selection
```bash
POST /operating-model/select
{
  "num_tenants": 45,
  "tenant_sophistication": "medium",
  "compliance_level": "moderate",
  "rate_of_change": "medium"
}

Response:
{
  "chosen_model": "hybrid",
  "explanation": "HYBRID OPERATING MODEL SELECTED\n\nWhy this model:...",
  "team_size_recommendation": 4
}
```

### Team Sizing Calculation
```bash
POST /team-sizing/calculate
{
  "num_tenants": 50,
  "complexity": "medium",
  "operating_model": "hybrid"
}

Response:
{
  "recommended_team_size": 5,
  "engineer_to_tenant_ratio": "1:12",
  "annual_cost_inr": 15000000,
  "annual_cost_usd": 182926,
  "cost_per_tenant_inr": 300000,
  "cost_per_tenant_usd": 3658,
  "breakdown": {...},
  "alternatives_comparison": {...}
}
```

### SLA Templates
```bash
GET /sla/templates

Response:
{
  "comparison_table": "SLA TIER COMPARISON:\n\n...",
  "tiers": {
    "platinum": {
      "availability": 0.9999,
      "availability_downtime": "52 minutes/year",
      "response_time_p95_ms": 200,
      "support_response_minutes": 15,
      "incident_priority": "P0",
      "dedicated_support": true
    },
    "gold": {...},
    "silver": {...}
  }
}
```

## Project Structure

```
gcc_mt_m14_v3/
├── app.py                                      # FastAPI entrypoint
├── config.py                                   # Environment & configuration
├── requirements.txt                            # Python dependencies
├── .env.example                                # Environment template
├── .gitignore                                  # Git ignore rules
├── LICENSE                                     # MIT License
├── README.md                                   # This file
├── example_data.json                           # Sample organizational contexts
├── example_data.txt                            # Sample governance scenarios
│
├── src/                                        # Source code package
│   └── l3_m14_operations_governance/          # Python package
│       └── __init__.py                         # Core business logic (1500+ lines)
│
├── notebooks/                                  # Jupyter notebooks
│   └── L3_M14_Operations_Governance.ipynb     # Interactive walkthrough
│
├── tests/                                      # Test suite
│   └── test_m14_operations_governance.py      # Pytest tests (20+ test cases)
│
├── configs/                                    # Configuration files
│   └── example.json                            # Sample config placeholder
│
└── scripts/                                    # Automation scripts
    ├── run_api.ps1                             # Windows PowerShell: Start API
    └── run_tests.ps1                           # Windows PowerShell: Run tests
```

## Core Classes and Functions

### OperatingModelSelector
```python
from src.l3_m14_operations_governance import (
    OperatingModelSelector,
    OrganizationalContext,
    TenantSophistication,
    ComplianceLevel
)

# Create organizational context
context = OrganizationalContext(
    num_tenants=45,
    tenant_sophistication=TenantSophistication.MEDIUM,
    compliance_level=ComplianceLevel.MODERATE,
    rate_of_change="medium"
)

# Select operating model
selector = OperatingModelSelector()
model = selector.choose_model(context)  # Returns: OperatingModel.HYBRID

# Get detailed explanation
explanation = selector.explain_decision(context, model)
print(explanation)  # Multi-paragraph explanation for stakeholders

# Calculate team size
team_size = selector.calculate_team_size(model, 45, "medium")  # Returns: 4
```

### TeamSizingCalculator
```python
from src.l3_m14_operations_governance import TeamSizingCalculator, OperatingModel

calculator = TeamSizingCalculator()

# Calculate team size with full cost justification
recommendation = calculator.calculate(
    num_tenants=50,
    complexity="medium",
    operating_model=OperatingModel.HYBRID
)

print(f"Team size: {recommendation.recommended_team_size}")
print(f"Annual cost: ₹{recommendation.annual_cost_inr/10_000_000:.2f}Cr")
print(f"Per tenant: ₹{recommendation.cost_per_tenant_inr/100_000:.1f}L")

# Compare with decentralized
comparison = calculator.compare_with_decentralized(50, recommendation.annual_cost_inr)
print(comparison["narrative"])  # "Centralized platform saves ₹13.5 Cr/year (90% reduction)..."
```

### SLAManager
```python
from src.l3_m14_operations_governance import SLAManager

# Get SLA template for tenant tier
platinum = SLAManager.get_template("platinum")
print(f"Availability: {platinum.availability*100:.2f}%")
print(f"Downtime: {platinum.availability_downtime()}")

# Compare all tiers
comparison = SLAManager.compare_tiers()
print(comparison)  # Formatted table
```

### SelfServicePortal
```python
from src.l3_m14_operations_governance import SelfServicePortal

portal = SelfServicePortal()

# Submit request (auto-approval logic applies)
request = portal.submit_request(
    tenant_id="finance-analytics",
    request_type="quota_increase",
    description="Increase quota by 5GB"
)

print(f"Status: {request.status}")  # "approved" (auto-approved)
print(f"Approved by: {request.approved_by}")  # "AUTO"

# Get tenant dashboard
dashboard = portal.get_tenant_dashboard("finance-analytics")
print(f"Self-service rate: {dashboard['auto_approved_percentage']:.0f}%")
```

### PlatformMaturityAssessment
```python
from src.l3_m14_operations_governance import PlatformMaturityAssessment, MaturityLevel

assessment = PlatformMaturityAssessment()

# Assess onboarding maturity
questions = [
    ("Onboarding process documented", MaturityLevel.REPEATABLE),
    ("Onboarding is automated", MaturityLevel.DEFINED),
    ("Onboarding time tracked", MaturityLevel.DEFINED),
]

dimension = assessment.assess_dimension("onboarding", questions)
print(f"Current level: {dimension.current_level.name}")
print(f"Evidence: {dimension.evidence}")
print(f"Next actions: {dimension.next_actions}")

# Generate report for leadership
report = assessment.generate_report()
print(report)  # Executive summary + dimension breakdown + prioritized actions
```

## Real GCC Scenario (Production Example)

**Tech company GCC in Bangalore** providing RAG platform for global operations:

**Year 1 (10 tenants, centralized):**
- Team: 2 engineers
- Cost: ₹60L/year
- Performance: 2-day onboarding, 3-day ticket backlog, 95% satisfaction

**Year 2 (30 tenants, cracks appear):**
- Team: 2 engineers (hiring delayed)
- Requests: 150/month (5× increase)
- Problem: 2-week backlog, 10-day onboarding
- Fix: Hired 2 more engineers (4 total), built self-service portal (₹15L, 3 months)

**Year 2.5 (Self-service launch):**
- Portal reduced requests 60% (150 → 60)
- Backlog: 2 weeks → 3 days
- But: Still centralized bottleneck for features

**Year 3 (50 tenants, hybrid redesign):**
- Platform team: 5 engineers (tier 3 only)
- Tenant champions: 50 champions (1 per BU, 2-4 hours/week)
- Self-service: 80% tier 1 auto-approved
- Escalation: Tier 1 → Tier 2 → Tier 3

**Results after 6 months:**
- Request handling: 400 tier 1 (80%), 75 tier 2 (15%), 25 tier 3 (5%)
- Platform team workload: 25 hours/month (was 120 hours)
- Onboarding: 10 days → 1 day
- Satisfaction: 65% → 92%
- Cost: ₹2.5Cr total (vs. ₹4Cr if stayed centralized)

**Key learnings:**
1. Centralized works until ~15 tenants, then needs self-service
2. Self-service buys time until ~30 tenants, then needs champions
3. Hybrid works from 30-100 tenants with proper training
4. CFO/CTO/Compliance alignment took 3 months (critical, don't skip)

## Next Module

**M15: GCC Compliance Basics** - We move from governance to compliance:
- M15.1: Compliance Stack Overview (SOX + DPDPA + GDPR + Client Regulations)
- M15.2: Three-Layer Compliance (Parent Company, India Operations, Global Clients)
- M15.3: Multi-Jurisdictional Data Residency
- M15.4: Compliance Monitoring & Reporting

Driving question: "How do we handle compliance when our GCC platform must satisfy 4+ regulatory frameworks simultaneously?"

## Resources

- **Code repository:** github.com/techvoyagehub/gcc-governance
- **RACI template:** docs/governance/raci-matrix.xlsx
- **Champion training slides:** docs/governance/champion-training.pptx
- **Maturity assessment tool:** tools/maturity-assessment.py

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
1. Check Troubleshooting section above
2. Run tests with `pytest -v tests/`
3. Check API health at `/health` endpoint
4. Review logs in console output

This is production-ready governance tooling used by real GCCs to manage 50+ business units. Happy governing! 🚀
