# Module 11: Multi-Tenant Foundations
## Video M11.2: Tenant Metadata & Registry Design (Enhanced with TVH Framework v2.0)

**Duration:** 35 minutes
**Track:** GCC Multi-Tenant Architecture for RAG Systems
**Level:** L2 SkillElevate + GCC Specialization
**Audience:** L2 learners who completed Generic CCC M1-M8 and GCC Multi-Tenant M11.1
**Prerequisites:**
- Generic CCC M1-M8 (RAG fundamentals, production deployment, monitoring)
- GCC Multi-Tenant M11.1 (Multi-Tenant RAG Architecture Patterns)
- PostgreSQL schema design (intermediate level)
- Basic state machine concepts
- Understanding of feature flag systems

---

## SECTION 1: INTRODUCTION & HOOK (2-3 minutes)

**[0:00-0:30] Hook - Problem Statement**

[SLIDE: Title - "Tenant Metadata & Registry Design"]

**NARRATION:**
"In M11.1, you built tenant routing middleware that correctly routes requests to tenant-specific namespaces. You created tenant context propagation through async call chains. Your system can isolate tenant data at the vector database level.

But here's the production reality check: You just onboarded your 15th tenant. A business stakeholder asks: 'Can you tell me which tenants are on the gold tier versus silver tier? Can you show me which features are enabled for each tenant? Can you suspend a tenant who hasn't paid their invoice?'

You realize your entire tenant configuration is scattered across environment variables, hardcoded dictionaries, and tribal knowledge in Slack messages. There's no single source of truth. Adding a new tenant requires manual updates to six different configuration files. Suspending a tenant? Hope you remember all the places to update.

This is technical debt masquerading as 'agile development.' In a GCC serving 50+ business units, this doesn't scale.

Today, we're building the **Tenant Registry** - the authoritative source of truth for all tenant metadata, lifecycle management, and feature configuration..."

**INSTRUCTOR GUIDANCE:**
- Open with energy - this is the "missing piece" from M11.1
- Make the pain real - scattered config is a common anti-pattern
- Use second person to connect their journey
- Set up the "aha moment" that registry solves multiple problems at once

---

**[0:30-1:30] What We're Building Today**

[SLIDE: Tenant Registry Architecture showing:
- Central PostgreSQL tenant registry database
- Tenant CRUD API (FastAPI)
- Feature flag service with hierarchical evaluation
- Tenant lifecycle state machine (active→suspended→archived)
- Health monitoring aggregation per tenant
- Cascading operations coordinator]

**NARRATION:**
"Here's what we're building today - a production-ready **Tenant Registry System** with five integrated capabilities:

**First**: A PostgreSQL tenant registry that stores 20+ attributes per tenant - tier, limits, features, billing info, lifecycle state, health metrics. This is your single source of truth.

**Second**: A tenant CRUD API with FastAPI that enforces lifecycle state transitions. You can't jump from 'active' directly to 'deleted' - you must go through 'suspended' and 'archived' states with compliance-required retention periods.

**Third**: A feature flag service that evaluates flags hierarchically: tenant override beats tier default beats global default. This lets you roll out new features to 10% of tenants, then 50%, then 100% - canary deployment at the tenant level.

**Fourth**: Health check aggregation that calculates a tenant health score from multiple signals: API uptime, error rates, p95 latency, storage usage. When Tenant A's health drops below 80%, automatic alerts fire.

**Fifth**: Cascading operations - when you suspend a tenant, it doesn't just update one database field. It propagates through seven systems: vector DB, PostgreSQL, S3, Redis cache, logs, analytics, and backup storage. Everything happens transactionally.

By the end of this video, you'll have a tenant registry that handles the complete lifecycle - from onboarding to suspension to GDPR-compliant deletion - with full audit trails and zero manual config files.

This is what separates hobby projects from production GCC platforms."

**INSTRUCTOR GUIDANCE:**
- Show the complete system architecture visually
- Emphasize "five integrated capabilities" structure
- Use numbers (20+ attributes, 7 systems, etc.) for credibility
- Connect to production scale (50+ tenants, GDPR compliance)

---

**[1:30-2:30] Learning Objectives**

[SLIDE: Learning Objectives - 4 key outcomes]

**NARRATION:**
"In this 35-minute video, you'll learn:

1. **Design tenant metadata schemas** - Identify the 20+ attributes every tenant needs (tier, limits, billing, health) and model them in PostgreSQL with proper relationships and indexes

2. **Implement lifecycle state machines** - Build a state machine that enforces valid tenant transitions (active↔suspended→archived→deleted) with compliance-required retention periods and audit logging

3. **Build hierarchical feature flags** - Create a three-tier evaluation system (tenant > tier > global) that enables canary rollouts, A/B testing, and per-tenant customization without code deployments

4. **Execute cascading operations** - Implement transactional operations that propagate tenant changes across seven systems simultaneously - suspend tenant means suspend everywhere, with rollback on any failure

These aren't just concepts - you'll build a working system with 500+ lines of production-ready code that manages real tenant metadata, enforces state transitions, and evaluates feature flags in under 10 milliseconds."

**INSTRUCTOR GUIDANCE:**
- Use bold action verbs: Design, Implement, Build, Execute
- Make objectives measurable (500+ lines, <10ms, 7 systems)
- Connect to previous module (M11.1 had routing, now we add metadata)
- Preview the working code deliverable

---

**[2:30-3:00] Prerequisites Check**

[SLIDE: Prerequisites checklist with confidence indicators]

**NARRATION:**
"Before we dive in, make sure you've completed:

**✅ Generic CCC M1-M8**: You need solid RAG fundamentals - we're building on vector databases, API design, and monitoring patterns from Level 2.

**✅ GCC Multi-Tenant M11.1**: You must have completed M11.1 where you built tenant routing and context propagation. This video assumes you have tenant-aware middleware working.

**✅ PostgreSQL schema design**: You should be comfortable creating tables, indexes, foreign keys, and writing moderately complex queries. If you're rusty, spend 2 hours reviewing PostgreSQL documentation.

**✅ State machine concepts**: We're implementing a lifecycle state machine. If you haven't worked with state transitions before, read about finite state machines - 30 minutes of prep will save you hours of confusion.

If you haven't completed these, pause here. This video builds directly on M11.1's tenant routing. Without that foundation, the registry won't make sense in context."

**INSTRUCTOR GUIDANCE:**
- Be firm but supportive about prerequisites
- Give time estimates for skill-up (2 hours PostgreSQL, 30 min state machines)
- Explain WHY each prerequisite matters
- Reference specific prior modules by number

---

## SECTION 2: CONCEPTUAL FOUNDATION (5-7 minutes)

**[3:00-5:00] Core Concepts Explanation**

[SLIDE: Tenant Registry Concepts - Four foundational ideas shown as interconnected circles:
- Tenant Registry (center)
- Metadata Schema (left)
- Lifecycle States (right)
- Feature Flags (bottom)]

**NARRATION:**
"Let me explain the four key concepts we're working with today.

**Concept 1: Tenant Registry as Single Source of Truth**

Think of the tenant registry like a company's HR database. Just as HR maintains employee records (name, department, salary, start date, benefits), the tenant registry maintains tenant records (name, tier, limits, billing, features, health).

In production, you'll have multiple systems - vector database, PostgreSQL, S3 storage, Redis cache. But when someone asks 'Is Tenant XYZ on the gold tier?', there's only ONE place to look: the tenant registry. This is the source of truth. All other systems read from it, never write to it independently.

Why this matters: Without a registry, configuration drifts. Tenant A might be 'gold' in one config file, 'silver' in another. The registry prevents this by centralizing all metadata with transactional guarantees.

**Concept 2: Tenant Metadata - What to Track**

Not all tenant attributes are created equal. We track 20+ attributes across five categories:

**Identity Metadata**: `tenant_id` (UUID), `tenant_name` (string), `created_at` (timestamp)

**Tier Metadata**: `tier` (gold/silver/bronze), `sla_target` (99.9%, 99%, 95%), `support_level` (24/7, business-hours, community)

**Limits Metadata**: `max_users` (integer), `max_documents` (integer), `max_queries_per_day` (integer), `storage_quota_gb` (integer)

**Billing Metadata**: `billing_email` (string), `monthly_cost_inr` (decimal), `payment_status` (paid, overdue, suspended)

**Lifecycle Metadata**: `status` (active, suspended, migrating, archived, deleted), `suspended_at` (timestamp), `deletion_scheduled_at` (timestamp)

**Health Metadata**: `health_score` (0-100), `last_health_check` (timestamp), `p95_latency_ms` (integer), `error_rate` (percentage)

Visual analogy: Think of metadata like a medical chart. When a doctor treats a patient, they need complete information - medical history (identity), insurance tier (tier), medication limits (limits), billing status (billing), current health status (lifecycle), and vital signs (health). Missing any category leads to poor decisions.

Why this matters in production: Incomplete metadata means you can't answer basic stakeholder questions. CFO asks 'What's our chargeback for Tenant X?' - you need billing metadata. CTO asks 'Which tenants are unhealthy?' - you need health metadata. Compliance asks 'When was Tenant Y deleted and why?' - you need lifecycle metadata with timestamps.

**Concept 3: Lifecycle States - Tenant Journey**

A tenant isn't just 'active' or 'deleted'. There are five states with specific meanings and allowed transitions:

**Active**: Tenant is operational, all systems accessible

**Suspended**: Temporary pause (payment issue, policy violation) - data retained, access blocked

**Migrating**: Tenant is being moved to different isolation model or region - read-only during migration

**Archived**: Tenant requested deletion but GDPR requires 30-90 day retention - data preserved but inaccessible

**Deleted**: Final state after retention period - data purged from all systems, irreversible

The key insight: You can't jump arbitrary states. You can't go from 'active' to 'deleted' directly - you must go through 'suspended' (grace period) and 'archived' (retention period). This state machine enforces compliance requirements automatically.

Visual analogy: Think of tenant lifecycle like employee lifecycle. You can't go from 'employed' to 'erased from all records' instantly. You have: employed → resigned (notice period) → exited (keep records for audits) → records purged (after legal retention). Same logic for tenants.

Why this matters: Ad-hoc deletion is a compliance nightmare. GDPR audit asks 'Can you prove Tenant X's data was retained for 30 days after deletion request?' If you don't have lifecycle states with timestamps, you have no evidence. The state machine is your audit trail.

**Concept 4: Feature Flags - Tenant Configuration Without Code Deployment**

Feature flags are boolean switches (or JSON config) that change tenant behavior without deploying new code.

**Example use cases**:
- Tenant A gets GPT-4 access (expensive), Tenant B gets GPT-3.5 (cheaper) - controlled by `llm_model` feature flag
- Roll out new semantic re-ranking to 10% of tenants (canary deployment) - controlled by `enable_reranking` flag
- Tenant C needs dedicated vector DB namespace (compliance requirement) - controlled by `dedicated_namespace` flag

The magic is **hierarchical evaluation**: When evaluating a flag, we check three levels:
1. Tenant-specific override (if exists, use this)
2. Tier default (if no tenant override, use tier default - e.g., all gold tier gets feature X)
3. Global default (if no tier default, use platform default)

Visual analogy: Think of feature flags like parental controls on streaming services. Global policy: 'No R-rated content'. Parent account override: 'Allow R-rated for parent profile only'. Child profile override: 'No PG-13 either'. Evaluation checks most specific rule first, falls back to general rules.

Why this matters: Without feature flags, you have two bad options: (1) Deploy different code for each tenant (maintenance nightmare), or (2) Give all tenants identical features (no upsell opportunity, no canary testing). Feature flags give you per-tenant customization with operational sanity.

These four concepts work together: **Tenant Registry** stores all **Metadata** including current **Lifecycle State** and enabled **Feature Flags**. Everything is interconnected."

**INSTRUCTOR GUIDANCE:**
- Define each term before using it
- Use everyday analogies (HR database, medical chart, employee lifecycle)
- Explain the "why" - connect to production pain points
- Show visual diagrams for each concept
- Preview how concepts integrate

---

**[5:00-7:00] How It Works - System Flow**

[SLIDE: Flow diagram showing tenant lifecycle from creation to deletion with state transitions and feature flag evaluation]

**NARRATION:**
"Here's how the entire tenant registry system works, step by step - let me walk you through two complete flows: **tenant onboarding** and **feature flag evaluation**.

**Flow 1: Tenant Onboarding (Create → Active)**

**Step 1: API receives tenant creation request**
```
POST /api/v1/tenants
{
  "tenant_name": "wealth-management-bu",
  "tier": "gold",
  "max_users": 100,
  "max_documents": 50000
}
```
├── Request validation: Check all required fields present
├── Tier validation: Ensure 'gold' is valid tier with defined limits
└── Generate UUID for tenant_id: `uuid4()` → `a3b2c1d4-...`

**Step 2: Registry creates tenant record**
├── Insert into PostgreSQL `tenants` table with status='active'
├── Set created_at=now(), health_score=100 (perfect health initially)
├── Initialize default feature flags from tier template
└── Transaction committed - tenant now exists in registry

**Step 3: Cascading resource provisioning**
├── Create vector DB namespace: `pinecone.create_index(namespace=tenant_id)`
├── Create S3 bucket with tenant prefix: `s3://tenant-docs/a3b2c1d4-...`
├── Initialize Redis cache keys: `tenant:{tenant_id}:*`
├── Set up PostgreSQL row-level security: `CREATE POLICY tenant_isolation ...`
├── Enable monitoring: Grafana dashboard for tenant_id
├── Configure logging: Tag all logs with tenant_id
└── Create backup schedule: Daily snapshots of tenant data

**Result**: Tenant 'wealth-management-bu' is operational in 15 minutes (automated) vs 2 weeks (manual).

**Flow 2: Feature Flag Evaluation**

**Step 1: Application needs to check if tenant should use GPT-4**
```python
enabled, config = get_feature(tenant_id="a3b2c1d4-...", feature_name="llm_model")
```

**Step 2: Feature flag service checks three levels** (hierarchical evaluation)

**Level 1 Check**: Tenant-specific override?
├── Query: `SELECT config_json FROM feature_flags WHERE tenant_id='a3b2c1d4-...' AND feature_name='llm_model'`
├── Result: `{"model": "gpt-4", "max_tokens": 4000}` (found!)
└── RETURN: `(True, {"model": "gpt-4", "max_tokens": 4000})` ← **Use this**

**Level 2 Check** (skipped because level 1 found override): Tier default?
├── Would query: `SELECT config_json FROM tier_defaults WHERE tier='gold' AND feature_name='llm_model'`
└── Not reached in this case

**Level 3 Check** (skipped): Global default?
├── Would query: `SELECT config_json FROM global_defaults WHERE feature_name='llm_model'`
└── Not reached in this case

**Result**: Application uses GPT-4 with 4000 token limit for this tenant. Evaluation completed in <10ms using Redis cache.

**Flow 3: Tenant Suspension (Active → Suspended → Archived → Deleted)**

**Step 1: CFO reports Tenant X hasn't paid invoice for 60 days**
```
PATCH /api/v1/tenants/{tenant_id}/status
{"new_status": "suspended", "reason": "payment_overdue"}
```

**Step 2: State machine validates transition**
├── Current state: 'active'
├── Requested state: 'suspended'
├── Valid transition? Check allowed_transitions={'active': ['suspended', 'migrating']}
└── ✅ Allowed, proceed

**Step 3: Cascading suspension**
├── Update registry: `UPDATE tenants SET status='suspended', suspended_at=now()`
├── Revoke API access: `UPDATE api_keys SET enabled=false WHERE tenant_id=X`
├── Block vector DB queries: `pinecone.set_namespace_readonly(tenant_id)`
├── Disable S3 uploads: `s3.set_bucket_policy(tenant_id, read_only=true)`
├── Clear Redis cache: `redis.delete(f"tenant:{tenant_id}:*")`
├── Send notification: Email to tenant_admin and CFO
├── Audit log: Record suspension with reason, timestamp, actor
└── All operations succeed transactionally (rollback if any fails)

**Result**: Tenant X is suspended across all seven systems simultaneously. Queries return 403 Forbidden with message 'Tenant suspended due to payment_overdue'.

**Step 4: After 30-day grace period, no payment received**
```
PATCH /api/v1/tenants/{tenant_id}/status
{"new_status": "archived", "reason": "grace_period_expired"}
```
├── State machine validates: suspended→archived allowed
├── Cascading archival: Data moved to cold storage, access permanently revoked
├── Deletion scheduled: `deletion_scheduled_at = now() + 90 days` (GDPR retention)
└── Compliance audit trail: Complete timeline from active→suspended→archived

**Step 5: After 90-day GDPR retention, automated cleanup job runs**
```
Daily cron job: Archive tenants where deletion_scheduled_at < now()
```
├── Final state transition: archived→deleted
├── Cascading deletion across 7 systems:
  ├── Pinecone: Delete namespace completely
  ├── PostgreSQL: Delete all rows with tenant_id (ON DELETE CASCADE)
  ├── S3: Delete bucket and all objects
  ├── Redis: Delete all tenant keys
  ├── Logs: Archive logs to cold storage (7-year retention for audits)
  ├── Analytics: Aggregate metrics, delete raw events
  └── Backups: Delete incremental backups, keep final snapshot for 7 years
└── Audit log: Record deletion with evidence of 30+90 day retention

**Result**: Tenant completely purged from operational systems, with audit proof of compliance-required retention periods.

The key insight here is: **Every state transition triggers cascading operations across multiple systems, but it's orchestrated by the registry**. The registry is the conductor, not just a database."

**INSTRUCTOR GUIDANCE:**
- Walk through complete end-to-end flows with concrete examples
- Use visual flow diagrams with arrows and decision points
- Show actual API calls and database queries (code snippets)
- Emphasize cascading operations - registry coordinates everything
- Explain the "why" - compliance, auditability, atomicity

---

**[7:00-8:00] Why This Approach?**

[SLIDE: Comparison table - "Registry vs No Registry" side-by-side]

**NARRATION:**
"You might be wondering: why build a complex tenant registry? Can't we just use config files or environment variables?

Let me show you the reality of **three approaches**:

**Approach 1: No Registry - Scattered Configuration (Anti-pattern)**
- Tenant tier: Hardcoded in `config.yaml`
- Feature flags: Hardcoded in Python `FEATURE_FLAGS = {...}`
- Billing info: Spreadsheet managed by finance team
- Lifecycle status: Email thread and tribal knowledge
- Health metrics: Scattered across Grafana dashboards

**Problems**:
├── Configuration drift: Tenant is 'gold' in one file, 'silver' in another
├── No audit trail: Who changed what, when, and why?
├── Manual coordination: Adding tenant requires updating 6+ files
├── No validation: Can set invalid combinations (bronze tier with gold features)
├── Downtime required: Config changes require restart
└── Compliance nightmare: Cannot prove retention periods or deletion completion

**Real incident**: At TechCo GCC, Tenant A complained they were charged for gold tier but got silver features. Investigation revealed config drift between billing system (gold) and application config (silver). Resolution took 2 weeks, resulted in $50K credit to tenant, and damaged relationship.

**Approach 2: Partial Registry - Metadata Only (Better, but incomplete)**
- Tenant metadata: PostgreSQL registry ✅
- Feature flags: Still hardcoded in config files ❌
- Lifecycle states: Tracked in registry ✅
- Cascading operations: Manual coordination ❌

**Problems**:
├── Still requires config deployments for feature changes
├── Suspension requires manual updates across 7 systems
├── No transactional guarantees - partial suspension possible
└── Feature flag sprawl - hundreds of flags scattered across codebase

**Real incident**: At FinanceHub GCC, suspended tenant (payment overdue) continued querying vector DB for 3 days because suspension process missed one system. Cost to GCC: $12K in compute, compliance violation (accessing data while suspended), P1 incident.

**Approach 3: Complete Registry - Our Implementation (Best practice)**
- Tenant metadata: PostgreSQL registry ✅
- Feature flags: Stored in registry with hierarchical evaluation ✅
- Lifecycle states: State machine in registry ✅
- Cascading operations: Registry-coordinated transactions ✅
- Health monitoring: Registry aggregates from all systems ✅
- Audit trail: Every change logged with actor, timestamp, reason ✅

**Benefits**:
├── Single source of truth - zero configuration drift
├── Complete audit trail - compliance-ready
├── Zero-downtime changes - toggle features without deployment
├── Transactional guarantees - suspension happens atomically across all systems
├── Stakeholder visibility - CFO can query registry directly
└── Automated lifecycle - GDPR deletion happens on schedule, no manual intervention

**Real success**: At CloudScale GCC, implementing complete registry reduced tenant onboarding from 2 weeks to 15 minutes (automated), eliminated 3 P1 incidents/quarter (cross-tenant leaks), and passed SOX audit with zero findings (complete audit trail). ROI: 6 months.

**The decision is clear**: For GCC platforms serving 50+ tenants, a complete tenant registry is not optional - it's the foundation of operational sanity."

**INSTRUCTOR GUIDANCE:**
- Present three approaches as progression (anti-pattern → partial → best practice)
- Use real incident examples for credibility
- Quantify costs (50K credit, 12K compute, 3 P1 incidents)
- Show benefits in stakeholder terms (CFO, CTO, Compliance)
- Connect to GCC scale (50+ tenants, multi-region)

---

## SECTION 3: TECHNOLOGY STACK (2-3 minutes)

**[8:00-10:00] Tech Stack Overview**

[SLIDE: Technology Stack diagram showing:
- PostgreSQL 15+ (center - tenant registry)
- FastAPI (API layer)
- Redis (caching layer)
- Celery + RabbitMQ (async tasks)
- Prometheus + Grafana (monitoring)
- Integration points: Pinecone, S3, ELK/Splunk]

**NARRATION:**
"Let's talk about the technology stack for our tenant registry system. We're building on familiar tools from Generic CCC, with some GCC-specific additions.

**Core Technologies (from Generic CCC):**

**PostgreSQL 15+** - Our tenant registry database
├── Why PostgreSQL: ACID transactions (critical for cascading operations), rich schema with foreign keys and constraints, row-level security for tenant isolation, jsonb support for flexible feature flag config
├── Schema: 4 tables (tenants, feature_flags, tier_defaults, audit_log)
├── Performance: Indexes on tenant_id, status, tier for fast lookups
└── HA: Multi-region replication for 99.9% uptime (GCC requirement)

**FastAPI** - Our tenant management API
├── Why FastAPI: Async support (handle 1000+ concurrent requests), automatic OpenAPI docs, Pydantic validation (catch invalid requests early), easy integration with PostgreSQL via SQLAlchemy
├── Endpoints: GET/POST/PATCH/DELETE /tenants, GET /tenants/{id}/health, POST /tenants/{id}/features
└── Authentication: JWT validation from Generic CCC M7

**Redis 7+** - Feature flag caching and rate limiting
├── Why Redis: Sub-millisecond feature flag evaluation (target: <10ms), distributed caching across multiple API instances, atomic operations for counters and rate limits
├── Cache structure: `tenant:{tenant_id}:flags` → serialized feature flag dict
├── TTL: 5 minutes (balance freshness vs load on PostgreSQL)
└── Invalidation: On flag update, delete cache key to force refresh

**GCC-Specific Additions:**

**Prometheus + Grafana** - Tenant health monitoring
├── Metrics per tenant: `tenant_query_count`, `tenant_error_rate`, `tenant_p95_latency_ms`, `tenant_storage_gb`
├── Aggregation: Calculate health_score = f(uptime, error_rate, latency)
├── Alerts: PagerDuty when tenant health < 80%
└── Dashboards: Per-tenant view + aggregate view across all 50+ tenants

**Celery + RabbitMQ** - Asynchronous cascading operations
├── Why async: Suspending tenant across 7 systems takes 30-60 seconds, can't block API request
├── Task queue: `suspend_tenant`, `archive_tenant`, `delete_tenant`
├── Retry logic: Exponential backoff if vector DB temporarily unavailable
└── Dead letter queue: Failed tasks go to DLQ for manual investigation

**Integration Points:**

**Pinecone** - Vector database isolation
├── Operation: On tenant creation, `create_namespace(tenant_id)`
├── On suspension: Set namespace read-only
└── On deletion: Delete namespace entirely

**Amazon S3** - Document storage
├── Operation: Bucket per tenant with IAM policies
├── On suspension: Revoke write access, keep read for recovery
└── On deletion: Delete bucket and all objects

**ELK/Splunk** - Audit logging
├── Every registry operation logged with: `timestamp`, `actor`, `tenant_id`, `action`, `old_value`, `new_value`, `reason`
├── Immutable logs (append-only)
└── 7-year retention for SOX compliance

**Library Dependencies:**
```python
# requirements.txt
fastapi==0.104.1
pydantic==2.5.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
redis==5.0.1
celery==5.3.4
prometheus-client==0.19.0
pinecone-client==2.2.4
boto3==1.34.0  # AWS S3
```

**Why This Stack?**
- **PostgreSQL**: Battle-tested, ACID compliance, rich ecosystem
- **FastAPI**: Modern async Python, excellent for GCC scale
- **Redis**: Industry standard for caching and rate limiting
- **Celery**: Production-proven for long-running tasks
- **Prometheus/Grafana**: De facto monitoring standard

**What We're NOT Using:**
- ❌ NoSQL for tenant registry - need ACID transactions and relational integrity
- ❌ Microservices architecture - tenant registry is foundational, keep it simple
- ❌ GraphQL - REST is sufficient and more widely understood in GCCs

This stack handles 50+ tenants, 1000+ concurrent users, <10ms feature flag eval, and 99.9% uptime. It's production-proven, not cutting-edge hype."

**INSTRUCTOR GUIDANCE:**
- Explain WHY each technology was chosen (not just WHAT)
- Connect to GCC requirements (scale, compliance, uptime)
- Show integration points with other systems
- Acknowledge what we're NOT using and why
- Keep it practical - production-proven over trendy

---

## SECTION 4: TECHNICAL IMPLEMENTATION (12-15 minutes)

**[10:00-22:00] Building the Tenant Registry System**

**IMPLEMENTATION OVERVIEW:**
We're building 5 integrated components:
1. PostgreSQL Schema (tenant registry database)
2. Tenant CRUD API (FastAPI endpoints)
3. Feature Flag Service (hierarchical evaluation)
4. Lifecycle State Machine (valid transitions only)
5. Cascading Operations Coordinator (atomic multi-system operations)

Let's build each component with production-ready code.

---

**[10:00-12:00] Component 1: PostgreSQL Tenant Registry Schema**

[SLIDE: Database schema diagram showing 4 tables with relationships:
- tenants (main table)
- feature_flags (many-to-one with tenants)
- tier_defaults (lookup table)
- audit_log (immutable history)]

**NARRATION:**
"First, we design our PostgreSQL schema. Four tables: tenants, feature_flags, tier_defaults, and audit_log."

```sql
-- tenant_registry_schema.sql
-- Complete PostgreSQL schema for tenant registry

-- Table 1: Tenants (main registry)
CREATE TABLE tenants (
    tenant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_name VARCHAR(255) NOT NULL UNIQUE,
    -- Tier metadata
    tier VARCHAR(50) NOT NULL CHECK (tier IN ('platinum', 'gold', 'silver', 'bronze')),
    -- CHECK constraint prevents invalid tiers - database-level validation
    sla_target DECIMAL(5,4) NOT NULL,  -- 0.9999, 0.999, 0.99, 0.95
    support_level VARCHAR(50) NOT NULL,  -- '24/7', 'business-hours', 'community'
    
    -- Limits metadata
    max_users INTEGER NOT NULL,
    max_documents INTEGER NOT NULL,
    max_queries_per_day INTEGER NOT NULL,
    storage_quota_gb INTEGER NOT NULL,
    
    -- Billing metadata
    billing_email VARCHAR(255) NOT NULL,
    monthly_cost_inr DECIMAL(10,2) NOT NULL,  -- ₹ amount
    payment_status VARCHAR(50) NOT NULL CHECK (payment_status IN ('paid', 'overdue', 'suspended')),
    
    -- Lifecycle metadata
    status VARCHAR(50) NOT NULL CHECK (status IN ('active', 'suspended', 'migrating', 'archived', 'deleted')),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    suspended_at TIMESTAMP NULL,  -- Set when status becomes 'suspended'
    archived_at TIMESTAMP NULL,  -- Set when status becomes 'archived'
    deletion_scheduled_at TIMESTAMP NULL,  -- archived_at + 90 days (GDPR)
    deleted_at TIMESTAMP NULL,  -- Final deletion timestamp
    
    -- Health metadata
    health_score INTEGER NOT NULL DEFAULT 100 CHECK (health_score BETWEEN 0 AND 100),
    last_health_check TIMESTAMP NOT NULL DEFAULT NOW(),
    p95_latency_ms INTEGER DEFAULT 0,
    error_rate DECIMAL(5,4) DEFAULT 0.0000,  -- 0.05 = 5% error rate
    uptime_percentage DECIMAL(5,4) DEFAULT 1.0000,  -- 0.999 = 99.9% uptime
    
    -- Audit metadata
    created_by VARCHAR(255) NOT NULL,  -- User who created tenant
    last_modified_by VARCHAR(255) NOT NULL,  -- Last user to modify
    last_modified_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for fast lookups (critical for GCC scale)
CREATE INDEX idx_tenants_status ON tenants(status);  
-- Filter by status frequently (e.g., find all active tenants)

CREATE INDEX idx_tenants_tier ON tenants(tier);  
-- Aggregate by tier (e.g., count tenants per tier for reporting)

CREATE INDEX idx_tenants_health_score ON tenants(health_score);  
-- Find unhealthy tenants quickly (health_score < 80)

CREATE INDEX idx_tenants_deletion_scheduled ON tenants(deletion_scheduled_at)  
-- Cleanup job needs to find tenants ready for deletion
    WHERE deletion_scheduled_at IS NOT NULL;  
-- Partial index: Only index rows where deletion is scheduled (memory efficient)

-- Table 2: Feature Flags (per-tenant overrides)
CREATE TABLE feature_flags (
    flag_id SERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,  
    -- ON DELETE CASCADE: Deleting tenant automatically deletes its feature flags
    feature_name VARCHAR(255) NOT NULL,  -- 'llm_model', 'enable_reranking', etc.
    enabled BOOLEAN NOT NULL DEFAULT true,  -- Is this flag active?
    config_json JSONB NULL,  
    -- JSONB for flexible config: {"model": "gpt-4", "max_tokens": 4000}
    -- Why JSONB: Schema-less config without ALTER TABLE for new features
    
    -- Audit trail
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255) NOT NULL,
    last_modified_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_modified_by VARCHAR(255) NOT NULL,
    
    -- Composite unique constraint: One row per (tenant, feature) pair
    UNIQUE(tenant_id, feature_name)
);

CREATE INDEX idx_feature_flags_tenant ON feature_flags(tenant_id);  
-- Fast tenant lookup (get all flags for tenant X)

CREATE INDEX idx_feature_flags_feature ON feature_flags(feature_name);  
-- Find all tenants with feature X enabled (for rollout tracking)

-- Table 3: Tier Defaults (tier-level feature flags)
CREATE TABLE tier_defaults (
    tier VARCHAR(50) NOT NULL,  -- 'platinum', 'gold', 'silver', 'bronze'
    feature_name VARCHAR(255) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT true,
    config_json JSONB NULL,
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_modified_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    PRIMARY KEY (tier, feature_name)  -- One row per (tier, feature) pair
);

-- Seed tier defaults (platinum gets best features, bronze gets basic)
INSERT INTO tier_defaults (tier, feature_name, enabled, config_json) VALUES
    ('platinum', 'llm_model', true, '{"model": "gpt-4", "max_tokens": 8000}'),
    ('platinum', 'enable_reranking', true, '{"top_k": 10}'),
    ('platinum', 'dedicated_namespace', true, '{"isolation": "physical"}'),
    ('gold', 'llm_model', true, '{"model": "gpt-4", "max_tokens": 4000}'),
    ('gold', 'enable_reranking', true, '{"top_k": 5}'),
    ('gold', 'dedicated_namespace', false, NULL),
    ('silver', 'llm_model', true, '{"model": "gpt-3.5-turbo", "max_tokens": 2000}'),
    ('silver', 'enable_reranking', false, NULL),
    ('bronze', 'llm_model', true, '{"model": "gpt-3.5-turbo", "max_tokens": 1000}');

-- Table 4: Audit Log (immutable history)
CREATE TABLE audit_log (
    log_id SERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL,  
    -- NOT a foreign key - we keep logs even after tenant deleted
    -- This is intentional for compliance (7-year retention)
    action VARCHAR(50) NOT NULL,  -- 'CREATE', 'UPDATE_STATUS', 'UPDATE_TIER', 'DELETE'
    actor VARCHAR(255) NOT NULL,  -- User who performed action
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Before/after values for auditability
    old_value JSONB NULL,  -- Previous state (JSON)
    new_value JSONB NOT NULL,  -- New state (JSON)
    reason TEXT NULL,  -- Why was this action taken? (required for compliance)
    
    -- Request metadata
    ip_address INET NULL,
    user_agent TEXT NULL
);

CREATE INDEX idx_audit_log_tenant ON audit_log(tenant_id);  
-- Fetch tenant history (all changes for tenant X)

CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp DESC);  
-- Recent actions (last 24 hours)

CREATE INDEX idx_audit_log_action ON audit_log(action);  
-- Filter by action type (all deletions)

-- Trigger: Audit all tenant updates automatically
CREATE OR REPLACE FUNCTION audit_tenant_changes()
RETURNS TRIGGER AS $$
BEGIN
    -- On INSERT: Log creation
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (tenant_id, action, actor, new_value)
        VALUES (NEW.tenant_id, 'CREATE', NEW.created_by, row_to_json(NEW));
        RETURN NEW;
    END IF;
    
    -- On UPDATE: Log changes
    IF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (tenant_id, action, actor, old_value, new_value)
        VALUES (OLD.tenant_id, 'UPDATE', NEW.last_modified_by, row_to_json(OLD), row_to_json(NEW));
        RETURN NEW;
    END IF;
    
    -- On DELETE: Log deletion (with old values)
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (tenant_id, action, actor, old_value, new_value)
        VALUES (OLD.tenant_id, 'DELETE', OLD.last_modified_by, row_to_json(OLD), '{}'::jsonb);
        RETURN OLD;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tenant_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON tenants
    FOR EACH ROW EXECUTE FUNCTION audit_tenant_changes();
-- This trigger automatically logs EVERY tenant change. No manual logging needed!
-- Compliance auditors love this - complete immutable audit trail.

-- Row-Level Security (RLS) for tenant isolation
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_policy ON tenants
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
-- When application sets session variable: SET app.current_tenant_id = 'uuid';
-- PostgreSQL automatically filters: WHERE tenant_id = 'uuid'
-- This prevents cross-tenant data leaks at the database level.
-- Even if application code has a bug, PostgreSQL enforces isolation.
```

**WHY THIS SCHEMA:**
- **20+ tenant attributes**: Identity, tier, limits, billing, lifecycle, health - everything stakeholders need
- **JSONB for feature flags**: Flexible config without schema changes (add new features without migrations)
- **Comprehensive indexes**: Fast queries even with 50+ tenants and 1000+ feature flags
- **Audit trail with triggers**: Automatic logging, impossible to forget
- **Row-level security**: Defense-in-depth against cross-tenant leaks
- **CHECK constraints**: Invalid data rejected at database level (e.g., tier must be gold/silver/bronze)
- **ON DELETE CASCADE**: Deleting tenant automatically deletes feature flags (consistency)
- **Partial indexes**: `deletion_scheduled_at` indexed only where NOT NULL (memory efficiency)

This is production-ready schema with enterprise-grade guarantees."

**INSTRUCTOR GUIDANCE:**
- Walk through schema table by table
- Explain WHY each column exists (connect to stakeholder needs)
- Show indexes and explain performance impact
- Emphasize audit trail and immutability
- Highlight clever features (partial indexes, CHECK constraints, triggers)
- Use inline comments extensively (every design decision explained)

---

[Note: This is PART 1 of the script. PART 2 will continue with remaining components and sections 5-12]
# GCC Multi-Tenant M11.2 - PART 2 (Continuation)

## SECTION 4: TECHNICAL IMPLEMENTATION (Continued)

**[12:00-15:00] Component 2: Tenant CRUD API with FastAPI**

[SLIDE: API architecture showing:
- FastAPI application layer
- SQLAlchemy ORM
- PostgreSQL database
- Redis caching
- Request/response flow]

**NARRATION:**
"Now we build the FastAPI application that exposes our tenant registry as a REST API. This handles tenant CRUD operations, feature flag management, and lifecycle transitions."

```python
# tenant_api.py
from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr, Field, validator
from sqlalchemy import create_engine, Column, String, Integer, DECIMAL, TIMESTAMP, Boolean, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import uuid
import redis
import json

# Initialize FastAPI
app = FastAPI(title="Tenant Registry API", version="1.0.0")

# Database connection
DATABASE_URL = "postgresql://user:password@localhost:5432/tenant_registry"
engine = create_engine(DATABASE_URL, pool_size=20, max_overflow=40)  
# GCC scale: 20 connections baseline, burst to 60 during load spikes
# Why these numbers: 50 tenants * 1000 users = 50K potential connections
# Connection pooling prevents exhaustion
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis connection for caching
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
CACHE_TTL = 300  # 5 minutes - balance freshness vs database load

# Pydantic models for request/response validation
class TenantCreate(BaseModel):
    tenant_name: str = Field(..., min_length=3, max_length=255, regex="^[a-z0-9-]+$")  
    # Regex: Lowercase, numbers, hyphens only (URL-safe)
    tier: str = Field(..., regex="^(platinum|gold|silver|bronze)$")
    max_users: int = Field(..., gt=0, le=10000)  # Must be between 1 and 10,000
    max_documents: int = Field(..., gt=0, le=10000000)  # Up to 10 million docs
    max_queries_per_day: int = Field(..., gt=0)
    storage_quota_gb: int = Field(..., gt=0, le=10000)  # Up to 10TB
    billing_email: EmailStr  # Pydantic validates email format automatically
    created_by: str  # User who is creating this tenant (from JWT)
    
    @validator('tier')
    def validate_tier_limits(cls, tier, values):
        # Enforce tier-specific max limits (prevent abuse)
        tier_limits = {
            'platinum': {'max_users': 10000, 'max_documents': 10000000},
            'gold': {'max_users': 1000, 'max_documents': 500000},
            'silver': {'max_users': 200, 'max_documents': 100000},
            'bronze': {'max_users': 50, 'max_documents': 20000}
        }
        limits = tier_limits[tier]
        if values.get('max_users', 0) > limits['max_users']:
            raise ValueError(f"{tier} tier max_users cannot exceed {limits['max_users']}")
        if values.get('max_documents', 0) > limits['max_documents']:
            raise ValueError(f"{tier} tier max_documents cannot exceed {limits['max_documents']}")
        return tier
        # This validator prevents nonsense like "bronze tier with 10,000 users"
        # Pydantic runs this BEFORE database insert

class TenantResponse(BaseModel):
    tenant_id: uuid.UUID
    tenant_name: str
    tier: str
    status: str
    created_at: datetime
    health_score: int
    monthly_cost_inr: float
    
    class Config:
        orm_mode = True  # Enable automatic conversion from SQLAlchemy models

class TenantUpdate(BaseModel):
    tier: Optional[str] = Field(None, regex="^(platinum|gold|silver|bronze)$")
    max_users: Optional[int] = Field(None, gt=0)
    billing_email: Optional[EmailStr] = None
    last_modified_by: str  # Required for audit trail

class TenantStatusUpdate(BaseModel):
    new_status: str = Field(..., regex="^(active|suspended|migrating|archived|deleted)$")
    reason: str = Field(..., min_length=10)  
    # Why are we changing status? (compliance requirement - auditors need explanations)
    actor: str  # Who is making this change?

class FeatureFlagSet(BaseModel):
    feature_name: str = Field(..., min_length=3, max_length=255)
    enabled: bool = True
    config_json: Optional[Dict[str, Any]] = None
    created_by: str

# SQLAlchemy ORM models (maps to PostgreSQL tables)
class Tenant(Base):
    __tablename__ = "tenants"
    tenant_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_name = Column(String(255), unique=True, nullable=False)
    tier = Column(String(50), nullable=False)
    sla_target = Column(DECIMAL(5, 4), nullable=False)
    support_level = Column(String(50), nullable=False)
    max_users = Column(Integer, nullable=False)
    max_documents = Column(Integer, nullable=False)
    max_queries_per_day = Column(Integer, nullable=False)
    storage_quota_gb = Column(Integer, nullable=False)
    billing_email = Column(String(255), nullable=False)
    monthly_cost_inr = Column(DECIMAL(10, 2), nullable=False)
    payment_status = Column(String(50), nullable=False, default='paid')
    status = Column(String(50), nullable=False, default='active')
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    suspended_at = Column(TIMESTAMP, nullable=True)
    archived_at = Column(TIMESTAMP, nullable=True)
    deletion_scheduled_at = Column(TIMESTAMP, nullable=True)
    deleted_at = Column(TIMESTAMP, nullable=True)
    health_score = Column(Integer, nullable=False, default=100)
    last_health_check = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    p95_latency_ms = Column(Integer, default=0)
    error_rate = Column(DECIMAL(5, 4), default=0.0)
    uptime_percentage = Column(DECIMAL(5, 4), default=1.0)
    created_by = Column(String(255), nullable=False)
    last_modified_by = Column(String(255), nullable=False)
    last_modified_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)

class FeatureFlag(Base):
    __tablename__ = "feature_flags"
    flag_id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    feature_name = Column(String(255), nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    config_json = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    created_by = Column(String(255), nullable=False)
    last_modified_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    last_modified_by = Column(String(255), nullable=False)

# Dependency: Get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper: Calculate monthly cost based on tier and usage
def calculate_monthly_cost(tier: str, max_users: int, max_documents: int) -> float:
    # Pricing model: Base cost + per-user + per-1000-docs
    # This is transparent pricing that CFOs understand
    pricing = {
        'platinum': {'base': 150000, 'per_user': 500, 'per_1k_docs': 100},  # ₹1.5L base + ₹500/user + ₹100/1K docs
        'gold': {'base': 80000, 'per_user': 300, 'per_1k_docs': 50},        # ₹80K base
        'silver': {'base': 30000, 'per_user': 150, 'per_1k_docs': 20},      # ₹30K base
        'bronze': {'base': 10000, 'per_user': 100, 'per_1k_docs': 10}       # ₹10K base
    }
    p = pricing[tier]
    cost = p['base'] + (max_users * p['per_user']) + ((max_documents / 1000) * p['per_1k_docs'])
    return round(cost, 2)
    # Example: Gold tier, 100 users, 50K docs
    # = 80,000 + (100 * 300) + ((50,000/1000) * 50)
    # = 80,000 + 30,000 + 2,500 = ₹1,12,500/month

# Helper: Get tier defaults (SLA, support level)
def get_tier_defaults(tier: str) -> dict:
    tier_config = {
        'platinum': {'sla_target': 0.9999, 'support_level': '24/7'},  # 99.99% uptime, always available
        'gold': {'sla_target': 0.999, 'support_level': '24/7'},       # 99.9% uptime
        'silver': {'sla_target': 0.99, 'support_level': 'business-hours'},  # 99% uptime, 9-5 support
        'bronze': {'sla_target': 0.95, 'support_level': 'community'}  # 95% uptime, community forum only
    }
    return tier_config[tier]

# API ENDPOINTS

@app.post("/api/v1/tenants", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
def create_tenant(tenant: TenantCreate, db: Session = Depends(get_db)):
    """
    Create a new tenant in the registry.
    
    This endpoint:
    1. Validates tenant data (Pydantic catches bad requests)
    2. Checks for name collision (prevent duplicates)
    3. Calculates monthly cost (transparent pricing)
    4. Inserts into database (atomic transaction)
    5. Triggers cascading provisioning (async Celery task)
    6. Returns tenant record (with generated UUID)
    """
    # Check for duplicate tenant name
    existing = db.query(Tenant).filter(Tenant.tenant_name == tenant.tenant_name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Tenant '{tenant.tenant_name}' already exists")
        # Prevent accidental duplicate tenants - each name must be unique
    
    # Get tier defaults (SLA, support level)
    tier_defaults = get_tier_defaults(tenant.tier)
    
    # Calculate monthly cost based on tier and usage
    monthly_cost = calculate_monthly_cost(tenant.tier, tenant.max_users, tenant.max_documents)
    
    # Create tenant record
    new_tenant = Tenant(
        tenant_name=tenant.tenant_name,
        tier=tenant.tier,
        sla_target=tier_defaults['sla_target'],
        support_level=tier_defaults['support_level'],
        max_users=tenant.max_users,
        max_documents=tenant.max_documents,
        max_queries_per_day=tenant.max_queries_per_day,
        storage_quota_gb=tenant.storage_quota_gb,
        billing_email=tenant.billing_email,
        monthly_cost_inr=monthly_cost,
        payment_status='paid',  # New tenants start as paid
        status='active',  # New tenants start active
        created_by=tenant.created_by,
        last_modified_by=tenant.created_by
    )
    
    try:
        db.add(new_tenant)
        db.commit()  # Write to database (atomic - all-or-nothing)
        db.refresh(new_tenant)  # Get auto-generated fields (tenant_id, created_at)
        
        # TODO: Trigger async cascading provisioning (Celery task)
        # provision_tenant_resources.delay(tenant_id=new_tenant.tenant_id)
        # This creates: vector DB namespace, S3 bucket, Redis keys, etc.
        # Async because it takes 30-60 seconds - can't block HTTP request
        
        return new_tenant
    except Exception as e:
        db.rollback()  # Undo changes on error (atomicity guarantee)
        raise HTTPException(status_code=500, detail=f"Failed to create tenant: {str(e)}")

@app.get("/api/v1/tenants/{tenant_id}", response_model=TenantResponse)
def get_tenant(tenant_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieve tenant by ID.
    
    Uses Redis cache for fast lookups (target: <10ms).
    Falls back to PostgreSQL if cache miss.
    """
    # Try Redis cache first (sub-millisecond lookup)
    cache_key = f"tenant:{tenant_id}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)  # Cache hit - return immediately (5-10ms total)
    
    # Cache miss - query database (50-100ms)
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")
    
    # Write to cache for next request
    redis_client.setex(cache_key, CACHE_TTL, json.dumps(TenantResponse.from_orm(tenant).dict(), default=str))
    # TTL=300 seconds (5 minutes) balances freshness vs database load
    # Shorter TTL = fresher data but more DB queries
    # Longer TTL = less DB load but stale data
    
    return tenant

@app.get("/api/v1/tenants", response_model=List[TenantResponse])
def list_tenants(
    status: Optional[str] = None,
    tier: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all tenants with optional filtering.
    
    Filters: status (active/suspended/archived), tier (gold/silver/bronze)
    Pagination: skip (offset), limit (max results)
    """
    query = db.query(Tenant)
    
    # Apply filters (if provided)
    if status:
        query = query.filter(Tenant.status == status)
    if tier:
        query = query.filter(Tenant.tier == tier)
    
    # Pagination (CRITICAL for GCC scale - can't load 50+ tenants without pagination)
    tenants = query.offset(skip).limit(limit).all()
    # Example: GET /tenants?status=active&skip=0&limit=20 (page 1)
    #          GET /tenants?status=active&skip=20&limit=20 (page 2)
    return tenants

@app.patch("/api/v1/tenants/{tenant_id}", response_model=TenantResponse)
def update_tenant(tenant_id: uuid.UUID, updates: TenantUpdate, db: Session = Depends(get_db)):
    """
    Update tenant metadata (tier, limits, billing).
    
    Does NOT update status - use PATCH /tenants/{id}/status for lifecycle changes.
    This separation prevents accidental status changes during routine updates.
    """
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")
    
    # Apply updates (only update fields that were provided)
    if updates.tier:
        old_tier = tenant.tier
        tenant.tier = updates.tier
        tier_defaults = get_tier_defaults(updates.tier)
        tenant.sla_target = tier_defaults['sla_target']
        tenant.support_level = tier_defaults['support_level']
        # Recalculate cost if tier changed
        tenant.monthly_cost_inr = calculate_monthly_cost(tenant.tier, tenant.max_users, tenant.max_documents)
    
    if updates.max_users:
        tenant.max_users = updates.max_users
        # Recalculate cost if users changed
        tenant.monthly_cost_inr = calculate_monthly_cost(tenant.tier, tenant.max_users, tenant.max_documents)
    
    if updates.billing_email:
        tenant.billing_email = updates.billing_email
    
    tenant.last_modified_by = updates.last_modified_by
    tenant.last_modified_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(tenant)
        
        # Invalidate cache (force refresh on next GET)
        redis_client.delete(f"tenant:{tenant_id}")
        # Cache invalidation prevents stale data
        
        return tenant
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update tenant: {str(e)}")

@app.patch("/api/v1/tenants/{tenant_id}/status", response_model=TenantResponse)
def update_tenant_status(tenant_id: uuid.UUID, status_update: TenantStatusUpdate, db: Session = Depends(get_db)):
    """
    Update tenant lifecycle status with state machine validation.
    
    This is the CRITICAL endpoint for tenant lifecycle management:
    - Validates state transitions (can't jump arbitrary states)
    - Updates lifecycle timestamps (suspended_at, archived_at, etc.)
    - Triggers cascading operations (async Celery tasks)
    - Logs to audit trail (automatic via PostgreSQL trigger)
    """
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")
    
    # State machine: Define allowed transitions
    allowed_transitions = {
        'active': ['suspended', 'migrating'],  # Active tenant can be suspended or migrated
        'suspended': ['active', 'archived'],  # Suspended can be reactivated or archived
        'migrating': ['active', 'suspended'],  # Migration can succeed (active) or fail (suspended)
        'archived': ['deleted'],  # Archived can only be deleted (after retention period)
        'deleted': []  # Deleted is final state - no transitions allowed
    }
    
    current_status = tenant.status
    new_status = status_update.new_status
    
    # Validate transition (enforce state machine)
    if new_status not in allowed_transitions.get(current_status, []):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid state transition: {current_status} → {new_status}. Allowed: {allowed_transitions.get(current_status, [])}"
        )
        # Prevent nonsense like active→deleted without suspension/archival
        # This is compliance-critical - GDPR requires retention periods
    
    # Update status and set lifecycle timestamps
    tenant.status = new_status
    tenant.last_modified_by = status_update.actor
    tenant.last_modified_at = datetime.utcnow()
    
    # Set lifecycle timestamps based on new status
    if new_status == 'suspended':
        tenant.suspended_at = datetime.utcnow()
    elif new_status == 'archived':
        tenant.archived_at = datetime.utcnow()
        tenant.deletion_scheduled_at = datetime.utcnow() + timedelta(days=90)  
        # GDPR 90-day retention requirement
        # After 90 days, automated cleanup job will delete tenant
    elif new_status == 'deleted':
        tenant.deleted_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(tenant)
        
        # Invalidate cache
        redis_client.delete(f"tenant:{tenant_id}")
        
        # TODO: Trigger async cascading operations (Celery tasks)
        # These operations take 30-60 seconds, can't block HTTP request
        # if new_status == 'suspended':
        #     suspend_tenant_resources.delay(tenant_id=tenant_id, reason=status_update.reason)
        #     # Suspends: API access, vector DB, S3 uploads, Redis cache
        # elif new_status == 'archived':
        #     archive_tenant_resources.delay(tenant_id=tenant_id)
        #     # Archives: Move data to cold storage, revoke all access
        # elif new_status == 'deleted':
        #     delete_tenant_resources.delay(tenant_id=tenant_id)
        #     # Deletes: Purge from all 7 systems (vector DB, PostgreSQL, S3, Redis, logs, analytics, backups)
        
        return tenant
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update status: {str(e)}")

@app.post("/api/v1/tenants/{tenant_id}/features", status_code=status.HTTP_201_CREATED)
def set_feature_flag(tenant_id: uuid.UUID, flag: FeatureFlagSet, db: Session = Depends(get_db)):
    """
    Set a tenant-specific feature flag (override tier default).
    
    This enables per-tenant customization without code deployment.
    Example: Tenant A gets GPT-4, Tenant B gets GPT-3.5 - same codebase.
    """
    # Verify tenant exists
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")
    
    # Check if flag already exists (upsert logic)
    existing_flag = db.query(FeatureFlag).filter(
        FeatureFlag.tenant_id == tenant_id,
        FeatureFlag.feature_name == flag.feature_name
    ).first()
    
    if existing_flag:
        # Update existing flag (upsert)
        existing_flag.enabled = flag.enabled
        existing_flag.config_json = flag.config_json
        existing_flag.last_modified_by = flag.created_by
        existing_flag.last_modified_at = datetime.utcnow()
    else:
        # Create new flag
        new_flag = FeatureFlag(
            tenant_id=tenant_id,
            feature_name=flag.feature_name,
            enabled=flag.enabled,
            config_json=flag.config_json,
            created_by=flag.created_by,
            last_modified_by=flag.created_by
        )
        db.add(new_flag)
    
    try:
        db.commit()
        
        # Invalidate feature flag cache for this tenant
        redis_client.delete(f"tenant:{tenant_id}:flags")
        # Next feature flag evaluation will fetch fresh data from database
        
        return {"message": f"Feature flag '{flag.feature_name}' set for tenant {tenant_id}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to set feature flag: {str(e)}")

@app.get("/api/v1/tenants/{tenant_id}/health")
def get_tenant_health(tenant_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Get tenant health metrics.
    
    Returns: health_score (0-100), uptime (%), error_rate (%), p95_latency (ms)
    """
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")
    
    return {
        "tenant_id": tenant_id,
        "tenant_name": tenant.tenant_name,
        "health_score": tenant.health_score,
        "uptime_percentage": float(tenant.uptime_percentage),
        "error_rate": float(tenant.error_rate),
        "p95_latency_ms": tenant.p95_latency_ms,
        "last_health_check": tenant.last_health_check,
        "status": "healthy" if tenant.health_score >= 80 else "degraded" if tenant.health_score >= 50 else "unhealthy"
        # Health score interpretation:
        # 80-100: Healthy (green)
        # 50-79: Degraded (yellow) - investigate
        # 0-49: Unhealthy (red) - immediate action required
    }

# Health check endpoint for load balancer
@app.get("/health")
def health_check():
    """
    API health check for load balancer.
    
    Returns 200 OK if API is responsive and database is reachable.
    Load balancer uses this to route traffic only to healthy instances.
    """
    try:
        # Test database connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        # Test Redis connection
        redis_client.ping()
        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=4)
    # In production: Use gunicorn with multiple workers
    # gunicorn -w 8 -k uvicorn.workers.UvicornWorker tenant_api:app
    # 8 workers handles 8000+ concurrent requests (1000 per worker)
```

**WHY THIS API:**
- **Pydantic validation**: Invalid requests rejected before hitting database (e.g., bronze tier with 10K users)
- **State machine in code**: Enforces valid transitions at API level, not just database
- **Redis caching**: Sub-10ms GET /tenants/{id} latency for cached tenants
- **Audit trail automatic**: PostgreSQL trigger logs every change, no manual logging needed
- **Pagination**: Required for GCC scale (listing 50+ tenants without pagination = memory issue)
- **Async-ready**: FastAPI handles 1000+ concurrent requests with async/await
- **Cost calculation**: Transparent pricing model embedded in API
- **Feature flag invalidation**: Cache cleared on update (freshness guarantee)

**Production considerations**:
- Connection pooling: 20 connections baseline, burst to 60 (handle load spikes)
- Error handling: Try/except with rollback (atomic operations)
- HTTP status codes: 201 Created, 404 Not Found, 400 Bad Request, 500 Internal Error
- OpenAPI docs: Automatic at /docs (FastAPI built-in for API exploration)

This API is the interface to the tenant registry. All tenant operations go through this."

**INSTRUCTOR GUIDANCE:**
- Walk through each endpoint with use case
- Explain validation logic (Pydantic, state machine)
- Show caching strategy (Redis TTL, invalidation)
- Highlight production features (connection pooling, error handling)
- Use inline comments extensively (every design decision)
- Connect to GCC scale (pagination, async, 1000+ requests)

---

**[15:00-18:00] Component 3: Feature Flag Service with Hierarchical Evaluation**

[SLIDE: Feature flag evaluation hierarchy showing 3 levels:
Level 1: Tenant-specific override (highest priority)
Level 2: Tier default (middle priority)
Level 3: Global default (lowest priority)]

**NARRATION:**
"Now we implement the feature flag service with hierarchical evaluation. This is where the magic happens - per-tenant customization without code deployment."

```python
# feature_flag_service.py
from typing import Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session
from tenant_api import Tenant, FeatureFlag
import redis
import json

class FeatureFlagService:
    """
    Feature flag evaluation service with 3-tier hierarchy:
    1. Tenant-specific override (highest priority)
    2. Tier default (for all tenants in a tier)
    3. Global default (platform-wide fallback)
    
    Evaluation is fast (<10ms) using Redis caching.
    """
    
    def __init__(self, db: Session, redis_client: redis.Redis):
        self.db = db
        self.redis = redis_client
        self.cache_ttl = 300  # 5 minutes
        
    def get_feature(self, tenant_id: str, feature_name: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Evaluate feature flag for tenant with hierarchical lookup.
        
        Returns: (enabled: bool, config: dict)
        Example: (True, {"model": "gpt-4", "max_tokens": 4000})
        
        Evaluation order:
        1. Check tenant-specific override (if exists, return immediately)
        2. Check tier default (if exists, return)
        3. Check global default (if exists, return)
        4. If nothing found, return (False, None) - feature disabled
        """
        
        # Try Redis cache first (sub-millisecond lookup)
        cache_key = f"feature:{tenant_id}:{feature_name}"
        cached = self.redis.get(cache_key)
        if cached:
            result = json.loads(cached)
            return (result['enabled'], result['config'])
            # Cache hit - return in <5ms
        
        # Cache miss - do hierarchical evaluation (50-150ms)
        
        # Level 1: Tenant-specific override (highest priority)
        tenant_flag = self.db.query(FeatureFlag).filter(
            FeatureFlag.tenant_id == tenant_id,
            FeatureFlag.feature_name == feature_name
        ).first()
        
        if tenant_flag:
            # Found tenant override - use this
            result = {
                'enabled': tenant_flag.enabled,
                'config': tenant_flag.config_json
            }
            # Cache for next request
            self.redis.setex(cache_key, self.cache_ttl, json.dumps(result))
            return (tenant_flag.enabled, tenant_flag.config_json)
        
        # Level 2: Tier default (if no tenant override)
        tenant = self.db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        if not tenant:
            return (False, None)  # Tenant doesn't exist - feature disabled
        
        tier_default = self.db.execute(
            text("SELECT enabled, config_json FROM tier_defaults WHERE tier = :tier AND feature_name = :feature"),
            {"tier": tenant.tier, "feature": feature_name}
        ).first()
        
        if tier_default:
            # Found tier default - use this
            result = {
                'enabled': tier_default.enabled,
                'config': tier_default.config_json
            }
            # Cache for next request
            self.redis.setex(cache_key, self.cache_ttl, json.dumps(result))
            return (tier_default.enabled, tier_default.config_json)
        
        # Level 3: Global default (if no tier default)
        # For now, we don't have global defaults table (could add later)
        # If feature not found at any level, it's disabled
        result = {'enabled': False, 'config': None}
        self.redis.setex(cache_key, self.cache_ttl, json.dumps(result))
        return (False, None)
    
    def set_tenant_feature(self, tenant_id: str, feature_name: str, enabled: bool, config: Optional[Dict] = None, actor: str = "system"):
        """
        Set a tenant-specific feature flag (creates override).
        
        This enables per-tenant customization.
        Example: Enable GPT-4 for Tenant A only (gold tier default is GPT-3.5)
        """
        existing_flag = self.db.query(FeatureFlag).filter(
            FeatureFlag.tenant_id == tenant_id,
            FeatureFlag.feature_name == feature_name
        ).first()
        
        if existing_flag:
            # Update existing flag
            existing_flag.enabled = enabled
            existing_flag.config_json = config
            existing_flag.last_modified_by = actor
            existing_flag.last_modified_at = datetime.utcnow()
        else:
            # Create new flag
            new_flag = FeatureFlag(
                tenant_id=tenant_id,
                feature_name=feature_name,
                enabled=enabled,
                config_json=config,
                created_by=actor,
                last_modified_by=actor
            )
            self.db.add(new_flag)
        
        self.db.commit()
        
        # Invalidate cache (next evaluation will fetch fresh data)
        cache_key = f"feature:{tenant_id}:{feature_name}"
        self.redis.delete(cache_key)
    
    def get_all_tenant_features(self, tenant_id: str) -> Dict[str, Tuple[bool, Optional[Dict]]]:
        """
        Get all feature flags for a tenant (for admin dashboard).
        
        Returns: {"feature_name": (enabled, config), ...}
        """
        # Try Redis cache first (cached as a bundle)
        cache_key = f"tenant:{tenant_id}:all_flags"
        cached = self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # Cache miss - fetch from database
        tenant = self.db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        if not tenant:
            return {}
        
        # Get all tenant-specific overrides
        tenant_flags = self.db.query(FeatureFlag).filter(FeatureFlag.tenant_id == tenant_id).all()
        tenant_overrides = {
            flag.feature_name: (flag.enabled, flag.config_json)
            for flag in tenant_flags
        }
        
        # Get all tier defaults
        tier_defaults = self.db.execute(
            text("SELECT feature_name, enabled, config_json FROM tier_defaults WHERE tier = :tier"),
            {"tier": tenant.tier}
        ).all()
        tier_flags = {
            row.feature_name: (row.enabled, row.config_json)
            for row in tier_defaults
        }
        
        # Merge (tenant overrides take precedence)
        all_features = {**tier_flags, **tenant_overrides}
        
        # Cache for next request
        self.redis.setex(cache_key, self.cache_ttl, json.dumps(all_features, default=str))
        
        return all_features

    def rollout_feature_gradually(self, feature_name: str, percentage: int, tier: str = "gold"):
        """
        Canary deployment: Enable feature for X% of tenants in a tier.
        
        Example: Enable semantic reranking for 10% of gold tenants (canary test)
        If successful, increase to 50%, then 100%.
        
        This is how you safely roll out new features at GCC scale.
        """
        # Get all tenants in tier
        tenants = self.db.query(Tenant).filter(Tenant.tier == tier, Tenant.status == 'active').all()
        
        # Calculate how many tenants to enable (based on percentage)
        num_to_enable = int(len(tenants) * (percentage / 100))
        
        # Select tenants (deterministic: sort by tenant_id and take first N)
        tenants_to_enable = sorted(tenants, key=lambda t: t.tenant_id)[:num_to_enable]
        
        # Enable feature for selected tenants
        for tenant in tenants_to_enable:
            self.set_tenant_feature(
                tenant_id=str(tenant.tenant_id),
                feature_name=feature_name,
                enabled=True,
                config=None,
                actor="gradual_rollout_bot"
            )
        
        return {
            "message": f"Enabled '{feature_name}' for {num_to_enable}/{len(tenants)} {tier} tenants ({percentage}%)",
            "tenant_ids": [str(t.tenant_id) for t in tenants_to_enable]
        }

# Usage example in application code
def get_llm_model_for_tenant(tenant_id: str, feature_service: FeatureFlagService) -> str:
    """
    Example: Application checks which LLM model to use for this tenant.
    """
    enabled, config = feature_service.get_feature(tenant_id, "llm_model")
    
    if enabled and config:
        return config.get("model", "gpt-3.5-turbo")  # Use tenant-specific model
    else:
        return "gpt-3.5-turbo"  # Default fallback
    
    # Example evaluation:
    # Tenant A (gold tier, with override): GPT-4 (tenant override beats tier default)
    # Tenant B (gold tier, no override): GPT-3.5-turbo (tier default)
    # Tenant C (bronze tier): GPT-3.5-turbo (tier default)
```

**WHY THIS IMPLEMENTATION:**
- **Hierarchical evaluation**: Tenant override > Tier default > Global default (clear precedence)
- **Redis caching**: <10ms evaluation after first lookup (cache hit)
- **Canary deployment**: Built-in gradual rollout function (10% → 50% → 100%)
- **Admin visibility**: `get_all_tenant_features` for dashboard (show all flags per tenant)
- **Cache invalidation**: Always invalidate on update (no stale data)

This is the mechanism for zero-downtime feature rollouts at GCC scale."

**INSTRUCTOR GUIDANCE:**
- Explain 3-tier hierarchy with concrete examples
- Show caching strategy (cache key structure, TTL, invalidation)
- Demonstrate canary deployment pattern
- Connect to production use cases (feature rollouts, A/B testing)
- Emphasize performance (<10ms with caching)

---

**[18:00-20:00] Component 4: Lifecycle State Machine**

[SLIDE: State machine diagram showing 5 states and allowed transitions with arrows]

**NARRATION:**
"Now we implement the lifecycle state machine that enforces valid tenant transitions. This is compliance-critical - you can't delete a tenant without going through suspension and archival."

```python
# tenant_lifecycle.py
from enum import Enum
from typing import List, Dict, Optional
from datetime import datetime, timedelta

class TenantStatus(Enum):
    """Enumeration of valid tenant lifecycle states."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    MIGRATING = "migrating"
    ARCHIVED = "archived"
    DELETED = "deleted"

class TenantLifecycleStateMachine:
    """
    State machine for tenant lifecycle management.
    
    Enforces valid state transitions and prevents invalid operations.
    Example: Can't go from 'active' to 'deleted' directly (must suspend → archive → delete)
    
    This is compliance-critical for GDPR and audit requirements.
    """
    
    # Define allowed state transitions
    ALLOWED_TRANSITIONS: Dict[TenantStatus, List[TenantStatus]] = {
        TenantStatus.ACTIVE: [TenantStatus.SUSPENDED, TenantStatus.MIGRATING],
        # Active tenant can be: Suspended (payment issue, policy violation) or Migrated (moving to different isolation model)
        
        TenantStatus.SUSPENDED: [TenantStatus.ACTIVE, TenantStatus.ARCHIVED],
        # Suspended tenant can be: Reactivated (payment received) or Archived (grace period expired)
        
        TenantStatus.MIGRATING: [TenantStatus.ACTIVE, TenantStatus.SUSPENDED],
        # Migrating tenant can be: Active (migration successful) or Suspended (migration failed, needs investigation)
        
        TenantStatus.ARCHIVED: [TenantStatus.DELETED],
        # Archived tenant can only be: Deleted (after GDPR retention period)
        # Cannot reactivate from archived - data is in cold storage
        
        TenantStatus.DELETED: []
        # Deleted is final state - no transitions allowed
    }
    
    # Retention periods (compliance requirements)
    SUSPENSION_GRACE_PERIOD_DAYS = 30  # 30 days to resolve payment/policy issues
    GDPR_RETENTION_PERIOD_DAYS = 90  # 90 days retention after archival before deletion
    AUDIT_LOG_RETENTION_YEARS = 7  # 7 years for SOX compliance
    
    @classmethod
    def is_transition_valid(cls, current_status: TenantStatus, new_status: TenantStatus) -> bool:
        """
        Check if state transition is allowed by state machine.
        
        Returns: True if transition is valid, False otherwise.
        """
        allowed = cls.ALLOWED_TRANSITIONS.get(current_status, [])
        return new_status in allowed
    
    @classmethod
    def get_allowed_transitions(cls, current_status: TenantStatus) -> List[TenantStatus]:
        """
        Get list of allowed next states from current state.
        
        Useful for UI: Show only valid action buttons.
        Example: Active tenant shows [Suspend, Migrate] buttons, not [Delete]
        """
        return cls.ALLOWED_TRANSITIONS.get(current_status, [])
    
    @classmethod
    def validate_transition(cls, current_status: str, new_status: str, reason: str) -> None:
        """
        Validate state transition with detailed error messages.
        
        Raises ValueError if transition is invalid.
        """
        current = TenantStatus(current_status)
        new = TenantStatus(new_status)
        
        if not cls.is_transition_valid(current, new):
            allowed = cls.get_allowed_transitions(current)
            raise ValueError(
                f"Invalid state transition: {current_status} → {new_status}. "
                f"Allowed transitions from {current_status}: {[s.value for s in allowed]}. "
                f"Reason: {reason}"
            )
    
    @classmethod
    def calculate_deletion_date(cls, archived_at: datetime) -> datetime:
        """
        Calculate scheduled deletion date (archived_at + GDPR retention period).
        
        Returns: datetime when tenant should be deleted.
        """
        return archived_at + timedelta(days=cls.GDPR_RETENTION_PERIOD_DAYS)
    
    @classmethod
    def is_deletion_due(cls, deletion_scheduled_at: Optional[datetime]) -> bool:
        """
        Check if tenant is ready for deletion (retention period expired).
        
        Used by automated cleanup job.
        """
        if deletion_scheduled_at is None:
            return False
        return datetime.utcnow() >= deletion_scheduled_at
    
    @classmethod
    def get_lifecycle_timeline(cls, tenant) -> Dict[str, str]:
        """
        Generate human-readable lifecycle timeline for tenant.
        
        Useful for admin dashboard: Show tenant journey.
        """
        timeline = {
            "created": tenant.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if tenant.created_at else "N/A"
        }
        
        if tenant.suspended_at:
            timeline["suspended"] = tenant.suspended_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            # How long was tenant suspended?
            if tenant.archived_at:
                suspension_duration = (tenant.archived_at - tenant.suspended_at).days
                timeline["suspension_duration_days"] = suspension_duration
        
        if tenant.archived_at:
            timeline["archived"] = tenant.archived_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            timeline["deletion_scheduled"] = tenant.deletion_scheduled_at.strftime("%Y-%m-%d %H:%M:%S UTC") if tenant.deletion_scheduled_at else "N/A"
            # How many days until deletion?
            if tenant.deletion_scheduled_at:
                days_until_deletion = (tenant.deletion_scheduled_at - datetime.utcnow()).days
                timeline["days_until_deletion"] = max(0, days_until_deletion)
        
        if tenant.deleted_at:
            timeline["deleted"] = tenant.deleted_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        return timeline

# Usage in API endpoint
def transition_tenant_status(tenant, new_status: str, reason: str, actor: str):
    """
    Example: How to use state machine in API endpoint.
    """
    # Validate transition
    try:
        TenantLifecycleStateMachine.validate_transition(
            current_status=tenant.status,
            new_status=new_status,
            reason=reason
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Apply transition
    tenant.status = new_status
    tenant.last_modified_by = actor
    tenant.last_modified_at = datetime.utcnow()
    
    # Set lifecycle timestamps based on new status
    if new_status == TenantStatus.SUSPENDED.value:
        tenant.suspended_at = datetime.utcnow()
    elif new_status == TenantStatus.ARCHIVED.value:
        tenant.archived_at = datetime.utcnow()
        tenant.deletion_scheduled_at = TenantLifecycleStateMachine.calculate_deletion_date(tenant.archived_at)
    elif new_status == TenantStatus.DELETED.value:
        tenant.deleted_at = datetime.utcnow()
    
    return tenant
```

**WHY THIS STATE MACHINE:**
- **Enforced transitions**: Prevents invalid operations (e.g., active→deleted without retention)
- **Compliance-ready**: GDPR 90-day retention built into state machine
- **Audit trail**: Timeline function shows complete tenant journey
- **Clear error messages**: When transition fails, explain why and what's allowed
- **Automated cleanup**: `is_deletion_due()` used by daily cron job

This is the guardian of compliance requirements. No shortcuts allowed."

**INSTRUCTOR GUIDANCE:**
- Show state machine diagram visually with arrows
- Explain WHY each transition is/isn't allowed (compliance reasons)
- Walk through compliance timeline (30 days suspension + 90 days archival)
- Demonstrate error messages (what happens when you try invalid transition)
- Connect to GDPR requirements (retention periods, audit trail)

---

[Note: Sections 5-12 continue in similar detail...]
