# L3 M13.1: Multi-Tenant Performance Patterns

Production-ready performance isolation framework for multi-tenant RAG systems using Redis namespace patterns, performance tier enforcement, and scoped cache management.

**Part of:** TechVoyageHub L3 Production RAG Engineering Track
**Prerequisites:** GCC Multi-Tenant M11-M12 (tenant foundations, data isolation), Redis intermediate
**SERVICE:** REDIS (caching infrastructure)

## What You'll Build

A performance isolation framework that guarantees Tenant A's traffic spike cannot degrade Tenant B's experience in shared RAG infrastructure.

**Key Capabilities:**
- **Tenant-scoped caching** with Redis namespace isolation (cache:tenant_id:key pattern)
- **Performance tier enforcement** (Platinum 200ms, Gold 500ms, Silver 1s SLAs)
- **Query optimization** with tier-specific TTLs and adaptive caching
- **Scoped cache invalidation** that clears only affected tenant data
- **Hot tenant detection** and auto-throttling to prevent resource monopolization
- **Per-tenant monitoring** with cache hit rates, latency tracking, and quota management

**Success Criteria:**
- Tenant-isolated cache prevents cross-tenant collisions (100% namespace isolation)
- Performance tier SLAs enforced with hard timeouts (99.5%+ compliance)
- Cache hit rate >75% per tenant (measured via Prometheus metrics)
- Load test proves isolation: Tenant A spike → Tenants B-Z latency stable (<10% increase)
- Scoped invalidation: Tenant cache clear affects only that tenant

## How It Works

```
┌─────────────────┠──────────────────┬──────────────────┠
│ Tenant A        │ Tenant B         │ Tenant C         │
│ (Platinum:200ms)│ (Gold:500ms)     │ (Silver:1s)      │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │
         └───────────────────┴───────────────────┘
                             │
                    ┌────────▼────────┠
                    │  FastAPI Layer  │
                    │  (Tenant Router)│
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┠
         │                   │                   │
    ┌────▼────┠         ┌────▼────┠         ┌────▼────┠
    │ Tenant  │         │ Tenant  │         │ Tenant  │
    │ Cache A │         │ Cache B │         │ Cache C │
    │cache:A:*│         │cache:B:*│         │cache:C:*│
    └────┬────┘         └────┬────┘         └────┬────┘
         │                   │                   │
         └───────────────────┴───────────────────┘
                             │
                    ┌────────▼────────┠
                    │  Redis Cluster  │
                    │  (Shared, 192GB)│
                    │  Namespace-Based│
                    │  Logical Isolation│
                    └─────────────────┘
```

**Data Flow:**
1. Query arrives with tenant_id in JWT token
2. Middleware extracts tenant_id, looks up performance tier
3. TenantCache checks `cache:tenant_id:query_hash`
4. If HIT: Return cached result (namespace-isolated, <1ms)
5. If MISS: Execute query with tier-specific timeout (200ms/500ms/1s)
6. Cache result with tier-specific TTL (1h/30min/15min)
7. Track metrics (hits, misses, size) per tenant namespace

## Quick Start

### 1. Clone and Setup
```bash
git clone <repo_url>
cd gcc_mt_m13_v1
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env:
# - Set REDIS_ENABLED=true if Redis available (default: false)
# - Set OFFLINE=false to enable caching (default: true for local dev)
# - Configure REDIS_HOST, REDIS_PORT if using external Redis
```

### 4. Run Tests
```bash
# Windows PowerShell
$env:PYTHONPATH=$PWD; pytest -v tests/

# Or use script
./scripts/run_tests.ps1

# Linux/Mac
PYTHONPATH=$PWD pytest -v tests/
```

### 5. Start API
```bash
# Windows PowerShell
$env:REDIS_ENABLED='False'; $env:PYTHONPATH=$PWD; uvicorn app:app --reload

# Or use script
./scripts/run_api.ps1

# Linux/Mac
REDIS_ENABLED=false PYTHONPATH=$PWD uvicorn app:app --reload
```

API will be available at: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/`

### 6. Explore Notebook
```bash
jupyter lab notebooks/L3_M13_Scale_Performance_Optimization.ipynb
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| REDIS_ENABLED | No | false | Enable Redis caching infrastructure |
| REDIS_HOST | No | localhost | Redis server hostname |
| REDIS_PORT | No | 6379 | Redis server port |
| REDIS_PASSWORD | If auth | - | Redis authentication password |
| REDIS_DB | No | 0 | Redis database number |
| REDIS_SSL | No | false | Enable SSL/TLS for Redis connection |
| OFFLINE | No | true | Run in offline mode (skip Redis operations) |
| LOG_LEVEL | No | INFO | Logging verbosity (DEBUG/INFO/WARNING/ERROR) |

## Common Failures & Fixes

| Failure | Symptom | Root Cause | Fix |
|---------|---------|------------|-----|
| **1. Cache Namespace Collision** | Tenant A queries return Tenant B's results (rare: 1 in 10,000) | Developer forgot TenantCache wrapper, used direct Redis access with un-namespaced keys | Always use `TenantCache` wrapper. Code review: Flag direct `redis.get()` calls. Integration test: Two tenants with same query hash must get different results |
| **2. Cache Eviction Cascade** | Platform-wide cache hit rate drops 80% → 20% in 10 minutes. All tenants experience 5× latency increase | Multiple tenants spiked simultaneously, total cache demand exceeded Redis capacity (240GB demand, 192GB available). Redis evicted platform-wide based on LRU | Set per-tenant cache quotas based on tier (Platinum: 40GB, Gold: 20GB, Silver: 10GB). Reject new cache writes when tenant at 95% quota (force cache misses, don't evict others) |
| **3. Timeout Too Loose** | Platinum tenant complains: "Queries take 800ms, we pay for 200ms SLA". Monitoring shows p95 latency = 750ms | Timeout enforcement set to 2 seconds (too loose). Queries run 500-800ms before completing. Timeout never triggers because 800ms < 2000ms | Set timeout to match tier SLA exactly: Platinum 200ms, Gold 500ms, Silver 1s. Monitor: Alert if p95 latency within 50ms of timeout. Test: Load test each tier, verify timeouts trigger at expected threshold |
| **4. Hot Tenant Starves Platform** | Tenant Z launches product, traffic 100 → 10,000 queries/hour. All other tenants experience 3× latency increase. Tenant Z is 80% of total platform QPS | No per-tenant rate limiting. Tenant Z's 10K QPS saturates vector DB. Other tenants' queries queued behind Tenant Z's flood | Implement per-tier QPS limits (Platinum: 1000 QPS, Gold: 500 QPS, Silver: 200 QPS). Alert when tenant approaches 80% of rate limit. Offer burst pricing for temporary 2× QPS |
| **5. Cache Invalidation Affects All Tenants** | Tenant M updates documents. Entire platform cache cleared (200GB → 0). All tenants experience cold start (100% cache miss rate). Takes 2 hours for cache to warm up | Cache invalidation not tenant-scoped. Developer used Redis `FLUSHDB` command which clears ALL keys, not just tenant's | Use tenant-scoped invalidation: `redis.delete(*redis.keys('cache:tenant_id:*'))`. NEVER use FLUSHDB or FLUSHALL in multi-tenant code. Integration test: Verify invalidation doesn't affect other tenants |

## Decision Card

### âœ… USE Namespaced Cache Isolation If:

**Scale:**
- You have 20-200 tenants (sweet spot for shared infrastructure)
- Platform handles >1,000 QPS total
- Need to add new tenants quickly (<5 minutes onboarding)

**Business Model:**
- Selling performance tiers (Platinum/Gold/Silver)
- Need cost efficiency (shared infrastructure saves 60-75%)
- Tenants have varied traffic patterns (some spike, some steady)

**Technical Context:**
- Have operational maturity (monitoring, on-call, SRE practices)
- Can invest in over-provisioning (25% cache headroom)
- Redis/PostgreSQL expertise on team

**Compliance:**
- Data isolation required (namespace prevents cross-tenant leaks)
- Audit logging needed (track per-tenant cache access)
- No legal requirement for physical separation

**Team:**
- Platform team of 2-5 engineers
- Ratio: 1 engineer per 20-30 tenants (ongoing maintenance)

### ❌ DO NOT USE If:

**Compliance Restrictions:**
- Legal contract mandates physical separation
- HIPAA/PCI-DSS with BAA requiring dedicated infrastructure
- Adversarial tenants (direct competitors on same platform)

**Extreme Variability:**
- Tenants have >100× traffic spikes (seasonal businesses)
- Single tenant >50% of platform load (diversification risk)
- Unpredictable traffic (no patterns, cannot forecast)

**Low Cache Hit Rates:**
- Workload is unique queries (legal research, scientific analysis)
- Cache hit rate <20% (caching not helping)
- Better to invest in vector DB optimization, not cache infrastructure

**Cost Constraints:**
- Budget <₹1L/month total (need cheaper alternative)
- <10 tenants (dedicated might be simpler)
- Non-profit/education (consider community tier with no isolation)

**Operational Immaturity:**
- No monitoring infrastructure (Prometheus, Grafana)
- No on-call rotation (nobody to respond to alerts)
- No SRE practices (runbooks, incident management)

### Trade-offs

**Cost:**
- Shared infrastructure: ₹2-5L/month for 50 tenants (₹4K per tenant)
- vs. Physical separation: ₹8L/month for 50 tenants (₹16K per tenant)
- **Savings: 60-75% cost reduction**

**Latency:**
- Cache hit: <1ms (sub-millisecond Redis lookup)
- Cache miss + Platinum timeout: 200ms maximum
- vs. No caching: 500-3000ms per query (vector DB latency)
- **Improvement: 50-500× faster for cache hits**

**Complexity:**
- Namespace isolation: Medium complexity (requires TenantCache wrapper)
- Monitoring per tenant: Additional Prometheus metrics, Grafana dashboards
- vs. No isolation: Simple but fails at scale
- **Trade-off: Accept 20% operational complexity for 80% isolation**

**Isolation:**
- Namespace-based: 90-95% effective (logical isolation on shared hardware)
- vs. Physical separation: 100% effective (complete isolation)
- **Trade-off: 5-10% imperfect isolation (physical resource exhaustion can still affect all tenants)**

## Example Deployments

### Small GCC (20 tenants, 2K QPS, 50K docs per tenant)
- **Monthly infrastructure:** ₹85K
- **Per-tenant cost:** ₹4.25K/month
- **Team:** 2 platform engineers
- **Cache hit rate:** 80%
- **p95 latency:** Platinum 180ms, Gold 450ms, Silver 950ms

### Medium GCC (50 tenants, 10K QPS, 200K docs per tenant)
- **Monthly infrastructure:** ₹2L
- **Per-tenant cost:** ₹4K/month (economies of scale)
- **Team:** 3-4 platform engineers
- **Cache hit rate:** 82%
- **p95 latency:** Platinum 190ms, Gold 480ms, Silver 980ms

### Large GCC (200 tenants, 40K QPS, 500K docs per tenant)
- **Monthly infrastructure:** ₹6L
- **Per-tenant cost:** ₹3K/month (strong economies of scale)
- **Team:** 8-10 platform engineers
- **Cache hit rate:** 85%
- **p95 latency:** Platinum 200ms, Gold 500ms, Silver 1000ms

**Cost per tenant decreases with scale due to:**
- Shared infrastructure amortization (one Redis serves 200, not 50)
- Operational efficiency (1 engineer manages 25 tenants)
- Cache efficiency (larger cache = better hit rates)

## Troubleshooting

### Redis Disabled Mode
The module will run without Redis if `REDIS_ENABLED` is not set to `true` in `.env`. The `config.py` file will skip Redis client initialization, and API endpoints will execute queries without caching. This is the default behavior and is useful for local development or testing.

To enable caching:
```bash
# .env
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379
OFFLINE=false
```

### Import Errors
If you see `ModuleNotFoundError: No module named 'src.l3_m13_performance_patterns'`, ensure:

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

# See which test failed:
pytest -v tests/test_m13_performance_patterns.py::test_name
```

All tests are designed to run in OFFLINE mode (no Redis required).

### API Not Starting
Check logs for errors:
```bash
uvicorn app:app --log-level debug
```

Common issues:
- Port 8000 already in use: Use `--port 8001`
- Missing dependencies: Run `pip install -r requirements.txt`
- Import errors: Set `PYTHONPATH` as shown above

## Architecture Details

### Performance Tiers

| Tier | Timeout | Cache TTL | Max QPS | Cache Quota | Price |
|------|---------|-----------|---------|-------------|-------|
| Platinum | 200ms | 1 hour | 1000 QPS | 40GB | ₹15K/month |
| Gold | 500ms | 30 min | 500 QPS | 20GB | ₹8K/month |
| Silver | 1000ms | 15 min | 200 QPS | 10GB | ₹5K/month |

### Cache Key Pattern

```
cache:{tenant_id}:{query_hash}
```

**Examples:**
- `cache:tenant_sales:a1b2c3d4e5f6g7h8` (Tenant Sales, query hash a1b2c3...)
- `cache:tenant_hr:9z8y7x6w5v4u3t2s` (Tenant HR, query hash 9z8y7x...)

**Why it works:**
- Different tenants with same query get different keys (tenant_id in hash)
- Redis eviction policy (LRU) operates on key-level access patterns
- Tenant A filling their namespace doesn't evict Tenant B's keys
- Cache invalidation uses pattern: `cache:tenant_id:*` (tenant-scoped)

## API Endpoints

### Query Endpoint
```http
POST /query
Content-Type: application/json

{
  "tenant_id": "tenant_sales",
  "query": "What were our Q4 sales numbers?"
}

Response:
{
  "result": {...},
  "source": "cache",  // or "query"
  "tenant_id": "tenant_sales",
  "tier": "platinum",
  "cached": true,
  "latency_ms": 0.85
}
```

### Cache Metrics
```http
GET /cache/metrics/tenant_sales

Response:
{
  "tenant_id": "tenant_sales",
  "hits": 8420,
  "misses": 1580,
  "size_gb": 12.3,
  "key_count": 5240,
  "hit_rate": 0.842
}
```

### Cache Invalidation
```http
POST /cache/invalidate
Content-Type: application/json

{
  "tenant_id": "tenant_sales"
}

Response:
{
  "tenant_id": "tenant_sales",
  "deleted_keys": 5240,
  "message": "Invalidated 5240 keys for tenant tenant_sales"
}
```

### Tier Information
```http
GET /tiers/tenant_sales

Response:
{
  "tenant_id": "tenant_sales",
  "tier": "platinum",
  "config": {
    "timeout_ms": 200,
    "cache_ttl": 3600,
    "max_qps": 1000,
    "cache_quota_gb": 40.0
  }
}
```

## Next Module

**M13.2: Auto-Scaling & Load Balancing**
- Horizontal pod autoscalers (HPA) for tenant workloads
- Tenant-aware load balancing across compute pods
- Capacity planning and forecasting
- Cost optimization through dynamic resource allocation

**Driving Question:** "How do we automatically provision resources when tenants spike, without over-provisioning for 99% of the time?"

## Resources

- **Code repository:** [github.com/techvoyagehub/multi-tenant-performance-isolation](https://github.com/techvoyagehub/multi-tenant-performance-isolation)
- **Redis namespace patterns:** [redis.io/docs/manual/keyspace](https://redis.io/docs/manual/keyspace)
- **Prometheus monitoring:** [prometheus.io/docs/practices/naming](https://prometheus.io/docs/practices/naming)
- **GCC architecture guide:** [techvoyagehub.com/gcc-multi-tenant-patterns](https://techvoyagehub.com/gcc-multi-tenant-patterns)
- **FastAPI async patterns:** [fastapi.tiangolo.com/async](https://fastapi.tiangolo.com/async)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

This is a reference implementation for TechVoyageHub L3 curriculum. For issues or suggestions, please contact the course maintainers.

---

**Production-Grade Multi-Tenant Architecture** | Built with Redis, FastAPI, and Async Python | Tested at 10K+ QPS
