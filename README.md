# L3 M11.2: Tenant Metadata & Registry Design

**Part of GCC Multi-Tenant Architecture Track**

Building a production-ready tenant registry system for multi-tenant RAG platforms serving 50+ business units.

## Overview

In multi-tenant RAG systems, **configuration drift** is a silent killer. When tenant metadata is scattered across environment files, YAML configs, and hardcoded constants, you get:

- **Configuration drift**: Finance has `max_users=100` in one file, `max_users=50` in another
- **No single source of truth**: Which config wins? Nobody knows
- **Operational nightmares**: Suspending a tenant requires manual updates across 7 systems
- **Compliance violations**: No audit trail of who changed what and when

This module solves these problems with a **production-ready Tenant Registry System** - your single source of truth for all tenant metadata, lifecycle management, and feature configuration.

**What You'll Build:**

A complete tenant registry system with five integrated capabilities:

1. **PostgreSQL Tenant Registry** - Single source of truth with 20+ attributes per tenant (identity, tier, limits, billing, lifecycle, health)
2. **Feature Flag Service** - Hierarchical evaluation system (tenant override > tier default > global default) for zero-downtime configuration changes
3. **Lifecycle State Machine** - Compliance-enforced state transitions (active ↔ suspended → archived → deleted) with retention policies
4. **Health Check Aggregation** - Multi-signal tenant health scoring from latency, error rates, query success, and storage utilization
5. **Cascading Operations** - Atomic transactional coordination across PostgreSQL, Vector DB, S3, Redis, and Monitoring systems

**Learning Outcomes:**

By completing this module, you will be able to:

- Design tenant metadata schemas with proper normalization and validation
- Implement lifecycle state machines with compliance-enforced transitions
- Build hierarchical feature flag systems enabling zero-downtime changes
- Execute transactional cascading operations across multiple systems
- Calculate tenant health scores from multi-signal monitoring data
- Design audit logging systems for compliance and troubleshooting

## How It Works

### Architecture Overview

The Tenant Registry acts as the **authoritative metadata repository** for your multi-tenant platform - analogous to an HR database for a company:

```
┌─────────────────────────────────────────────────────────────┐
│                   Tenant Registry (PostgreSQL)              │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │ Identity │   Tier   │  Limits  │ Billing  │Lifecycle │  │
│  ├──────────┼──────────┼──────────┼──────────┼──────────┤  │
│  │tenant_id │platinum  │max_users │cost_ctr  │ active   │  │
│  │  name    │gold      │max_docs  │monthly_$ │suspended │  │
│  │  email   │silver    │max_query │chargeback│migrating │  │
│  │          │bronze    │sla_target│          │archived  │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
    ┌───────────▼──────────┐    ┌──────────▼──────────┐
    │  Feature Flag Service│    │  Lifecycle Manager  │
    │  (Redis Cache)       │    │  (State Machine)    │
    │                      │    │                     │
    │  Hierarchy:          │    │  Valid Transitions: │
    │  Tenant > Tier >     │    │  ACTIVE ↔ SUSPENDED │
    │  Global              │    │  SUSPENDED→ARCHIVED │
    └──────────────────────┘    │  ARCHIVED → DELETED │
                                └─────────────────────┘
                                          │
                        ┌─────────────────┴─────────────────┐
                        │  Cascading Operations Coordinator │
                        │  (Atomic Multi-System Updates)    │
                        └───────────────────────────────────┘
                                          │
        ┌─────────────┬─────────────┬────┴────┬─────────────┬─────────────┐
        │             │             │         │             │             │
    ┌───▼───┐  ┌──────▼─────┐  ┌───▼────┐ ┌──▼────┐  ┌────▼─────┐  ┌───▼────┐
    │ PG RLS│  │ Vector DB  │  │   S3   │ │ Redis │  │Monitoring│  │  Audit │
    │Policies│  │ Namespace  │  │ Bucket │ │ Cache │  │  Alerts  │  │  Log   │
    └───────┘  └────────────┘  └────────┘ └───────┘  └──────────┘  └────────┘
```

**Five Integrated Capabilities:**

1. **PostgreSQL Tenant Registry**
   - Single source of truth with 20+ attributes per tenant
   - Row-level security (RLS) for database-level isolation
   - CHECK constraints for data validation
   - JSONB columns for flexible metadata
   - Automated audit triggers

2. **Feature Flag Service**
   - Three-tier hierarchical evaluation:
     - **Tenant override**: `tenant_flags["finance"]["advanced_analytics"] = true`
     - **Tier default**: `tier_defaults["platinum"]["advanced_analytics"] = true`
     - **Global default**: `global_defaults["advanced_analytics"] = false`
   - Redis caching for sub-millisecond evaluation
   - Cache invalidation on flag updates
   - Zero-downtime configuration changes

3. **Lifecycle State Machine**
   - Five states: `active` ↔ `suspended` → `archived` → `deleted` ← `migrating`
   - Valid transitions enforced programmatically
   - Compliance-required retention periods (archived data kept for audit)
   - Prevents invalid transitions (e.g., `active` → `deleted` requires intermediate states)

4. **Health Check Aggregation**
   - Multi-signal health scoring (0-100 scale):
     - API latency (P95 < 500ms = healthy)
     - Error rate (< 1% = healthy)
     - Query success rate (> 95% = healthy)
     - Storage utilization (< 90% = healthy)
   - Automatic degradation detection
   - Alert thresholds for warning/critical states

5. **Cascading Operations**
   - Atomic multi-system coordination when suspending/activating tenants
   - Propagates changes across 5 systems:
     - PostgreSQL RLS policies
     - Vector DB namespace access
     - S3 bucket permissions
     - Redis cache invalidation
     - Monitoring alert rules
   - Rollback capability on partial failure
   - Immutable audit log for compliance

## Installation

```bash
# Clone repository
git clone <repo-url>
cd gcc_multi_tenant_ai_pra_l2

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database connections (optional for demo)

# Setup PostgreSQL (optional for demo)
# The code includes schema definitions but works without live DB
# See config.py for PostgreSQL schema reference
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | `postgresql://localhost:5432/tenant_registry` | PostgreSQL connection |
| `REDIS_URL` | No | `redis://localhost:6379/0` | Redis connection |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `CACHE_TTL_CRITICAL` | No | `60` | Cache TTL for critical fields (seconds) |
| `CACHE_TTL_STANDARD` | No | `300` | Cache TTL for standard fields (seconds) |
| `CACHE_TTL_STATIC` | No | `3600` | Cache TTL for static fields (seconds) |

**Note:** This module demonstrates tenant registry design patterns. Live database connections are optional for learning purposes.

## Usage

### API Server

```bash
# Start the API (PowerShell on Windows)
.\scripts\run_api.ps1

# Or using uvicorn directly
python -m uvicorn app:app --reload

# API will be available at:
# - Endpoint: http://localhost:8000
# - Docs: http://localhost:8000/docs
```

**Example API Calls:**

```bash
# Create tenant
curl -X POST http://localhost:8000/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "finance_dept",
    "tenant_name": "Finance Department",
    "tier": "platinum",
    "max_users": 100,
    "max_documents": 50000,
    "max_queries_per_day": 10000,
    "sla_target": 0.9999,
    "support_level": "24/7"
  }'

# Get tenant
curl http://localhost:8000/tenants/finance_dept

# List all tenants
curl http://localhost:8000/tenants

# Filter by status
curl "http://localhost:8000/tenants?status=active"

# Filter by tier
curl "http://localhost:8000/tenants?tier=platinum"

# Suspend tenant (cascading operations)
curl -X POST http://localhost:8000/tenants/finance_dept/suspend

# Activate tenant
curl -X POST http://localhost:8000/tenants/finance_dept/activate

# Set feature flag (tier-level)
curl -X POST http://localhost:8000/feature-flags \
  -H "Content-Type: application/json" \
  -d '{
    "feature_name": "advanced_analytics",
    "enabled": true,
    "scope": "tier",
    "scope_id": "platinum"
  }'

# Evaluate feature flag for tenant
curl http://localhost:8000/feature-flags/finance_dept/advanced_analytics

# Update health score
curl -X POST http://localhost:8000/tenants/finance_dept/health \
  -H "Content-Type: application/json" \
  -d '{
    "latency_p95": 350.5,
    "error_rate": 0.01,
    "query_success_rate": 0.98,
    "storage_utilization": 0.75
  }'

# Get registry statistics
curl http://localhost:8000/statistics
```

### Jupyter Notebook

```bash
jupyter notebook notebooks/L3_M11_Multi_Tenant_Foundations.ipynb
```

The notebook provides an interactive walkthrough of all 12 sections covering the complete system architecture.

### Python Package

```python
from src.l3_m11_multi_tenant_foundations import (
    TenantRegistry, TenantStatus, FeatureFlag
)

# Initialize registry
registry = TenantRegistry()

# Create tenant
tenant = registry.create_tenant({
    "tenant_id": "legal_dept",
    "tenant_name": "Legal Department",
    "tier": "platinum",
    "max_users": 50,
    "max_documents": 10000
})

# Set feature flag
flag = FeatureFlag(
    feature_name="advanced_analytics",
    enabled=True,
    scope="tier",
    scope_id="platinum"
)
registry.feature_service.set_flag(flag)

# Evaluate feature
enabled = registry.feature_service.evaluate("legal_dept", "advanced_analytics", "platinum")
print(f"Advanced analytics enabled: {enabled}")

# Suspend tenant (cascading)
result = registry.suspend_tenant("legal_dept", reason="Non-payment")
print(f"Suspension completed: {result}")
```

## Project Structure

```
gcc_multi_tenant_ai_pra_l2/
├── app.py                              # FastAPI entrypoint (REST API)
├── config.py                           # Environment & database config
├── requirements.txt                    # Pinned dependencies
├── .env.example                        # Environment template
├── .gitignore                          # Python defaults
├── LICENSE                             # MIT License
├── README.md                           # This file
├── example_data.json                   # Sample tenant configurations
│
├── src/                                # Source code package
│   └── l3_m11_multi_tenant_foundations/
│       └── __init__.py                 # Core business logic
│
├── notebooks/                          # Jupyter notebooks
│   └── L3_M11_Multi_Tenant_Foundations.ipynb
│
├── tests/                              # Test suite
│   └── test_m11_multi_tenant_foundations.py
│
├── configs/                            # Configuration files
│   └── example.json                    # Sample config
│
└── scripts/                            # Automation scripts
    ├── run_api.ps1                     # Start API (Windows)
    └── run_tests.ps1                   # Run tests (Windows)
```

## Concepts Covered

### 1. Tenant Metadata Schema Design

**20+ attributes across five categories:**

- **Identity**: `tenant_id`, `tenant_name`, billing email
- **Tier**: `platinum`, `gold`, `silver`, `bronze` (determines default limits and features)
- **Limits**: `max_users`, `max_documents`, `max_queries_per_day`
- **Billing**: Cost center, monthly charges, chargeback allocation
- **Lifecycle**: Current state (`active`, `suspended`, etc.)
- **Health**: Aggregate health score (0-100)

**Design principles:**
- Single source of truth (no duplicate configs)
- Normalization (tier defaults in separate table)
- Validation (CHECK constraints on enums and ranges)
- Flexibility (JSONB for tenant-specific metadata)

### 2. Lifecycle State Machines

**Five states with compliance-enforced transitions:**

```
    ACTIVE ←────────────┐
      ↕                 │
  SUSPENDED            │
      ↓                 │
  ARCHIVED          MIGRATING
      ↓
   DELETED (terminal)
```

**Valid transitions:**
- `ACTIVE` ↔ `SUSPENDED` (temporary suspension, e.g., non-payment)
- `ACTIVE` → `MIGRATING` (data migration in progress)
- `MIGRATING` → `ACTIVE` or `SUSPENDED`
- `SUSPENDED` → `ARCHIVED` (long-term retention for compliance)
- `ARCHIVED` → `DELETED` (final deletion after retention period)

**Why state machines?**
- Prevents invalid operations (can't delete active tenant without archiving first)
- Compliance requirements (data must be archived before deletion)
- Audit trail (every transition logged with actor and reason)

### 3. Hierarchical Feature Flags

**Three-tier evaluation system:**

1. **Tenant override** (highest priority): Enable beta features for specific tenants
2. **Tier default** (middle priority): All platinum tenants get advanced analytics
3. **Global default** (lowest priority): All tenants get basic search

**Example:**
```python
# Global: advanced_analytics = False
# Tier platinum: advanced_analytics = True
# Tenant marketing: advanced_analytics = True (override)

evaluate("finance", "advanced_analytics", tier="platinum")  # → True (tier)
evaluate("marketing", "advanced_analytics", tier="silver")  # → True (tenant override)
evaluate("ops", "advanced_analytics", tier="silver")        # → False (global)
```

**Why hierarchical?**
- Zero-downtime rollouts (enable for 10% → 50% → 100% of tenants)
- Tenant-specific customization without code deployment
- Cost management (expensive features only for premium tiers)

### 4. Cascading Operations

**Atomic multi-system coordination:**

When suspending a tenant, changes propagate across 5 systems simultaneously:

1. **PostgreSQL**: Update RLS policies to block queries
2. **Vector DB**: Revoke namespace access (Pinecone/Qdrant)
3. **S3**: Update bucket IAM policies to prevent uploads/downloads
4. **Redis**: Invalidate all cache entries for tenant
5. **Monitoring**: Update alert rules (stop alerting on suspended tenant)

**Transactional guarantees:**
- All-or-nothing: If any system fails, rollback all changes
- Idempotent: Can safely retry operations
- Auditable: Every operation logged with timestamp and results

### 5. Health Score Aggregation

**Multi-signal tenant health monitoring:**

```python
score = 100

# Latency penalty: -10 points per 100ms over 500ms
if latency_p95 > 500:
    score -= min(30, (latency_p95 - 500) / 100 * 10)

# Error rate penalty: -20 points per 1% error rate
score -= min(40, error_rate * 100 * 20)

# Query success penalty: -30 points if <95% success
if query_success_rate < 0.95:
    score -= min(30, (0.95 - query_success_rate) * 100 * 3)

# Storage penalty: -20 points if >90% utilized
if storage_utilization > 0.9:
    score -= 20
```

**Health score uses:**
- Alert thresholds (warn at <70, critical at <50)
- SLA compliance tracking
- Capacity planning (identify tenants approaching limits)
- Proactive support (reach out to unhealthy tenants)

## Reality Check: Feature Flags at Scale

**From Script Part 2, Section 5: The Myth vs. Reality**

### The Myth

"Feature flags solve everything - just put every tenant difference behind a flag for infinite flexibility!"

### The Reality

**Flag Explosion:**
- Month 1: 20 flags (manageable)
- Month 6: 150 flags (getting messy)
- Month 18: 500+ flags (complete chaos)

**Performance Degradation:**
- Evaluating 500 flags adds **250ms latency** to every request
- Violates SLA requirements (<500ms response time)
- **Cost impact**: ₹15,000/month just evaluating flags

**Testing Impossibility:**
- 2^500 possible flag combinations
- Exceeds atoms in observable universe (10^80)
- Cannot test all combinations

**Dependency Hell:**
- Flag A requires Flag B
- Flag B conflicts with Flag C
- Flag C depends on Flag A being disabled
- Result: Impossible configuration matrices

### The Solution: Strategic Flag Usage

**Flags are for TEMPORARY rollouts, not PERMANENT configuration:**

- ✅ **Good use**: Rolling out new feature to 10% → 50% → 100% of tenants over 2 weeks
- ❌ **Bad use**: Using flags to configure max_users limits (that's configuration, not a flag)

**Rule of thumb:** If a flag will exist >90 days, it's configuration, not a flag. Move it to the database.

**Cost savings:** This discipline saved ₹12 lakh/year ($15K/year) at one GCC platform.

## Alternative Solutions

**From Script Part 2, Section 6: When to Use What**

### Alternative 1: Manual Configuration Files

**Best for:** <5 tenants with identical requirements

**How it works:**
```yaml
# tenants.yaml
finance:
  tier: platinum
  max_users: 100

legal:
  tier: gold
  max_users: 50
```

**Pros:**
- Simple, no infrastructure
- Version controlled (Git)
- Easy to audit (diff history)

**Cons:**
- Requires deployment for changes
- No runtime validation
- Doesn't scale beyond ~5 tenants

**Cost:** ₹0 infrastructure (just developer time)

### Alternative 2: Centralized Database Registry (This Module)

**Best for:** 10-100 tenants with different requirements

**Pros:**
- Single source of truth
- Runtime updates (no deployment)
- Audit logging built-in
- Scales to 100+ tenants

**Cons:**
- Database becomes critical dependency
- Requires high availability setup
- Cache invalidation complexity

**Cost:** ₹11 lakh/year (PostgreSQL + Redis + monitoring)

### Alternative 3: Service Mesh (Istio)

**Best for:** 50+ tenants with complex routing requirements

**Pros:**
- Traffic routing at infrastructure level
- Built-in observability
- A/B testing capabilities
- Scales to 500+ tenants

**Cons:**
- High operational complexity
- Steep learning curve
- Expensive infrastructure

**Cost:** ₹24.6 lakh/year (Kubernetes + Istio + monitoring)

### Alternative 4: Managed SaaS (Frontegg, Auth0)

**Best for:** <20 tenants, limited customization needs

**Pros:**
- Fast setup (hours, not weeks)
- Vendor maintains infrastructure
- Built-in UI for tenant management

**Cons:**
- Vendor lock-in
- Limited customization
- Expensive at scale

**Cost:** $500-5000/month ($6K-60K/year)

### Recommendation for GCC Contexts (20-100 Business Units)

**Use Centralized Database Registry (this module) when:**
- ✅ 20+ tenants with different requirements
- ✅ Need compliance audit trails
- ✅ Multi-tier service offerings
- ✅ Chargeback/cost attribution needed

**Break-even analysis:**
- **Small GCC (20 tenants)**: Month 8 in Year 1
- **Medium GCC (50 tenants)**: Month 6 in Year 1
- **Large GCC (100 tenants)**: Month 9 in Year 1

## Common Failures & Solutions

**From Script Part 2, Section 8: Production Failure Scenarios**

### Failure 1: Database Outage Takes Platform Offline

**What Happened:**
PostgreSQL crashed at 10:03 AM. All 50 tenants lost access for 47 minutes. Platinum SLA allows only 4.38 minutes/month downtime.

**Impact:**
- SLA breach for 15 platinum tenants
- ₹5 lakh penalty clause triggered
- Executive escalation

**Prevention:**
Three-layer defense:

1. **PostgreSQL replicas** with auto-failover (30-second failover time)
2. **Redis cache fallback** (30-minute TTL, accepts stale data during outage)
3. **Hourly disk-based backup** (degraded mode from last snapshot)

**Result:** Outage reduced from 47 minutes to 30 seconds.

### Failure 2: Cache Inconsistency - Suspended Tenant Still Active

**What Happened:**
Admin suspended Finance tenant at 10:00 AM. PostgreSQL updated, but Redis cache wasn't invalidated. Tenant continued running unauthorized queries for 5 minutes.

**Cost:** ₹48,000 in compute charges before automated shutdown.

**Root Cause:** Cache invalidation not triggered on suspension.

**Fix: Active Cache Invalidation Pattern**

```python
def suspend_tenant(tenant_id):
    # 1. Update database
    db.update(tenant_id, status='suspended')

    # 2. CRITICAL: Invalidate cache immediately
    redis.delete(f"tenant:{tenant_id}:*")

    # 3. Increment version number (for multi-region cache)
    redis.incr(f"tenant:{tenant_id}:version")

    # 4. Broadcast invalidation via pub/sub
    redis.publish("tenant_updates", {"tenant_id": tenant_id, "action": "invalidate"})

    # 5. VERIFY invalidation succeeded
    assert redis.get(f"tenant:{tenant_id}:status") is None
```

### Failure 3: Stale Tenant Limits Produce False Alerts

**What Happened:**
Legal upgraded from silver (5K queries/day) to gold (20K queries/day) at 10:00 AM. Monitoring service cached old limits for 30 minutes. At 10:15 AM, tenant hit 8,500 queries → false alert "170% over quota!"

**Fix: Tiered Cache TTL Strategy**

```python
CACHE_TTL = {
    "critical_fields": 60,      # 1 minute (limits, status, tier)
    "standard_fields": 300,     # 5 minutes (metadata, configs)
    "static_fields": 3600       # 1 hour (tier definitions)
}
```

**Lesson:** Always verify alerts against live database before sending.

### Failure 4: Permission Bypass - Cross-Tenant Data Leak

**What Happened:**
Legal admin queried registry API with arbitrary `tenant_id`, successfully retrieving Finance's billing email, monthly costs, and user counts.

**Prevention: Strict Authorization Checks**

```python
@app.get("/tenants/{tenant_id}")
async def get_tenant(tenant_id: str, current_user: User = Depends(get_current_user)):
    # CRITICAL: Verify user belongs to requested tenant
    if not user_has_access(current_user, tenant_id):
        raise HTTPException(403, "Access denied")

    # AUDIT: Log all registry API calls
    audit_log.write({
        "user": current_user.email,
        "action": "get_tenant",
        "tenant_id": tenant_id,
        "timestamp": datetime.now()
    })

    return get_tenant_data(tenant_id)
```

### Failure 5: Audit Log Tampering - Compliance Violation

**What Happened:**
Compliance investigation required audit trail proving who suspended which tenant. Logs were manually edited, creating regulatory violation risk.

**Prevention: Immutable Audit Logs**

```python
# PostgreSQL table with append-only constraint
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),
    tenant_id VARCHAR(255),
    operation VARCHAR(100),
    actor VARCHAR(255),
    previous_state JSONB,
    new_state JSONB,
    reason TEXT,
    signature VARCHAR(512)  -- Cryptographic signature
);

# Prevent updates/deletes
REVOKE UPDATE, DELETE ON audit_log FROM app_user;
GRANT INSERT, SELECT ON audit_log TO app_user;

# Replicate to separate, read-only system
# (prevents tampering via SQL injection)
```

**Key Takeaway:** Treat audit logs as immutable compliance artifacts, not debugging convenience.

## GCC Enterprise Context

**From Script Part 3, Section 9C: Production Considerations**

### What's Different in GCC Multi-Tenancy?

**1. Tenant = Business Unit (Not External Customer)**

In GCC platforms, tenants are internal departments:

- **Legal Department**: 50 attorneys, 10K privileged documents, attorney-client privilege enforcement
- **Finance Trading**: 100 analysts, real-time market data, SOX compliance, MNPI controls
- **HR Operations**: 30 recruiters, 50K employee records, GDPR Article 9 protections
- **Global Operations**: 75 coordinators, operational playbooks, ISO 27001 compliance

**Implications:**
- Shared users across tenants (same employee works in multiple departments)
- Cross-tenant access control (Senior VP needs access to Finance + Legal + HR)
- Internal SLAs (penalties are budget reallocations, not legal damages)

**2. Shared Users Across Tenants**

External SaaS: 1 user = 1 tenant (customer isolation)
GCC Platform: 1 user = N tenants (role-based department access)

**Example:**
```
Alice Johnson (Senior VP, Finance & Legal)
├── Finance Department (Analyst role)
│   └── Access: Query financial reports
└── Legal Department (Reviewer role)
    └── Access: Review contracts

Tenant context switching via SSO attribute:
GET /tenants?user_id=alice.johnson
→ Returns: [finance_dept, legal_dept]
```

**3. Cost Attribution & Chargeback**

**Monthly cost calculation formula:**
```
cost = (api_calls × ₹0.50) + (storage_gb × ₹200) + (compute_hours × ₹50)
```

**Example chargeback report:**

| Tenant | API Calls | Storage (GB) | Compute (hrs) | Monthly Cost (₹) |
|--------|-----------|--------------|---------------|------------------|
| Legal | 125,000 | 500 | 2,400 | ₹2,48,000 |
| Finance | 320,000 | 1,200 | 3,600 | ₹4,70,000 |
| HR | 45,000 | 150 | 800 | ₹85,500 |
| **Total** | | | | **₹8,03,500** |

**Budget variance tracking:**
- Legal: Budgeted ₹2.5L, actual ₹2.48L → **0.8% under budget** ✅
- Finance: Budgeted ₹4.2L, actual ₹4.7L → **11.9% over budget** ⚠️
- HR: Budgeted ₹1L, actual ₹85.5K → **14.5% under budget** ✅

**CFO reporting:** Monthly chargeback reports by cost center for budget reconciliation.

**4. Three-Layer Compliance**

Each tenant has **different** regulatory requirements:

**Legal Department:**
- Attorney-client privilege (ACP) enforcement
- Document retention policies (7-year minimum)
- Conflict-of-interest screening
- No cross-tenant data leakage

**Finance Department:**
- SOX compliance (financial reporting accuracy)
- SEC regulations (material non-public information - MNPI)
- Real-time trading data isolation
- Audit trail for every query

**HR Department:**
- GDPR Article 9 (special category data - employee health, biometrics)
- India DPDP Act compliance
- Right to erasure (RTBF) workflows
- Consent management

**Implication:** Tenant registry must store compliance requirements per tenant and enforce different policies.

## Decision Card

**From Script Part 3, Section 10: When to Build vs. Buy**

### Use Tenant Registry When

✅ **20+ tenants** with different requirements (different tiers, limits, or features)
✅ **Feature flag management** at scale (need hierarchical evaluation)
✅ **Compliance requires audit trails** (SOX, GDPR, SEC)
✅ **Multi-tier service offerings** (platinum/gold/silver with different limits)
✅ **Chargeback/cost attribution** needed (allocate costs to business units)
✅ **Lifecycle management** required (suspend/archive/delete workflows)

### Avoid Tenant Registry When

❌ **<5 tenants** (manual config files sufficient)
❌ **All tenants identical** (no customization needed - use single-tenant architecture)
❌ **No compliance requirements** (startup/prototype without audit needs)
❌ **Budget <₹50L/year** (ROI doesn't justify infrastructure costs)
❌ **Using managed SaaS** (Frontegg, Auth0 handle multi-tenancy)

### Cost-Benefit Analysis

**Build Costs (Centralized Registry):**

| Component | Small GCC (20 tenants) | Medium GCC (50 tenants) | Large GCC (100 tenants) |
|-----------|------------------------|-------------------------|-------------------------|
| PostgreSQL (HA) | ₹15K/month | ₹25K/month | ₹45K/month |
| Redis Cluster | ₹8K/month | ₹15K/month | ₹30K/month |
| Monitoring | ₹5K/month | ₹10K/month | ₹20K/month |
| Developer Time | ₹17K/month | ₹75K/month | ₹1.65L/month |
| **Total** | **₹45K/month** | **₹1.25L/month** | **₹3.6L/month** |
| **Annual** | **₹5.4L/year** | **₹15L/year** | **₹43.2L/year** |

**Buy Costs (Managed SaaS - Frontegg/Auth0):**

| Tier | Price | Tenants Supported |
|------|-------|-------------------|
| Startup | $500/month | Up to 10 tenants |
| Growth | $2,000/month | Up to 50 tenants |
| Enterprise | $5,000/month | Unlimited |

**Break-Even Analysis:**

- **Small GCC (20 tenants)**: Break-even at **Month 8 in Year 1**
- **Medium GCC (50 tenants)**: Break-even at **Month 6 in Year 1**
- **Large GCC (100 tenants)**: Break-even at **Month 9 in Year 1**

**Recommendation:** Build registry if >20 tenants AND need custom compliance/chargeback.

## PractaThon™ Connection

**From Script Part 3, Section 11: Hands-On Mission**

### Mission

Build a tenant registry that manages **5 tenants** with different tiers, enforces lifecycle transitions, and evaluates feature flags hierarchically.

### Acceptance Criteria

**1. Create 5 Tenants with Different Tiers:**
- 1 platinum tenant (Finance Department)
- 2 gold tenants (Legal Department, Global Operations)
- 2 silver tenants (HR Operations, Marketing)

**2. Configure Tier-Specific Feature Flags:**
- Global default: `basic_search=true`, `advanced_analytics=false`
- Platinum tier: `advanced_analytics=true`, `dedicated_namespace=true`, `priority_support=true`
- Gold tier: `advanced_analytics=true`, `shared_namespace=true`
- Silver tier: `basic_analytics=true`, `shared_namespace=true`
- Tenant override: Marketing (silver) gets `advanced_analytics=true`

**3. Demonstrate Lifecycle Transitions:**
- Transition HR from `active` → `suspended` (valid)
- Attempt transition Finance from `active` → `deleted` (should fail - invalid)
- Transition Legal from `active` → `suspended` → `archived` (valid)

**4. Show Cascading Suspension:**
- Suspend Finance tenant
- Verify changes propagated to:
  - PostgreSQL (RLS updated)
  - Vector DB (namespace access revoked)
  - S3 (bucket permissions updated)
  - Redis (cache cleared)
  - Monitoring (alerts updated)

**5. Calculate Tenant Health Scores:**
- Finance: P95 latency=350ms, error_rate=0.5%, success=98%, storage=70% → Score = 100
- Legal: P95 latency=600ms, error_rate=2%, success=95%, storage=85% → Score = ~70
- HR: P95 latency=1200ms, error_rate=10%, success=80%, storage=95% → Score = ~20

### Validation Tests

Run the included test suite:

```bash
pytest tests/test_m11_multi_tenant_foundations.py
```

**Required passing tests:**
- [ ] Invalid lifecycle transitions rejected (e.g., `active` → `deleted`)
- [ ] Feature flag hierarchy works correctly (tenant > tier > global)
- [ ] Suspension propagates to all 5 systems
- [ ] Health scores update based on metrics
- [ ] Audit logs capture all changes

### Deliverables

1. **Working API** accepting tenant CRUD operations
2. **5 tenants created** with correct tier configurations
3. **Feature flags evaluated** hierarchically
4. **Lifecycle transitions** enforced by state machine
5. **Cascading suspension** demonstrated across systems
6. **Health scores** calculated from mock metrics
7. **Audit log** showing all operations

## Testing

Run the complete test suite:

```bash
# Run all tests (PowerShell on Windows)
.\scripts\run_tests.ps1

# Or using pytest directly
pytest -v tests/

# Run with coverage report
pytest --cov=src --cov-report=term-missing tests/

# Run specific test
pytest tests/test_m11_multi_tenant_foundations.py::test_lifecycle_valid_transition_active_to_suspended
```

**Test coverage includes:**
- Tenant CRUD operations (create, read, update, delete, list)
- Lifecycle state machine transitions (valid and invalid)
- Feature flag hierarchical evaluation
- Cascading operations across systems
- Health score calculation from metrics
- Registry statistics and filtering

## Troubleshooting

### Common Issues

**1. Database Connection Errors**

```
Error: psycopg2.OperationalError: could not connect to server
```

**Solution:** This module works without live database connections (demo mode). If you want to use PostgreSQL:

```bash
# Install PostgreSQL
# Create database
createdb tenant_registry

# Apply schema (see config.py for SQL)
psql tenant_registry < schema.sql
```

**2. Feature Flag Cache Issues**

```
Warning: Feature flag showing stale value after update
```

**Solution:** Cache invalidation is automatic, but you can manually clear:

```python
registry.feature_service._invalidate_cache()
```

**3. Lifecycle Transition Failures**

```
ValueError: Invalid lifecycle transition: active → deleted
```

**Solution:** Follow valid transition paths:
- `active` → `suspended` → `archived` → `deleted`
- Use `get_valid_transitions()` to check allowed targets

**4. API Server Won't Start**

```
Error: Address already in use (port 8000)
```

**Solution:** Kill existing process or change port:

```bash
# Kill process on port 8000
# Windows PowerShell:
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process

# Or run on different port
uvicorn app:app --port 8001
```

## Resources

### Script References

- **Part 1 (Sections 1-4)**: [Introduction, Concepts, Tech Stack, Technical Implementation](https://github.com/yesvisare/gcc_multi_tenant_ai_pra_l2/blob/main/Augmented_GCC_MultiTenant_M11_2_Tenant_Metad_Part1.md)
- **Part 2 (Sections 5-8)**: [Reality Check, Alternatives, Failures](https://github.com/yesvisare/gcc_multi_tenant_ai_pra_l2/blob/main/Augmented_GCC_MultiTenant_M11_2_SECTIONS_5_12_PART2.md)
- **Part 3 (Sections 9C-12)**: [GCC Context, Decision Card, PractaThon, Wrap-Up](https://github.com/yesvisare/gcc_multi_tenant_ai_pra_l2/blob/main/Augmented_GCC_MultiTenant_M11_2_SECTIONS_9C_Part3.md)

### Related Modules

- **Previous Module**: M11.1 - Multi-Tenant RAG Architecture Patterns
- **Next Module**: M11.3 - Database Multi-Tenancy with Row-Level Security (RLS)

### External Documentation

- [PostgreSQL Row-Level Security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [Redis Caching Patterns](https://redis.io/docs/manual/patterns/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Feature Flag Best Practices](https://martinfowler.com/articles/feature-toggles.html)

## License

MIT License - see LICENSE file for details.

## Author

TechVoyageHub Content Team

---

**Module Navigation:**
← [M11.1: Architecture Patterns](../m11_1/) | [M11.3: Database Multi-Tenancy](../m11_3/) →

---

**Production-Ready:** This codebase demonstrates enterprise patterns used in real GCC platforms serving 50+ business units. While database connections are optional for learning, the architecture is production-tested.
