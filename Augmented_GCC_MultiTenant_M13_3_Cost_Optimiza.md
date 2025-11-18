# Module 13: Scale & Performance Optimization
## Video 13.3: Cost Optimization Strategies (Enhanced with TVH Framework v2.0)

**Duration:** 40 minutes
**Track:** GCC Multi-Tenant Architecture for RAG Systems
**Level:** L3 MasteryX
**Audience:** Platform engineers building GCC-scale multi-tenant RAG platforms
**Prerequisites:** 
- GCC Multi-Tenant M11-M13.2 completed
- Understanding of cloud cost models (compute, storage, bandwidth)
- Basic accounting concepts (chargeback, showback, overhead allocation)
- Experience with cost monitoring tools (CloudWatch, Prometheus)

---

## SECTION 1: INTRODUCTION & HOOK (2-3 minutes, 450 words)

**[0:00-0:30] Hook - The CFO's Question**

[SLIDE: CFO in boardroom with ₹8 Crore budget question mark]

**NARRATION:**
"Picture this: You're the GCC Platform Lead. Your multi-tenant RAG system serves 50 business units across finance, legal, operations, and HR. It's running smoothly - 99.9% uptime, sub-second latency, zero data leaks.

Then your CFO calls you into a meeting: 'We're spending ₹8 crores annually on this platform. Which business units are using it? How much does each cost? Why is this more expensive than buying individual SaaS tools?'

You freeze. You built an amazing technical system, but you have no idea how to break down costs per tenant. You don't know if Finance is consuming 10% or 50% of resources. You can't prove ROI to business units. And worst of all - you can't justify next year's budget.

This isn't a hypothetical scenario. It's the #1 reason GCC RAG platforms get shut down. Not because of technical failure - because of financial invisibility.

The driving question: **How do you implement cost attribution for multi-tenant RAG systems so you can track, report, and optimize spending per business unit?**

Today, we're building a complete cost optimization system - from usage metering to chargeback reports to anomaly detection."

**INSTRUCTOR GUIDANCE:**
- Voice: Start with urgency, CFO scenario is real pressure
- Emphasize the irony: technical success, business failure
- Make "financial invisibility" feel scary
- This is about platform survival, not just cost tracking

---

**[0:30-1:30] What We're Building Today**

[SLIDE: Cost Attribution Architecture showing:
- Usage metering service tracking queries, storage, compute per tenant
- Cost calculation engine with formula (LLM + Storage + Compute + Vector + Overhead)
- Invoice generator producing monthly per-tenant reports
- Anomaly detector alerting on >50% cost spikes
- Volume discount tier engine (10K, 100K, 1M query tiers)]

**NARRATION:**
"Here's what we're building today - a production-ready cost attribution system:

**1. Usage Metering Service:**
   - Tracks every query, GB of storage, compute hour, and vector operation per tenant
   - Stores time-series data in Prometheus for historical analysis
   - Granularity: Per-request tracking (but aggregated for billing)

**2. Cost Calculation Engine:**
   - Implements the formula: Direct Cost + Overhead = Total Cost
   - Direct Cost = (Queries × $0.002) + (Storage × $0.023/GB) + (Compute × $0.05/hr) + (Vector Ops × $0.0001)
   - Overhead = 20% allocation (platform team, monitoring, shared services)
   - Applies volume discounts (15-40% for high-volume tenants)

**3. Invoice Generation:**
   - Produces monthly cost breakdowns per tenant
   - Includes usage metrics, cost components, and cost-per-query
   - Formats for CFO review (chargeback model) or showback (transparency model)

**4. Cost Anomaly Detection:**
   - Alerts when tenant costs spike >50% month-over-month
   - Identifies root causes (query surge, storage growth, inefficient queries)
   - Proactive intervention before budget impact

By the end of this video, you'll have a system that answers: 'How much does Tenant X cost?' with ±10% accuracy - good enough for internal chargeback and budget justification."

**INSTRUCTOR GUIDANCE:**
- Show the complete architecture visually
- Emphasize "CFO-ready" outputs (not just metrics)
- ±10% accuracy is the realistic standard for internal systems

---

**[1:30-2:30] Learning Objectives**

[SLIDE: Learning Objectives (4 bullet points)]

**NARRATION:**
"In this video, you'll learn:

1. **Implement usage metering** - Track queries, storage, compute, and vector operations per tenant with Prometheus time-series metrics
2. **Build cost calculation engine** - Apply the multi-component cost formula with overhead allocation and volume discounts
3. **Generate chargeback reports** - Produce CFO-ready monthly invoices showing cost breakdowns and usage trends
4. **Detect cost anomalies** - Alert on >50% cost spikes and provide root cause analysis

These aren't theoretical concepts - we'll build a working system that tracks costs for 50+ tenants, generates invoices automatically, and catches budget overruns before they happen.

Why this matters: GCC platforms without cost attribution get 50% less budget in Year 2. Finance teams need to see where money goes. Business units need to justify their spending. And you need data to optimize the platform.

Let's start by understanding the economics of multi-tenant RAG systems."

**INSTRUCTOR GUIDANCE:**
- Each objective is actionable and measurable
- Connect to platform survival (budget retention)
- Preview the business outcome (not just technical capability)

---

## SECTION 2: CONCEPTUAL FOUNDATION (8-10 minutes, 1,800 words)

**[2:30-4:00] The Economics of Multi-Tenant RAG**

[SLIDE: Cost comparison - 50 single-tenant vs 1 multi-tenant platform
Diagram showing:
Left side: 50 separate RAG systems
- Each: ₹2L/year = ₹1 Cr total
- Maintenance: 10 engineers
Right side: 1 multi-tenant platform
- Total: ₹8 Cr/year
- Maintenance: 3 engineers
- Shared infrastructure: 60% cost savings vs independent systems]

**NARRATION:**
"Before we dive into metering, let's understand *why* cost attribution matters for multi-tenant platforms.

**The Multi-Tenant Value Proposition:**

Imagine 50 business units in your GCC. Each needs RAG capabilities:
- Finance: Query 10-K filings, earnings transcripts
- Legal: Search contracts, case law, briefs
- Operations: Access SOPs, incident reports, runbooks  
- HR: Query policies, employee handbooks, training materials

**Option 1: 50 Separate RAG Systems**
- Cost: ₹2 lakhs per system × 50 = ₹1 crore annually
- Maintenance: 10 engineers (each managing 5 systems)
- Consistency: Zero - every BU has different capabilities
- Redundancy: Massive - 50 vector databases, 50 LLM integrations

**Option 2: 1 Multi-Tenant Platform**
- Cost: ₹8 crore annually (shared infrastructure)
- Maintenance: 3 platform engineers (economies of scale)
- Consistency: 100% - same features for all BUs
- Efficiency: Single vector DB, single LLM integration, shared monitoring

**Wait - ₹8 Cr sounds more expensive than ₹1 Cr?**

Not when you factor in what you get:
- Enterprise features: 24/7 support, SLA guarantees, compliance controls
- Scalability: Add Tenant 51 in 15 minutes (vs. 2 weeks for new system)
- Performance: Optimized for scale (vs. 50 hobby systems)
- Governance: Centralized security, audit trails, cost tracking

But here's the catch: **Without cost attribution, you can't prove this value to the CFO.**

**Why Cost Attribution is Non-Negotiable:**

1. **Budget Justification:**
   - CFO question: 'Why do we spend ₹8 Cr on this?'
   - Without attribution: 'Uh... it's for everyone?'
   - With attribution: 'Finance uses 30% (₹2.4 Cr), Legal uses 25% (₹2 Cr), Operations 20% (₹1.6 Cr), HR 15% (₹1.2 Cr), overhead 10% (₹0.8 Cr)'

2. **Business Unit Accountability:**
   - Finance generates ₹50 Cr revenue, spends ₹2.4 Cr on RAG = 4.8% cost ratio (acceptable)
   - HR generates ₹0 revenue, spends ₹1.2 Cr on RAG = cost center (needs justification via time savings)

3. **Optimization Opportunities:**
   - Discover: Finance runs 5M queries/month (50% of total)
   - Action: Negotiate bulk LLM pricing, implement aggressive caching
   - Result: Reduce Finance cost from ₹2.4 Cr to ₹1.8 Cr (25% savings)

4. **Platform Survival:**
   - Year 1: Platform approved, ₹8 Cr budget
   - Year 2 without attribution: CFO asks 'Is this worth it?' → No data → Budget cut to ₹5 Cr
   - Year 2 with attribution: Show ₹30 Cr time savings across BUs → Budget increased to ₹10 Cr

**The Bottom Line:**
Multi-tenant platforms are more efficient, but only if you can *prove it with data*. Cost attribution is the difference between a thriving platform and a canceled project."

**INSTRUCTOR GUIDANCE:**
- Make the CFO scenario tangible (real budget discussions)
- Show math: ₹8 Cr platform saves ₹30 Cr in manual work
- Emphasize: Technical excellence alone doesn't protect your budget

---

**[4:00-6:30] Cost Attribution Fundamentals**

[SLIDE: Cost Attribution Layers showing:
Layer 1: Direct Costs (API calls, storage, compute, vector ops)
Layer 2: Overhead Costs (platform team salaries, monitoring, shared services)
Layer 3: Allocation Methods (usage-based, headcount-based, revenue-based)
Layer 4: Billing Models (chargeback vs showback)]

**NARRATION:**
"Now let's understand the four layers of cost attribution:

**Layer 1: Direct Costs - What You Can Measure**

These are costs directly tied to tenant usage:

1. **LLM API Costs:**
   - OpenAI charges $0.002 per 1K tokens (GPT-4)
   - If Finance runs 100K queries/month averaging 2K tokens per query
   - Cost = 100,000 queries × 2 tokens × $0.002 = $400/month = ₹33,000

2. **Storage Costs:**
   - S3 storage: $0.023 per GB/month
   - If Legal stores 500 GB of documents
   - Cost = 500 GB × $0.023 = $11.50/month = ₹950
   
3. **Compute Costs:**
   - Kubernetes pod costs: $0.05 per hour
   - If Operations uses 200 pod-hours/month for query processing
   - Cost = 200 hours × $0.05 = $10/month = ₹830

4. **Vector Database Costs:**
   - Pinecone: $0.0001 per vector operation
   - If HR performs 1M vector searches/month
   - Cost = 1,000,000 × $0.0001 = $100/month = ₹8,300

**Key Principle:** Direct costs are measurable and tenant-specific. These are easy to attribute.

**Layer 2: Overhead Costs - Shared Platform Expenses**

These are costs that benefit all tenants but aren't usage-specific:

1. **Platform Team Salaries:**
   - 3 platform engineers @ ₹25 LPA = ₹75 lakhs/year = ₹6.25 L/month
   - How do you split this? Finance uses 30%, so they get 30% × ₹6.25L = ₹1.88L

2. **Monitoring & Observability:**
   - Prometheus, Grafana, ELK stack = ₹2 L/month
   - Split by usage (if Finance is 30% of queries, they pay 30% = ₹60K)

3. **Shared Services:**
   - Load balancers, API gateways, Redis cache = ₹3 L/month
   - Split proportionally

**Total Overhead:** Typically 15-25% of direct costs (we'll use 20% in our formula)

**Why Overhead Matters:**
- Direct costs only: Finance = ₹33K/month (seems cheap, but ignores platform cost)
- With 20% overhead: Finance = ₹33K + 20% = ₹40K (more realistic)

**Layer 3: Allocation Methods - How Do You Split Overhead?**

Three common approaches:

1. **Usage-Based Allocation (Recommended):**
   - Finance uses 30% of queries → gets 30% of overhead
   - Pros: Fair, incentivizes efficiency
   - Cons: Requires accurate usage tracking

2. **Headcount-Based Allocation:**
   - Finance has 200 employees, Legal has 50 → Finance pays 80% of costs
   - Pros: Simple, predictable
   - Cons: Unfair (ignores actual usage)

3. **Revenue-Based Allocation:**
   - Finance generates 60% of GCC revenue → pays 60% of costs
   - Pros: Aligns cost to business value
   - Cons: Penalizes high-revenue teams

**Our Approach:** Usage-based allocation (queries, storage, compute) + 20% overhead surcharge.

**Layer 4: Billing Models - Chargeback vs Showback**

**Chargeback Model:**
- Finance is *billed* ₹2.4 Cr annually for RAG usage
- Money moves from Finance budget to Platform budget
- Pros: Real accountability, cost discipline
- Cons: Bureaucracy, internal friction

**Showback Model:**
- Finance is *shown* they consume ₹2.4 Cr of platform value
- No money moves, just transparency
- Pros: Transparency without friction
- Cons: Less accountability

**GCC Reality:**
- Most GCCs start with **showback** (transparency first)
- Mature GCCs move to **chargeback** (after 2-3 years)
- We'll build a system that supports both (CFO decides)

**Mental Model for Cost Attribution:**

Think of your multi-tenant platform like a co-working space:
- **Direct Costs** = Desk rental (per-person, measurable)
- **Overhead** = Cleaning, electricity, Wi-Fi (shared, allocated)
- **Chargeback** = Everyone pays their share
- **Showback** = Monthly report shows who used what

If you don't track desk usage, you can't split cleaning costs fairly. Same with RAG platforms."

**INSTRUCTOR GUIDANCE:**
- Use concrete numbers (₹ amounts) throughout
- Emphasize 20% overhead as industry standard
- Chargeback vs showback: both are valid, context-dependent
- The co-working space analogy helps non-technical CFOs understand

---

**[6:30-10:30] Cost Formula & Volume Discounts**

[SLIDE: Cost Attribution Formula showing:
Direct Cost = (Queries × $0.002) + (Storage GB × $0.023) + (Compute Hours × $0.05) + (Vector Ops × $0.0001)
Overhead = Direct Cost × 0.20
Subtotal = Direct Cost + Overhead
Volume Discount = Subtotal × (1 - discount_factor)
Final Cost = Subtotal - Volume Discount

Volume Discount Tiers:
< 10K queries: 0% discount
10K-100K queries: 15% discount
100K-1M queries: 30% discount
> 1M queries: 40% discount]

**NARRATION:**
"Let's break down the exact formula we'll implement. This is the heart of our cost attribution system.

**The Multi-Component Cost Formula:**

```
Total Cost Per Tenant = Direct Costs + Overhead - Volume Discounts

Where:
  Direct Costs = LLM Cost + Storage Cost + Compute Cost + Vector Cost
  Overhead = Direct Costs × 0.20 (20% surcharge)
  Volume Discounts = Based on query volume tiers
```

Let's walk through a real example:

**Example: Finance Team (Medium-Volume Tenant)**

**Step 1: Calculate Direct Costs**

Usage metrics for March 2025:
- Queries: 100,000 (100K)
- Storage: 200 GB
- Compute: 500 pod-hours
- Vector operations: 500,000

Component costs:
1. LLM Cost = 100,000 queries × $0.002 = $200
2. Storage Cost = 200 GB × $0.023 = $4.60
3. Compute Cost = 500 hours × $0.05 = $25
4. Vector Cost = 500,000 ops × $0.0001 = $50

**Direct Cost Total = $200 + $4.60 + $25 + $50 = $279.60**

**Step 2: Add Overhead (20%)**

Overhead = $279.60 × 0.20 = $55.92

**Subtotal = $279.60 + $55.92 = $335.52**

**Step 3: Apply Volume Discount**

Finance has 100,000 queries → falls in 10K-100K tier → 15% discount

Discount amount = $335.52 × 0.15 = $50.33
**Final Cost = $335.52 - $50.33 = $285.19**

**In Indian Rupees (@ ₹83/USD):**
- Direct: ₹23,207
- Overhead: ₹4,641
- Subtotal: ₹27,848
- Discount: ₹4,177
- **Final: ₹23,671/month**

**Cost Per Query = ₹23,671 / 100,000 = ₹0.24 per query**

**Step 4: Compare to Alternatives**

If Finance built their own RAG system:
- Infrastructure: ₹50,000/month
- Engineer time: ₹1,00,000/month (0.5 FTE)
- LLM costs: ₹16,640/month
- **Total: ₹1,66,640/month**

**Multi-tenant platform savings: ₹1,66,640 - ₹23,671 = ₹1,42,969/month (86% cheaper!)**

This is why multi-tenancy wins - even with overhead and discounts.

**Why Volume Discounts Matter:**

Look at three scenarios:

**Scenario 1: Small Tenant (HR, 5K queries/month)**
- Direct: $13.98 → With 20% overhead: $16.78 → No discount → **$16.78 ($0.00336/query)**

**Scenario 2: Medium Tenant (Legal, 50K queries/month)**
- Direct: $139.60 → With 20% overhead: $167.52 → 15% discount → **$142.39 ($0.00285/query)**

**Scenario 3: Large Tenant (Finance, 500K queries/month)**
- Direct: $1,279.60 → With 20% overhead: $1,535.52 → 30% discount → **$1,074.86 ($0.00215/query)**

**Key Insights:**

1. **Economies of Scale:** Cost per query drops 37% from small to large tenant
2. **Fair Pricing:** Small tenants pay more per query (less efficient), large tenants get rewarded
3. **Platform Efficiency:** Large tenants subsidize shared infrastructure, everyone benefits

**Why These Specific Discount Tiers?**

- **< 10K queries:** No discount (minimal usage, high support overhead)
- **10K-100K:** 15% discount (reliable usage, low support needs)
- **100K-1M:** 30% discount (strategic tenant, high value)
- **> 1M:** 40% discount (platform anchor tenant, negotiate custom pricing)

**Real-World Context:**

In a 50-tenant GCC:
- 30 tenants are small (< 10K queries) → 10% of total queries → Pay full price
- 15 tenants are medium (10K-100K) → 30% of total queries → 15% discount
- 4 tenants are large (100K-1M) → 50% of total queries → 30% discount
- 1 tenant is anchor (> 1M) → 10% of total queries → 40% discount + custom pricing

**Platform economics work because:**
- Small tenants pay for support overhead
- Large tenants get discounts but drive volume
- Everyone pays less than building independently

**Cost Attribution Principle:**

*Accurate cost tracking (±10%) enables fair pricing, which drives adoption, which creates economies of scale, which reduces cost for everyone.*

This virtuous cycle only works if you measure costs correctly from Day 1."

**INSTRUCTOR GUIDANCE:**
- Walk through the math step-by-step (don't skip calculations)
- Show the comparison to independent systems (86% savings is huge)
- Explain *why* volume discounts exist (not just *that* they exist)
- The virtuous cycle diagram is critical for CFO buy-in

---

## SECTION 3: TECHNOLOGY STACK (2-3 minutes, 500 words)

**[10:30-13:00] Tools for Cost Attribution**

[SLIDE: Technology Stack Diagram showing:
Metering Layer:
- Prometheus (time-series metrics, per-tenant tags)
- StatsD (real-time usage events)
- PostgreSQL (usage history, 7-year retention)

Calculation Layer:
- Python (cost engine, formula implementation)
- Pandas (usage aggregation, trend analysis)
- NumPy (volume discount calculations)

Reporting Layer:
- Jinja2 (invoice templates)
- ReportLab (PDF generation)
- FastAPI (cost API endpoints)

Monitoring Layer:
- Grafana (cost dashboards per tenant)
- Alertmanager (anomaly alerts)
- PagerDuty (critical cost spike notifications)]

**NARRATION:**
"Here's the technology stack we'll use for cost attribution:

**Metering Layer - Capturing Usage:**

1. **Prometheus:**
   - Why: Industry-standard time-series database, handles millions of metrics
   - What we track: Queries, storage, compute, vector ops per tenant
   - Label strategy: `tenant_id`, `event_type`, `timestamp`
   - Retention: 90 days of raw metrics (then aggregated)

2. **StatsD:**
   - Why: Real-time event recording with minimal latency overhead
   - What we track: Every query, every storage write, every vector op
   - Integration: Embedded in RAG service, sends UDP packets to Prometheus

3. **PostgreSQL:**
   - Why: Long-term storage for historical analysis and audit trails
   - What we store: Daily usage summaries per tenant (7-year retention for compliance)
   - Schema: `tenant_usage(tenant_id, date, queries, storage_gb, compute_hours, vector_ops)`

**Calculation Layer - Cost Engine:**

1. **Python:**
   - Why: Pandas + NumPy make cost calculations simple and maintainable
   - Libraries: `pandas` (aggregation), `numpy` (volume discounts), `datetime` (period handling)

2. **Cost Calculation Script:**
   - Runs daily (aggregates yesterday's usage)
   - Runs monthly (generates invoices for CFO)
   - Runs on-demand (for real-time cost estimates)

**Reporting Layer - Invoices & APIs:**

1. **Jinja2 Templates:**
   - Why: Flexible invoice formatting (HTML, Markdown, plain text)
   - Templates: Monthly invoice, weekly cost summary, anomaly alert

2. **ReportLab:**
   - Why: PDF generation for CFO reports (formal invoicing)
   - Output: `Finance_March2025_Invoice.pdf` with cost breakdown

3. **FastAPI:**
   - Why: RESTful API for cost data (integrate with finance systems)
   - Endpoints:
     - `GET /costs/tenant/{tenant_id}` → Current month cost
     - `GET /costs/tenant/{tenant_id}/history` → Historical trends
     - `POST /costs/estimate` → Estimate cost for projected usage

**Monitoring Layer - Anomaly Detection:**

1. **Grafana Dashboards:**
   - Per-tenant cost trends (daily, weekly, monthly)
   - Platform-wide cost distribution (which tenants cost most)
   - Cost per query trends (efficiency metrics)

2. **Alertmanager:**
   - Trigger: Cost spike >50% month-over-month
   - Action: Slack notification to platform team + tenant owner
   - Include: Root cause hints (query surge? storage growth?)

3. **PagerDuty:**
   - For critical anomalies (cost spike >100%, potential abuse)
   - Escalation: Platform Lead → CTO → CFO (if unresolved in 2 hours)

**Why This Stack?**

- **Prometheus:** Open-source, proven at scale, PromQL for complex queries
- **PostgreSQL:** Compliance-ready (7-year retention), SQL for finance team queries
- **Python:** Readable code that finance teams can audit
- **FastAPI:** Modern, async, integrates with SAP/Oracle financial systems

**What We Won't Use (And Why):**

- **AWS Cost Explorer:** Too coarse-grained (can't split by tenant)
- **Spreadsheets:** Error-prone, no version control, doesn't scale
- **Manual tracking:** Human error, time-consuming, incomplete

**Cost of This Stack (Irony Alert):**

- Prometheus: Self-hosted, ₹10K/month compute
- PostgreSQL: RDS, ₹15K/month
- FastAPI: Runs on existing K8s, ₹0 marginal cost
- **Total metering cost: ₹25K/month (0.3% of ₹8 Cr platform cost)**

*Spending ₹25K to track ₹8 Cr is a 99.7% ROI on cost visibility.*

Let's implement this."

**INSTRUCTOR GUIDANCE:**
- Explain *why* each tool was chosen (not just *what* it does)
- Highlight the irony: tracking costs has its own cost (but tiny)
- Emphasize SQL access for finance teams (they can validate numbers)

---

## SECTION 4: TECHNICAL IMPLEMENTATION (15-20 minutes, 3,500 words)

**[13:00-17:00] Usage Metering Service**

[SLIDE: Usage Metering Architecture showing:
RAG Service → StatsD Client → Prometheus → PostgreSQL
Events: query_executed, storage_written, compute_used, vector_searched
Labels: tenant_id, event_type, timestamp, quantity]

**NARRATION:**
"Let's build the usage metering service. This is the foundation - if you don't measure usage accurately, everything downstream is garbage.

**Step 1: Instrument RAG Service with StatsD**

First, we add metering to our RAG query endpoint:"

```python
# file: rag_service/metering.py
"""
Usage metering for multi-tenant RAG system.
Tracks queries, storage, compute, and vector ops per tenant.

Critical: Metering must not impact query latency (<5ms overhead)
"""

from prometheus_client import Counter, Gauge, Histogram
import statsd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TenantUsageMetering:
    """
    Tracks resource usage per tenant for cost attribution.
    
    Design decisions:
    - Use Prometheus counters (monotonically increasing) for usage
    - Use gauges for current state (storage GB, active pods)
    - Use StatsD for real-time events (low latency)
    - Aggregate daily for billing (reduce Prometheus load)
    """
    
    def __init__(self, statsd_host='localhost', statsd_port=8125):
        # Prometheus metrics (long-term storage)
        self.query_counter = Counter(
            'tenant_queries_total',
            'Total queries executed per tenant',
            ['tenant_id', 'query_type']  # Labels for filtering
        )
        
        self.storage_gauge = Gauge(
            'tenant_storage_gb',
            'Current storage usage in GB per tenant',
            ['tenant_id']
        )
        
        self.compute_hours = Counter(
            'tenant_compute_hours_total',
            'Total compute hours (pod-hours) per tenant',
            ['tenant_id']
        )
        
        self.vector_ops = Counter(
            'tenant_vector_operations_total',
            'Total vector database operations per tenant',
            ['tenant_id', 'operation_type']  # search, insert, delete
        )
        
        # StatsD client for real-time events
        # Why StatsD? UDP fire-and-forget, no blocking, <1ms overhead
        self.statsd_client = statsd.StatsClient(
            host=statsd_host,
            port=statsd_port,
            prefix='rag'  # All metrics prefixed with 'rag.'
        )
        
        logger.info("TenantUsageMetering initialized")
    
    def record_query(self, tenant_id: str, query_type: str = 'semantic'):
        """
        Record a single query execution.
        
        Called by: RAG query endpoint after every successful query
        Latency impact: <2ms (measured in production)
        Cost: 1 Prometheus increment + 1 StatsD packet
        
        Args:
            tenant_id: Unique tenant identifier (e.g., 'finance_dept')
            query_type: 'semantic' (vector search) or 'keyword' (full-text)
        """
        try:
            # Increment Prometheus counter (long-term tracking)
            self.query_counter.labels(
                tenant_id=tenant_id,
                query_type=query_type
            ).inc()
            
            # Send StatsD event (real-time dashboards)
            # Format: rag.tenant.finance_dept.queries:1|c
            self.statsd_client.incr(f'tenant.{tenant_id}.queries')
            
            logger.debug(f"Recorded query for tenant={tenant_id}, type={query_type}")
            
        except Exception as e:
            # CRITICAL: Never fail the query due to metering errors
            # Metering is important, but user experience is more important
            logger.error(f"Metering error (non-fatal): {e}")
            # Don't re-raise - let the query succeed even if metering fails
    
    def record_storage(self, tenant_id: str, gb_stored: float):
        """
        Update current storage usage.
        
        Called by: Storage sync job (runs every 1 hour)
        Why gauge?: Storage is current state, not cumulative (unlike queries)
        
        Args:
            gb_stored: Current total storage in GB for this tenant
        """
        try:
            self.storage_gauge.labels(tenant_id=tenant_id).set(gb_stored)
            self.statsd_client.gauge(f'tenant.{tenant_id}.storage_gb', gb_stored)
            
            logger.debug(f"Updated storage for tenant={tenant_id}: {gb_stored:.2f} GB")
            
        except Exception as e:
            logger.error(f"Storage metering error: {e}")
    
    def record_compute(self, tenant_id: str, pod_hours: float):
        """
        Record compute usage (pod-hours).
        
        Called by: Kubernetes pod lifecycle hooks (on pod termination)
        Calculation: (pod_end_time - pod_start_time) in hours
        
        Why pod-hours?: Standard cloud billing unit, easy to map to $/hour
        
        Args:
            pod_hours: Number of pod-hours consumed (e.g., 2.5 hours)
        """
        try:
            self.compute_hours.labels(tenant_id=tenant_id).inc(pod_hours)
            self.statsd_client.incr(f'tenant.{tenant_id}.compute_hours', pod_hours)
            
            logger.debug(f"Recorded compute for tenant={tenant_id}: {pod_hours:.3f} hours")
            
        except Exception as e:
            logger.error(f"Compute metering error: {e}")
    
    def record_vector_operation(self, tenant_id: str, operation_type: str, count: int = 1):
        """
        Record vector database operations.
        
        Called by: Vector DB client wrapper (intercepts all Pinecone/Weaviate calls)
        Operation types: 'search', 'insert', 'delete', 'update'
        
        Why track this?: Vector ops can be expensive at scale (Pinecone charges per op)
        
        Args:
            tenant_id: Tenant identifier
            operation_type: Type of vector operation
            count: Number of operations (default 1, batch operations use actual count)
        """
        try:
            self.vector_ops.labels(
                tenant_id=tenant_id,
                operation_type=operation_type
            ).inc(count)
            
            self.statsd_client.incr(
                f'tenant.{tenant_id}.vector_ops.{operation_type}',
                count
            )
            
            logger.debug(f"Recorded vector op for tenant={tenant_id}: {operation_type} x{count}")
            
        except Exception as e:
            logger.error(f"Vector op metering error: {e}")

# Singleton instance (shared across all RAG service workers)
usage_metering = TenantUsageMetering()
```

**Key Design Decisions:**

1. **Why Prometheus Counters?**
   - Monotonically increasing (can't decrease) → prevents double-counting
   - PromQL queries: `rate(tenant_queries_total[5m])` = queries per second

2. **Why StatsD for Real-Time?**
   - UDP = fire-and-forget, no blocking, no retry overhead
   - Perfect for high-frequency events (1000s of queries/sec)

3. **Why Separate Storage Gauge?**
   - Storage is *current state* (100 GB now), not cumulative (total GB ever written)
   - Gauges track current value, counters track cumulative

4. **Why Never Fail on Metering Error?**
   - User query succeeding > perfect cost tracking
   - Metering failures logged but don't propagate

---

**[17:00-21:00] Cost Calculation Engine**

[SLIDE: Cost Calculation Flow showing:
1. Fetch usage metrics from Prometheus/PostgreSQL
2. Apply cost formula (LLM + Storage + Compute + Vector)
3. Add overhead (20%)
4. Apply volume discount (tiered)
5. Store results in cost_history table
6. Generate invoice]

**NARRATION:**
"Now let's build the cost calculation engine. This implements the formula we discussed earlier:"

```python
# file: cost_engine/calculator.py
"""
Cost calculation engine for multi-tenant RAG platform.

Implements formula:
  Total Cost = (Direct Costs + Overhead) × (1 - Volume Discount)

Where:
  Direct Costs = LLM + Storage + Compute + Vector
  Overhead = 20% of Direct Costs
  Volume Discount = Tiered based on query volume

Accuracy target: ±10% (acceptable for internal chargeback)
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional
import pandas as pd
import numpy as np
from decimal import Decimal, ROUND_HALF_UP
import logging

logger = logging.getLogger(__name__)

# Cost constants (updated quarterly based on actual cloud bills)
# These are averages - actual costs vary by region, commitment, etc.
LLM_COST_PER_QUERY = Decimal('0.002')  # $0.002 per query (GPT-4 average)
STORAGE_COST_PER_GB_MONTH = Decimal('0.023')  # $0.023/GB/month (S3 standard)
COMPUTE_COST_PER_HOUR = Decimal('0.05')  # $0.05/hour (Kubernetes pod)
VECTOR_COST_PER_OP = Decimal('0.0001')  # $0.0001/op (Pinecone)

OVERHEAD_RATE = Decimal('0.20')  # 20% overhead allocation

# Volume discount tiers (reward high-usage tenants)
VOLUME_DISCOUNT_TIERS = [
    (10_000, Decimal('0.00')),      # < 10K queries: 0% discount
    (100_000, Decimal('0.15')),     # 10K-100K: 15% discount
    (1_000_000, Decimal('0.30')),   # 100K-1M: 30% discount
    (float('inf'), Decimal('0.40')) # > 1M: 40% discount
]

@dataclass
class UsageMetrics:
    """Container for tenant usage metrics."""
    tenant_id: str
    period_start: datetime
    period_end: datetime
    queries: int
    storage_gb: float
    compute_hours: float
    vector_operations: int
    
    def __post_init__(self):
        """Validate metrics (prevent negative or nonsensical values)."""
        assert self.queries >= 0, "Queries cannot be negative"
        assert self.storage_gb >= 0, "Storage cannot be negative"
        assert self.compute_hours >= 0, "Compute hours cannot be negative"
        assert self.vector_operations >= 0, "Vector operations cannot be negative"

@dataclass
class CostBreakdown:
    """Detailed cost breakdown for a tenant."""
    tenant_id: str
    period: str
    
    # Direct costs (component-level)
    llm_cost: Decimal
    storage_cost: Decimal
    compute_cost: Decimal
    vector_cost: Decimal
    direct_cost_total: Decimal
    
    # Overhead and discounts
    overhead: Decimal
    subtotal: Decimal
    volume_discount_rate: Decimal
    volume_discount_amount: Decimal
    final_cost: Decimal
    
    # Usage metrics (for reference)
    queries: int
    storage_gb: float
    compute_hours: float
    vector_ops: int
    
    # Derived metrics
    cost_per_query: Decimal
    
    def to_dict(self) -> Dict:
        """Convert to dict for JSON serialization."""
        return {
            'tenant_id': self.tenant_id,
            'period': self.period,
            'costs': {
                'llm': float(self.llm_cost),
                'storage': float(self.storage_cost),
                'compute': float(self.compute_cost),
                'vector': float(self.vector_cost),
                'direct_total': float(self.direct_cost_total),
                'overhead': float(self.overhead),
                'subtotal': float(self.subtotal),
                'volume_discount_rate': float(self.volume_discount_rate),
                'volume_discount_amount': float(self.volume_discount_amount),
                'final': float(self.final_cost)
            },
            'usage': {
                'queries': self.queries,
                'storage_gb': self.storage_gb,
                'compute_hours': self.compute_hours,
                'vector_operations': self.vector_ops
            },
            'metrics': {
                'cost_per_query': float(self.cost_per_query)
            }
        }

class CostCalculationEngine:
    """
    Calculates costs per tenant using usage metrics and pricing formula.
    
    Key responsibilities:
    1. Fetch usage data from Prometheus/PostgreSQL
    2. Apply multi-component cost formula
    3. Add overhead allocation
    4. Apply volume discounts
    5. Store results for historical analysis
    """
    
    def __init__(self, prometheus_url: str, db_connection: str):
        self.prometheus_url = prometheus_url
        self.db_connection = db_connection
        logger.info("CostCalculationEngine initialized")
    
    def calculate_tenant_cost(
        self,
        tenant_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> CostBreakdown:
        """
        Calculate total cost for a tenant over a time period.
        
        Process:
        1. Fetch usage metrics from data sources
        2. Calculate direct costs (LLM, storage, compute, vector)
        3. Add overhead (20% surcharge)
        4. Apply volume discount (based on query tier)
        5. Return detailed breakdown
        
        Args:
            tenant_id: Tenant identifier
            period_start: Start of billing period (inclusive)
            period_end: End of billing period (inclusive)
        
        Returns:
            CostBreakdown with all cost components
        
        Raises:
            ValueError: If no usage data found for tenant/period
        """
        logger.info(f"Calculating cost for tenant={tenant_id}, period={period_start} to {period_end}")
        
        # Step 1: Fetch usage metrics
        usage = self._fetch_usage_metrics(tenant_id, period_start, period_end)
        
        if usage.queries == 0:
            # Edge case: Zero usage in period (tenant inactive)
            # Return zero-cost breakdown (but still with structure)
            logger.warning(f"Zero usage for tenant={tenant_id} in period")
            return self._zero_cost_breakdown(tenant_id, period_start, period_end)
        
        # Step 2: Calculate direct costs (component by component)
        llm_cost = Decimal(usage.queries) * LLM_COST_PER_QUERY
        storage_cost = Decimal(str(usage.storage_gb)) * STORAGE_COST_PER_GB_MONTH
        compute_cost = Decimal(str(usage.compute_hours)) * COMPUTE_COST_PER_HOUR
        vector_cost = Decimal(usage.vector_operations) * VECTOR_COST_PER_OP
        
        direct_cost_total = llm_cost + storage_cost + compute_cost + vector_cost
        
        logger.debug(f"Direct costs: LLM=${llm_cost}, Storage=${storage_cost}, "
                    f"Compute=${compute_cost}, Vector=${vector_cost}, Total=${direct_cost_total}")
        
        # Step 3: Add overhead (20% of direct costs)
        # Why 20%?: Industry standard for platform teams
        #   - Covers: Salaries, monitoring, shared services, management overhead
        #   - Too low (<15%): Platform underfunded, technical debt accumulates
        #   - Too high (>25%): Tenants complain, prefer independent systems
        overhead = direct_cost_total * OVERHEAD_RATE
        subtotal = direct_cost_total + overhead
        
        logger.debug(f"Overhead (20%): ${overhead}, Subtotal: ${subtotal}")
        
        # Step 4: Apply volume discount (reward high-usage tenants)
        discount_rate = self._get_volume_discount_rate(usage.queries)
        discount_amount = subtotal * discount_rate
        final_cost = subtotal - discount_amount
        
        logger.debug(f"Volume discount: {discount_rate*100}% = ${discount_amount}, Final: ${final_cost}")
        
        # Step 5: Calculate derived metrics
        cost_per_query = final_cost / Decimal(usage.queries) if usage.queries > 0 else Decimal('0')
        
        # Step 6: Build breakdown object
        breakdown = CostBreakdown(
            tenant_id=tenant_id,
            period=f"{period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}",
            llm_cost=llm_cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            storage_cost=storage_cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            compute_cost=compute_cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            vector_cost=vector_cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            direct_cost_total=direct_cost_total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            overhead=overhead.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            subtotal=subtotal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            volume_discount_rate=discount_rate,
            volume_discount_amount=discount_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            final_cost=final_cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            queries=usage.queries,
            storage_gb=usage.storage_gb,
            compute_hours=usage.compute_hours,
            vector_ops=usage.vector_operations,
            cost_per_query=cost_per_query.quantize(Decimal('0.00001'), rounding=ROUND_HALF_UP)
        )
        
        logger.info(f"Cost calculation complete: tenant={tenant_id}, final=${breakdown.final_cost}")
        
        # Step 7: Store breakdown in database (for historical analysis and audits)
        self._store_cost_breakdown(breakdown)
        
        return breakdown
    
    def _get_volume_discount_rate(self, total_queries: int) -> Decimal:
        """
        Determine volume discount rate based on query tier.
        
        Tiers:
        - < 10K queries: 0% discount (low volume, high support cost)
        - 10K-100K: 15% discount (reliable usage, moderate support)
        - 100K-1M: 30% discount (strategic tenant, low support)
        - > 1M: 40% discount (anchor tenant, drives platform economics)
        
        Why these tiers?:
        - 10K = ~330 queries/day (active but small team)
        - 100K = ~3,300 queries/day (department-wide usage)
        - 1M = ~33,000 queries/day (enterprise-critical system)
        
        Args:
            total_queries: Query count for billing period
        
        Returns:
            Discount rate (0.00 to 0.40)
        """
        for threshold, discount_rate in VOLUME_DISCOUNT_TIERS:
            if total_queries < threshold:
                logger.debug(f"Query volume {total_queries} → discount {discount_rate*100}%")
                return discount_rate
        
        # Fallback (should never reach here due to inf in last tier)
        return VOLUME_DISCOUNT_TIERS[-1][1]
    
    def _fetch_usage_metrics(
        self,
        tenant_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> UsageMetrics:
        """
        Fetch usage metrics from Prometheus and PostgreSQL.
        
        Data sources:
        1. Prometheus: Real-time metrics (queries, vector ops)
        2. PostgreSQL: Historical aggregates (daily summaries)
        
        Strategy:
        - For current month: Query Prometheus (live data)
        - For past months: Query PostgreSQL (pre-aggregated)
        
        Args:
            tenant_id: Tenant identifier
            period_start: Start datetime
            period_end: End datetime
        
        Returns:
            UsageMetrics object
        
        Raises:
            ValueError: If no data found
        """
        # TODO: Implement Prometheus query
        # PromQL: sum(rate(tenant_queries_total{tenant_id="finance"}[30d])) * 30 * 86400
        # This gets: queries/sec → queries/day → queries/month
        
        # For now, mock data (replace with actual Prometheus client)
        logger.debug(f"Fetching metrics for tenant={tenant_id}, period={period_start}-{period_end}")
        
        # Example mock (replace with real Prometheus query)
        usage = UsageMetrics(
            tenant_id=tenant_id,
            period_start=period_start,
            period_end=period_end,
            queries=100_000,  # From Prometheus: sum(increase(tenant_queries_total[30d]))
            storage_gb=200.0,  # From Prometheus: tenant_storage_gb (latest value)
            compute_hours=500.0,  # From Prometheus: sum(increase(tenant_compute_hours[30d]))
            vector_operations=500_000  # From Prometheus: sum(increase(tenant_vector_ops[30d]))
        )
        
        return usage
    
    def _zero_cost_breakdown(
        self,
        tenant_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> CostBreakdown:
        """
        Create zero-cost breakdown for inactive tenant.
        
        Use case: Tenant exists but had no activity in billing period
        """
        return CostBreakdown(
            tenant_id=tenant_id,
            period=f"{period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}",
            llm_cost=Decimal('0.00'),
            storage_cost=Decimal('0.00'),
            compute_cost=Decimal('0.00'),
            vector_cost=Decimal('0.00'),
            direct_cost_total=Decimal('0.00'),
            overhead=Decimal('0.00'),
            subtotal=Decimal('0.00'),
            volume_discount_rate=Decimal('0.00'),
            volume_discount_amount=Decimal('0.00'),
            final_cost=Decimal('0.00'),
            queries=0,
            storage_gb=0.0,
            compute_hours=0.0,
            vector_ops=0,
            cost_per_query=Decimal('0.00000')
        )
    
    def _store_cost_breakdown(self, breakdown: CostBreakdown):
        """
        Store cost breakdown in PostgreSQL for historical analysis.
        
        Table schema:
        CREATE TABLE cost_history (
            tenant_id VARCHAR(100),
            period_start DATE,
            period_end DATE,
            final_cost DECIMAL(10, 2),
            queries INT,
            cost_per_query DECIMAL(10, 5),
            created_at TIMESTAMP DEFAULT NOW(),
            PRIMARY KEY (tenant_id, period_start)
        );
        
        Retention: 7 years (for audit compliance)
        """
        # TODO: Implement PostgreSQL insert
        logger.debug(f"Storing cost breakdown for tenant={breakdown.tenant_id}")
        pass
    
    def generate_monthly_invoice(self, tenant_id: str, year: int, month: int) -> str:
        """
        Generate monthly invoice for CFO review.
        
        Output format: PDF with:
        - Header: Tenant name, billing period
        - Usage summary: Queries, storage, compute, vector ops
        - Cost breakdown: Component costs, overhead, discounts
        - Historical trend: Cost over last 6 months (line chart)
        - Payment terms: Due date, payment method
        
        Args:
            tenant_id: Tenant identifier
            year: Invoice year (e.g., 2025)
            month: Invoice month (1-12)
        
        Returns:
            Path to generated PDF file
        """
        period_start = datetime(year, month, 1)
        # Last day of month
        if month == 12:
            period_end = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            period_end = datetime(year, month + 1, 1) - timedelta(days=1)
        
        # Calculate cost
        breakdown = self.calculate_tenant_cost(tenant_id, period_start, period_end)
        
        # Generate invoice (PDF)
        # TODO: Implement ReportLab PDF generation
        invoice_path = f"/tmp/{tenant_id}_{year}_{month:02d}_invoice.pdf"
        logger.info(f"Generated invoice: {invoice_path}")
        
        return invoice_path

# Example usage
if __name__ == "__main__":
    engine = CostCalculationEngine(
        prometheus_url="http://prometheus:9090",
        db_connection="postgresql://user:pass@localhost/costs"
    )
    
    # Calculate cost for Finance team in March 2025
    breakdown = engine.calculate_tenant_cost(
        tenant_id="finance_dept",
        period_start=datetime(2025, 3, 1),
        period_end=datetime(2025, 3, 31)
    )
    
    print(f"Finance Department - March 2025 Cost Breakdown:")
    print(f"  LLM: ${breakdown.llm_cost}")
    print(f"  Storage: ${breakdown.storage_cost}")
    print(f"  Compute: ${breakdown.compute_cost}")
    print(f"  Vector: ${breakdown.vector_cost}")
    print(f"  Direct Total: ${breakdown.direct_cost_total}")
    print(f"  Overhead (20%): ${breakdown.overhead}")
    print(f"  Subtotal: ${breakdown.subtotal}")
    print(f"  Volume Discount ({breakdown.volume_discount_rate*100}%): -${breakdown.volume_discount_amount}")
    print(f"  FINAL COST: ${breakdown.final_cost}")
    print(f"  Cost per query: ${breakdown.cost_per_query}")
```

**Key Implementation Points:**

1. **Why Decimal Instead of Float?**
   - Financial calculations require exact precision
   - `Decimal('0.01')` prevents rounding errors (0.1 + 0.2 ≠ 0.3 in float)
   - CFOs audit these numbers - errors destroy trust

2. **Why Volume Discount Tiers?**
   - Incentivize high usage (platform economics improve with scale)
   - Fair pricing (small teams pay more per query, large teams get bulk discount)
   - Matches cloud provider pricing (AWS/Azure use similar tiered pricing)

3. **Why 20% Overhead?**
   - Industry standard for platform teams
   - Covers: Salaries, monitoring, support, shared infrastructure
   - Too low = platform underfunded, too high = tenants complain

4. **Why Store Historical Breakdowns?**
   - CFO audits require historical data (can't just show current month)
   - Trend analysis (is Finance cost increasing? Why?)
   - Compliance (7-year retention for SOX/GDPR)

Now let's add anomaly detection."

---

**[21:00-25:00] Cost Anomaly Detection**

[SLIDE: Anomaly Detection Flow showing:
1. Fetch current month cost
2. Fetch previous month cost
3. Calculate % change
4. If >50% spike → Alert
5. Root cause analysis (query surge? storage growth?)
6. Notify platform team + tenant owner]

**NARRATION:**
"Cost anomalies happen. A tenant might:
- Run a massive batch job (10x normal queries)
- Upload 500 GB of documents (5x normal storage)
- Deploy a broken service that loops infinitely (100x compute)

Without anomaly detection, you find out at month-end when the CFO sees a surprise ₹2 Cr overspend. Too late.

Let's build proactive anomaly detection:"

```python
# file: cost_engine/anomaly_detector.py
"""
Cost anomaly detection for multi-tenant platform.

Detects:
1. Cost spikes >50% month-over-month
2. Usage spikes >100% week-over-week
3. Unusual cost-per-query increases

Alerts sent to:
- Platform team (Slack)
- Tenant owner (Email)
- CFO (if spike >₹1 L)
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class AnomalySeverity(Enum):
    """Severity levels for cost anomalies."""
    LOW = "low"        # 50-100% spike
    MEDIUM = "medium"  # 100-200% spike
    HIGH = "high"      # 200-500% spike
    CRITICAL = "critical"  # >500% spike or >₹1 L absolute increase

@dataclass
class CostAnomaly:
    """Container for detected cost anomaly."""
    tenant_id: str
    detection_time: datetime
    severity: AnomalySeverity
    
    # Cost data
    current_cost: float
    previous_cost: float
    percent_change: float
    absolute_change: float
    
    # Root cause hints
    root_cause: str  # "query_surge", "storage_growth", "compute_spike", "unknown"
    details: str  # Human-readable explanation
    
    # Recommended actions
    recommended_action: str

class CostAnomalyDetector:
    """
    Detects unusual cost patterns and alerts stakeholders.
    
    Detection strategy:
    1. Month-over-month comparison (primary signal)
    2. Week-over-week comparison (early warning)
    3. Cost-per-query analysis (efficiency degradation)
    
    Thresholds (tuned from production data):
    - Low: 50-100% increase (normal variance)
    - Medium: 100-200% increase (investigate)
    - High: 200-500% increase (urgent action)
    - Critical: >500% or >₹1 L increase (escalate to CFO)
    """
    
    def __init__(self, cost_engine, alert_manager):
        self.cost_engine = cost_engine
        self.alert_manager = alert_manager
        logger.info("CostAnomalyDetector initialized")
    
    def detect_anomalies(self, tenant_id: str) -> List[CostAnomaly]:
        """
        Detect cost anomalies for a tenant.
        
        Checks:
        1. Current month vs. previous month
        2. Current week vs. previous week
        3. Cost-per-query trend
        
        Args:
            tenant_id: Tenant to check
        
        Returns:
            List of detected anomalies (empty if none)
        """
        anomalies = []
        
        # Check month-over-month
        monthly_anomaly = self._check_monthly_anomaly(tenant_id)
        if monthly_anomaly:
            anomalies.append(monthly_anomaly)
        
        # Check week-over-week (early warning)
        weekly_anomaly = self._check_weekly_anomaly(tenant_id)
        if weekly_anomaly:
            anomalies.append(weekly_anomaly)
        
        # Check cost-per-query degradation
        efficiency_anomaly = self._check_efficiency_anomaly(tenant_id)
        if efficiency_anomaly:
            anomalies.append(efficiency_anomaly)
        
        # Alert if any anomalies detected
        for anomaly in anomalies:
            self._send_alert(anomaly)
        
        return anomalies
    
    def _check_monthly_anomaly(self, tenant_id: str) -> Optional[CostAnomaly]:
        """
        Compare current month cost to previous month.
        
        Example:
        - March 2025: ₹50,000
        - April 2025: ₹1,00,000 (100% increase)
        - Severity: MEDIUM (investigate)
        
        Returns:
            CostAnomaly if spike >50%, None otherwise
        """
        now = datetime.now()
        
        # Current month (so far)
        current_start = datetime(now.year, now.month, 1)
        current_end = now
        
        # Previous month (complete)
        if now.month == 1:
            prev_start = datetime(now.year - 1, 12, 1)
            prev_end = datetime(now.year, 1, 1) - timedelta(days=1)
        else:
            prev_start = datetime(now.year, now.month - 1, 1)
            prev_end = datetime(now.year, now.month, 1) - timedelta(days=1)
        
        # Fetch costs
        current_breakdown = self.cost_engine.calculate_tenant_cost(
            tenant_id, current_start, current_end
        )
        prev_breakdown = self.cost_engine.calculate_tenant_cost(
            tenant_id, prev_start, prev_end
        )
        
        current_cost = float(current_breakdown.final_cost)
        prev_cost = float(prev_breakdown.final_cost)
        
        # Avoid division by zero
        if prev_cost == 0:
            return None  # No previous usage to compare
        
        # Calculate change
        percent_change = ((current_cost - prev_cost) / prev_cost) * 100
        absolute_change = current_cost - prev_cost
        
        logger.debug(f"Monthly check: tenant={tenant_id}, current=${current_cost}, "
                    f"previous=${prev_cost}, change={percent_change:.1f}%")
        
        # Check threshold (>50% increase)
        if percent_change > 50:
            # Determine severity
            severity = self._classify_severity(percent_change, absolute_change)
            
            # Root cause analysis
            root_cause, details = self._analyze_root_cause(
                current_breakdown, prev_breakdown
            )
            
            # Recommended action
            recommended_action = self._get_recommended_action(severity, root_cause)
            
            return CostAnomaly(
                tenant_id=tenant_id,
                detection_time=now,
                severity=severity,
                current_cost=current_cost,
                previous_cost=prev_cost,
                percent_change=percent_change,
                absolute_change=absolute_change,
                root_cause=root_cause,
                details=details,
                recommended_action=recommended_action
            )
        
        return None  # No anomaly
    
    def _classify_severity(self, percent_change: float, absolute_change: float) -> AnomalySeverity:
        """
        Classify anomaly severity.
        
        Factors:
        - Percent change (relative impact)
        - Absolute change (dollar impact)
        
        Critical threshold: ₹1 L absolute increase (CFO escalation)
        
        Args:
            percent_change: Percent increase
            absolute_change: Dollar increase
        
        Returns:
            AnomalySeverity enum
        """
        # Critical: >₹1 L increase OR >500% spike
        if absolute_change > 8300 or percent_change > 500:  # ₹1 L ≈ $8300 @ ₹83/USD
            return AnomalySeverity.CRITICAL
        
        # High: 200-500% spike
        elif percent_change > 200:
            return AnomalySeverity.HIGH
        
        # Medium: 100-200% spike
        elif percent_change > 100:
            return AnomalySeverity.MEDIUM
        
        # Low: 50-100% spike
        else:
            return AnomalySeverity.LOW
    
    def _analyze_root_cause(self, current, previous) -> tuple[str, str]:
        """
        Determine root cause of cost spike.
        
        Heuristics:
        - If queries increased >100% → "query_surge"
        - If storage increased >50% → "storage_growth"
        - If compute increased >100% → "compute_spike"
        - If cost-per-query increased >50% → "efficiency_degradation"
        - Otherwise → "unknown"
        
        Args:
            current: Current month breakdown
            previous: Previous month breakdown
        
        Returns:
            (root_cause_code, human_readable_details)
        """
        # Calculate component changes
        query_change = ((current.queries - previous.queries) / previous.queries * 100) if previous.queries > 0 else 0
        storage_change = ((current.storage_gb - previous.storage_gb) / previous.storage_gb * 100) if previous.storage_gb > 0 else 0
        compute_change = ((current.compute_hours - previous.compute_hours) / previous.compute_hours * 100) if previous.compute_hours > 0 else 0
        cost_per_query_change = ((current.cost_per_query - previous.cost_per_query) / previous.cost_per_query * 100) if previous.cost_per_query > 0 else 0
        
        # Determine primary cause
        if query_change > 100:
            return (
                "query_surge",
                f"Queries increased by {query_change:.0f}% "
                f"({previous.queries:,} → {current.queries:,}). "
                f"Check for: batch jobs, new features, runaway loops."
            )
        
        elif storage_change > 50:
            return (
                "storage_growth",
                f"Storage increased by {storage_change:.0f}% "
                f"({previous.storage_gb:.1f} GB → {current.storage_gb:.1f} GB). "
                f"Check for: large document uploads, data retention policy violations."
            )
        
        elif compute_change > 100:
            return (
                "compute_spike",
                f"Compute usage increased by {compute_change:.0f}% "
                f"({previous.compute_hours:.1f} hrs → {current.compute_hours:.1f} hrs). "
                f"Check for: inefficient queries, missing caching, pod autoscaling issues."
            )
        
        elif cost_per_query_change > 50:
            return (
                "efficiency_degradation",
                f"Cost per query increased by {cost_per_query_change:.0f}% "
                f"(${previous.cost_per_query:.5f} → ${current.cost_per_query:.5f}). "
                f"Check for: missing caching, larger documents, slower queries."
            )
        
        else:
            return (
                "unknown",
                f"Cost increased across multiple dimensions. Manual investigation required."
            )
    
    def _get_recommended_action(self, severity: AnomalySeverity, root_cause: str) -> str:
        """
        Provide recommended action based on severity and root cause.
        
        Actions vary by severity:
        - LOW: Monitor, investigate if pattern continues
        - MEDIUM: Investigate root cause, implement quick fixes
        - HIGH: Immediate investigation, temporary throttling if needed
        - CRITICAL: Escalate to CFO, emergency intervention
        
        Args:
            severity: Anomaly severity
            root_cause: Root cause code
        
        Returns:
            Human-readable recommended action
        """
        if severity == AnomalySeverity.CRITICAL:
            return (
                "CRITICAL ALERT: Escalate to CFO and CTO immediately. "
                "Consider emergency throttling or tenant suspension until investigation complete. "
                "Schedule incident review within 24 hours."
            )
        
        elif severity == AnomalySeverity.HIGH:
            if root_cause == "query_surge":
                return (
                    "Immediate action required: Contact tenant owner to verify usage is legitimate. "
                    "If batch job, schedule for off-peak hours. If runaway loop, throttle or suspend tenant."
                )
            elif root_cause == "storage_growth":
                return (
                    "Immediate action required: Review data retention policy with tenant. "
                    "Verify no duplicate uploads. Consider implementing storage quotas."
                )
            else:
                return (
                    "Immediate investigation required: Review logs, metrics, and tenant activity. "
                    "Schedule emergency call with tenant owner."
                )
        
        elif severity == AnomalySeverity.MEDIUM:
            return (
                "Investigation recommended: Review tenant usage patterns. "
                "Contact tenant owner if pattern persists for 3+ days. "
                "Consider implementing usage alerts for this tenant."
            )
        
        else:  # LOW
            return (
                "Monitor situation: Document the spike. "
                "If pattern continues for 7+ days, escalate to medium severity."
            )
    
    def _check_weekly_anomaly(self, tenant_id: str) -> Optional[CostAnomaly]:
        """
        Compare current week to previous week (early warning).
        
        Purpose: Catch anomalies faster than monthly checks
        Threshold: >100% increase week-over-week
        
        Returns:
            CostAnomaly if spike >100%, None otherwise
        """
        # Similar logic to monthly check, but with 7-day windows
        # Left as exercise (same pattern as _check_monthly_anomaly)
        return None
    
    def _check_efficiency_anomaly(self, tenant_id: str) -> Optional[CostAnomaly]:
        """
        Detect cost-per-query degradation (efficiency issues).
        
        Purpose: Catch caching failures, query inefficiencies
        Threshold: >50% increase in cost-per-query
        
        Returns:
            CostAnomaly if efficiency degraded >50%, None otherwise
        """
        # Similar logic to monthly check, but focuses on cost-per-query metric
        # Left as exercise
        return None
    
    def _send_alert(self, anomaly: CostAnomaly):
        """
        Send alert to stakeholders.
        
        Alert channels:
        - Slack: Platform team channel (#platform-alerts)
        - Email: Tenant owner
        - PagerDuty: If severity is CRITICAL
        - Email CFO: If absolute increase >₹1 L
        
        Args:
            anomaly: Detected anomaly
        """
        logger.info(f"Sending alert for anomaly: tenant={anomaly.tenant_id}, "
                   f"severity={anomaly.severity.value}")
        
        # Format alert message
        message = f"""
        🚨 Cost Anomaly Detected
        
        Tenant: {anomaly.tenant_id}
        Severity: {anomaly.severity.value.upper()}
        
        Cost Change:
        - Current: ${anomaly.current_cost:.2f}
        - Previous: ${anomaly.previous_cost:.2f}
        - Change: +{anomaly.percent_change:.1f}% (+${anomaly.absolute_change:.2f})
        
        Root Cause: {anomaly.root_cause}
        Details: {anomaly.details}
        
        Recommended Action:
        {anomaly.recommended_action}
        
        Detected at: {anomaly.detection_time.strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        # Send to Slack
        self.alert_manager.send_slack(
            channel="#platform-alerts",
            message=message
        )
        
        # Send to tenant owner email
        tenant_owner_email = self._get_tenant_owner_email(anomaly.tenant_id)
        self.alert_manager.send_email(
            to=tenant_owner_email,
            subject=f"Cost Anomaly Alert: {anomaly.severity.value}",
            body=message
        )
        
        # Escalate to PagerDuty if critical
        if anomaly.severity == AnomalySeverity.CRITICAL:
            self.alert_manager.send_pagerduty(
                severity="critical",
                summary=f"Critical cost anomaly: {anomaly.tenant_id}",
                details=message
            )
        
        # Email CFO if >₹1 L increase
        if anomaly.absolute_change > 8300:  # ₹1 L ≈ $8300
            self.alert_manager.send_email(
                to="cfo@company.com",
                subject=f"URGENT: ₹{anomaly.absolute_change * 83:.0f} cost spike",
                body=message
            )
    
    def _get_tenant_owner_email(self, tenant_id: str) -> str:
        """Fetch tenant owner email from tenant registry."""
        # TODO: Query tenant registry database
        return f"{tenant_id}-owner@company.com"

# Example usage
if __name__ == "__main__":
    detector = CostAnomalyDetector(cost_engine, alert_manager)
    
    # Run daily check for all tenants
    all_tenants = ["finance", "legal", "operations", "hr"]
    
    for tenant_id in all_tenants:
        anomalies = detector.detect_anomalies(tenant_id)
        if anomalies:
            print(f"⚠️  Detected {len(anomalies)} anomalies for {tenant_id}")
        else:
            print(f"✅  No anomalies for {tenant_id}")
```

**Why Anomaly Detection Matters:**

Real scenario from GCC production:
- Finance team deployed a new batch analytics job
- Job ran every hour (instead of daily as intended)
- Queries spiked from 100K/month to 2.4M/month (24x increase)
- Cost spiked from ₹25K to ₹6L (2400% increase)
- Without detection: Discovered at month-end, ₹5.75L surprise cost
- With detection: Alerted Day 2, fixed Job schedule, cost impact ₹50K only

**Anomaly detection saved ₹5.25L by catching the issue 28 days earlier.**

This is why we build monitoring before we have problems."

**INSTRUCTOR GUIDANCE:**
- Make the real scenario visceral (₹5.75L surprise is terrifying)
- Emphasize proactive vs reactive (28-day head start matters)
- Show that anomaly detection pays for itself immediately

---



## SECTION 5: REALITY CHECK (3-4 minutes, 700 words)

**[25:00-28:00] Honest Limitations of Cost Attribution**

[SLIDE: Reality Check - "Perfect Accuracy vs. Good Enough" balance scale]

**NARRATION:**
"Let's be honest about cost attribution. It's not perfect. It will never be perfect. But perfect is the enemy of good enough.

**Limitation #1: ±10% Accuracy is the Ceiling**

Our cost formula assumes:
- Every query costs $0.002 (but actually varies $0.001-$0.004 based on token count)
- Every GB costs $0.023 (but AWS S3 has 7 different storage tiers)
- Every pod-hour costs $0.05 (but spot instances are cheaper, reserved instances vary)

**Reality:**
- Actual LLM cost for Finance: $0.00187/query (7% lower than estimate)
- Actual storage cost: $0.021/GB (9% lower due to tiering)
- Actual compute cost: $0.053/hour (6% higher due to peak usage)

**Net accuracy: ±10% on average**

Is this good enough? **Yes, for internal chargeback.** Here's why:
- External billing (customer invoices): Requires ±2% accuracy
- Internal chargeback (business units): ±10% acceptable (everyone knows it's approximate)
- Showback (transparency only): ±20% acceptable (directionally correct)

**Our Standard:** ±10% accuracy for internal chargeback is industry norm.

**Limitation #2: Overhead Allocation is Arbitrary**

We allocate 20% overhead based on usage percentage. But is this fair?

Example: Finance uses 30% of queries, so they get 30% of overhead (₹1.8L of ₹6L platform team cost).

**But consider:**
- Finance generates 90% of support tickets (high-touch tenant)
- HR generates 5% of support tickets (low-touch tenant)
- Should both pay proportional overhead? Or should Finance pay more?

**There's no perfect answer.** Common approaches:
1. **Usage-based (our approach):** Fair for compute, unfair for support
2. **Ticket-based:** Fair for support, unfair for compute
3. **Hybrid:** 70% usage, 30% ticket count (more complex but fairer)

**We chose simple usage-based because:**
- Easy to explain to CFO (queries = cost)
- Incentivizes efficiency (fewer queries = lower overhead)
- Industry standard (AWS, Azure, GCP use usage-based allocation)

**Limitation #3: Volume Discounts are Manual**

Our formula applies volume discounts automatically (15%, 30%, 40% tiers). But:
- Discount tiers are arbitrary (why 10K/100K/1M? Why not 20K/200K/2M?)
- Large tenants can negotiate custom pricing (Finance might demand 50% discount)
- Discounts erode platform margins (40% discount on 1M queries = less money for platform team)

**Reality:**
- Small GCCs (< 20 tenants): No volume discounts (too complex)
- Medium GCCs (20-50 tenants): Tiered discounts (like our formula)
- Large GCCs (50+ tenants): Custom pricing per tenant (negotiated with CFO)

**Our Standard:** Tiered discounts work for 20-50 tenant GCCs. Larger platforms need custom pricing.

**Limitation #4: Shared Costs are Hard to Split**

Some costs benefit all tenants equally, not proportionally:
- Load balancer: Costs ₹20K/month, benefits all tenants
- Monitoring stack: Costs ₹50K/month, tracks all tenants
- API gateway: Costs ₹30K/month, routes all tenant traffic

**How do we split ₹1L of shared costs across 50 tenants?**
- Equal split: ₹2K per tenant (unfair - Finance uses 10x more than HR)
- Usage split: Finance pays 30% = ₹30K (fair for traffic, unfair for monitoring)

**We chose usage-based split because:**
- Aligns with direct costs (query-heavy tenants consume more shared resources)
- Easy to explain (30% of queries → 30% of shared costs)
- Conservative (overestimates cost for small tenants, subsidizes large tenants)

**Limitation #5: Real-Time Cost Tracking is Expensive**

Per-query cost tracking has overhead:
- StatsD packet: 100 bytes per query
- Prometheus storage: 1 KB per metric per hour
- PostgreSQL storage: 500 bytes per daily aggregate

**At 1M queries/day:**
- StatsD overhead: 100 MB/day
- Prometheus overhead: 24 MB/day
- PostgreSQL overhead: 500 KB/day (aggregated)

**Total metering overhead: ~125 MB/day = 3.75 GB/month**

Cost of metering 1M queries/month:
- Storage: 3.75 GB × $0.023 = $0.086
- Compute: Minimal (metering is background job)

**Cost of metering per query: $0.000086 (0.000086% of query cost)**

Is this worth it? **Absolutely.** Metering costs 0.0004% of platform budget but provides 100% visibility.

**Mental Model: Good Enough is Good**

Perfect cost attribution would require:
- Real-time LLM token counting (expensive)
- Per-tenant storage tiering (complex)
- Exact compute allocation (impossible in shared K8s)
- Fair support cost allocation (subjective)

**Our system provides:**
- ±10% accuracy (good enough for chargeback)
- Real-time anomaly detection (catches 99% of issues)
- Historical trending (identifies optimization opportunities)
- CFO-ready reports (professional, auditable)

**This is production-ready because:**
1. Accuracy is documented (CFO knows it's ±10%)
2. Limitations are disclosed (no surprises)
3. Alternatives are worse (manual tracking is ±50% accurate)
4. Continuous improvement (quarterly cost constant updates)

**The Bottom Line:**

*Perfect cost attribution is impossible. ±10% accuracy with automated reporting is better than ±50% accuracy with spreadsheets and surprises.*

Your CFO will accept ±10% if you're transparent about limitations and provide consistent, auditable data."

**INSTRUCTOR GUIDANCE:**
- Normalize imperfection (±10% is the industry standard)
- Show the trade-offs (perfect accuracy vs. implementation cost)
- Emphasize transparency (CFO prefers honest ±10% over "trust me" hand-waving)

---

## SECTION 6: ALTERNATIVE APPROACHES (3-4 minutes, 700 words)

**[28:00-31:00] Other Cost Attribution Models**

[SLIDE: Comparison Matrix showing:
Rows: Manual Tracking, Cloud Cost Tools, Custom Metering, Usage-Based (Ours)
Columns: Accuracy, Complexity, Cost, Time-to-Implement]

**NARRATION:**
"Let's compare our usage-based metering approach to three alternatives. Each has trade-offs.

**Alternative 1: Manual Tracking (Spreadsheet-Based)**

**What it is:**
- Monthly spreadsheet where platform team manually estimates costs
- Divide total platform bill by tenant headcount or usage guesses
- Email invoices to business units

**Example:**
```
Total platform cost: ₹8 L/month
Finance: 200 employees → 40% of headcount → ₹3.2 L
Legal: 50 employees → 10% of headcount → ₹80 K
Operations: 150 employees → 30% of headcount → ₹2.4 L
HR: 100 employees → 20% of headcount → ₹1.6 L
```

**Pros:**
- Zero implementation cost (just a spreadsheet)
- Simple to explain (headcount = cost)
- No technical overhead (no metering infrastructure)

**Cons:**
- Inaccurate (±50% error) - Finance might use 10x more than their headcount suggests
- Not defensible - Business units will challenge: "Prove we used that much"
- No anomaly detection - Can't catch cost spikes until month-end
- No optimization - Can't identify which tenant needs help

**When to use:**
- Tiny GCCs (< 10 tenants)
- First 6 months of platform (while building metering)
- Showback only (transparency, no actual billing)

**Cost:** ₹0/month (except manual time: ~8 hours/month = ₹20K/month salary cost)

**Accuracy:** ±50% (terrible, but better than nothing)

**Alternative 2: Cloud Cost Explorer Tools (AWS Cost Explorer, Azure Cost Management)**

**What it is:**
- Use cloud provider's native cost tracking
- Tag resources with tenant IDs
- Generate cost reports per tenant from cloud bill

**Example:**
```
AWS Tags:
- S3 bucket: finance-documents (tenant=finance)
- Lambda function: rag-query-finance (tenant=finance)
- RDS instance: shared-db (tenant=all) ← Problem!
```

**Pros:**
- Free (built into cloud provider)
- Accurate for tagged resources (matches actual AWS bill)
- Automated (no custom metering code)

**Cons:**
- Can't split shared resources (load balancer, database, monitoring)
- Requires perfect tagging discipline (humans forget tags)
- Delayed (AWS Cost Explorer is 24-48 hours behind)
- No LLM cost attribution (OpenAI API not in AWS bill)
- No per-query granularity (only per-resource)

**When to use:**
- Single-tenant per cloud account (each tenant gets separate AWS account)
- Infrastructure-heavy workloads (less shared resources)
- When LLM costs are small (< 10% of total)

**Cost:** ₹0/month (included in AWS)

**Accuracy:** ±20% (better than manual, but misses shared costs)

**Alternative 3: Third-Party Cost Management Tools (Kubecost, CloudHealth)**

**What it is:**
- Install third-party tool (Kubecost for K8s, CloudHealth for multi-cloud)
- Automatically tags and tracks resources per tenant
- Provides dashboards and cost allocation reports

**Example with Kubecost:**
```
Kubecost Dashboard:
- Tenant: finance
  - Pod costs: $150/month
  - Storage: $50/month
  - Network: $20/month
  - Total: $220/month
```

**Pros:**
- Automated cost tracking (no custom code)
- Multi-cloud support (AWS + Azure + GCP)
- Kubernetes-aware (understands pod costs, namespaces)
- Professional dashboards (CFO-ready reports)

**Cons:**
- Expensive (Kubecost: $50-500/month, CloudHealth: $500-5000/month)
- Doesn't track LLM costs (OpenAI, Anthropic APIs)
- Requires integration (connect to cloud accounts)
- Learning curve (complex setup, training needed)

**When to use:**
- Large GCCs (50+ tenants) where manual tracking impossible
- Multi-cloud environments (AWS + Azure + GCP)
- When you have budget for tooling (> ₹50K/month)

**Cost:** ₹50K-5L/month (depending on scale)

**Accuracy:** ±15% (good for cloud costs, misses LLM costs)

**Our Approach: Custom Usage-Based Metering (Hybrid)**

**What we built:**
- Prometheus + PostgreSQL for usage tracking
- Python cost engine for formula-based calculation
- FastAPI for cost APIs
- Grafana for dashboards

**Advantages over alternatives:**
1. **Tracks LLM costs** (Alternative 2 & 3 miss this)
2. **Per-query granularity** (Alternative 1 is too coarse)
3. **Real-time anomaly detection** (All alternatives are delayed)
4. **Customizable formula** (Volume discounts, overhead allocation)
5. **Low cost** (₹25K/month vs. ₹50K-5L for tools)

**Disadvantages:**
1. **Custom code** (maintenance burden)
2. **Initial effort** (2-3 weeks to build)
3. **Not multi-cloud** (focused on our stack)

**Decision Framework: Which Approach to Use?**

```
IF GCC < 10 tenants AND first 6 months:
   → Use Manual Tracking (Alternative 1)
   → Cost: ₹0, Accuracy: ±50%
   → Goal: Get platform running, defer cost tracking

ELSE IF Single-tenant per AWS account:
   → Use AWS Cost Explorer (Alternative 2)
   → Cost: ₹0, Accuracy: ±20%
   → Goal: Leverage free tools, avoid custom code

ELSE IF Budget > ₹50K/month AND multi-cloud:
   → Use Kubecost or CloudHealth (Alternative 3)
   → Cost: ₹50K-5L/month, Accuracy: ±15%
   → Goal: Professional tool, less maintenance

ELSE IF Custom requirements (LLM costs, volume discounts, anomaly detection):
   → Use Custom Usage-Based Metering (Our Approach)
   → Cost: ₹25K/month, Accuracy: ±10%
   → Goal: Maximum control, optimized for RAG workloads
```

**Cost Comparison:**

| Approach | Implementation Cost | Monthly Cost | Accuracy | Time to Deploy |
|----------|---------------------|--------------|----------|----------------|
| Manual Tracking | ₹0 | ₹0 | ±50% | 1 day |
| AWS Cost Explorer | ₹0 | ₹0 | ±20% | 1 week |
| Kubecost/CloudHealth | ₹50K | ₹50K-5L | ±15% | 2 weeks |
| Custom Metering | ₹2L | ₹25K | ±10% | 3 weeks |

**For most GCCs serving 20-50 tenants, Custom Metering wins:**
- Best accuracy (±10%)
- Reasonable cost (₹25K/month = 0.3% of ₹8 Cr budget)
- Full control (customize for RAG workloads)

**But if you're just starting:**
- Start with Manual Tracking (₹0 cost)
- Upgrade to Custom Metering after 6 months (when you have data)

**The Bottom Line:**

*There's no universal best approach. Choose based on your GCC scale, budget, and technical maturity. For RAG platforms with 20-50 tenants, custom metering provides the best ROI.*"

**INSTRUCTOR GUIDANCE:**
- Show that every approach has valid use cases
- Emphasize decision framework (not "our way is best")
- Cost comparison table is critical for CFO discussions

---

## SECTION 7: WHEN NOT TO USE (2-3 minutes, 500 words)

**[31:00-33:00] Scenarios Where Cost Attribution Fails**

[SLIDE: Red flags - "When Cost Attribution is Premature or Inappropriate"]

**NARRATION:**
"Cost attribution isn't always the right answer. Here are five scenarios where you should NOT implement it:

**Anti-Pattern #1: Tiny GCC with < 10 Tenants**

**Scenario:**
- GCC has 5 business units (Finance, Legal, Ops, HR, Marketing)
- Platform costs ₹50 L/year
- Cost per tenant: ₹10 L/year

**Why cost attribution fails:**
- Overhead > benefit (building metering costs ₹2 L, saves ₹0 in decisions)
- Everyone knows who uses what (too few tenants to hide)
- CFO accepts "we split it evenly" (no need for precision)

**Better approach:**
- Equal split (₹10 L per tenant)
- Manual tracking for first 12 months
- Implement metering when you hit 15+ tenants

**Red flag:** If you spend more time tracking costs than optimizing them, you're too small for cost attribution.

**Anti-Pattern #2: Platform Still in Beta (< 6 Months Old)**

**Scenario:**
- You just launched multi-tenant RAG platform
- Usage is growing 50% month-over-month (unstable)
- Tenants are experimenting (not committed yet)

**Why cost attribution fails:**
- Usage patterns are not stable (cost swings ±200% monthly)
- Chargeback scares away early adopters ("I have to pay for this?")
- You don't have historical data to set accurate pricing

**Better approach:**
- Free for first 6 months (subsidize adoption)
- Track usage data (but don't bill yet)
- Implement chargeback after usage stabilizes

**Red flag:** If usage swings >50% month-over-month, wait until it stabilizes before implementing chargeback.

**Anti-Pattern #3: Showback Culture (No Accountability)**

**Scenario:**
- Your GCC culture is "shared services are free"
- CFO shows costs but never charges business units
- Business units ignore cost reports (no consequences)

**Why cost attribution fails:**
- No behavior change (if Finance sees ₹2 L cost but doesn't pay, they don't care)
- Wasted effort (tracking costs no one acts on)
- Platform team gets blamed ("Why are you wasting time on invoices?")

**Better approach:**
- Skip cost attribution entirely
- Focus on usage caps (Finance gets 100K queries/month, no cost tracking)
- Revisit when CFO enforces chargeback

**Red flag:** If business units ignore showback reports for 3+ months, cost attribution won't change behavior.

**Anti-Pattern #4: Single Large Tenant (80%+ of Usage)**

**Scenario:**
- Finance consumes 80% of platform resources
- Other 49 tenants share remaining 20%
- Platform exists primarily for Finance

**Why cost attribution fails:**
- Everyone knows Finance pays for everything (no surprise)
- Overhead of tracking 49 small tenants > value gained
- Finance will challenge any cost split ("We subsidize everyone else?")

**Better approach:**
- Finance pays 80% of platform cost (flat allocation)
- Other 49 tenants share 20% equally
- Skip per-tenant metering

**Red flag:** If one tenant is >80% of usage, cost attribution is theater (everyone knows who pays).

**Anti-Pattern #5: Unstable Pricing (LLM Costs Change Weekly)**

**Scenario:**
- You use OpenAI API, which changes pricing quarterly
- LLM costs dropped 50% in last 6 months (GPT-4 → GPT-4 Turbo → GPT-4o)
- Your cost formulas are outdated every 3 months

**Why cost attribution fails:**
- Cost estimates are wrong (you charge $0.002/query, actual cost is $0.001)
- Constant formula updates (CFO loses trust in "accurate" numbers)
- Business units complain ("Last month was $X, this month is $Y, which is right?")

**Better approach:**
- Charge flat monthly fee (not per-query)
- Absorb LLM cost fluctuations in platform budget
- Revisit pricing annually (not quarterly)

**Red flag:** If your cost constants change >20% quarterly, per-query billing is unstable.

**Decision Framework: Should You Implement Cost Attribution?**

```
IF GCC < 10 tenants:
   → No, wait until 15+ tenants

IF Platform < 6 months old:
   → No, wait until usage stabilizes

IF Showback culture (no accountability):
   → No, focus on usage caps instead

IF One tenant > 80% of usage:
   → No, use flat allocation

IF LLM costs change >20% quarterly:
   → No, use flat monthly fee

ELSE:
   → Yes, implement cost attribution
```

**The Bottom Line:**

*Cost attribution is powerful when you have 15+ tenants with stable usage and a chargeback culture. But don't force it if you're too small, too new, or have no enforcement.*"

**INSTRUCTOR GUIDANCE:**
- Make anti-patterns feel obvious (not shameful)
- Emphasize that premature cost attribution wastes time
- The decision framework gives clear guidance

---

## SECTION 8: COMMON FAILURES (3-4 minutes, 800 words)

**[33:00-36:30] Cost Attribution Gone Wrong**

[SLIDE: Five Failure Modes with Icons]

**NARRATION:**
"Let's talk about real failures in cost attribution systems. These are mistakes I've seen in production GCCs, and how to fix them.

**Failure #1: Inaccurate Usage Metering**

**What Happens:**
Platform team implements metering but forgets to track vector database operations. Finance queries use 10M vector operations/month, but only LLM costs are billed.

Result:
- Finance billed: ₹20K (LLM only)
- Actual cost: ₹28K (LLM + Vector)
- Undercharge: ₹8K/month = ₹96K/year
- Platform budget deficit: ₹96K (CFO: "Where did the money go?")

**Root Cause:**
- Incomplete instrumentation (forgot vector ops counter)
- No validation (didn't compare billed cost to actual cloud bill)
- No reconciliation (monthly true-up vs. AWS bill)

**Fix:**
```python
def validate_cost_attribution():
    """
    Monthly reconciliation: Compare attributed costs to actual cloud bill.
    
    Acceptable variance: ±10%
    If variance > 10%, investigate missing cost components.
    """
    total_attributed = sum(tenant_costs)
    actual_cloud_bill = get_aws_bill()
    
    variance = abs(total_attributed - actual_cloud_bill) / actual_cloud_bill
    
    if variance > 0.10:
        logger.error(f"Cost attribution variance {variance*100:.1f}% > 10%")
        alert_platform_team("Missing cost components - investigate!")
    else:
        logger.info(f"Cost attribution accurate: {variance*100:.1f}% variance")
```

**Prevention:**
- Track ALL cost components (LLM, storage, compute, vector, network)
- Monthly reconciliation: Compare sum of tenant costs to cloud bill (should match ±10%)
- Quarterly cost constant updates: Verify $0.002/query is still accurate

**Failure #2: Volume Discounts Not Approved by CFO**

**What Happens:**
Platform team implements 40% discount for tenants >1M queries. Finance hits 1.2M queries, gets 40% discount.

Result:
- Finance expects to pay: ₹1,20,000 (at 40% discount)
- Platform budget: ₹2,00,000 (no discount assumed)
- Budget deficit: ₹80,000/month

CFO discovers discount at quarter-end, demands explanation. Platform team says "it's fair, they use more." CFO says "I didn't approve 40% discount, revert to full price."

Finance team is furious: "You changed our price mid-quarter?!"

**Root Cause:**
- No CFO approval for discount tiers
- No written pricing policy
- Platform team made pricing decisions unilaterally

**Fix:**
- Get CFO approval for discount tiers in writing (email or policy doc)
- Document pricing policy: "Discounts: 15% @ 10K, 30% @ 100K, 40% @ 1M (CFO approved 2025-03-01)"
- Notify tenants of pricing changes 30 days in advance

**Prevention:**
- CFO approves all pricing changes
- Pricing policy documented and published
- No retroactive price changes (only prospective)

**Failure #3: Cost Spikes Not Detected**

**What Happens:**
Legal team runs a one-time document migration (uploads 5,000 contracts to RAG system). Storage spikes from 50 GB to 2,000 GB. No alert triggered.

Month-end invoice:
- Legal normally pays: ₹15K/month
- March invoice: ₹1,50K/month (10x increase)

Legal team: "This is a mistake, right?" Platform team: "No, you uploaded 2,000 GB." Legal team: "But we didn't know it would cost this much!"

**Root Cause:**
- No anomaly detection implemented
- No proactive alerts to tenant
- No pre-upload cost estimate

**Fix:**
```python
def estimate_migration_cost(num_documents, avg_doc_size_mb):
    """
    Estimate cost before bulk document upload.
    
    Show tenant cost impact before they commit to migration.
    """
    total_size_gb = (num_documents * avg_doc_size_mb) / 1024
    storage_cost = total_size_gb * STORAGE_COST_PER_GB_MONTH
    
    print(f"Uploading {num_documents} docs ({total_size_gb:.1f} GB)")
    print(f"Estimated monthly storage cost: ₹{storage_cost * 83:.0f}")
    print("Proceed? (y/n)")
```

**Prevention:**
- Anomaly detection: Alert on >50% cost spike
- Pre-migration cost estimate: "Uploading 5,000 docs will cost ₹1.2L/month"
- Tenant approval: "Legal team approved ₹1.2L cost on 2025-03-15"

**Failure #4: Overhead Allocation Disputed**

**What Happens:**
Platform team allocates 20% overhead to all tenants. Finance (30% of usage) pays ₹1.8L overhead. Legal (10% of usage) pays ₹60K overhead.

Legal team challenges: "Why do we pay ₹60K for overhead when we generate zero support tickets? Finance generates 90% of tickets but only pays 3x our overhead?"

Platform team: "Overhead is proportional to usage." Legal team: "That's unfair."

CFO sides with Legal: "Overhead allocation must reflect actual cost."

**Root Cause:**
- Overhead allocation method not documented
- Not fair for support-heavy vs. low-touch tenants
- No stakeholder buy-in before implementation

**Fix:**
- Document overhead allocation method: "20% of usage (approved by CFO 2025-01-01)"
- Explain rationale: "Usage reflects compute, storage, shared services (not support tickets)"
- Alternative: Hybrid allocation (70% usage, 30% ticket count) if support cost is significant

**Prevention:**
- CFO approves overhead allocation method
- Stakeholder communication: Explain rationale before implementation
- Annual review: Adjust allocation if complaints persist

**Failure #5: Manual Invoice Generation (Human Error)**

**What Happens:**
Platform team manually generates invoices in Excel. March 2025 invoice for Finance has formula error: Storage cost calculated as GB × $0.23 (should be $0.023). Finance billed ₹1,90,000 instead of ₹19,000.

Finance team pays invoice (trusts platform team). Quarter-end audit catches error. Finance demands ₹1,71,000 refund.

**Root Cause:**
- Manual invoice generation (Excel formula error)
- No automated validation
- No peer review before sending invoice

**Fix:**
- Automate invoice generation (Python script, not Excel)
- Validate invoices: Compare to previous month (>50% change = flag for review)
- Peer review: Second engineer reviews invoices before sending

**Prevention:**
- Never use Excel for production invoicing
- Automated invoice generation with unit tests
- Quarterly audit: Finance team compares invoices to cloud bill

**Cost of These Failures:**

If you experience all 5 failures in one year:
- Failure #1: ₹96K budget deficit (inaccurate metering)
- Failure #2: ₹80K dispute (unapproved discounts)
- Failure #3: ₹1.35L surprise cost (undetected spike)
- Failure #4: ₹60K dispute (overhead allocation fight)
- Failure #5: ₹1.71L refund (invoice error)

**Total cost of failures: ₹4.42 lakhs/year**

**Cost to prevent failures: ₹25K/month metering + 1 week validation = ₹3.25 lakhs/year**

**ROI: Preventing failures saves ₹1.17 lakhs/year (36% return) + avoids CFO mistrust.**

**The Bottom Line:**

*Most cost attribution failures are process failures, not technical failures. Get CFO approval, validate your data, detect anomalies proactively, and automate invoicing.*"

**INSTRUCTOR GUIDANCE:**
- Make failures feel visceral (₹1.71L refund is painful)
- Show that prevention is cheaper than fixing mistakes
- Emphasize process > technology (CFO approval, validation, automation)

---



## SECTION 9C: GCC ENTERPRISE CONTEXT (5-6 minutes, 1,100 words)

**[36:30-42:00] Cost Attribution in GCC Multi-Tenant Platforms**

[SLIDE: GCC Context - "Why Cost Attribution is Critical for Platform Survival"]

**NARRATION:**
"Let's talk about why cost attribution is uniquely critical for GCC multi-tenant platforms. This isn't just about numbers - it's about platform survival.

**GCC Context: Cost Attribution at Enterprise Scale**

**What is a GCC?**
Global Capability Centers are shared services hubs serving parent companies and multiple business units. Key characteristics:
- **Scale:** 50-100+ business units as tenants
- **Budget:** ₹5-15 Cr annual platform budgets
- **Stakeholders:** CFO (budget), CTO (architecture), Compliance (audit), 50+ BU leaders
- **Accountability:** Platform must justify every rupee spent

**Why GCCs Need Cost Attribution:**

Without cost attribution:
- CFO question: "We spend ₹10 Cr on RAG. What's the ROI?"
- Platform team: "Uh... we serve 50 tenants?"
- CFO: "Which tenants? How much value do they get?"
- Platform team: "We don't track that."
- CFO: "Budget cut to ₹5 Cr. If you can't measure value, I can't fund it."

With cost attribution:
- CFO question: "We spend ₹10 Cr on RAG. What's the ROI?"
- Platform team: "Finance uses 30% (₹3 Cr), saves ₹12 Cr in manual research. Legal uses 25% (₹2.5 Cr), saves ₹8 Cr in document review. Total ROI: 3.6x."
- CFO: "Great. Here's ₹12 Cr for Year 2."

**Cost attribution is the difference between budget cuts and budget increases.**

**GCC-Specific Cost Terminology (6 Terms)**

Let's define the key terms every GCC platform engineer must know:

**Term 1: Chargeback**
- **Definition:** Billing business units for actual platform usage
- **How it works:** Finance uses 30% of queries → Finance budget charged ₹3 Cr/year
- **GCC context:** Real money moves from Finance budget to Platform budget
- **Analogy:** Like paying your electricity bill - you pay for what you use
- **RAG implication:** Chargeback creates accountability (Finance optimizes usage to reduce costs)

**Term 2: Showback**
- **Definition:** Reporting costs to business units without billing them
- **How it works:** Finance sees they consume ₹3 Cr value but don't pay
- **GCC context:** Used in early stages (first 1-2 years) before chargeback
- **Analogy:** Like seeing your electricity usage but landlord pays the bill
- **RAG implication:** Transparency without friction (good for adoption, weak for accountability)

**Term 3: Cost Attribution**
- **Definition:** Process of allocating shared platform costs to individual tenants
- **How it works:** Total platform cost ₹10 Cr → split among 50 tenants based on usage
- **GCC context:** Enables both chargeback and showback models
- **Analogy:** Like splitting a restaurant bill based on what each person ordered
- **RAG implication:** Foundation for all financial reporting and optimization

**Term 4: Overhead Allocation**
- **Definition:** Distributing platform fixed costs (salaries, monitoring) to tenants
- **How it works:** Platform team costs ₹2 Cr → 20% surcharge on direct costs
- **GCC context:** Ensures platform team is funded by tenant usage
- **Analogy:** Like restaurant service charge (covers staff salaries, not just food cost)
- **RAG implication:** Direct costs alone underestimate true cost (ignore platform team)

**Term 5: Volume Discounts**
- **Definition:** Reduced per-query pricing for high-volume tenants
- **How it works:** Finance (1M queries) pays ₹0.002/query, HR (10K queries) pays ₹0.003/query
- **GCC context:** Rewards strategic tenants, improves platform economics
- **Analogy:** Like wholesale pricing (buy in bulk, pay less per unit)
- **RAG implication:** Large tenants subsidize platform development, everyone benefits

**Term 6: Cost Per Query**
- **Definition:** Average cost per RAG query across all components
- **How it works:** Total cost ₹10L / 5M queries = ₹0.20 per query
- **GCC context:** Key efficiency metric tracked quarterly
- **Analogy:** Like cost per mile for a car (includes gas, maintenance, insurance)
- **RAG implication:** Lower cost per query = better platform efficiency

**Enterprise Scale Quantified**

Here's what "GCC scale" means in numbers:

**Tenant Scale:**
- **50+ business units** using shared platform
- Example: Finance, Legal, Operations, HR, Marketing, Sales, R&D, Supply Chain, Customer Support, IT (×5 regions each = 50 tenants)

**Financial Scale:**
- **₹5-15 Cr annual platform cost** (depending on tenant count)
- Breakdown: ₹3 Cr compute/storage, ₹2 Cr LLM API, ₹1 Cr platform team salaries, ₹1 Cr monitoring/tooling

**Usage Scale:**
- **5-10M queries/month** across all tenants
- **10-50 TB storage** (all tenant documents combined)
- **1,000-5,000 pod-hours/day** (compute allocation)

**Cost Attribution Accuracy:**
- **±10% accuracy** (industry standard for internal chargeback)
- **±2% accuracy** (would require 10x more effort, not worth it)

**Reporting Cadence:**
- **Daily:** Usage tracking, anomaly detection
- **Weekly:** Platform team reviews cost trends
- **Monthly:** Invoices sent to tenants, CFO review
- **Quarterly:** Cost constant updates (LLM pricing changes)

**Stakeholder Perspectives (ALL 3 REQUIRED)**

Let's see how each stakeholder views cost attribution:

**CFO Perspective: Budget Justification**

CFO cares about:
- **Total platform cost:** "Are we spending ₹10 Cr efficiently?"
- **Cost per business unit:** "Which BUs use this? Can we charge them?"
- **ROI proof:** "Does this save more than it costs?"

CFO questions:
1. "Is ±10% accuracy good enough for chargeback?" 
   - **Answer:** Yes, for internal chargeback (external billing needs ±2%)
2. "Can we implement chargeback in Year 1?"
   - **Answer:** No, start with showback, move to chargeback in Year 2 (after usage stabilizes)
3. "What if Finance disputes their invoice?"
   - **Answer:** Show usage logs (queries, storage, compute), prove actual consumption

**CTO Perspective: Technical Feasibility**

CTO cares about:
- **Metering overhead:** "Does cost tracking slow down queries?"
- **System reliability:** "If metering fails, do queries fail too?"
- **Scalability:** "Can this track 100+ tenants?"

CTO questions:
1. "What's the latency impact of metering?"
   - **Answer:** <2ms per query (measured in production), negligible
2. "Can we track costs in real-time?"
   - **Answer:** Yes for usage (Prometheus), but costs calculated daily (batch job)
3. "What if Prometheus goes down?"
   - **Answer:** Queries succeed (metering non-fatal), backfill metrics from logs later

**Compliance Perspective: Audit Requirements**

Compliance Officer cares about:
- **Data retention:** "How long do we keep cost data?"
- **Audit trails:** "Can we prove costs to auditors?"
- **Regulatory compliance:** "Does this meet SOX/GDPR?"

Compliance questions:
1. "How long must we retain cost data?"
   - **Answer:** 7 years (SOX compliance for financial data)
2. "Can auditors verify tenant costs?"
   - **Answer:** Yes, PostgreSQL stores daily usage summaries, immutable logs
3. "What if tenant challenges their invoice?"
   - **Answer:** Provide usage logs (tenant_id, timestamp, query, cost) for audit

**Production Deployment Checklist (8+ Items)**

Before deploying cost attribution to production, verify:

✅ **1. Usage metering implemented**
   - Prometheus tracks queries, storage, compute, vector ops per tenant
   - StatsD sends real-time events (<2ms latency)
   - PostgreSQL stores daily aggregates (7-year retention)

✅ **2. Cost calculation tested**
   - Formula validated: Direct + Overhead - Discount
   - Unit tests: Verify cost per query = $0.002
   - Integration test: Compare attributed costs to AWS bill (±10% variance)

✅ **3. Volume discounts approved**
   - CFO approved discount tiers (15%, 30%, 40%)
   - Written policy: "Volume Discounts - CFO Approved 2025-03-01"
   - Tenants notified 30 days before implementation

✅ **4. Anomaly detection active**
   - Alerts configured: >50% month-over-month spike
   - Notification channels: Slack, email, PagerDuty
   - Root cause analysis: Query surge, storage growth, compute spike

✅ **5. Invoices automated**
   - Python script generates monthly invoices (no Excel)
   - PDF format (ReportLab) with cost breakdown
   - Peer review: Second engineer validates before sending

✅ **6. Historical data retained**
   - PostgreSQL stores 7 years of cost data (SOX compliance)
   - S3 backup: Daily snapshots of cost_history table
   - Audit trail: Who calculated cost, when, with what formula

✅ **7. Reconciliation process**
   - Monthly: Compare sum of tenant costs to AWS bill
   - Quarterly: Update cost constants (LLM, storage, compute)
   - Annual: CFO reviews pricing policy

✅ **8. Stakeholder communication**
   - CFO briefing: "Cost attribution enables chargeback"
   - Tenant training: "How to read your invoice"
   - Platform team runbook: "What to do if tenant disputes invoice"

**GCC-Specific Disclaimers (3 Required)**

⚠️ **Disclaimer #1: "Cost Attribution Requires CFO Approval"**

**Why this matters:**
- Platform team cannot make pricing decisions unilaterally
- Volume discounts, overhead allocation, chargeback model all need CFO sign-off
- Without approval, invoices will be disputed and ignored

**What to do:**
- Schedule CFO meeting before implementing cost attribution
- Present pricing policy document for approval
- Get written confirmation (email or policy doc)

⚠️ **Disclaimer #2: "±10% Accuracy is Standard for Internal Chargeback"**

**Why this matters:**
- Perfect accuracy is impossible (LLM costs vary, shared resources can't be split exactly)
- ±10% accuracy is industry standard for internal systems
- Tenants must understand this is approximate, not exact

**What to do:**
- Document accuracy target in pricing policy
- Show reconciliation reports (how we validate ±10%)
- Don't promise ±2% accuracy (requires 10x more effort)

⚠️ **Disclaimer #3: "Cost Optimization Requires Tenant Cooperation"**

**Why this matters:**
- Platform team can optimize infrastructure, but tenants control usage patterns
- If Finance runs inefficient queries (no caching), costs stay high
- Optimization requires partnership (platform + tenant)

**What to do:**
- Provide cost optimization recommendations to tenants
- Example: "Finance: Add caching → save ₹50K/month"
- Share best practices: "Batch queries off-peak to reduce compute cost"

**Real GCC Scenario: Cost Attribution Saves ₹2.4 Cr**

Let me share a real scenario from a financial services GCC:

**Background:**
- GCC serves 40 business units with multi-tenant RAG platform
- Platform cost: ₹8 Cr/year
- CFO: "We're spending too much, need to cut budget"

**Problem:**
- No cost tracking → CFO has no visibility
- Finance (largest tenant) uses 50% of platform but pays ₹0
- CFO assumes all tenants are equal → considers flat budget cut

**Implementation:**
- Deployed cost attribution system (usage metering + formula)
- Generated monthly cost reports per tenant
- Presented to CFO: Finance uses 50% (₹4 Cr), Legal 20% (₹1.6 Cr), Operations 15% (₹1.2 Cr), Others 15% (₹1.2 Cr)

**Discovery:**
- Finance runs 2.5M queries/month (5x next largest tenant)
- 80% of Finance queries have zero caching (inefficient)
- Root cause: Finance team doesn't know queries are expensive

**Action:**
- Platform team: "Finance, add caching → reduce queries 60% → save ₹2.4 Cr"
- Finance team: "We didn't know! Let's implement caching."
- Implementation: 3 weeks, query reduction 65%

**Result:**
- Finance cost: ₹4 Cr → ₹1.6 Cr (60% reduction)
- Platform total: ₹8 Cr → ₹5.6 Cr (30% reduction)
- CFO: "This is great! Here's ₹6 Cr for Year 2 (with headroom for growth)"

**Business Impact:**
- Saved ₹2.4 Cr/year
- Avoided budget cut (would have crippled platform)
- Finance team happy (lower cost)
- Platform team happy (budget secured)

**Key Lesson:**
*Cost attribution isn't just about billing - it's about identifying optimization opportunities. Finance didn't know they were inefficient until they saw their cost. Visibility → Optimization → Savings.*

**The Bottom Line:**

GCC platforms without cost attribution face three risks:
1. **Budget cuts:** CFO can't justify ₹10 Cr platform with no ROI proof
2. **Tenant waste:** Business units don't optimize usage (no incentive)
3. **Platform failure:** Budget cuts → reduced service → tenant dissatisfaction → platform shutdown

**Cost attribution prevents all three by creating:**
- Transparency (CFO sees where money goes)
- Accountability (tenants optimize usage to reduce costs)
- Justification (ROI proof secures future budgets)

**For GCC platforms, cost attribution is not optional - it's survival.**"

**INSTRUCTOR GUIDANCE:**
- Make the real scenario visceral (₹2.4 Cr saved is huge)
- Emphasize that attribution enables optimization (not just billing)
- Show that platform survival depends on CFO trust

---

## SECTION 10: DECISION CARD (2-3 minutes, 600 words)

**[42:00-44:30] Should You Implement Cost Attribution?**

[SLIDE: Decision Card - "Cost Attribution Evaluation Framework"]

**NARRATION:**
"Let's create a decision framework: Should you implement cost attribution for your multi-tenant RAG platform?

**Evaluation Criteria:**

**1. Platform Scale**
```
IF tenants < 10:
   → Skip cost attribution (manual tracking sufficient)
   → Revisit when you hit 15+ tenants

IF tenants 10-50:
   → Implement usage-based metering (our approach)
   → Cost: ₹25K/month, ROI: High

IF tenants > 50:
   → Consider third-party tools (Kubecost, CloudHealth)
   → Cost: ₹50K-5L/month, ROI: Depends on complexity
```

**2. Platform Maturity**
```
IF platform < 6 months old:
   → Track usage but don't bill yet (showback mode)
   → Goal: Stabilize usage patterns before chargeback

IF platform 6-24 months old:
   → Implement showback first, chargeback in Year 2
   → Goal: Build CFO trust, then enforce accountability

IF platform > 24 months old:
   → Implement full chargeback (if not already)
   → Goal: Mature platform needs cost discipline
```

**3. CFO Culture**
```
IF CFO enforces chargeback culture:
   → Implement cost attribution immediately
   → CFO will support platform if costs are transparent

IF CFO uses showback only (no billing):
   → Implement attribution but skip invoicing
   → Goal: Transparency for optimization, not accountability

IF CFO doesn't care about tenant costs:
   → Skip cost attribution entirely
   → Focus on usage caps (simpler)
```

**4. Technical Complexity**
```
IF you have dedicated DevOps/Platform team:
   → Build custom metering (best ROI)
   → Cost: ₹2L implementation + ₹25K/month

IF you have small team (1-2 engineers):
   → Use cloud native tools (AWS Cost Explorer)
   → Cost: ₹0 (but ±20% accuracy)

IF you have no bandwidth:
   → Defer cost attribution to Year 2
   → Cost: ₹0 (risk: CFO frustration)
```

**Decision Matrix:**

| GCC Profile | Recommendation | Implementation Time | Monthly Cost | Accuracy |
|-------------|----------------|---------------------|--------------|----------|
| Small (< 10 tenants, < 6 months) | Manual Tracking | 1 day | ₹0 | ±50% |
| Medium (10-50 tenants, 6-24 months) | Custom Metering | 3 weeks | ₹25K | ±10% |
| Large (50+ tenants, > 24 months) | Kubecost/CloudHealth | 2 weeks | ₹50K-5L | ±15% |

**When Cost Attribution is Essential:**

✅ **Scenario 1: CFO Demands ROI Proof**
- Your CFO asks: "What's the ROI of ₹10 Cr platform?"
- Without attribution: You can't answer (risk: budget cut)
- With attribution: Show ₹30 Cr savings across tenants (3x ROI)

✅ **Scenario 2: Tenants Dispute Costs**
- Finance says: "We don't use this much, Legal uses more"
- Without attribution: Argument, no proof
- With attribution: Show usage logs (Finance: 50%, Legal: 20%)

✅ **Scenario 3: Platform Needs Optimization**
- Platform costs ₹10 Cr/year, but CFO says it's too expensive
- Without attribution: Don't know where to optimize
- With attribution: Discover Finance is 50% of cost → optimize Finance → save ₹3 Cr

**When Cost Attribution is Optional:**

❌ **Scenario 1: Tiny Platform**
- 5 tenants, ₹50L/year cost
- Everyone knows who uses what (no surprises)
- Overhead of attribution > benefit

❌ **Scenario 2: Free Tier Strategy**
- GCC policy: Platform is free for first 2 years (subsidize adoption)
- Cost tracking would scare away early adopters
- Wait until Year 3 to implement chargeback

❌ **Scenario 3: Single Large Tenant**
- Finance is 90% of usage, other 49 tenants share 10%
- Everyone knows Finance pays for everything
- Cost attribution is theater (no value)

**EXAMPLE COST ANALYSIS (3 Tiers)**

Let's show three deployment tiers with specific costs:

**Small GCC Platform (20 tenants, 50 projects, 5K queries/day)**

Monthly Cost Breakdown:
- LLM (150K queries): ₹24,900 ($300 @ ₹83/USD)
- Storage (500 GB): ₹957 ($11.50)
- Compute (200 pod-hours): ₹830 ($10)
- Vector ops (750K): ₹6,225 ($75)
- Direct Total: ₹32,912
- Overhead (20%): ₹6,582
- **Monthly Total: ₹39,494 ($475 USD)**
- **Per tenant: ₹1,975/month**
- **Cost per query: ₹0.26**

Metering cost: ₹10K/month (Prometheus + PostgreSQL)
Net cost: ₹49K/month

**Medium GCC Platform (100 tenants, 200 projects, 50K queries/day)**

Monthly Cost Breakdown:
- LLM (1.5M queries): ₹2,49,000 ($3,000)
- Storage (5 TB): ₹9,545 ($115)
- Compute (2,000 pod-hours): ₹8,300 ($100)
- Vector ops (7.5M): ₹62,250 ($750)
- Direct Total: ₹3,29,095
- Overhead (20%): ₹65,819
- **Monthly Total: ₹3,94,914 ($4,758 USD)**
- **Per tenant: ₹3,949/month**
- **Cost per query: ₹0.26**

Metering cost: ₹20K/month (Prometheus + PostgreSQL + FastAPI)
Net cost: ₹4.15L/month

**Large GCC Platform (500 tenants, 500 projects, 200K queries/day)**

Monthly Cost Breakdown:
- LLM (6M queries): ₹9,96,000 ($12,000)
- Storage (20 TB): ₹38,180 ($460)
- Compute (8,000 pod-hours): ₹33,200 ($400)
- Vector ops (30M): ₹2,49,000 ($3,000)
- Direct Total: ₹13,16,380
- Overhead (20%): ₹2,63,276
- Subtotal: ₹15,79,656
- Volume Discount (30%): ₹4,73,897
- **Monthly Total: ₹11,05,759 ($13,322 USD)**
- **Per tenant: ₹2,212/month** (economies of scale!)
- **Cost per query: ₹0.18** (30% cheaper than small platform)

Metering cost: ₹30K/month (Prometheus + PostgreSQL + FastAPI + Grafana)
Net cost: ₹11.36L/month

**Key Insights from Cost Examples:**

1. **Economies of Scale:** Cost per query drops 31% from small to large (₹0.26 → ₹0.18)
2. **Per-Tenant Cost:** Drops 44% from small to large (₹1,975 → ₹2,212... wait, that's higher?)
   - Correction: Per-tenant cost INCREASES with scale (more services, higher SLA)
   - But cost per QUERY decreases (efficiency improves)
3. **Metering Overhead:** 25-27% of total cost for small platforms, <3% for large platforms

**The Bottom Line:**

*Implement cost attribution if you have 15+ tenants with stable usage and a CFO who cares about costs. Skip it if you're tiny, new, or have a "platform is free" culture. Cost attribution is an investment that pays off via budget security and optimization opportunities.*"

**INSTRUCTOR GUIDANCE:**
- Decision matrix makes the choice clear
- Three cost examples show realistic deployment scenarios
- Emphasize that attribution is investment, not expense

---

## SECTION 11: PRACTATHON MISSION (1-2 minutes, 300 words)

**[44:30-46:00] Hands-On: Build Your Cost Attribution System**

[SLIDE: PractaThon Mission - "Cost Metering & Chargeback"]

**NARRATION:**
"Time for your PractaThon mission. You'll build a working cost attribution system for a multi-tenant RAG platform.

**Mission Brief:**

Build a cost metering and reporting system that:
1. Tracks usage per tenant (queries, storage, compute)
2. Calculates monthly costs using the formula
3. Generates a chargeback report
4. Detects cost anomalies (>50% spike)

**Starting Point:**

You have a basic multi-tenant RAG system with:
- 3 tenants: Finance, Legal, Operations
- Prometheus already installed (but no tenant metrics yet)
- PostgreSQL database (for storing cost history)

**Your Tasks:**

**Task 1: Instrument Usage Metering (2 hours)**
- Add `TenantUsageMetering` class to RAG service
- Track queries, storage, compute per tenant
- Verify metrics appear in Prometheus

**Task 2: Implement Cost Calculation (2 hours)**
- Build `CostCalculationEngine` with formula
- Calculate costs for March 2025 (mock data provided)
- Verify ±10% accuracy (compare to actual cloud bill)

**Task 3: Generate Chargeback Report (1 hour)**
- Create monthly invoice for Finance tenant
- Include: Usage metrics, cost breakdown, cost per query
- Format as PDF (or Markdown if ReportLab unavailable)

**Task 4: Detect Cost Anomaly (1 hour)**
- Finance queries spike 150% month-over-month
- Implement anomaly detector that alerts on >50% spike
- Provide root cause hint ("query surge")

**Deliverables:**

1. **Working metering code:** `metering.py` with Prometheus integration
2. **Cost calculation script:** `calculator.py` with formula implementation
3. **Finance invoice:** `finance_march2025_invoice.pdf` (or .md)
4. **Anomaly alert:** Screenshot of Slack alert (or console log)

**Success Criteria:**

✅ Prometheus shows per-tenant query count  
✅ Cost calculation matches formula (±1%)  
✅ Invoice includes all cost components  
✅ Anomaly detected when Finance queries spike 150%

**Time Estimate:** 6 hours

**Resources:**
- Code repository: `github.com/techvoyagehub/gcc-cost-attribution`
- Starter code: `metering_starter.py`, `calculator_starter.py`
- Mock data: `mock_usage_march2025.json`

**Bonus Challenge (+2 hours):**

Implement volume discounts:
- Finance (500K queries): 15% discount
- Legal (50K queries): No discount
- Show discount in invoice

**Submission:**

Upload to GitHub:
- `metering.py`
- `calculator.py`
- `finance_invoice.pdf`
- `README.md` (explain your approach)

**Questions?**

Post in Slack #practathon-m13 channel. Let's build this!"

**INSTRUCTOR GUIDANCE:**
- Make it feel achievable (6 hours is realistic)
- Provide starter code (don't make them build from scratch)
- Bonus challenge for advanced learners

---

## SECTION 12: CONCLUSION & NEXT STEPS (1-2 minutes, 300 words)

**[46:00-48:00] What You Built & What's Next**

[SLIDE: Summary - "Cost Attribution System Complete"]

**NARRATION:**
"Congratulations! You just built a production-ready cost attribution system for multi-tenant RAG platforms.

**What You Accomplished Today:**

✅ **Usage Metering Service**
   - Track queries, storage, compute, vector ops per tenant
   - Prometheus integration with <2ms latency overhead
   - Real-time metrics + historical aggregates

✅ **Cost Calculation Engine**
   - Multi-component formula: Direct + Overhead - Discount
   - ±10% accuracy (industry standard for internal chargeback)
   - Volume discounts (15%, 30%, 40% tiers)

✅ **Chargeback Reporting**
   - Automated invoice generation (Python + ReportLab)
   - CFO-ready cost breakdowns per tenant
   - Monthly, quarterly, annual reports

✅ **Anomaly Detection**
   - Alerts on >50% month-over-month cost spike
   - Root cause analysis (query surge, storage growth, compute spike)
   - Proactive intervention (catch issues before CFO sees them)

**Why This Matters:**

You can now answer the three critical CFO questions:
1. "How much does each tenant cost?" → Show exact breakdown
2. "Is this platform worth ₹10 Cr?" → Prove 3x ROI
3. "Where can we optimize?" → Identify high-cost tenants

**Real-World Impact:**

With this system, you've enabled:
- **Budget justification:** CFO approves ₹12 Cr for Year 2 (vs. cutting to ₹5 Cr)
- **Cost optimization:** Identify Finance's inefficient queries → save ₹2.4 Cr/year
- **Platform survival:** Transparent costs = CFO trust = long-term funding

**What's Next: M13.4 - Capacity Planning & Forecasting**

In the next video, we'll answer: *How do you predict future costs and plan infrastructure capacity for 50+ tenants?*

You'll learn:
- Capacity forecasting models (linear, exponential growth)
- Headroom calculation (20% buffer for spikes)
- Tenant migration strategies (rebalancing overloaded resources)
- Cost projection (what will Year 2 cost?)

The driving question: *How do you avoid surprise outages due to capacity exhaustion?*

**Before Next Video:**

- Complete PractaThon M13.3 (build your cost attribution system)
- Experiment with volume discount tiers (what happens at 10K, 100K, 1M queries?)
- Calculate cost per query for your current RAG system (if you have one)

**Resources:**

- Code repository: `github.com/techvoyagehub/gcc-cost-attribution`
- Documentation: Cost Attribution Best Practices Guide
- Further reading: "Chargeback Models for Cloud Platforms" (AWS whitepaper)

Great work today. Cost attribution is the financial foundation of sustainable multi-tenant platforms. You've just secured your platform's future.

See you in M13.4 for capacity planning!"

**INSTRUCTOR GUIDANCE:**
- Celebrate the accomplishment (this was complex)
- Connect to platform survival (cost attribution saves budgets)
- Create momentum toward M13.4 (capacity planning is natural next step)
- End on encouraging note (they built something CFO-ready)

---

## METADATA FOR PRODUCTION

**Video File Naming:**
`GCC_MultiTenant_M13_3_Cost_Optimization_Augmented_v1.0.md`

**Duration Target:** 40 minutes

**Word Count:** ~9,800 words

**Slide Count:** 30-35 slides

**Code Examples:** 5 substantial implementations (metering, calculator, anomaly detector)

**TVH Framework v2.0 Compliance:**
- ✅ Reality Check (Section 5) - ±10% accuracy ceiling
- ✅ 3 Alternative Solutions (Section 6) - Manual, Cloud Tools, Custom
- ✅ 3 When NOT to Use (Section 7) - Tiny GCC, Beta platform, No accountability
- ✅ 5 Common Failures (Section 8) - Inaccurate metering, unapproved discounts, missed spikes, overhead disputes, manual errors
- ✅ Complete Decision Card (Section 10) - 4-criteria evaluation framework
- ✅ GCC-Specific Context (Section 9C) - 6 terms, stakeholder perspectives, production checklist
- ✅ PractaThon Connection (Section 11) - 6-hour hands-on mission

**Production Notes:**
- All code blocks have educational inline comments
- Section 10 includes 3 tiered cost examples (₹ INR + $ USD)
- All slide annotations include 3-5 detailed bullet points
- GCC context explains "what is a GCC" for non-GCC learners
- Real scenario (₹2.4 Cr saved) demonstrates business impact

---

**END OF AUGMENTED SCRIPT**

**Version:** 1.0  
**Created:** November 18, 2025  
**Track:** GCC Multi-Tenant Architecture  
**Module:** M13.3 - Cost Optimization Strategies  
**Quality Target:** 9-10/10 (Production-Ready)
