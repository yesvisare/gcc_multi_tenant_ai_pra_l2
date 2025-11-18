# L3 M11.3: Database Isolation & Cross-Tenant Security

Build defense-in-depth multi-tenant isolation systems that prevent cross-tenant data leaks at the database, vector store, cache, and storage layers using PostgreSQL RLS, Pinecone namespaces, and separate database strategies.

**Part of:** TechVoyageHub L3 Production RAG Engineering Track
**Prerequisites:**
- Generic CCC M1-M8 (RAG fundamentals, vector databases, PostgreSQL)
- GCC Multi-Tenant M11.1 (Architecture Patterns)
- GCC Multi-Tenant M11.2 (Tenant Registry & Lifecycle)

**Services:** Multi-Service Architecture (PostgreSQL, Pinecone, Redis, AWS S3)

---

## What You'll Build

### The 2:47 AM Cross-Tenant Data Leak Nightmare

Your GCC platform supports 50 tenants (Finance, Legal, HR, Marketing, etc.). At 2:47 AM, the Legal VP messages:

> "Why is Finance seeing our privileged attorney-client documents in their RAG queries? We're testing a $500M merger - this data cannot leak. We need answers NOW."

**What happened:** Finance ran a routine embedding search. The vector database returned 5 documents - ALL from Legal's privileged namespace. Your 'multi-tenant' system leaked cross-tenant data.

**The brutal truth:** Tenant registry alone doesn't prevent data leakage. You need isolation at EVERY data layer.

### Key Capabilities

This module implements defense-in-depth multi-tenant isolation with:

- **PostgreSQL Row-Level Security (RLS)** - 99.9% isolation, ₹5L/month for 50 tenants, cost-efficient for moderate-risk data
- **Namespace-Based Isolation (Pinecone)** - 99.95% isolation, ₹15L/month for 50 tenants, balanced security vs. cost
- **Separate Database Per Tenant** - 99.999% isolation, ₹50L/month for 50 tenants, highest security for critical data
- **Cross-Tenant Leak Testing** - 1,000+ automated adversarial queries to validate isolation before production
- **Defense-in-Depth Patterns** - Multiple isolation layers so single failure doesn't cause breach
- **Tenant Context Management** - Never trust user input for tenant_id (always verify from JWT)
- **Redis Cache Isolation** - Tenant-scoped key prefixing (pattern: `tenant:{uuid}:{key}`)
- **S3 Prefix Isolation** - Document storage with IAM-enforced prefix patterns
- **Audit Logging** - Track every data access with tenant context for incident investigation
- **Incident Response Playbook** - Handle isolation breaches with proper procedures
- **Cost vs. Security Trade-offs** - Decision framework for choosing isolation strategy
- **Real Production Failures** - CVE-2022-1552, namespace typos, performance degradation lessons

### Success Criteria

After completing this module, you will:

- ✅ Implement PostgreSQL RLS policies that enforce tenant_id filtering on every query, preventing cross-tenant reads even from admin users
- ✅ Build namespace-based isolation in vector databases with validation logic that rejects cross-tenant queries before they reach the store
- ✅ Design automated cross-tenant leak testing with 1,000+ adversarial queries trying to break isolation
- ✅ Choose the right isolation strategy based on cost, security requirements, scale, and team expertise
- ✅ Implement defense-in-depth where multiple layers protect against leaks even if one layer fails
- ✅ Create audit trails that capture every data access with tenant context for incident response
- ✅ Respond to isolation incidents with proper investigation, containment, and notification procedures
- ✅ Recognize when NOT to use multi-tenancy (1-5 tenants, extreme customization, physical separation requirements)

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                    Multi-Tenant Isolation                        │
│                      (Defense-in-Depth)                          │
└─────────────────────────────────────────────────────────────────┘

Layer 1: Application (Tenant Context)
┌────────────────────────────────────────────────────────────────┐
│  JWT Token → Extract tenant_id (NEVER trust user input)        │
│  Validate tenant in registry → Set tenant context              │
│  Audit log all access attempts                                 │
└────────────────────────────────────────────────────────────────┘
                            ↓
Layer 2: Database Isolation (Choose Strategy)
┌────────────────────────────────────────────────────────────────┐
│ Strategy 1: PostgreSQL RLS (99.9% - ₹5L/month)                 │
│   SET LOCAL app.tenant_id = '{uuid}'                           │
│   RLS policy: WHERE tenant_id = current_setting('app.tenant_id')│
│                                                                 │
│ Strategy 2: Pinecone Namespace (99.95% - ₹15L/month)           │
│   namespace = f'tenant-{uuid}' (validated)                     │
│   index.query(vector, namespace=namespace)                     │
│                                                                 │
│ Strategy 3: Separate DB (99.999% - ₹50L/month)                 │
│   Each tenant: separate PostgreSQL instance                    │
│   Physical isolation, no shared resources                      │
└────────────────────────────────────────────────────────────────┘
                            ↓
Layer 3: Cache & Storage Isolation
┌────────────────────────────────────────────────────────────────┐
│  Redis: tenant:{uuid}:{key} (key prefixing)                    │
│  S3: tenants/{uuid}/{doc_id}/filename (prefix + IAM policy)    │
└────────────────────────────────────────────────────────────────┘
                            ↓
Layer 4: Monitoring & Testing
┌────────────────────────────────────────────────────────────────┐
│  Daily: 1,000+ adversarial queries test isolation              │
│  Alert: Cross-tenant access attempts detected                  │
│  Audit: Every access logged with tenant context                │
└────────────────────────────────────────────────────────────────┘

Result: If one layer fails, others still protect (no single point of failure)
```

---

## Quick Start

### 1. Clone and Setup

```bash
git clone <repo_url>
cd gcc_mt_m11_v3
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env to enable services (optional - works offline by default)
```

**Service Configuration Options:**

- **OFFLINE mode (default):** All services disabled, code demonstrations only
- **PostgreSQL:** Set `POSTGRES_ENABLED=true` + database credentials (Strategy 1: RLS)
- **Pinecone:** Set `PINECONE_ENABLED=true` + API key (Strategy 2: Namespace)
- **Redis:** Set `REDIS_ENABLED=true` + host/port (Cache isolation)
- **AWS S3:** Set `AWS_ENABLED=true` + credentials (S3 prefix isolation)

### 4. Run Tests

```bash
# Windows PowerShell
$env:PYTHONPATH=$PWD; pytest -q

# Or use script
./scripts/run_tests.ps1
```

**Expected output:** All tests pass in offline mode (no external services required).

### 5. Start API

```bash
# Windows PowerShell
$env:PYTHONPATH=$PWD; uvicorn app:app --reload

# Or use script
./scripts/run_api.ps1
```

**API Endpoints:**
- Health check: http://localhost:8000
- API docs: http://localhost:8000/docs
- Query with RLS: POST /query/rls
- Query with namespace: POST /query/namespace
- Security tests: POST /security/test
- Audit logs: GET /audit/logs

### 6. Explore Notebook

```bash
jupyter lab notebooks/L3_M11_Multi_Tenant_Foundations.ipynb
```

**Notebook sections:**
1. Learning Arc & Environment Setup
2. The Cross-Tenant Data Leak Nightmare
3. Tenant Context Management (Defense Layer 0)
4. Strategy 1: PostgreSQL RLS
5. Strategy 2: Pinecone Namespace Isolation
6. Strategy 3: Separate Database Per Tenant
7. Defense-in-Depth (Multiple Layers)
8. Cross-Tenant Security Testing
9. Audit Logging & Incident Response
10. Redis Cache & S3 Prefix Isolation
11. Decision Card - Choosing the Right Strategy
12. Common Failures & Fixes
13. Summary & Next Steps

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `POSTGRES_ENABLED` | No | `false` | Enable PostgreSQL RLS strategy |
| `POSTGRES_HOST` | If enabled | `localhost` | PostgreSQL server host |
| `POSTGRES_PORT` | If enabled | `5432` | PostgreSQL server port |
| `POSTGRES_DB` | If enabled | `multi_tenant_rag` | Database name |
| `POSTGRES_USER` | If enabled | `postgres` | Database user |
| `POSTGRES_PASSWORD` | If enabled | - | Database password |
| `PINECONE_ENABLED` | No | `false` | Enable Pinecone namespace strategy |
| `PINECONE_API_KEY` | If enabled | - | Pinecone API key |
| `PINECONE_ENVIRONMENT` | If enabled | - | Pinecone environment |
| `PINECONE_INDEX` | If enabled | `multi-tenant-rag` | Pinecone index name |
| `REDIS_ENABLED` | No | `false` | Enable Redis cache isolation |
| `REDIS_HOST` | If enabled | `localhost` | Redis server host |
| `REDIS_PORT` | If enabled | `6379` | Redis server port |
| `AWS_ENABLED` | No | `false` | Enable AWS S3 prefix isolation |
| `AWS_ACCESS_KEY_ID` | If enabled | - | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | If enabled | - | AWS secret key |
| `AWS_REGION` | If enabled | `us-east-1` | AWS region |
| `AWS_S3_BUCKET` | If enabled | `multi-tenant-docs` | S3 bucket name |
| `OFFLINE` | No | `true` | Run in offline mode (skip all external calls) |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |

---

## Common Failures & Fixes

### Failure 1: CVE-2022-1552 (PostgreSQL RLS Bypass)

| Aspect | Details |
|--------|---------|
| **The Bug** | PostgreSQL 14.3 had RLS policy bypass vulnerability where attackers could manipulate session variables through `current_setting()` |
| **Cause** | RLS policies using `current_setting()` could be bypassed if application allowed user to set arbitrary session variables |
| **Impact** | Tenants could potentially see each other's data. Compliance incident. |
| **Fix** | 1. Upgrade to PostgreSQL 14.4+ (security patch)<br>2. Never allow user input to set session variables<br>3. Run penetration testing to catch bypasses |
| **Lesson** | Even battle-tested database features have bugs. That 0.1% isolation gap is why you need defense-in-depth. |

### Failure 2: Namespace Typo Causing Silent Failures (2024 GCC Incident)

| Aspect | Details |
|--------|---------|
| **The Bug** | Developer deployed code with trailing dash: `namespace = f'tenant-{tenant_id}-'` (should be `f'tenant-{tenant_id}'`) |
| **Cause** | String manipulation error in namespace construction. No validation before query. |
| **Impact** | All queries returned 0 results (namespace doesn't exist). 2-hour outage. ₹5L revenue loss (SLA credits). |
| **Fix** | 1. Add namespace validation before every query<br>2. Verify namespace exists in vector store stats<br>3. Add integration tests for namespace format |
| **Lesson** | String manipulation is error-prone. Always validate before using. |

### Failure 3: Performance Degradation with 100+ Tenants

| Aspect | Details |
|--------|---------|
| **Symptom** | Query latency increased:<br>- 10 tenants: 50ms<br>- 50 tenants: 150ms<br>- 100 tenants: 400ms |
| **Cause** | Index size growth (tenant_id index on 100M rows), connection pool contention, cache thrashing (each tenant's working set competes) |
| **Impact** | User-facing slowness. SLA violations. |
| **Fix** | Shard by tenant groups:<br>- DB1: Tenants 1-25<br>- DB2: Tenants 26-50<br>- DB3: Tenants 51-75<br>Now each DB has 25 tenants. Latency back to 80ms. |
| **Lesson** | 'Shared everything' sounds great until scale hits. Plan for sharding at > 50 tenants. |

### Failure 4: Admin User Accidentally Bypassed Isolation

| Aspect | Details |
|--------|---------|
| **Scenario** | DBA with `BYPASSRLS` privilege forgot to set tenant context while debugging Finance issue |
| **Cause** | Admin exception in RLS policy: `OR current_user = 'admin'` |
| **Impact** | Query returned ALL tenants' contracts. DBA accidentally saw Legal's privileged documents. Compliance violation. |
| **Fix** | 1. Remove `BYPASSRLS` from all users (even DBAs)<br>2. Create audited admin views that log every access<br>3. Require incident ticket for admin access |
| **Lesson** | Admin privileges are dangerous. Require justification + audit every use. |

### Failure 5: Forgot to Set Tenant Context

| Aspect | Details |
|--------|---------|
| **Code** | `results = db.query("SELECT * FROM documents WHERE title LIKE '%contract%'")` (no `set_tenant_context()` called) |
| **Cause** | Developer assumed ORM would set tenant context automatically. It didn't. |
| **Impact** | RLS policy falls back to default UUID. Query returns 0 results. User complains: "System shows no documents." |
| **Fix** | Use decorator to enforce tenant context:<br>`@require_tenant_context`<br>`def query_documents(tenant_id, pattern): ...` |
| **Lesson** | Make tenant context mandatory. Add integration test: "Query without tenant context → must fail." |

### Failure 6: Namespace Constructed from User Input

| Aspect | Details |
|--------|---------|
| **Code** | `user_provided_tenant = request.get('tenant_id')  # From URL param!`<br>`namespace = f'tenant-{user_provided_tenant}'` |
| **Cause** | Trusted user input for tenant_id. Classic security mistake. |
| **Impact** | Attacker changes URL: `?tenant_id=legal` and sees Legal's documents. Cross-tenant breach. |
| **Fix** | 1. Get tenant_id from verified JWT (not user input)<br>2. Validate tenant exists in registry<br>3. Never trust URL parameters for security decisions |
| **Lesson** | ALWAYS extract tenant_id from JWT, NEVER from user input. |

### Failure 7: Single Encryption Key for All Tenants

| Aspect | Details |
|--------|---------|
| **Code** | `KEY = os.environ['ENCRYPTION_KEY']`<br>`encrypted_doc = encrypt(document, KEY)` |
| **Cause** | Cost-saving (single KMS key cheaper than 50 keys). |
| **Impact** | Key compromised → ALL tenants' data decryptable. Complete breach. |
| **Fix** | Use tenant-specific encryption keys:<br>`tenant_key = get_tenant_encryption_key(tenant_id)  # AWS Secrets Manager`<br>`encrypted_doc = encrypt(document, tenant_key)` |
| **Lesson** | Blast radius matters. Tenant-specific keys contain breach. Cost: ₹200/month per tenant (worth it). |

### Failure 8: Connection Pool Not Tenant-Scoped

| Aspect | Details |
|--------|---------|
| **Issue** | Single global connection pool shared across all tenants. One tenant's slow query blocks others. |
| **Cause** | Assumed shared pool would be efficient. Didn't account for "noisy neighbor" problem. |
| **Impact** | Finance runs expensive report query (2 min execution). Legal's queries timeout waiting for connection. |
| **Fix** | Tenant-scoped connection pools:<br>- High-priority tenants: Dedicated pool (10 connections)<br>- Standard tenants: Shared pool with limits (2 connections per tenant) |
| **Lesson** | Fair resource allocation requires isolation at ALL layers, including connection pools. |

---

## Decision Card

### When to Use Each Strategy

**Use PostgreSQL RLS (99.9% isolation, ₹5L/month) when:**

- ✅ Cost of data leak < ₹1Cr (low-sensitivity data like marketing content, internal knowledge base)
- ✅ Small to medium scale (< 50 tenants)
- ✅ Cost efficiency is priority
- ✅ Team has senior PostgreSQL DBAs who can write correct policies
- ✅ No regulatory requirement for physical separation
- ✅ Acceptable to have 0.1% risk from policy bugs
- ✅ Can quickly patch PostgreSQL security updates

**Use Pinecone Namespace Isolation (99.95% isolation, ₹15L/month) when:**

- ✅ Cost of data leak ₹1-10Cr (general enterprise data)
- ✅ Medium to large scale (10-100 tenants)
- ✅ Balance cost vs. security is goal
- ✅ Standard GCC RAG system (most common use case)
- ✅ Team is mid-level engineers, strong on APIs
- ✅ Compliance allows logical separation (GDPR, SOX acceptable)
- ✅ Can implement namespace validation logic
- ✅ Need better isolation than RLS without separate DB cost

**Use Separate Database Per Tenant (99.999% isolation, ₹50L/month) when:**

- ✅ Cost of data leak > ₹10Cr (legal, healthcare, financial trading)
- ✅ Small number of high-value tenants (< 10)
- ✅ Regulatory requirement for physical separation (HIPAA, PCI-DSS Level 1, defense contracts)
- ✅ Customer explicitly demands separate infrastructure
- ✅ Junior team or small team (least risk of misconfiguration)
- ✅ Noisy neighbor problem requires complete isolation
- ✅ Can afford 4× cost increase vs. namespace isolation
- ✅ Have Terraform/IaC expertise for provisioning

**Use Hybrid Approach (tiered isolation) when:**

- ✅ > 100 tenants with varying risk levels
- ✅ 5-10 high-risk tenants (Finance, Legal) + 90+ standard tenants
- ✅ Need to optimize cost while maintaining highest security for critical data
- ✅ 63% cost savings vs. all separate DBs (₹18.5L vs. ₹50L/month)

### When NOT to Use Multi-Tenancy

**Avoid multi-tenancy when:**

- ❌ Only 1-5 tenants (overhead not justified, use single-tenant deployments)
- ❌ Highly customized per tenant (> 40% engineering time managing tenant-specific code)
- ❌ Extreme security requirements where customer demands air-gapped network
- ❌ Customer already rejected shared infrastructure concept
- ❌ Tenant requirements change frequently (each change risks affecting other tenants)
- ❌ Physical separation is non-negotiable requirement

**Real Example:** Defense contractor GCC with Ministry of Defense customer requiring air-gapped on-premise deployment. Trying to fit this into multi-tenant SaaS was absurd. Give them dedicated single-tenant environment.

### Trade-offs

**PostgreSQL RLS:**
- **Cost:** ₹5L/month for 50 tenants (lowest)
- **Latency:** 50-150ms (single shared database)
- **Complexity:** High (RLS policies, session management, CVE risks)
- **Isolation:** 99.9% (policy bugs possible)
- **Onboarding:** Fast (add row, enable RLS)

**Pinecone Namespace:**
- **Cost:** ₹15L/month for 50 tenants (medium)
- **Latency:** 80-120ms (logical partitioning)
- **Complexity:** Medium (namespace validation, typo risks)
- **Isolation:** 99.95% (namespace enforced by vector store)
- **Onboarding:** Fast (create namespace, validate)

**Separate Database:**
- **Cost:** ₹50L/month for 50 tenants (highest)
- **Latency:** 50-80ms per tenant (dedicated resources)
- **Complexity:** High (50 databases to manage, Terraform required)
- **Isolation:** 99.999% (only hardware failure)
- **Onboarding:** Slow (10-15 min to provision via IaC)

### Example Deployments

**Small GCC (10 business units, 500 users, 5M docs):**
- Strategy: RLS
- Monthly: ₹8L ($98K USD)
- Per tenant: ₹80K/month
- Isolation: 99.9% (acceptable for low-risk)

**Medium GCC (50 business units, 5K users, 50M docs):**
- Strategy: Namespace Isolation
- Monthly: ₹18L ($220K USD)
- Per tenant: ₹36K/month
- Isolation: 99.95% (standard for enterprise)

**Large GCC (100 business units, 20K users, 200M docs):**
- Strategy: Hybrid (5 separate DB, 95 namespace)
- Monthly: ₹35L ($430K USD)
- Per tenant: ₹35K/month (economies of scale)
- Isolation: 99.999% for high-risk, 99.95% for standard

### When to Upgrade

**From RLS to Namespace Isolation:**
- Security incident detected in testing (leak in adversarial queries)
- Compliance requirement changed (auditor demands stronger isolation)
- Performance degradation at > 50 tenants (150ms → 400ms latency)
- Cost: ₹10L one-time migration

**From Namespace to Separate Database:**
- High-value tenant (e.g., Finance) demands physical separation
- Regulatory requirement (HIPAA, PCI-DSS compliance audit)
- Noisy neighbor problem (can't throttle effectively in shared namespace)
- Cost: ₹5L one-time migration per tenant

**Key Insight:** Start with namespace isolation for most GCCs. Upgrade specific high-risk tenants to separate DB as needed. Don't over-engineer from day 1.

---

## Troubleshooting

### Service Disabled Mode

The module runs without external service integration by default (`OFFLINE=true`). All managers will skip client initialization and return informative responses:

- PostgreSQL RLS manager returns empty results
- Pinecone namespace manager returns `{"skipped": True}`
- Redis cache operations return `False` / `None`
- S3 operations return `{"skipped": True}`

This is the default behavior and is useful for:
- Local development without service dependencies
- Testing isolation logic without external APIs
- Understanding concepts before connecting real services

**To enable services:** Set `{SERVICE}_ENABLED=true` in `.env` and provide credentials.

### Import Errors

If you see `ModuleNotFoundError: No module named 'src.l3_m11_multi_tenant_foundations'`:

```bash
# Windows PowerShell
$env:PYTHONPATH=$PWD

# Linux/Mac
export PYTHONPATH=$PWD
```

The `src/` directory must be in Python path for imports to work.

### Tests Failing

Run tests with verbose output to see detailed error messages:

```bash
pytest -v tests/
```

**Common issues:**
- Missing PYTHONPATH (see above)
- Service enabled but credentials missing (set to offline mode in tests)
- Python version mismatch (requires Python 3.9+)

### API Not Starting

Check that all dependencies are installed:

```bash
pip install -r requirements.txt
```

Verify FastAPI and Uvicorn versions:

```bash
pip show fastapi uvicorn
```

### Notebook Kernel Issues

If Jupyter notebook can't find modules:

1. Install ipykernel in your environment:
   ```bash
   pip install ipykernel
   ```

2. Register the kernel:
   ```bash
   python -m ipykernel install --user --name=l3_m11
   ```

3. Select the kernel in Jupyter: Kernel → Change Kernel → l3_m11

---

## Next Module

**M11.4: Rate Limiting & Resource Quotas**

Now you have:
- ✅ Tenant identities (M11.2 Tenant Registry)
- ✅ Data isolation (M11.3 Database Security)

Next challenge: **Fair resource usage**
- What if one tenant runs 10,000 queries/sec?
- How do you prevent "noisy neighbor" problem?
- How do you enforce per-tenant quotas (CPU, memory, API calls)?

In M11.4, you'll implement:
- Token bucket rate limiting (per-tenant)
- Resource quotas (CPU, memory, storage)
- Throttling and backpressure
- Fair queueing across tenants

**Continue to M11.4 to complete your multi-tenant foundation!**

---

## Resources

### Official Documentation
- [PostgreSQL Row-Level Security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [Pinecone Namespaces](https://docs.pinecone.io/docs/namespaces)
- [AWS S3 IAM Policies](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-policy-language-overview.html)
- [Redis Key Patterns](https://redis.io/docs/manual/patterns/)

### Security Resources
- [CVE-2022-1552 (PostgreSQL RLS Bypass)](https://nvd.nist.gov/vuln/detail/CVE-2022-1552)
- [OWASP Multi-Tenancy Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Multitenant_Security_Cheat_Sheet.html)

### TechVoyageHub Modules
- [M11.1: Multi-Tenant Architecture Patterns](../m11_1_architecture)
- [M11.2: Tenant Registry & Lifecycle](../m11_2_tenant_registry)
- [M11.4: Rate Limiting & Resource Quotas](../m11_4_rate_limiting)

---

## License

MIT License - See LICENSE file for details.

Copyright (c) 2025 TechVoyageHub

---

## Version History

**v1.0.0 (2025-01-18):**
- Initial release with three isolation strategies
- Multi-service architecture (PostgreSQL, Pinecone, Redis, AWS S3)
- Complete cross-tenant security testing framework
- Audit logging and incident response playbook
- Decision card with cost vs. security trade-offs
- 8 real production failures documented with fixes
