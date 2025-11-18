# L3 M11.1: Multi-Tenant RAG Architecture Patterns

Production-ready multi-tenant RAG system implementing namespace isolation, tenant routing middleware, and cost attribution for Global Capability Centers serving 30+ business units.

**Part of:** TechVoyageHub L3 Production RAG Engineering Track
**Prerequisites:** Generic CCC M1-M8, Single-tenant RAG implementation, PostgreSQL fundamentals, FastAPI experience
**Services:** PINECONE (vector database), OPENAI (embeddings/LLM), PostgreSQL, Redis

## What You'll Build

A production multi-tenant RAG architecture that reduces infrastructure costs from ₹29 crore to ₹5.8 crore annually while maintaining complete data isolation across tenants. The system supports 50+ business units with automated tenant onboarding, per-tenant rate limiting, and comprehensive audit logging.

**Key Capabilities:**
- **Four Isolation Models:** Shared-DB (logical filters), Shared-Schema (RLS policies), Separate-DB (physical isolation), Hybrid (80/20 cost-optimized)
- **Tenant Routing:** JWT claim extraction, API key parsing, subdomain-based routing with FastAPI middleware
- **Context Propagation:** Async-safe tenant_id propagation using Python contextvars across complex call chains
- **Vector Namespace Isolation:** Pinecone namespace-per-tenant pattern preventing cross-tenant data leaks
- **PostgreSQL RLS:** Row-Level Security policies for defense-in-depth metadata isolation
- **Per-Tenant Rate Limiting:** Independent quota tracking preventing noisy neighbor problems
- **Cost Attribution:** Metering vector operations, LLM calls, and storage for accurate chargeback
- **GDPR Compliance:** Soft-delete with 90-day retention, complete tenant data purge capability
- **Automated Testing:** Cross-tenant leak detection, RLS validation, spoofed JWT protection

**Success Criteria:**
- ✅ Tenant isolation validated via external penetration testing
- ✅ Cross-tenant leak detection automated (runs on every deployment)
- ✅ Cost tracking accurate to ±2% (CFO chargeback validation)
- ✅ Tenant onboarding automated (<1 day for standard tier, vs 2 weeks manual)
- ✅ Blast radius containment verified (one tenant's failure isolated)
- ✅ Per-tenant SLA monitoring (99.9% premium, 99.5% standard)
- ✅ Audit trail comprehensive (every query logged with tenant_id)

## How It Works

```
                                   ┌─────────────────────┐
                                   │  Client Request     │
                                   │  (JWT or API Key)   │
                                   └──────────┬──────────┘
                                              │
                                   ┌──────────▼──────────┐
                                   │ Tenant Routing      │
                                   │ Middleware          │
                                   │ - Extract tenant_id │
                                   │ - Validate status   │
                                   │ - Set context       │
                                   └──────────┬──────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
         ┌──────────▼──────────┐   ┌──────────▼──────────┐   ┌─────────▼────────┐
         │ PostgreSQL          │   │ Pinecone Vector DB  │   │ OpenAI LLM       │
         │ RLS: WHERE          │   │ namespace=          │   │ Rate Limit:      │
         │ tenant_id='finance' │   │ 'tenant_finance'    │   │ {tenant_id}:rpm  │
         └─────────────────────┘   └─────────────────────┘   └──────────────────┘
                    │                         │                         │
                    └─────────────────────────┼─────────────────────────┘
                                              │
                                   ┌──────────▼──────────┐
                                   │ Audit Log           │
                                   │ tenant_id: finance  │
                                   │ query: "Q4 targets" │
                                   │ result_count: 5     │
                                   └─────────────────────┘
```

**Data Flow:**
1. **Request arrives** with JWT token or API key containing tenant identifier
2. **Middleware extracts** tenant_id, validates tenant is active, checks rate limits
3. **Context propagates** through async call chain using contextvars module
4. **Vector query executes** with namespace=`tenant_{tenant_id}` ensuring isolation
5. **PostgreSQL RLS** automatically filters metadata by tenant_id
6. **LLM call tracked** with per-tenant quota, cost attributed to tenant
7. **Audit log records** complete query trail for compliance and debugging

## Quick Start

### 1. Clone and Setup
```bash
cd gcc_mt_m11_v1
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env and set:
# PINECONE_ENABLED=true
# PINECONE_API_KEY=your_pinecone_api_key
# OPENAI_ENABLED=true
# OPENAI_API_KEY=your_openai_api_key
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
$env:PINECONE_ENABLED='True'; $env:OPENAI_ENABLED='True'; $env:PYTHONPATH=$PWD; uvicorn app:app --reload

# Or use script
./scripts/run_api.ps1
```

### 6. Explore Notebook
```bash
jupyter lab notebooks/L3_M11_Multi_Tenant_Foundations.ipynb
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PINECONE_ENABLED` | No | `false` | Enable Pinecone vector database integration |
| `PINECONE_API_KEY` | If enabled | - | API key for Pinecone service |
| `OPENAI_ENABLED` | No | `false` | Enable OpenAI embeddings and LLM |
| `OPENAI_API_KEY` | If enabled | - | API key for OpenAI service |
| `OFFLINE` | No | `false` | Run in offline mode (notebook testing) |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) |
| `JWT_SECRET` | Yes | - | Secret key for JWT token validation |

## Common Failures & Fixes

| Failure | Cause | Fix |
|---------|-------|-----|
| **Context Propagation Breaks in Background Tasks** | Celery workers don't inherit async context from HTTP request, documents indexed to wrong namespace | Pass tenant_id explicitly to Celery tasks as parameter, call `set_current_tenant()` at start of worker task |
| **Forgetting Namespace in Vector Query** | Developer omits `namespace` parameter in `index.query()`, returns cross-tenant results | Create wrapper function `query_vectors_for_tenant()` that ALWAYS adds namespace, add assertion validating all results match tenant_id |
| **PostgreSQL RLS Policy Disabled During Migration** | DBA disables RLS for bulk updates, forgets to re-enable, 3+ hours of cross-tenant access | Wrap `ALTER TABLE ... DISABLE ROW LEVEL SECURITY` in same transaction as re-enable, add daily cron job checking `pg_class.relrowsecurity` |
| **Cache Poisoning Across Tenants** | Redis cache key doesn't include tenant_id, Finance retrieves Legal's cached embeddings | Include tenant_id as first cache key segment: `{tenant_id}:embedding:{query_hash}`, validate on cache hit |
| **Rate Limiting Shared Across Tenants** | Global rate limiter increments single counter, one tenant exhausts quota blocking all 49 others | Implement per-tenant Redis keys: `rate_limit:{tenant_id}:rpm`, separate sliding window per tenant |

## Decision Card

**When to Use Multi-Tenancy:**
- **30+ tenants** with similar resource requirements (compute, storage, query patterns)
- **Cost savings critical** to business model (₹20 crore+ annual reduction)
- **Non-overlapping compliance requirements** (Finance and Legal can share infrastructure)
- **Infrastructure scaling** needed across 50+ business units in GCC

**When NOT to Use Multi-Tenancy:**
- **<10 tenants** (operational complexity exceeds cost savings, separate systems simpler)
- **Banking/financial services** with customer account data (regulatory prohibition on shared infrastructure)
- **Healthcare** with patient records (HIPAA requires isolated environments)
- **Government/classified data** (physical separation mandatory for Top Secret/classified)
- **Vastly different tenant customization requirements** (custom models, unique pipelines per tenant)

**Hybrid Model (Recommended for GCC):**
- **80% standard-tier tenants** → Shared-DB (cost-efficient at ₹11.6L/tenant/year)
- **20% high-security tenants** → Separate-DB (regulatory compliance at ₹58L/tenant/year)
- **Combined cost:** ₹11.2 crore for 50 tenants (61% savings vs all-dedicated)

**Trade-offs:**

| Factor | Shared-DB | Separate-DB | Hybrid |
|--------|-----------|-------------|--------|
| **Cost** | ₹5.8Cr (50 tenants) | ₹29Cr (50 tenants) | ₹11.2Cr (50 tenants) |
| **Per-Tenant** | ₹11.6L/year | ₹58L/year | ₹22.4L/year avg |
| **Isolation** | Logical (filters) | Physical (dedicated) | Mixed |
| **Latency** | +20ms routing overhead | Baseline | +20ms (shared), baseline (dedicated) |
| **Complexity** | 3× operational overhead | 1× (simple) | 2× (moderate) |
| **Scaling Ceiling** | 50 tenants (connection pool limit) | 1000+ tenants | 200 tenants |
| **Onboarding Time** | 15 minutes (automated) | 2 weeks (manual provisioning) | 1 day (tiered automation) |
| **Noisy Neighbor Risk** | High (shared compute/memory) | None (isolated resources) | Medium (80% shared) |
| **Blast Radius** | All tenants (database outage affects 50) | Single tenant (isolated failure) | Partial (shared tier affected) |

## Troubleshooting

### Service Disabled Mode
The module will run without external service integration if `PINECONE_ENABLED` or `OPENAI_ENABLED` are not set to `true` in `.env`. The `config.py` file will skip client initialization, and API endpoints will return informative skip responses. This is the default behavior and is useful for local development, testing, or learning the architecture without incurring API costs.

### Import Errors
If you see `ModuleNotFoundError: No module named 'src.l3_m11_multi_tenant_foundations'`, ensure:
```bash
$env:PYTHONPATH=$PWD  # Windows PowerShell
export PYTHONPATH=$PWD  # Linux/Mac
```

### Tests Failing
Run tests with verbose output to see detailed failure information:
```bash
pytest -v tests/
```

### Cross-Tenant Leak Detected
If automated tests detect cross-tenant data access:
1. Check all vector queries include `namespace` parameter
2. Verify PostgreSQL RLS policies are enabled: `SELECT relrowsecurity FROM pg_class WHERE relname='documents'`
3. Review cache keys for tenant_id prefix: `{tenant_id}:resource:id`
4. Audit middleware logs for context propagation failures

### Rate Limit Errors
If seeing `429 Rate limit exceeded` errors:
1. Check tenant-specific limits in `tenant_limits` table
2. Verify Redis keys are tenant-aware: `rate_limit:{tenant_id}:rpm`
3. Review tier configuration (premium=1000rpm, standard=100rpm, trial=50rpm)

## Architecture Patterns

### Isolation Model Comparison

| Model | Description | Cost/Tenant | Onboarding | Use Case |
|-------|-------------|-------------|------------|----------|
| **Shared-DB** | One PostgreSQL, one vector DB, logical isolation via filters | ₹11.6L/year | 15 min | 80% of GCC tenants (standard security) |
| **Shared-Schema** | Tenant_id column + RLS policies | ₹13.6L/year | 30 min | Defense-in-depth requirements |
| **Separate-DB** | Dedicated PostgreSQL + vector DB per tenant | ₹58L/year | 2 weeks | Banking, healthcare, classified data |
| **Hybrid** | 80% shared, 20% dedicated | ₹22.4L/year avg | Variable | GCC production recommendation |

### Cost Analysis (50 Tenants)

| Isolation Model | Infrastructure | Operations | Annual Total | Savings vs Separate |
|-----------------|----------------|------------|--------------|---------------------|
| Separate Systems | ₹25Cr | ₹4Cr | ₹29Cr | Baseline |
| Shared-DB | ₹5Cr | ₹80L | ₹5.8Cr | 80% savings |
| Shared-Schema (RLS) | ₹6Cr | ₹80L | ₹6.8Cr | 77% savings |
| Hybrid (80/20) | ₹10Cr | ₹1.2Cr | ₹11.2Cr | 61% savings |

### Tenant Routing Strategies

**1. JWT Claim Extraction (Recommended for Web Users):**
```python
# JWT payload contains tenant_id claim
{
  "user_id": "user@finance.example.com",
  "tenant_id": "finance",
  "exp": 1735689600
}
```

**2. API Key Parsing (Recommended for Service Accounts):**
```python
# API key format: rag_{tenant_id}_{random}
X-API-Key: rag_finance_7a3f2e1c9b4d
```

**3. Subdomain-Based Routing (Alternative):**
```python
# Extract tenant from subdomain
finance.rag.example.com → tenant_id = "finance"
legal.rag.example.com → tenant_id = "legal"
```

## Next Module

**L3 M11.2:** Multi-Tenant Monitoring & Cost Attribution - Implement per-tenant Prometheus metrics, Grafana dashboards, and chargeback reporting for accurate cost recovery in shared infrastructure.

## References

- **Pinecone Namespaces:** https://docs.pinecone.io/guides/indexes/use-namespaces
- **PostgreSQL RLS:** https://www.postgresql.org/docs/current/ddl-rowsecurity.html
- **FastAPI Middleware:** https://fastapi.tiangolo.com/tutorial/middleware/
- **Python Contextvars:** https://docs.python.org/3/library/contextvars.html

## Contributing

This is an educational module from TechVoyageHub L3 track. For production deployment:
1. Replace `JWT_SECRET` with actual secret from vault (not hardcoded)
2. Configure PostgreSQL connection pooling for 50+ tenants
3. Set up external penetration testing (quarterly recommended)
4. Implement tenant-aware monitoring dashboards
5. Configure automated backup with per-tenant restore capability

## License

MIT License - See LICENSE file for details
