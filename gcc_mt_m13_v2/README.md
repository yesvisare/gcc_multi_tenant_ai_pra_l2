# L3 M13.2: Auto-Scaling Multi-Tenant Infrastructure

Intelligent Kubernetes auto-scaling for multi-tenant RAG platforms using per-tenant queue depth metrics to drive HPA scaling decisions while enforcing resource quotas and maintaining SLA compliance across 50+ business units.

**Part of:** TechVoyageHub L3 Production RAG Engineering Track
**Prerequisites:** M11.1-M11.4 (Tenant routing, RBAC, provisioning), M12.1-M12.4 (Vector isolation, compliance)
**Services:** Prometheus (metrics), Redis (cache), Kubernetes (orchestration)

---

## What You'll Build

This module implements a production-ready auto-scaling system that solves a critical GCC problem:

**The Crisis:** At 2:47 AM, media tenants processing 10× normal traffic during a sporting event cause platform-wide latency spikes (200ms → 12 seconds) affecting 44 other tenants, despite HPA being configured.

**The Solution:** Tier-based auto-scaling with per-tenant queue depth metrics, resource quotas, and graceful scale-down that prevents noisy neighbor problems while reducing infrastructure costs by 30-45%.

**Key Capabilities:**
- **Per-tenant queue depth tracking** - HPA scales based on tenant-specific load, not global CPU
- **Tier-based scaling policies** - Premium (5-30 pods), Standard (3-15 pods), Free (1-5 pods)
- **Resource quota enforcement** - No tenant exceeds 40% of cluster resources
- **Graceful scale-down** - 30-second connection draining prevents query drops
- **Cost attribution** - Per-tenant pod-hour tracking for CFO chargeback
- **Compliance audit trail** - SOX/DPDPA logging of all scale events

**Success Criteria:**
- ✅ HPA scales up within 2 minutes of queue depth >10
- ✅ No tenant can monopolize resources (quota enforcement)
- ✅ Scale-down occurs without dropping active queries
- ✅ 30-45% cost reduction vs fixed capacity
- ✅ 99.9%+ SLA compliance across all tiers

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                    Multi-Tenant Query Flow                       │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
        ┌────────────────────────────────────────────┐
        │         FastAPI Application                 │
        │  ┌─────────────────────────────────────┐  │
        │  │  TenantQueueManager                 │  │
        │  │  - tenant_a: 50 queries queued      │  │
        │  │  - tenant_b: 10 queries queued      │  │
        │  │  - tenant_c: 5 queries queued       │  │
        │  └─────────────────────────────────────┘  │
        │              │                              │
        │              ▼                              │
        │  ┌─────────────────────────────────────┐  │
        │  │  Prometheus Metrics Exporter        │  │
        │  │  tenant_queue_depth{tenant_a} = 50  │  │
        │  │  tenant_queue_depth{tenant_b} = 10  │  │
        │  └─────────────────────────────────────┘  │
        └────────────────────────────────────────────┘
                                 │
                                 ▼ (scrape every 15s)
        ┌────────────────────────────────────────────┐
        │           Prometheus Server                 │
        │  Stores time-series metrics                 │
        └────────────────────────────────────────────┘
                                 │
                                 ▼
        ┌────────────────────────────────────────────┐
        │         Prometheus Adapter                  │
        │  Translates metrics to K8s Custom Metrics   │
        │  API: queue_depth_per_tenant                │
        └────────────────────────────────────────────┘
                                 │
                                 ▼
        ┌────────────────────────────────────────────┐
        │   Kubernetes HPA (Horizontal Pod Autoscaler)│
        │  - Reads queue_depth_per_tenant             │
        │  - Calculates target replicas               │
        │  - Updates Deployment spec                  │
        │  - Enforces min/max constraints             │
        └────────────────────────────────────────────┘
                                 │
                                 ▼
        ┌────────────────────────────────────────────┐
        │         Kubernetes Deployment               │
        │  - Scales pods from 3 → 15 (example)        │
        │  - Checks ResourceQuota (40% limit)         │
        │  - Applies Pod Anti-Affinity rules          │
        │  - Sends SIGTERM for graceful termination   │
        └────────────────────────────────────────────┘
```

**Control Loop Timeline:**
- T+0s: Traffic spike begins
- T+15s: Prometheus scrapes metrics
- T+30s: HPA queries Prometheus Adapter
- T+60s: HPA updates Deployment spec
- T+90s: New pods ready, queue depth normalizes

**Total scale-up latency: 2-5 minutes** (not instant - this is important for architecture decisions)

---

## Quick Start

### 1. Clone and Setup
```bash
git clone <repo_url>
cd gcc_mt_m13_v2
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env and configure services (optional - works offline by default)
```

### 4. Run Tests
```bash
# Windows PowerShell
$env:PYTHONPATH=$PWD; pytest -v tests/

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

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDIS_ENABLED` | No | `false` | Enable Redis for pod warm-up state cache |
| `REDIS_HOST` | If enabled | `localhost` | Redis server hostname |
| `REDIS_PORT` | If enabled | `6379` | Redis server port |
| `PROMETHEUS_ENABLED` | No | `false` | Enable Prometheus for metrics queries |
| `PROMETHEUS_URL` | If enabled | `http://localhost:9090` | Prometheus server URL |
| `MIN_REPLICAS` | No | `3` | Minimum pods (baseline capacity) |
| `MAX_REPLICAS` | No | `20` | Maximum pods (budget ceiling) |
| `TARGET_QUEUE_DEPTH` | No | `10` | Target queries per pod for scaling |
| `OFFLINE` | No | `false` | Run in offline mode (notebook/testing) |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |

---

## Common Failures & Fixes

Based on real GCC production incidents from the script:

| Failure | Cause | Fix |
|---------|-------|-----|
| **HPA scales on wrong metric → wasteful scaling** | Using CPU instead of queue depth for I/O-bound workload | Switch to custom metric `tenant_queue_depth` via Prometheus Adapter |
| **HPA thrashing (rapid up/down) → wasted ₹15K/month** | Choppy load with default 0s stabilization window | Set `stabilizationWindowSeconds: 60` (scale-up), `300` (scale-down) |
| **New pods get traffic before ready → 503 errors** | Readiness probe only checks if server running, not if models loaded | Implement proper readiness check validating embeddings loaded, vector DB connected |
| **HPA can't scale beyond 12 pods** | Hard pod anti-affinity requires different nodes, only 12 nodes available | Use `preferredDuringSchedulingIgnoredDuringExecution` (soft constraint) instead of `required` |
| **HPA scales down during peak → premature scale-down** | Brief 10-second pauses in load trigger scale-down | Increase `stabilizationWindowSeconds` to 600s (10 min) for scale-down |
| **Tenant A's scaling triggers Tenant B's quota limit** | Cluster-wide ResourceQuota instead of per-tenant | Use per-namespace ResourceQuota with tier-specific limits |
| **Cross-region scaling violates data residency (DPDPA)** | HPA scales pods to US nodes for India tenant data | Add hard `nodeAffinity` constraint requiring `ap-south-1` region |
| **Black Friday cost spike: ₹5L in 48 hours** | No capacity planning for multi-tenant events | Pre-provision capacity 1 week before known events |

---

## Decision Card

### ✅ USE KUBERNETES HPA WHEN:
- You have **variable load** (>50% difference between peak and trough)
- You serve **multiple tenants** with different scaling profiles
- You need **cost optimization** (pay for actual usage, not peak capacity)
- You have **unpredictable spikes** (cannot schedule pre-provisioning)
- Your platform has **>10 tenants** (economies of scale justify HPA complexity)
- You need **SLA compliance** (99.9%+) without massive over-provisioning

### ❌ AVOID KUBERNETES HPA WHEN:
- Load is **predictable and stable** (<20% variation) - fixed capacity is simpler
- You have **<5 tenants** - overhead of HPA configuration exceeds benefits
- Your queries are **extremely latency-sensitive** (<50ms) - 2-minute scale-up lag unacceptable
- Your organization **lacks Kubernetes expertise** - HPA failures cause outages
- You need **instant scale-up** (sub-10-second) - HPA takes 2-5 minutes minimum
- You have **strict data residency** with limited regions - node constraints block scaling

### 💰 COST IMPLICATIONS:

**Small GCC Platform (5 tenants, 500 queries/sec peak, 200 queries/sec average):**
- **Fixed Capacity:** 10 pods always running
  - Monthly: ₹83K ($1,000 USD)
  - Utilization: 40% (wasted 60% of time)
- **Auto-Scaling (HPA):** 5-12 pods dynamically
  - Monthly: ₹58K ($700 USD)
  - **Savings: ₹25K/month (30%)**
  - Break-even: Immediate (no upfront cost)

**Medium GCC Platform (25 tenants, 2,500 queries/sec peak, 800 queries/sec average):**
- **Fixed Capacity:** 50 pods always running
  - Monthly: ₹4.15L ($5,000 USD)
  - Utilization: 32% (wasted 68% of time)
- **Auto-Scaling (HPA):** 15-40 pods dynamically
  - Monthly: ₹2.5L ($3,000 USD)
  - **Savings: ₹1.65L/month (40%)**
  - Additional: ₹20K setup (Prometheus, Grafana, custom metrics)

**Large GCC Platform (50+ tenants, 10K queries/sec peak, 3K queries/sec average):**
- **Fixed Capacity:** 200 pods always running
  - Monthly: ₹16.6L ($20,000 USD)
  - Utilization: 30% (wasted 70% of time)
- **Auto-Scaling (HPA):** 60-150 pods dynamically
  - Monthly: ₹9.15L ($11,000 USD)
  - **Savings: ₹7.45L/month (45%)**
  - Additional: ₹1.5L setup (enterprise Prometheus, Cluster Autoscaler, FinOps tooling)

### ⚖️ FUNDAMENTAL TRADE-OFFS:
- **Benefit:** 30-45% cost reduction vs fixed capacity (pay for actual usage)
- **Limitation:** 2-5 minute scale-up lag (cannot handle instant spikes)
- **Complexity:** High (requires Kubernetes expertise, custom metrics, monitoring)

### 📊 EXPECTED PERFORMANCE:
- **Scale-up latency:** 2-5 minutes (metric detection → pod ready)
- **Scale-down latency:** 5-10 minutes (stabilization window + graceful termination)
- **Query latency:** <500ms p95 (assuming warm pods with cache)
- **Throughput:** 20-50 queries/sec per pod (depends on query complexity)
- **SLA compliance:** 99.9%+ uptime (if configured correctly with pre-warming)

### 🏢 GCC ENTERPRISE SCALE:
- **Tenants supported:** 50+ business units on single platform
- **Regions:** Multi-region deployment (US, EU, India, APAC) with data residency
- **Compliance:** SOX/DPDPA/GDPR audit trails for all scale events
- **Uptime SLA:** 99.9% (standard), 99.95% (premium), 99.99% (enterprise)
- **Resource quotas:** Per-tenant caps (premium: 40%, standard: 20%, free: 10%)
- **Cost attribution:** Per-tenant pod-hour tracking with monthly chargeback

### 🔍 ALTERNATIVE APPROACHES:

**Use Fixed Capacity (no auto-scaling) if:**
- Load is stable (<20% variation)
- Platform is small (<5 tenants)
- Organization lacks K8s expertise

**Use Vertical Pod Autoscaler (VPA) if:**
- You want to optimize pod resource requests (CPU/memory)
- Horizontal scaling (adding pods) is not needed
- Focus is cost optimization, not scale

**Use Cluster Autoscaler (CA) + HPA if:**
- You need to scale both pods AND nodes
- You have hard anti-affinity constraints (one pod per node)
- You want maximum flexibility

**Use Predictive Scaling (KEDA + scheduled) if:**
- Your load is predictable (daily/weekly patterns)
- You want zero-delay scaling (pre-provision before spike)
- You can tolerate complexity of scheduled policies

**Use Managed Services (AWS Fargate, Cloud Run) if:**
- You want serverless auto-scaling (no K8s management)
- Cost is less important than operational simplicity
- You're willing to accept vendor lock-in

---

## Troubleshooting

### Services Disabled Mode
The module runs without external service integration by default. Redis and Prometheus are optional:
- `REDIS_ENABLED=false`: No cache (pods start fresh each time)
- `PROMETHEUS_ENABLED=false`: Metrics only exported via `/metrics` endpoint, not queried

This is the default behavior and is useful for local development or testing without infrastructure dependencies.

### Import Errors
If you see `ModuleNotFoundError: No module named 'src.l3_m13_scale_performance_optimization'`, ensure:
```bash
$env:PYTHONPATH=$PWD  # Windows PowerShell
# or
export PYTHONPATH=$(pwd)  # Linux/Mac
```

### Tests Failing
Run tests with verbose output to see detailed errors:
```bash
pytest -v tests/
```

All tests run in offline mode (no external services required) and should pass out of the box.

### API Not Starting
Check if port 8000 is already in use:
```bash
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000
```

---

## Architecture Decisions

### Why Per-Tenant Queue Depth (Not CPU)?
**Problem:** CPU is a lagging indicator. By the time CPU hits 80%, queries are already queuing for 10+ seconds.

**Solution:** Queue depth is a leading indicator—it tells us "load is incoming" before pods are saturated. Testing showed: <10 queries/pod = <200ms latency, >10 queries/pod = latency degrades.

**Result:** HPA reacts 30-60 seconds faster than CPU-based scaling.

### Why Asymmetric Scaling Policies?
**Scale-up:** Aggressive (100% increase or +4 pods, whichever is more)
- Cost of under-provisioning: SLA breaches, customer churn, ₹50K+ penalties
- Better to over-scale and pay ₹5K extra

**Scale-down:** Conservative (10% decrease or -2 pods, whichever is less)
- Cost of premature scale-down: Latency spike, immediate scale-up again
- Better to run extra pods for 5 minutes than cause outage

**Result:** Risk management translated into HPA policy.

### Why 3 Min Replicas (Not 1)?
**Problem:** Kubernetes pod startup time is 30-90 seconds. Scaling from 1 → 10 pods takes 2-3 minutes. During that time, single pod is overwhelmed.

**Solution:** With min=3, we have baseline capacity. A spike triggers scale from 3 → 10 (7 new pods), but initial 3 pods handle load until reinforcements arrive.

**Cost:** ₹6K/month for 24/7 readiness—acceptable for 50-tenant platform serving enterprise clients.

### Why 300s Scale-Down Stabilization (Not 60s)?
**Problem:** Media tenant sends 100 queries in 5 seconds (fat-finger in UI), then stops. Without stabilization, HPA scales up, realizes load is gone, scales down—all within 2 minutes (thrashing).

**Solution:** 5-minute confidence period ensures load is truly gone before scaling down.

**Result:** Rather waste ₹5 running extra pods for 5 minutes than cause latency spike costing ₹50K in SLA penalties.

---

## Next Module

**M13.3: Cost Attribution & Chargeback Systems** builds on this auto-scaling foundation with:
- Usage metering service tracking per-tenant pod-hours, query counts, storage usage
- Cost calculation engine applying pricing tiers and volume discounts
- Chargeback report generator creating monthly invoices per tenant
- Cost anomaly detection alerting when tenant costs spike >50% unexpectedly

**Before M13.3, complete:**
- Configure HPA for 10 tenants (1 premium, 5 standard, 4 free)
- Run load test simulating premium tenant 10× spike, verify standard tenants unaffected
- Generate cost report proving 30%+ savings vs fixed capacity

---

## Resources

- **Code repository:** Complete HPA manifests, Prometheus configuration, load generators
- **Documentation:** [Kubernetes HPA Best Practices](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- **Further reading:**
  - "Multi-Tenant Auto-Scaling at Netflix" - Engineering blog
  - "Cost Optimization with Kubernetes HPA" - AWS whitepaper
  - "GCC Platform Engineering Patterns" - TechVoyageHub guide

---

## License

MIT License - See LICENSE file for details.

---

**Version:** 1.0
**Track:** GCC Multi-Tenant Architecture for RAG Systems
**Module:** M13 - Scale & Performance Optimization
**Video:** M13.2 - Auto-Scaling Multi-Tenant Infrastructure
