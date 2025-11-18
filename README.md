# L3 M12.3: Query Isolation & Rate Limiting

Production-grade per-tenant rate limiting using Redis token bucket algorithm to prevent noisy neighbor problems in multi-tenant RAG systems. Implements automated detection and mitigation with <5ms latency overhead.

**Part of:** TechVoyageHub L3 Production RAG Engineering Track
**Prerequisites:** L3 M12.1 (Tenant Identification), L3 M12.2 (Resource Allocation)
**Services:** Redis (rate limiting), PostgreSQL (tenant registry), Prometheus (metrics)

## What You'll Build

A complete rate limiting system that:
- **Prevents noisy neighbors** from degrading service for other tenants
- **Enforces per-tenant quotas** using Redis atomic operations (<5ms overhead)
- **Detects anomalies** within 30 seconds using sliding window metrics
- **Auto-mitigates** with circuit breakers and rate reductions
- **Notifies stakeholders** via Slack and email within 10 seconds

**Key Capabilities:**
- Token bucket rate limiting with automatic TTL-based refill
- Multi-tier tenant system (Bronze/Silver/Gold) with priority queuing
- Real-time noisy neighbor detection (3x/5x baseline thresholds)
- Automated mitigation (50% reduction for high severity, circuit breaker for critical)
- Graceful degradation with HTTP 429 and Retry-After headers
- Prometheus metrics integration for monitoring and alerting
- Offline mode with in-memory fallback for testing

**Success Criteria:**
- Rate limit checks complete in <5ms (p95)
- Noisy neighbor detection within 30 seconds of threshold breach
- Auto-mitigation applied within 60 seconds (vs 15-20 minutes manual response)
- Zero false positives for legitimate traffic spikes (≤3x baseline)
- All tenants maintain minimum allocation (10-25%) even during contention

## How It Works

```
┌─────────────┐
│   Client    │
│  (Tenant)   │
└──────┬──────┘
       │
       │ HTTP Request
       │ X-Tenant-ID: tenant_gold
       ▼
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Middleware                     │
│  ┌───────────────────────────────────────────────────┐  │
│  │ 1. Extract Tenant ID                              │  │
│  │ 2. Load Tenant Config (cached, 5min TTL)         │  │
│  │ 3. Check Circuit Breaker Status                   │  │
│  │ 4. Redis Token Bucket Check (INCR + EXPIRE)      │  │
│  └───────────────────────────────────────────────────┘  │
└────────┬───────────────────────────┬────────────────────┘
         │                           │
         │ Allowed                   │ Blocked
         ▼                           ▼
  ┌─────────────┐          ┌──────────────────┐
  │   Process   │          │  HTTP 429        │
  │   Request   │          │  Rate Limit      │
  │             │          │  Exceeded        │
  │  ┌───────┐  │          │                  │
  │  │Handler│  │          │  Retry-After: 42 │
  │  └───┬───┘  │          └──────────────────┘
  │      │      │
  │      ▼      │
  │  Response   │
  └─────┬───────┘
        │
        ▼
  ┌─────────────────────────────────────┐
  │   Noisy Neighbor Detection          │
  │  (Background Process)                │
  │                                      │
  │  Prometheus Metrics:                 │
  │  • tenant_queries_total              │
  │  • tenant_queries_blocked_total      │
  │  • tenant_query_latency_seconds      │
  │                                      │
  │  Alert Rules:                        │
  │  • 3x baseline >1min  → High         │
  │  • 5x baseline >30sec → Critical     │
  └────────┬────────────────────────────┘
           │
           │ Alert Webhook
           ▼
  ┌─────────────────────────────────────┐
  │   NoisyNeighborMitigator            │
  │                                      │
  │  High:     50% rate reduction       │
  │  Critical: Circuit breaker (5min)   │
  └────────┬────────────────────────────┘
           │
           │ Notification
           ▼
  ┌─────────────────────────────────────┐
  │   NotificationService               │
  │                                      │
  │  • Slack (ops team)                 │
  │  • Email (tenant admin)             │
  │  • Ops dashboard                    │
  └─────────────────────────────────────┘
```

**Data Flow:**
1. Request arrives with tenant identifier
2. Middleware loads tenant config from PostgreSQL (cached)
3. Redis atomic INCR on key `{tenant_id}:{minute}` with 60s TTL
4. If count ≤ limit: Allow + update metrics + check for anomaly
5. If count > limit: Block with 429 + Retry-After header
6. Background: Prometheus monitors per-tenant QPS
7. On threshold breach: Auto-mitigate + notify stakeholders

## Quick Start

### 1. Clone and Setup
```bash
git clone https://github.com/yesvisare/gcc_multi_tenant_ai_pra_l2.git
cd gcc_multi_tenant_ai_pra_l2
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env - for quick start, leave services disabled (offline mode)
# Set REDIS_ENABLED=true and POSTGRES_ENABLED=true only if you have services running
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
$env:OFFLINE='true'; $env:PYTHONPATH=$PWD; uvicorn app:app --reload

# Or use script
./scripts/run_api.ps1
```

The API will start at `http://localhost:8000`. Visit `http://localhost:8000/docs` for interactive API documentation.

### 6. Test Rate Limiting
```bash
# Send queries as bronze tenant (100 QPM limit)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant_bronze" \
  -d '{"query": "What are Q4 revenue trends?"}'

# Check tenant stats
curl http://localhost:8000/tenant/tenant_bronze/stats
```

### 7. Explore Notebook
```bash
jupyter lab notebooks/L3_M12_Data_Isolation_Security.ipynb
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDIS_ENABLED` | No | `false` | Enable Redis for rate limiting |
| `REDIS_URL` | If enabled | `redis://localhost:6379/0` | Redis connection string |
| `REDIS_MAX_CONNECTIONS` | No | `50` | Redis connection pool size |
| `POSTGRES_ENABLED` | No | `false` | Enable PostgreSQL for tenant configs |
| `POSTGRES_URL` | If enabled | `postgresql://...` | PostgreSQL connection string |
| `POSTGRES_MAX_CONNECTIONS` | No | `20` | PostgreSQL connection pool size |
| `PROMETHEUS_ENABLED` | No | `false` | Enable Prometheus metrics |
| `PROMETHEUS_PORT` | No | `8001` | Prometheus metrics port |
| `OFFLINE` | No | `true` | Run in offline mode (in-memory fallbacks) |
| `SLACK_WEBHOOK_URL` | No | - | Slack webhook for notifications |
| `EMAIL_SMTP_SERVER` | No | - | SMTP server for email notifications |
| `DEFAULT_RATE_LIMIT_PER_MINUTE` | No | `100` | Default rate limit for unknown tenants |
| `NOISY_NEIGHBOR_THRESHOLD_MULTIPLIER` | No | `5` | Critical threshold multiplier |
| `CIRCUIT_BREAKER_DURATION_SECONDS` | No | `300` | Circuit breaker duration (5 minutes) |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |

## Common Failures & Fixes

| Failure | Cause | Fix |
|---------|-------|-----|
| **No rate limiting applied** | Single tenant spike causes platform-wide outage affecting all tenants | Implement per-tenant isolation from Day 1. Use `{tenant_id}:{minute}` Redis keys, not global counters |
| **Global limit instead of per-tenant** | Large tenant (500 QPM) monopolizes capacity, starving small tenants | Use tenant-specific keys in Redis. Each tenant gets independent quota tracking |
| **Manual-only mitigation** | 10-20 minute response time for ops team to identify and throttle noisy tenant | Automate via Prometheus webhooks. Target: detect in 30s, mitigate in 60s |
| **Over-sensitive circuit breaker** | Legitimate traffic spikes (2x baseline) get blocked, frustrating users | Set threshold at 5x baseline for circuit breaker, 3x for warnings. Allow normal variance |
| **No tenant notification** | Surprise 429 errors with no warning, tenant opens angry support ticket | Send email + Slack within 10 seconds of mitigation. Include reason and duration |
| **Rate limit check adds 50ms latency** | Business rejects feature due to performance impact | Use Redis pipelining and connection pooling. Target <5ms p95 latency |
| **Circuit breaker never lifts** | Tenant permanently blocked due to bug in expiration logic | Use TTL-based expiration. Store `end_time` and check on each request |
| **Fair queuing not working** | Gold tier and bronze tier get same treatment during contention | Implement priority queue. Gold=3, Silver=2, Bronze=1. Process higher priority first |
| **Minimum allocation violated** | Bronze tenant gets 0% during gold spike, violating fairness guarantee | Enforce minimum floor (10-25% based on tier). Always reserve capacity for each tier |
| **Token refill logic fails** | Complex manual refill process has off-by-one errors and race conditions | Use Redis key TTL for automatic refill. Keys expire after 60s, no manual logic needed |
| **Cache stampede on config** | All servers query PostgreSQL simultaneously when cache expires | Add jitter to cache TTL (300±30s). Use cache-aside pattern with fallback |
| **Redis connection pool exhausted** | High QPS exceeds connection pool, requests timeout waiting for connections | Increase `REDIS_MAX_CONNECTIONS`. Monitor connection usage. Use pipelining for batches |

## Decision Card

### When to Use This Approach

✅ **Multi-tenant SaaS platform** with shared infrastructure (10+ business units or customers)
✅ **Unpredictable tenant workloads** where any tenant could spike without warning
✅ **Cost-sensitive environment** requiring shared resources instead of dedicated infrastructure per tenant
✅ **Tier-based service levels** (Bronze/Silver/Gold) mapping to business criticality
✅ **Need for fairness guarantees** to prevent monopolization by large tenants
✅ **Platform reliability is critical** and noisy neighbor incidents are unacceptable
✅ **Automated operations required** to handle incidents faster than manual response (15-20 min)
✅ **10,000+ aggregate QPS** across 50+ tenants where interference is statistically likely

### When NOT to Use This Approach

❌ **Single-tenant system** (no noisy neighbors possible)
❌ **All-internal teams** with political resistance to throttling colleagues
❌ **Wildly different tenant sizes** (>10× variation) - dedicate infrastructure to largest tenants instead
❌ **Regulatory isolation requirement** (healthcare, finance) - use separate infrastructure, not shared + limits
❌ **Using rate limits as pricing enforcement** - separate metering from protection (charge overages, don't block)
❌ **Budget allows dedicated resources** - simpler to give each tenant their own infrastructure
❌ **Tenant workloads are predictable** and similar - less risk of interference
❌ **Ultra-low latency requirement (<1ms)** where even 5ms overhead is unacceptable

### Trade-offs

**Cost:**
- Infrastructure: ₹75,000/month (3-node Redis cluster + 4 API servers for 50 tenants)
- Per tenant: ₹1,500/month
- ROI: Prevents incidents costing ₹20-50 lakh each; recoups in ~10 days

**Latency:**
- Added overhead: 3-8ms per request (p50-p95)
- Trade-off: 5% latency increase to prevent 100% service degradation during incidents

**Complexity:**
- Components: Redis, PostgreSQL, Prometheus, FastAPI middleware
- Operational overhead: Moderate (alerts, monitoring, occasional manual intervention)
- Alternative: No rate limiting = simpler but risky; dedicated infrastructure = simpler but expensive

**Fairness vs. Flexibility:**
- Strict limits prevent noisy neighbors but may frustrate legitimate spike users
- Mitigation: Set high thresholds (5x baseline) and provide clear notification/escalation path

**Detection Speed vs. False Positives:**
- 30-second detection window balances speed with accuracy
- Faster windows (10s) increase false positives on legitimate variance
- Slower windows (2min) allow more damage before intervention

## Production Deployment

### Infrastructure Requirements

**Redis Cluster (3 nodes):**
- Purpose: Token bucket state storage
- Specs: 8GB RAM per node, persistence disabled (TTL-based keys)
- HA: Sentinel or Redis Cluster mode for failover
- Monitoring: Track connection pool usage, memory, latency

**PostgreSQL (1 primary + 1 replica):**
- Purpose: Tenant tier registry
- Specs: 16GB RAM, SSD storage
- Schema: `tenant_configs` table with tenant_id, tier, queries_per_minute, priority
- Cache: 5-minute TTL to reduce load

**Prometheus + Grafana:**
- Purpose: Metrics collection and alerting
- Metrics: Per-tenant QPS, blocked queries, latency
- Alerts: Webhooks to NoisyNeighborMitigator for auto-mitigation

**API Servers (4 instances):**
- Purpose: FastAPI application with rate limiting middleware
- Specs: 4 CPU, 8GB RAM per instance
- Load balancer: Nginx or AWS ALB distributing traffic

### PostgreSQL Schema

```sql
CREATE TABLE tenant_configs (
    tenant_id VARCHAR(255) PRIMARY KEY,
    tier VARCHAR(50) NOT NULL CHECK (tier IN ('bronze', 'silver', 'gold')),
    queries_per_minute INTEGER NOT NULL,
    priority INTEGER NOT NULL,
    min_allocation_pct INTEGER DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed data
INSERT INTO tenant_configs (tenant_id, tier, queries_per_minute, priority) VALUES
('tenant_bronze', 'bronze', 100, 1),
('tenant_silver', 'silver', 500, 2),
('tenant_gold', 'gold', 2000, 3);
```

### Prometheus Alert Rules

```yaml
groups:
  - name: noisy_neighbor_alerts
    interval: 30s
    rules:
      - alert: TenantHighUsage
        expr: rate(tenant_queries_total[1m]) > 3 * tenant_baseline_qpm
        for: 1m
        labels:
          severity: high
        annotations:
          summary: "Tenant {{ $labels.tenant_id }} exceeding 3x baseline"

      - alert: TenantCriticalUsage
        expr: rate(tenant_queries_total[30s]) > 5 * tenant_baseline_qpm
        for: 30s
        labels:
          severity: critical
        annotations:
          summary: "Tenant {{ $labels.tenant_id }} exceeding 5x baseline"
```

## Troubleshooting

### Service Disabled Mode
The module runs in **offline mode** by default (no external services required). If `REDIS_ENABLED` and `POSTGRES_ENABLED` are `false` in `.env`:
- Rate limiting uses in-memory fallback (simple bucket algorithm)
- Tenant configs use static defaults (3 tiers: bronze/silver/gold)
- Prometheus metrics are skipped
- API endpoints return mock responses

This is useful for local development, testing, and learning without infrastructure setup.

### Import Errors
If you see `ModuleNotFoundError: No module named 'src.l3_m12_data_isolation_security'`:
```bash
# Windows PowerShell
$env:PYTHONPATH=$PWD

# Linux/Mac
export PYTHONPATH=$PWD
```

### Redis Connection Failed
If you see `Redis connection failed` in logs:
1. Check if Redis is running: `redis-cli ping` (should return `PONG`)
2. Verify `REDIS_URL` in `.env` matches your Redis instance
3. Check firewall/network access to Redis port (default 6379)
4. Fallback: Set `REDIS_ENABLED=false` to use in-memory limiter

### PostgreSQL Connection Failed
If you see `PostgreSQL setup failed`:
1. Check if PostgreSQL is running: `psql -h localhost -U user -d tenants`
2. Verify `POSTGRES_URL` connection string format
3. Ensure `tenant_configs` table exists (see schema above)
4. Fallback: Set `POSTGRES_ENABLED=false` to use static configs

### Tests Failing
Run tests with verbose output:
```bash
pytest -v tests/

# Run specific test class
pytest tests/test_m12_data_isolation_security.py::TestTenantRateLimiter -v

# Run with coverage report
pytest --cov=src tests/ --cov-report=html
```

### Rate Limiting Not Working
1. Check middleware is applied: Look for `X-RateLimit-Limit` header in responses
2. Verify tenant ID is being extracted: Check logs for "Processing query for {tenant_id}"
3. Test manually:
```bash
# Send 10 requests quickly
for i in {1..10}; do
  curl -X POST http://localhost:8000/query \
    -H "X-Tenant-ID: tenant_bronze" \
    -d '{"query": "test"}' &
done
# Some should return HTTP 429
```

### Circuit Breaker Not Lifting
Check circuit breaker status:
```bash
curl http://localhost:8000/tenant/tenant_id/stats
```
If `circuit_broken: true` persists beyond expected duration:
1. Verify `CIRCUIT_BREAKER_DURATION_SECONDS` is set correctly (default 300s)
2. Check server time synchronization (circuit breaker uses timestamps)
3. Restart API server to clear in-memory circuit breaker state

## Next Module
**L3 M13: Cost Attribution & Chargeback** - Implement per-tenant cost tracking and usage-based billing to allocate infrastructure costs accurately across business units.

## Contributing
This module is part of the TechVoyageHub curriculum. For issues or improvements, please open a GitHub issue or submit a pull request.

## License
MIT License - see LICENSE file for details.

## References
- Redis Rate Limiting Patterns: https://redis.io/docs/manual/patterns/rate-limiter/
- Token Bucket Algorithm: https://en.wikipedia.org/wiki/Token_bucket
- Noisy Neighbor Problem: https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/noisy-neighbor.html
- Prometheus Alerting: https://prometheus.io/docs/alerting/latest/overview/
