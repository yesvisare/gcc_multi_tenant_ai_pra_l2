# L3 M13.3: Cost Optimization Strategies

Multi-tenant cost attribution and optimization for RAG platforms serving enterprise organizations. This module implements usage metering, cost calculation with volume discounts, chargeback report generation, and anomaly detection for GCC platforms.

**Part of:** TechVoyageHub L3 Production RAG Engineering Track
**Prerequisites:** M13.1 (Caching Strategies), M13.2 (Query Optimization)
**Infrastructure:** Local processing (Prometheus, StatsD, PostgreSQL optional)

## What You'll Build

Solve the "financial invisibility" problem that threatens platform survival:

**Scenario:** CFO questions ₹8 Cr annual platform spend across 50 business units with zero visibility into per-tenant costs. Without cost attribution, the platform faces budget cuts despite technical success.

**Solution:** Implement comprehensive cost attribution system that:
- Tracks per-tenant usage (queries, storage, compute, vector operations)
- Calculates costs with multi-component formula and overhead allocation
- Applies volume discounts (15% @ 10K, 30% @ 100K, 40% @ 1M queries)
- Generates CFO-ready monthly invoices with detailed cost breakdowns
- Detects cost anomalies (>50% spikes) with root cause analysis
- Validates attribution accuracy against cloud bills (±10% tolerance)

**Key Capabilities:**
- **Usage Metering:** Track 4 cost components per tenant with <5ms latency overhead
- **Cost Calculation:** Multi-component formula (LLM + Storage + Compute + Vector + Overhead - Discounts)
- **Volume Discounts:** Reward high-volume tenants (0% → 15% → 30% → 40%)
- **Chargeback Reports:** Generate JSON invoices (extendable to PDF with ReportLab)
- **Anomaly Detection:** Alert on >50% cost spikes with root cause hints
- **Migration Estimation:** Prevent surprise costs with pre-upload cost estimates
- **Attribution Validation:** Monthly reconciliation ensures ±10% accuracy

**Success Criteria:**
- ✅ Track usage for 50+ tenants with minimal performance impact
- ✅ Calculate costs within ±10% of actual cloud bills
- ✅ Generate monthly invoices in <5 seconds
- ✅ Detect cost anomalies within 24 hours
- ✅ Provide ROI proof to CFO (platform cost vs. value generated)
- ✅ Enable optimization based on cost insights

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG PLATFORM USAGE                        │
│  (Queries, Storage, Compute, Vector Operations)             │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              USAGE METERING (Prometheus/StatsD)             │
│  • record_query(tenant_id, count)                           │
│  • record_storage(tenant_id, gb)                            │
│  • record_compute(tenant_id, pod_hours)                     │
│  • record_vector_operation(tenant_id, count)                │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              COST CALCULATION ENGINE                         │
│  Direct = LLM + Storage + Compute + Vector                  │
│  Overhead = Direct × 20%                                     │
│  Discount = (Direct + Overhead) × discount_rate             │
│  Final = Direct + Overhead - Discount                       │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              CHARGEBACK REPORT GENERATOR                     │
│  • Monthly invoices (CFO-ready format)                      │
│  • Platform summary (50+ tenants)                           │
│  • Historical trends (12 months)                            │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              COST ANOMALY DETECTOR                           │
│  IF cost increase > 50% MoM:                                │
│    → Alert platform team                                     │
│    → Analyze root cause (query surge, storage spike)        │
│    → Contact tenant owner                                    │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Clone and Setup
```bash
git clone https://github.com/yesvisare/gcc_multi_tenant_ai_pra_l2.git
cd gcc_multi_tenant_ai_pra_l2/gcc_mt_m13_v3
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env if you want to enable optional infrastructure services
# (Prometheus, StatsD, PostgreSQL - all optional)
```

### 4. Run Tests
```bash
# Windows PowerShell
$env:PYTHONPATH=$PWD; pytest -v

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

### 6. Explore Notebook
```bash
jupyter lab notebooks/L3_M13_Scale_Performance_Optimization.ipynb
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PROMETHEUS_ENABLED` | No | `false` | Enable Prometheus metrics collection |
| `PROMETHEUS_HOST` | No | `localhost` | Prometheus server hostname |
| `PROMETHEUS_PORT` | No | `9090` | Prometheus server port |
| `STATSD_ENABLED` | No | `false` | Enable StatsD event recording |
| `STATSD_HOST` | No | `localhost` | StatsD daemon hostname |
| `STATSD_PORT` | No | `8125` | StatsD daemon port |
| `POSTGRES_ENABLED` | No | `false` | Enable PostgreSQL historical storage |
| `POSTGRES_HOST` | No | `localhost` | PostgreSQL server hostname |
| `POSTGRES_PORT` | No | `5432` | PostgreSQL server port |
| `POSTGRES_DB` | No | `cost_attribution` | PostgreSQL database name |
| `POSTGRES_USER` | No | `postgres` | PostgreSQL username |
| `POSTGRES_PASSWORD` | No | - | PostgreSQL password |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |

**Note:** All infrastructure services are **optional**. The module works entirely in-memory without any external services, making it perfect for local development and testing.

## API Endpoints

### Usage Recording
- `POST /usage/query` - Record query execution
- `POST /usage/storage` - Record storage usage
- `POST /usage/compute` - Record compute usage
- `POST /usage/vector` - Record vector operations

### Cost Calculation
- `GET /costs/tenant/{tenant_id}` - Get cost breakdown
- `GET /costs/tenant/{tenant_id}/invoice` - Get CFO invoice
- `GET /costs/platform/summary` - Get platform summary

### Anomaly Detection
- `GET /anomalies/tenant/{tenant_id}` - Check for anomalies
- `GET /anomalies/tenant/{tenant_id}/trend` - Get cost trend

### Utilities
- `POST /estimate/migration` - Estimate migration cost
- `POST /validate/attribution` - Validate accuracy

### Admin
- `POST /admin/reset/{tenant_id}` - Reset tenant usage
- `GET /admin/tenants` - List all tenants

## Common Failures & Fixes

| Failure | Cause | Fix |
|---------|-------|-----|
| **Inaccurate Usage Metering** | Missing cost components (e.g., vector ops not tracked) → Finance billed ₹20K but actual cost ₹28K → ₹96K annual budget deficit | Track ALL cost components (LLM, storage, compute, vector, network). Monthly reconciliation: compare sum of tenant costs to cloud bill (±10% tolerance). Quarterly cost constant updates. |
| **Volume Discounts Not Approved by CFO** | Platform team implements 40% discount without approval → Finance expects ₹1.2L, platform budget assumes ₹2L → ₹80K monthly deficit. CFO discovers at quarter-end, demands price revert. Finance furious about mid-quarter price change. | Get CFO approval in writing for all discount tiers. Document pricing policy: "Discounts: 15% @ 10K, 30% @ 100K, 40% @ 1M (CFO approved 2025-03-01)". Notify tenants of price changes 30 days in advance. Never retroactive changes. |
| **Cost Spikes Not Detected** | Legal uploads 5,000 contracts (50 GB → 2 TB) with no alert → Normal invoice ₹15K, March invoice ₹1.5L (10x spike). Legal shocked: "We didn't know it would cost this much!" | Implement anomaly detection: alert on >50% cost spike. Pre-migration cost estimate: "Uploading 5,000 docs will cost ₹1.2L/month - proceed? (y/n)". Get tenant approval before large uploads. |
| **Overhead Allocation Disputed** | Platform allocates 20% overhead proportionally. Legal (10% usage) pays ₹60K overhead but generates zero support tickets. Finance (30% usage) generates 90% of tickets but only pays ₹1.8L (3x Legal's overhead). Legal challenges fairness. | Document overhead allocation method: "20% of usage (CFO approved 2025-01-01)". Explain rationale: "Usage reflects compute/storage/shared services, not support tickets." Alternative: Hybrid allocation (70% usage, 30% ticket count) if support cost is significant. Get stakeholder buy-in. |
| **Manual Invoice Generation (Excel Errors)** | Platform team manually generates invoices in Excel. March 2025: Formula error calculates storage as GB × $0.23 instead of $0.023. Finance billed ₹1.9L instead of ₹19K. Finance pays invoice (trusts platform team). Quarter-end audit catches error. Finance demands ₹1.71L refund. | Never use Excel for production invoicing. Automate invoice generation (Python script, not spreadsheets). Validate invoices: compare to previous month (>50% change = flag for review). Peer review: second engineer reviews before sending. Unit tests for cost formulas. |

**Cost of These Failures:** ₹4.42 lakhs/year
**Cost to Prevent:** ₹3.25 lakhs/year (metering + validation)
**ROI:** 36% return + avoids CFO mistrust

## Decision Card

### When to Use Cost Attribution

**Platform Scale:**
- ✅ **10-50 tenants:** Implement usage-based metering (our approach). Cost: ₹25K/month, ROI: High
- ⚠️ **> 50 tenants:** Consider third-party tools (Kubecost, CloudHealth). Cost: ₹50K-5L/month
- ❌ **< 10 tenants:** Skip cost attribution (manual tracking sufficient). Revisit at 15+ tenants

**Platform Maturity:**
- ❌ **< 6 months old:** Track usage but don't bill yet (showback mode). Stabilize patterns first.
- ✅ **6-24 months old:** Implement showback first, chargeback in Year 2. Build CFO trust.
- ✅ **> 24 months old:** Implement full chargeback if not already. Mature platforms need cost discipline.

**CFO Culture:**
- ✅ **CFO enforces chargeback:** Implement immediately. CFO will support if costs are transparent.
- ⚠️ **CFO uses showback only:** Implement attribution but skip invoicing. Transparency without accountability.
- ❌ **CFO doesn't care:** Skip cost attribution entirely. Focus on usage caps (simpler).

**Technical Complexity:**
- ✅ **Dedicated DevOps team:** Build custom metering (best ROI). Cost: ₹2L implementation + ₹25K/month
- ⚠️ **Small team (1-2 engineers):** Use cloud-native tools (AWS Cost Explorer). Cost: ₹0 but ±20% accuracy
- ❌ **No bandwidth:** Defer to Year 2. Risk: CFO frustration

### When Cost Attribution is Essential

**✅ Scenario 1: CFO Demands ROI Proof**
- CFO asks: "What's the ROI of ₹10 Cr platform?"
- Without attribution: Can't answer → risk budget cut
- With attribution: Show ₹30 Cr savings across tenants → 3x ROI → CFO approves ₹12 Cr Year 2 budget

**✅ Scenario 2: Tenants Dispute Costs**
- Finance says: "We don't use this much, Legal uses more"
- Without attribution: Argument, no proof
- With attribution: Show usage logs (Finance: 50%, Legal: 20%) → dispute resolved

**✅ Scenario 3: Platform Needs Optimization**
- Platform costs ₹10 Cr/year, CFO says too expensive
- Without attribution: Don't know where to optimize
- With attribution: Discover Finance is 50% of cost → optimize Finance queries → save ₹3 Cr

### When Cost Attribution is Optional

**❌ Scenario 1: Tiny Platform**
- 5 tenants, ₹50L/year cost
- Everyone knows who uses what (no surprises)
- Overhead of attribution > benefit

**❌ Scenario 2: Free Tier Strategy**
- GCC policy: Platform free for first 2 years (subsidize adoption)
- Cost tracking would scare away early adopters
- Wait until Year 3 for chargeback

**❌ Scenario 3: Single Large Tenant**
- Finance is 90% of usage, other 49 tenants share 10%
- Everyone knows Finance pays for everything
- Cost attribution is theater (no value)

### Decision Matrix

| GCC Profile | Recommendation | Implementation Time | Monthly Cost | Accuracy |
|-------------|----------------|---------------------|--------------|----------|
| Small (< 10 tenants, < 6 months) | Manual Tracking | 1 day | ₹0 | ±50% |
| Medium (10-50 tenants, 6-24 months) | Custom Metering | 3 weeks | ₹25K | ±10% |
| Large (50+ tenants, > 24 months) | Kubecost/CloudHealth | 2 weeks | ₹50K-5L | ±15% |

### Cost Analysis Examples

**Small GCC Platform (20 tenants, 5K queries/day):**
- Monthly Total: ₹39,494 ($475 USD)
- Per Tenant: ₹1,975/month
- Cost per Query: ₹0.26

**Medium GCC Platform (100 tenants, 50K queries/day):**
- Monthly Total: ₹3,94,914 ($4,758 USD)
- Per Tenant: ₹3,949/month
- Cost per Query: ₹0.26

**Volume Discount Impact:**
Finance grows 50K → 120K queries:
- Before (TIER_1: 15%): ₹11.9L
- After (TIER_2: 30%): ₹23.52L
- Query increase: +140%
- Cost increase: +97% (less due to better discount)
- Cost per query: ₹0.24 → ₹0.196 (-18% efficiency gain)

## Troubleshooting

### Infrastructure Services Disabled
The module runs in **in-memory mode** by default (no external services required). This is perfect for:
- ✅ Local development and testing
- ✅ Learning and experimentation
- ✅ Running tests

For production, enable optional infrastructure in `.env`:
```bash
PROMETHEUS_ENABLED=true
STATSD_ENABLED=true
POSTGRES_ENABLED=true
```

### Import Errors
If you see `ModuleNotFoundError: No module named 'src.l3_m13_cost_optimization_strategies'`, ensure:
```bash
# Windows PowerShell
$env:PYTHONPATH=$PWD

# Linux/Mac
export PYTHONPATH=$PWD
```

### Tests Failing
Run tests with verbose output:
```bash
pytest -v tests/
```

Common issues:
- Missing PYTHONPATH (see above)
- Missing dependencies (run `pip install -r requirements.txt`)

### API Not Starting
Check uvicorn is installed:
```bash
pip install uvicorn[standard]
```

Verify no port conflicts:
```bash
# Change port if 8000 is in use
uvicorn app:app --reload --port 8001
```

### Notebook Kernel Issues
Install Jupyter kernel:
```bash
pip install ipykernel
python -m ipykernel install --user --name=l3_m13
```

Then select "l3_m13" kernel in Jupyter Lab.

## Architecture Details

### Cost Formula

```python
# Direct costs (per tenant per month)
llm_cost = query_count × $0.002 × 83  # USD to INR
storage_cost = storage_gb × $0.023 × 83
compute_cost = pod_hours × $0.05 × 83
vector_cost = vector_ops × $0.0001 × 83

direct_total = llm + storage + compute + vector

# Overhead (20% of direct)
overhead = direct_total × 0.20

# Volume discount (based on query tier)
if query_count < 10K: discount_rate = 0%
elif query_count < 100K: discount_rate = 15%
elif query_count < 1M: discount_rate = 30%
else: discount_rate = 40%

discount_amount = (direct_total + overhead) × discount_rate

# Final cost
final_cost = direct_total + overhead - discount_amount
cost_per_query = final_cost / query_count
```

### Anomaly Detection Algorithm

```python
# Check for cost spike
if len(historical_costs) > 0:
    previous_cost = historical_costs[-1]
    change_rate = (current_cost - previous_cost) / previous_cost

    if change_rate > 0.50:  # >50% increase
        alert = {
            "type": "cost_spike",
            "change_percent": change_rate × 100,
            "root_cause_hints": analyze_usage(current_usage)
        }
        notify_platform_team(alert)
```

### Validation Process

```python
# Monthly reconciliation
total_attributed = sum(tenant_costs)
actual_cloud_bill = get_aws_bill()
variance = abs(total_attributed - actual_cloud_bill) / actual_cloud_bill

if variance > 0.10:  # >10% variance
    logger.error("Missing cost components - investigate!")
else:
    logger.info(f"Accurate: {variance*100:.1f}% variance")
```

## Real-World Impact

**Before Cost Attribution:**
- CFO: "₹8 Cr spend, no visibility → cut to ₹4 Cr"
- Platform team: "But we serve 50 tenants!"
- CFO: "Prove it." → Can't → Budget cut

**After Cost Attribution:**
- CFO: "₹8 Cr spend across 50 tenants"
- Platform team: "Finance: ₹2.5 Cr (saves ₹12 Cr). Legal: ₹2 Cr (saves ₹8 Cr). Total ROI: 3.6x"
- CFO: "Approved. Here's ₹10 Cr for Year 2."

**Platform Economics:**
- Multi-tenant saves 86% vs. building separately
- Volume discounts incentivize growth
- Cost per query drops with scale
- Chargeback drives optimization

**GCC-Specific Value:**
- Demonstrates ROI to parent company
- Justifies platform team headcount
- Enables cost optimization decisions
- Prevents budget cuts
- Supports expansion to new business units

## Next Module

**M13.4: Infrastructure Scaling**
- Quantify cost impact of scaling decisions
- Auto-scaling policies based on cost thresholds
- Right-sizing infrastructure for cost efficiency
- Trade-offs: performance vs. cost

**How M13.3 Connects:**
- Cost attribution provides data for scaling decisions
- Know which tenants drive costs → prioritize their optimization
- Volume discounts inform capacity planning
- Anomaly detection prevents runaway costs during scaling

## Contributing

This module is part of the TechVoyageHub L3 Production RAG Engineering Track. For issues or improvements, please file an issue in the GitHub repository.

## License

MIT License - See LICENSE file for details.

---

**Version:** 1.0.0
**Last Updated:** 2025-01-18
**Module Code:** L3_M13_3
**Track:** Production RAG Engineering (L3)
**Difficulty:** Advanced
**Estimated Time:** 6-8 hours
