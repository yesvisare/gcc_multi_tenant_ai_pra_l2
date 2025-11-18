# L3 M12.1: Vector Database Multi-Tenancy Patterns

Production-ready implementation of namespace-based isolation, metadata filtering enforcement, and tenant-scoped vector stores for multi-tenant vector databases.

**Part of:** TechVoyageHub L3 Production RAG Engineering Track
**Prerequisites:** L3 M11 (Vector Database Fundamentals), understanding of multi-tenancy concepts
**SERVICE:** PINECONE (auto-detected from script)

## What You'll Build

This module implements three isolation models for multi-tenant vector databases, addressing the critical challenge of preventing data leakage between competing tenants (e.g., investment banks, law firms) while optimizing infrastructure costs. You'll build production-grade tenant isolation with defense-in-depth security layers.

**Key Capabilities:**
- **Namespace-based isolation** - Architectural guarantee preventing cross-tenant access (9/10 security strength)
- **Metadata filtering with defense-in-depth** - Multi-layer validation preventing filter bypass attacks (7/10 security strength)
- **Dedicated index routing** - Complete physical isolation for regulatory compliance (10/10 security strength)
- **Cross-tenant attack detection** - Real-time monitoring and security alerts for malicious query attempts
- **Cost-optimized isolation strategies** - Decision framework balancing security vs. infrastructure costs (10x variation)
- **Audit logging and compliance** - Comprehensive forensic trail for incident response

**Success Criteria:**
- Zero cross-tenant data leaks in 5,000+ penetration test attempts
- Sub-60-second tenant provisioning with namespace-based isolation
- Comprehensive audit logging for all vector queries
- Cost-awareness in isolation model selection (₹5-40L/month per 50 tenants)
- Detection and blocking of filter bypass attacks in real-time

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                  USER REQUEST (with JWT)                        │
│  Contains: tenant_id, user_id, roles (immutable from JWT)      │
└────────────┬────────────────────────────────────────────────────┘
             │
             â"" Extract Tenant Context
             │
┌────────────â"´────────────────────────────────────────────────────┐
│             ISOLATION MODEL ROUTER                              │
│  Decision: Metadata Filtering | Namespace-Based | Dedicated    │
└────┬────────────────┬────────────────────┬─────────────────────┘
     │                │                    │
     â"‚ Model 1        â"‚ Model 2            â"‚ Model 3
     â""â"€â"€â"€â"€â"€â"€â"€â"€â"      â""â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"      â""â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"
     │                │                    │
┌────â"´──────────┐ ┌───â"´──────────────┐ ┌──â"´─────────────────┐
│ METADATA      │ │ NAMESPACE ROUTER │ │ DEDICATED INDEX    │
│ FILTER        │ │                  │ │ ROUTER             │
│ - Inject      │ │ - Map tenant_id  │ │ - Map tenant_id    │
│   tenant_id   │ │   to namespace   │ │   to index_name    │
│ - Validate    │ │ - Query with     │ │ - Query separate   │
│   user filter │ │   namespace      │ │   index            │
│ - Post-query  │ │   parameter      │ │                    │
│   validation  │ │ - Architecturally│ │ - Complete         │
│               │ │   isolated       │ │   isolation        │
│ Cost: ₹5-8L   │ │ Cost: ₹8-12L     │ │ Cost: ₹30-40L      │
│ Security: 7/10│ │ Security: 9/10   │ │ Security: 10/10    │
└───────┬───────┘ └────────┬─────────┘ └──────┬─────────────┘
        │                  │                  │
        â""â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"¼â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"˜
                           │
        ┌──────────────────â"´──────────────────┐
        │   PINECONE VECTOR DATABASE          │
        │  - Stores embeddings                │
        │  - Metadata: tenant_id, category... │
        │  - Namespaces: tenant_001, tenant_002│
        └──────────────┬──────────────────────┘
                       │
        ┌──────────────â"´──────────────────────┐
        │   DEFENSE-IN-DEPTH LAYERS           │
        │  1. Middleware filter injection     │
        │  2. AST parser validation           │
        │  3. Post-query result validation    │
        │  4. Audit logging (all queries)     │
        │  5. Security alerts (violations)    │
        └─────────────────────────────────────┘
                       │
                       â""â"€â"€â"€â"€> AUDIT LOG & FORENSICS
```

## Quick Start

### 1. Clone and Setup
```bash
git clone <repo_url>
cd gcc_multi_tenant_ai_pra_l2
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env and set:
#   PINECONE_ENABLED=true
#   PINECONE_API_KEY=your_api_key_here
#   PINECONE_ENVIRONMENT=us-west1-gcp
```

### 4. Run Tests
```bash
# Windows PowerShell
$env:PYTHONPATH=$PWD; pytest -q tests/

# Or use script
./scripts/run_tests.ps1

# Expected output: 30+ tests passing
```

### 5. Start API
```bash
# Windows PowerShell
$env:PINECONE_ENABLED='True'; $env:PYTHONPATH=$PWD; uvicorn app:app --reload

# Or use script
./scripts/run_api.ps1

# API available at: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### 6. Explore Notebook
```bash
jupyter lab notebooks/L3_M12_Data_Isolation_Security.ipynb
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PINECONE_ENABLED` | No | `false` | Enable Pinecone vector database integration |
| `PINECONE_API_KEY` | If enabled | - | API key for Pinecone service |
| `PINECONE_ENVIRONMENT` | No | `us-west1-gcp` | Pinecone environment region |
| `OFFLINE` | No | `false` | Run in offline mode (notebook/testing) |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) |

## Common Failures & Fixes

| Failure | Cause | Fix |
|---------|-------|-----|
| **Middleware bypass via direct vector DB access** | Missing network isolation, direct client access to Pinecone | Implement API-only access with firewall rules blocking direct connections |
| **Filter logic bug in complex AND/OR queries** | Incomplete AST parser failing to detect nested cross-tenant filters | Add comprehensive penetration test suite (5,000+ malicious query attempts) |
| **Metadata corruption during ingestion** | Race condition in multi-threaded writes assigning wrong tenant_id | Implement atomic metadata updates with transaction isolation |
| **API version mismatch - old clients lack filtering** | Legacy clients bypass filter injection middleware | Enforce API versioning, deprecate unfiltered endpoints |
| **Cross-tenant leakage via OR filter** | Malicious query: `{"$or": [{"tenant_id": "A"}, {"tenant_id": "B"}]}` | AST parser extracts all tenant_id values, blocks if multiple found |
| **Namespace limit exceeded (>1,000 namespaces)** | Platform constraint: Pinecone supports ~1,000 namespaces per index | Migrate to multi-index architecture or dedicated indexes tier |
| **Semantic clustering attack** | Attacker infers other tenants' data from vector clustering patterns | Namespace isolation prevents visibility into other tenants' vector space |
| **Query-time latency spike (5-10ms)** | Metadata filtering adds overhead vs namespace-based | Acceptable trade-off for cost savings; optimize with cached filters |

## Decision Card

### When to Use Metadata Filtering

âœ… **Use when:**
- Cost is primary concern (₹5-8L/month vs ₹30-40L for dedicated)
- Tenants have similar security requirements (non-competing)
- Robust penetration testing framework exists (5,000+ automated tests)
- Query-time latency of 5-10ms is acceptable
- Rapid iteration and deployment needed (immediate provisioning)

❌ **NOT for:**
- Regulatory physical isolation mandates (SOX, HIPAA requiring dedicated infrastructure)
- Competing tenants with insider trading risk (investment banks, law firms)
- High-value data where filter bug cost exceeds infrastructure savings

**Trade-offs:**
- Cost: 10x cheaper than dedicated indexes (₹5-8L vs ₹30-40L/month for 50 tenants)
- Latency: 5-10ms query overhead from filter injection
- Complexity: Requires comprehensive penetration testing suite
- Risk: Filter bug affects ALL tenants simultaneously (blast radius = 100%)

### When to Use Namespace-Based Isolation

âœ… **Use when:**
- Balanced cost/security trade-off needed (most GCC scenarios)
- Moderate isolation required without full dedicated infrastructure
- 50-1,000 tenant scale (platform limit: ~1,000 namespaces per index)
- Fast onboarding critical (provisioning time: <60 seconds)
- Good isolation strength acceptable (9/10 vs 10/10 for dedicated)

❌ **NOT for:**
- Competing tenants with insider trading risk (still shared infrastructure)
- >1,000 tenants (namespace limit exceeded)
- Absolute maximum security required (use dedicated indexes)

**Trade-offs:**
- Cost: 5x cheaper than dedicated (₹8-12L vs ₹30-40L/month for 50 tenants)
- Latency: Minimal overhead (<1ms vs metadata filtering)
- Complexity: Simple architecture with namespace parameter
- Scale: Limited to ~1,000 namespaces per index

### When to Use Dedicated Indexes

âœ… **Use when:**
- Maximum security required (10/10 isolation strength)
- Competing tenants (investment banks, law firms, pharma companies)
- Regulatory mandate (SOX, HIPAA, SEBI requiring physical isolation)
- Budget allows 10x infrastructure cost (₹30-40L vs ₹5-8L/month)
- Zero blast radius critical (failure affects single tenant only)

❌ **NOT for:**
- Cost constraints or tight budgets
- Rapid tenant growth (provisioning takes hours to days)
- Non-competing tenants (over-engineering)

**Trade-offs:**
- Cost: 10x more expensive than metadata filtering
- Latency: No query overhead (direct index access)
- Complexity: Requires index management per tenant
- Security: Maximum isolation (10/10), complete physical separation

## Architecture Deep Dive

### Three Isolation Models Compared

| Aspect | Metadata Filtering | Namespace-Based | Dedicated Indexes |
|--------|-------------------|-----------------|-------------------|
| **Cost (50 tenants)** | ₹5-8L/month | ₹8-12L/month | ₹30-40L/month |
| **Isolation Strength** | 7/10 | 9/10 | 10/10 |
| **Provisioning Time** | Immediate | <60 seconds | Hours to days |
| **Scale Limit** | Unlimited | ~1,000 namespaces | Unlimited |
| **Query Latency** | +5-10ms | <1ms overhead | Zero overhead |
| **Blast Radius** | All tenants | Single namespace | Single tenant |
| **Best For** | Cost-sensitive | Most GCC scenarios | Regulatory/competing |

### Defense-in-Depth Security Layers

**Layer 1: Middleware Filter Injection**
- Automatically injects `{"tenant_id": "<authenticated_tenant>"}` into ALL queries
- Immutable tenant context from JWT (not user input)
- Prevents accidental cross-tenant queries

**Layer 2: AST Parser Validation**
- Recursively parses filter dictionary to extract ALL tenant_id references
- Blocks queries with multiple tenant_id values (OR filter attack)
- Rejects queries missing tenant_id entirely

**Layer 3: Post-Query Result Validation**
- Scans returned results to verify tenant_id matches authenticated user
- Catches filter bugs that passed AST validation
- Triggers security alerts on violations

**Layer 4: Comprehensive Audit Logging**
- Logs every vector query with tenant_id, user_id, filter, timestamp
- Enables forensic reconstruction after security incidents
- Compliance requirement for financial services (SOX, SEBI)

**Layer 5: Real-Time Security Alerts**
- Monitors for cross-tenant query attempts
- Triggers incident response protocol (circuit breaker shuts down API)
- Integrates with SIEM (Splunk, ELK) for enterprise monitoring

## API Endpoints

### POST `/query/namespace`
Query vector database using **namespace-based isolation** (Model 2).

**Request:**
```json
{
  "query_vector": [0.1, 0.2, 0.3, ...],
  "top_k": 10
}
```

**Headers:**
- `X-Tenant-ID`: Authenticated tenant ID from JWT
- `X-User-ID`: User ID from JWT

**Response:**
```json
{
  "result": {
    "status": "success",
    "namespace": "tenant_morgan_stanley",
    "isolation_model": "namespace_based",
    "results": [...],
    "audit": {...}
  }
}
```

### POST `/query/metadata-filter`
Query vector database using **metadata filtering** (Model 1) with defense-in-depth.

**Request:**
```json
{
  "query_vector": [0.1, 0.2, 0.3, ...],
  "top_k": 10,
  "filter": {
    "category": "finance",
    "status": "active"
  }
}
```

**Response:**
```json
{
  "result": {
    "status": "success",
    "isolation_model": "metadata_filtering",
    "filter_applied": {
      "$and": [
        {"tenant_id": "morgan_stanley"},
        {"category": "finance", "status": "active"}
      ]
    },
    "results": [...],
    "audit": {...}
  }
}
```

### POST `/tenant/create`
Create new tenant namespace.

**Request:**
```json
{
  "tenant_id": "goldman_sachs"
}
```

**Response:**
```json
{
  "result": {
    "status": "created",
    "namespace": "tenant_goldman_sachs",
    "provisioning_time": "<60 seconds",
    "isolation_strength": "9/10"
  }
}
```

### POST `/evaluate`
Evaluate which isolation model to use based on requirements.

**Request:**
```json
{
  "num_tenants": 100,
  "security_requirement": "high",
  "budget_constraint": "moderate"
}
```

**Response:**
```json
{
  "recommendation": {
    "recommended_model": "namespace_based",
    "cost_range": "₹8-12L/month",
    "isolation_strength": "9/10",
    "provisioning_time": "<60 seconds",
    "trade_offs": {...}
  }
}
```

### GET `/costs/{num_tenants}`
Calculate costs for each isolation model.

**Example:** `/costs/50`

**Response:**
```json
{
  "num_tenants": 50,
  "cost_breakdown": {
    "metadata_filtering": {
      "annual_cost": "₹50.0L",
      "monthly_cost": "₹4.2L",
      "savings_vs_dedicated": "10x cost reduction"
    },
    "namespace_based": {
      "annual_cost": "₹80.0L",
      "monthly_cost": "₹6.7L"
    },
    "dedicated_indexes": {
      "annual_cost": "₹400.0L",
      "monthly_cost": "₹33.3L"
    }
  }
}
```

## Real-World GCC Scenario: Financial Services

**Threat Model:** 30 competing investment banking tenants
- Morgan Stanley: M&A target analysis
- Goldman Sachs: Equity research valuations
- JP Morgan: Wealth management portfolios

**Insider Trading Exposure if Leak Occurs:**
- Criminal charges (not just civil penalties)
- ₹10-50Cr annual contract termination
- SEC/SEBI regulatory shutdown possible
- Named personal liability for architects

**Required Isolation Model:** Dedicated Indexes (10/10 security)

**Cost Impact:**
- Infrastructure: ₹60-80L/month (30 tenants)
- vs. Metadata Filtering: ₹3-5L/month (12x cost increase)
- Justification: One leak costs ₹10-100Cr â†' infrastructure premium pays for itself

## Incident Response Protocol

### Hour 0 (Immediate)
1. **Circuit breaker** shuts down vector query API
2. Notify security team, compliance, affected tenants
3. Preserve audit logs for forensic investigation
4. Activate incident response team

### Hour 1-24
1. **Forensic analysis:** Which queries? How many records leaked?
2. Compliance notification to auditors
3. Legal consultation on breach notification requirements
4. Quantify impact: Number of tenants, sensitivity of data

### Week 1-4
1. **Implement architectural fix** (e.g., migrate to dedicated indexes)
2. Red team testing (5,000+ penetration attempts)
3. Production re-deployment with enhanced monitoring
4. Post-mortem and process improvements

### Cost of Data Leak
- Technical fix: ₹20-50L
- Compliance penalties: ₹50L-5Cr
- Client contract loss: ₹10-100Cr (annual recurring revenue)
- Reputation damage: Immeasurable

## Hybrid Production Model (Common Practice)

**Tiered Tenant Service:**
- **Standard tier:** ₹50K/month per tenant (shared namespace, moderate security)
- **Premium tier:** ₹5L/month per tenant (dedicated index, high security)
- **Enterprise tier:** ₹20L/month per tenant (dedicated index + private deployment)

**Typical GCC Mix:**
- 80% of tenants: Shared namespaces (cost-optimized)
- 20% of tenants: Dedicated indexes (high security)
- Total cost: 40-60% savings vs. all-dedicated approach

## Testing & Validation Strategy

**Penetration Test Suite:**
- 5,000 attempted cross-tenant queries (automated)
- 100% isolation verification required
- Test every tenant pair combination
- Filter bypass attempts with OR/AND operators
- Malicious metadata injection attempts
- Namespace boundary probing

**Test Coverage:**
- Unit tests: 30+ tests covering all functions
- Integration tests: Full workflow testing
- Security tests: Cross-tenant attack scenarios
- Performance tests: Query latency benchmarks

## Troubleshooting

### Service Disabled Mode
The module will run without Pinecone integration if `PINECONE_ENABLED` is not set to `true` in `.env`. The `config.py` file will skip client initialization, and API endpoints will return skipped responses. This is the default behavior and is useful for local development or testing.

### Import Errors
If you see `ModuleNotFoundError: No module named 'src.l3_m12_data_isolation_security'`, ensure:
```bash
$env:PYTHONPATH=$PWD  # Windows PowerShell
export PYTHONPATH=$PWD  # Linux/macOS
```

### Tests Failing
Run tests with verbose output:
```bash
pytest -v tests/
```

All tests should pass in offline mode (no Pinecone connection required).

### Pinecone Connection Errors
- Verify `PINECONE_API_KEY` is set correctly
- Check `PINECONE_ENVIRONMENT` matches your account
- Confirm API key has necessary permissions

## Project Structure

```
gcc_multi_tenant_ai_pra_l2/
â"œâ"€â"€ app.py                              # FastAPI entrypoint (thin wrapper)
â"œâ"€â"€ config.py                           # Environment & Pinecone client management
â"œâ"€â"€ requirements.txt                    # Pinned dependencies
â"œâ"€â"€ .env.example                        # API key template
â"œâ"€â"€ .gitignore                          # Python defaults + .ipynb_checkpoints
â"œâ"€â"€ LICENSE                             # MIT License
â"œâ"€â"€ README.md                           # This file
â"œâ"€â"€ example_data.json                   # Sample tenant contexts and attack scenarios
â"œâ"€â"€ example_data.txt                    # Text-based examples and decision framework
â"‚
â"œâ"€â"€ src/                                # Source code package
â"‚   â""â"€â"€ l3_m12_data_isolation_security/  # Python package (importable)
â"‚       â""â"€â"€ __init__.py                 # Core business logic (NO CLI block)
â"‚
â"œâ"€â"€ notebooks/                          # Jupyter notebooks
â"‚   â""â"€â"€ L3_M12_Data_Isolation_Security.ipynb  # Interactive walkthrough
â"‚
â"œâ"€â"€ tests/                              # Test suite
â"‚   â""â"€â"€ test_m12_data_isolation_security.py   # Pytest-compatible tests (30+ tests)
â"‚
â"œâ"€â"€ configs/                            # Configuration files
â"‚   â""â"€â"€ example.json                    # Sample config
â"‚
â""â"€â"€ scripts/                            # Automation scripts
    â"œâ"€â"€ run_api.ps1                     # Windows PowerShell: Start API
    â""â"€â"€ run_tests.ps1                   # Windows PowerShell: Run tests
```

## Next Module

**L3 M12.2:** Vector Database Performance Optimization
- Learn advanced query optimization techniques
- Implement caching strategies for vector searches
- Scale to millions of vectors per tenant

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Contributing

This module is part of the TechVoyageHub L3 Production RAG Engineering Track. For issues or improvements, please follow the standard contribution guidelines.
