# L3 M11.4: Tenant Provisioning & Automation

Transform manual 2-week tenant onboarding into 15-minute automated deployments using Infrastructure as Code, intelligent validation, and transaction-like rollback semantics.

**Part of:** TechVoyageHub L3 Production RAG Engineering Track
**Prerequisites:** M11.2 (Tenant Registry), M11.3 (Data Isolation Strategies)
**SERVICE:** PROVISIONING (Terraform-based infrastructure automation)

---

## What You'll Build

An automated tenant provisioning system that replaces manual ClickOps with orchestrated Infrastructure as Code workflows, reducing onboarding from 2 weeks to 15 minutes while cutting costs by 90% and error rates from 17.5% to <1%.

**Key Capabilities:**
- **Infrastructure as Code (IaC):** Terraform modules provision PostgreSQL schemas (RLS), vector DB namespaces, S3 buckets, Redis namespaces, and monitoring dashboards
- **8-Step Workflow:** Request → Approval (budget-based) → Provision → Configure → Validate (8 tests) → Activate → Notify → Rollback (on failure)
- **Validation Suite:** 8 automated tests covering database connectivity, cross-tenant isolation, vector search, JWT auth, query performance (<500ms SLA), S3 permissions, metrics collection, and cost tagging
- **Transaction-like Rollback:** Automatic `terraform destroy` + registry cleanup on ANY failure to prevent orphaned resources
- **Tier-Based Configuration:** Gold (GPT-4, 1000 qpm), Silver (GPT-3.5, 500 qpm), Bronze (GPT-3.5, 100 qpm)
- **Budget-Based Approval:** Auto-approve <₹10L, CFO manual approval ≥₹10L
- **Cost Optimization:** Resource tagging for chargeback, tier pricing, regional multipliers
- **Compliance Enforcement:** Data residency checks, audit trails (Git + Terraform state), SOX/GDPR/DPDPA support

**Success Criteria:**
- Provision 3 tenants (Gold/Silver/Bronze) end-to-end in <15 minutes each
- All 8 validation tests pass for each tenant
- Rollback successfully removes ALL resources when validation fails
- High-budget tenant (≥₹10L) correctly triggers manual approval workflow
- Cost tags (TenantID, Tier, CostCenter) present on all provisioned resources
- No orphaned resources after failed provisioning attempts

---

## How It Works

```
┌─────────────────┐
│ Self-Service    │  Tenant submits request:
│ Portal          │  - Name, Tier (Gold/Silver/Bronze), Region, Budget, Email
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Approval        │  Budget-based governance:
│ Workflow        │  - <₹10L: Auto-approved (5s)
└────────┬────────┘  - ≥₹10L: CFO approval (1-3 days)
         │
         ▼
┌─────────────────┐
│ Orchestration   │  Python FastAPI + async workflow:
│ Service         │  - Coordinates Terraform execution
└────────┬────────┘  - Manages configuration
         │           - Triggers validation
         ▼
┌─────────────────┐
│ Terraform       │  Provisions (8-12 min):
│ IaC Engine      │  - PostgreSQL schema with RLS
└────────┬────────┘  - Pinecone vector namespace
         │           - S3 bucket + IAM policies
         │           - Redis namespace
         │           - Grafana dashboard
         ▼
┌─────────────────┐
│ Validation      │  8-test suite (2-3 min):
│ Suite           │  1. Database connectivity
└────────┬────────┘  2. Cross-tenant isolation
         │           3. Vector search
         │           4. JWT authentication
         │           5. Query performance (<500ms)
         │           6. S3 permissions
         │           7. Metrics collection
         │           8. Cost tag verification
         │
    Success? ──No──> ┌─────────────────┐
         │           │ Rollback        │ terraform destroy
        Yes          │ Mechanism       │ + registry cleanup
         │           └─────────────────┘
         ▼
┌─────────────────┐
│ Tenant ACTIVE   │  Mark active in registry
│ + Notifications │  Send email + Slack alerts
└─────────────────┘
```

**Timeline Breakdown:**
- Request submission: <1 minute
- Approval: 5 seconds (auto) or 1-3 days (manual)
- Infrastructure provisioning: 8-12 minutes
- Configuration initialization: 30 seconds
- Validation testing: 2-3 minutes
- Activation + notifications: 10 seconds
- **Total (auto-approved):** ~15 minutes

---

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

**Key Dependencies:**
- `fastapi` + `uvicorn` (API server)
- `boto3` (AWS infrastructure)
- `psycopg2-binary` (PostgreSQL)
- `pinecone-client` (vector DB)
- `redis` (caching)
- `prometheus-client` (monitoring)
- `pytest` + `pytest-asyncio` (testing)

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

**Minimum Configuration (Simulation Mode):**
```bash
PROVISIONING_ENABLED=false  # Safe for development - no infrastructure changes
OFFLINE=true
```

**Production Configuration:**
```bash
PROVISIONING_ENABLED=true
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
PINECONE_API_KEY=your_pinecone_key
REGISTRY_DB_PASSWORD=your_db_password
```

### 4. Run Tests

**Windows PowerShell:**
```powershell
.\scripts\run_tests.ps1
```

**Manual:**
```bash
export PYTHONPATH=$PWD  # Linux/Mac
$env:PYTHONPATH=$PWD    # Windows PowerShell
pytest -v tests/
```

**Expected Output:**
```
✓ test_provision_infrastructure_offline PASSED
✓ test_validate_tenant_offline PASSED
✓ test_provision_tenant_workflow_success PASSED
...
========================================
✓ All tests passed!
========================================
```

### 5. Start API

**Windows PowerShell:**
```powershell
.\scripts\run_api.ps1
```

**Manual:**
```bash
export PYTHONPATH=$PWD  # Linux/Mac
$env:PYTHONPATH=$PWD    # Windows PowerShell
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

API available at:
- Health check: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Configuration: http://localhost:8000/config

**Example API Request:**
```bash
curl -X POST http://localhost:8000/provision \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_name": "Acme Corporation",
    "tier": "Gold",
    "region": "us-east-1",
    "budget": 2000000,
    "owner_email": "cto@acmecorp.com"
  }'
```

### 6. Explore Notebook

```bash
jupyter lab notebooks/L3_M11_Multi_Tenant_Foundations.ipynb
```

**Notebook Sections:**
1. Learning Arc & Environment Setup
2. Introduction & Hook (Business Case)
3. Conceptual Foundation (IaC, Workflow, Validation, Rollback)
4. Technology Stack
5. Technical Implementation (All Functions)
6. Reality Check (Honest Limitations)
7. Alternative Approaches (Pulumi, CloudFormation, etc.)
8. Anti-Patterns (When NOT to Automate)
9. Common Failures & Debugging
10. Multi-Tenant at GCC Scale
11. Decision Card & PractaThon Mission

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PROVISIONING_ENABLED` | No | `false` | Enable actual infrastructure provisioning (Terraform) |
| `AWS_REGION` | If enabled | `us-east-1` | AWS region for resource provisioning |
| `AWS_ACCESS_KEY_ID` | If enabled | - | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | If enabled | - | AWS secret key |
| `TERRAFORM_STATE_BUCKET` | If enabled | `terraform-state-bucket` | S3 bucket for Terraform state |
| `AUTO_APPROVE_THRESHOLD` | No | `1000000` | Budget threshold (₹) for auto-approval |
| `REGISTRY_DB_HOST` | If enabled | `localhost` | PostgreSQL host for tenant registry |
| `REGISTRY_DB_PASSWORD` | If enabled | - | PostgreSQL password |
| `VECTOR_DB_TYPE` | No | `pinecone` | Vector database type (pinecone/qdrant/chroma) |
| `PINECONE_API_KEY` | If Pinecone | - | Pinecone API key |
| `GRAFANA_URL` | No | - | Grafana dashboard URL |
| `PROMETHEUS_URL` | No | - | Prometheus metrics URL |
| `SLACK_WEBHOOK_URL` | No | - | Slack notifications webhook |
| `VALIDATION_TIMEOUT_SECONDS` | No | `300` | Validation suite timeout |
| `QUERY_PERFORMANCE_SLA_MS` | No | `500` | Query latency SLA (milliseconds) |
| `OFFLINE` | No | `false` | Skip external API calls (notebook mode) |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity (INFO/DEBUG/ERROR) |

---

## Common Failures & Fixes

| Failure | Cause | Fix |
|---------|-------|-----|
| **Terraform plan failure** | Invalid configuration, AWS quota exceeded, VPC subnet conflict | Check Terraform logs: `terraform plan -out=tfplan`, verify AWS quotas, review VPC configuration |
| **Isolation test failure** | RLS policies not applied, schema permissions incorrect | Verify PostgreSQL RLS: `SELECT * FROM pg_policies WHERE schemaname='tenant_X'`, re-apply policies |
| **Performance test failure (>500ms)** | Vector DB not provisioned, index missing, network latency | Check Pinecone namespace exists, rebuild vector index, verify AWS region latency |
| **Validation suite timeout** | Network latency, resource contention, slow provisioning | Increase `VALIDATION_TIMEOUT_SECONDS`, check AWS service health, verify EC2 instance type |
| **Budget approval rejection** | CFO denied request, budget exceeds threshold | Revise budget to <₹10L for auto-approval, escalate to business stakeholders, provide cost justification |
| **Configuration initialization failure** | Registry database connection timeout, invalid tier | Check PostgreSQL connectivity: `psql -h $REGISTRY_DB_HOST -U $REGISTRY_DB_USER`, verify tier value (Gold/Silver/Bronze) |
| **Rollback fails (orphaned resources)** | Terraform state locked, AWS resource dependencies, IAM permissions | Check Terraform state lock: `terraform force-unlock`, manually delete resources via AWS Console, verify IAM permissions for destroy |
| **S3 permissions test failure** | IAM policy missing, bucket not created, region mismatch | Verify S3 bucket exists: `aws s3 ls`, check IAM policy: `aws iam get-policy`, ensure region consistency |
| **Cost tag verification failure** | Tags not applied during Terraform execution, tag key mismatch | Update Terraform modules to include tags, verify tag keys: TenantID, Tier, CostCenter |
| **JWT authentication failure** | Secret key missing, token expiration, invalid claims | Set `JWT_SECRET_KEY` in .env, verify token expiration (default 24h), check tenant_id claim |

---

## Decision Card

### When to Use Automated Provisioning

**Invest in automation when:**
- ✅ **Managing 10+ tenants:** ROI breakeven point
- ✅ **Onboarding 1+ tenant per week:** Manual process becomes bottleneck
- ✅ **Multi-stakeholder approvals required:** CFO, CTO, Legal, Compliance
- ✅ **Compliance is non-negotiable:** GDPR, DPDPA, SOX audit trails required
- ✅ **Chargeback/cost allocation needed:** Resource tagging for finance reporting
- ✅ **Manual error rate >10%:** Automation reduces to <1%
- ✅ **Need for redundancy:** 2+ provisioners required for business continuity
- ✅ **Scaling to 50+ tenants:** Manual provisioning impossible at scale

### When NOT to Use

**Don't automate if:**
- ❌ **<5 tenants with stable requirements:** Manual provisioning cheaper (₹50K vs. ₹5-8L automation investment)
- ❌ **Onboarding <1 tenant per month:** Low utilization, high maintenance overhead
- ❌ **Provisioning process still evolving:** Automating unstable process creates technical debt
- ❌ **Team lacks IaC expertise:** 2-4 week training investment required (Terraform, Python, AWS)
- ❌ **Budget constraints:** ₹5-8 lakh initial investment + ₹50K/month maintenance
- ❌ **Single-cloud, simple infrastructure:** CloudFormation may suffice
- ❌ **Regulatory restrictions on automation:** Some industries require manual approval at every step

### Trade-offs

**Cost:**
- **Initial Investment:** ₹5-8 lakh (2-4 weeks engineering time)
  - Terraform module development: 1 week
  - Orchestration service: 1 week
  - Validation suite: 3-5 days
  - Rollback mechanism: 2-3 days
  - Testing + documentation: 3-5 days
- **Ongoing Maintenance:** ₹50K/month (monitoring, updates, on-call support)
- **Break-even:** 10-15 tenants (₹45K savings/tenant × 15 = ₹6.75L)
- **Annual Savings (50 tenants):** ₹22.5 lakh

**Latency:**
- **Manual:** 2 weeks (10 business days)
- **Automated (auto-approved):** 15 minutes
- **Automated (CFO approval):** 1-3 days (approval) + 15 minutes (provisioning)
- **Speedup:** 1344x faster (2 weeks → 15 min)

**Complexity:**
- **Technology Stack:** Terraform + Python + FastAPI + AWS + PostgreSQL + Pinecone + Redis + Grafana + Prometheus
- **Expertise Required:** DevOps (Terraform), Backend (Python), Cloud (AWS), Database (PostgreSQL), Monitoring (Grafana/Prometheus)
- **Learning Curve:** 2-4 weeks for new team members
- **Dependencies:** 8 external services (potential failure points)

**Reliability:**
- **Manual Error Rate:** 15-20% (misconfigurations, missing steps, human error)
- **Automated Error Rate:** <1% (with validation suite)
- **Silent Failures:** 10% without validation, <0.1% with 8-test suite
- **Rollback Success Rate:** 95% (5% require manual cleanup for orphaned resources)

---

## Troubleshooting

### Provisioning Disabled Mode (Simulation)

The module runs in **simulation mode** by default when `PROVISIONING_ENABLED` is not set to `true` in `.env`.

**Behavior:**
- `config.py` skips AWS client initialization
- API endpoints return simulated responses
- No actual Terraform execution
- No infrastructure charges

**Use Cases:**
- Local development and testing
- Demonstrations without AWS credentials
- Learning the provisioning workflow
- CI/CD pipeline testing

**Enable Production Mode:**
```bash
# .env
PROVISIONING_ENABLED=true
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
```

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'src.l3_m11_tenant_provisioning'`

**Cause:** `PYTHONPATH` not set to include `src` directory

**Fix:**
```bash
# Linux/Mac
export PYTHONPATH=$PWD

# Windows PowerShell
$env:PYTHONPATH=$PWD

# Permanent (Linux/Mac .bashrc)
echo 'export PYTHONPATH=$HOME/gcc_multi_tenant_ai_pra_l2' >> ~/.bashrc
```

### Tests Failing

**Run tests with verbose output:**
```bash
pytest -v tests/ --tb=long
```

**Common test failures:**
- **Async fixture errors:** Install `pytest-asyncio`: `pip install pytest-asyncio`
- **Import errors:** Set `PYTHONPATH` (see above)
- **Offline mode not set:** Tests automatically set `OFFLINE=true`, but verify in logs

### Terraform State Conflicts

**Error:** `Error acquiring the state lock`

**Cause:** Previous Terraform run crashed, leaving lock

**Fix:**
```bash
cd terraform/  # Navigate to Terraform directory
terraform force-unlock <LOCK_ID>  # Use lock ID from error message
```

### API Server Won't Start

**Error:** `Address already in use: 8000`

**Cause:** Port 8000 occupied by another process

**Fix (Linux/Mac):**
```bash
lsof -ti:8000 | xargs kill -9
```

**Fix (Windows PowerShell):**
```powershell
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process
```

**Alternative:** Use different port:
```bash
uvicorn app:app --port 8080
```

---

## Architecture Deep Dive

### Tenant Tier Configuration

| Feature | Gold | Silver | Bronze |
|---------|------|--------|--------|
| **Advanced Search** | ✓ | ✗ | ✗ |
| **Real-time Indexing** | ✓ | ✓ | ✗ |
| **Custom Models** | ✓ | ✗ | ✗ |
| **Batch Processing** | ✓ | ✓ | ✓ |
| **API Access** | ✓ | ✓ | ✓ |
| **Queries/Minute** | 1000 | 500 | 100 |
| **Documents/Month** | 100,000 | 50,000 | 10,000 |
| **LLM Model** | GPT-4 | GPT-3.5-turbo | GPT-3.5-turbo |
| **Max Tokens** | 4096 | 2048 | 1024 |
| **Temperature** | 0.7 | 0.7 | 0.7 |
| **Demo Documents** | ✓ | ✗ | ✗ |

### Validation Suite Details

**Test 1: Database Connectivity (30s timeout)**
```sql
-- Verify PostgreSQL schema provisioned correctly
SELECT 1 FROM tenant_acme_schema.test_table;
```
**Critical:** Yes | **Failure Action:** Immediate rollback

**Test 2: Cross-Tenant Isolation (60s timeout)**
```sql
-- Negative test: Tenant A should NOT access Tenant B's data
SET ROLE tenant_b_user;
SELECT * FROM tenant_a_schema.documents;  -- Should fail with permission denied
```
**Critical:** Yes | **Failure Action:** Immediate rollback + security alert

**Test 3: Vector Search (45s timeout)**
```python
# Verify Pinecone namespace operational
index = pinecone.Index(f"tenant-{tenant_id}-vectors")
results = index.query(vector=[0.1]*1536, top_k=5)
assert len(results) > 0
```
**Critical:** Yes | **Failure Action:** Immediate rollback

**Test 4: JWT Authentication (15s timeout)**
```python
# Generate tenant-specific JWT token
token = jwt.encode({"tenant_id": tenant_id, "exp": exp}, SECRET_KEY)
decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
assert decoded["tenant_id"] == tenant_id
```
**Critical:** Yes | **Failure Action:** Immediate rollback

**Test 5: Query Performance (120s timeout)**
```python
# Execute RAG query and measure latency
start = time.time()
response = rag_query("What are the key risks?", tenant_id)
latency_ms = (time.time() - start) * 1000
assert latency_ms < 500  # SLA: <500ms
```
**Critical:** Yes | **Failure Action:** Immediate rollback (performance regression)

**Test 6: S3 Permissions (30s timeout)**
```python
# Upload test file to tenant-specific bucket
s3.put_object(
    Bucket=f"tenant-{tenant_id}-documents",
    Key="test.txt",
    Body="validation test"
)
```
**Critical:** No | **Failure Action:** Log warning, continue (non-blocking)

**Test 7: Prometheus Metrics (20s timeout)**
```bash
# Verify Prometheus scraping tenant metrics
curl http://prometheus:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.tenant_id == "tenant_acme")'
```
**Critical:** No | **Failure Action:** Log warning, continue

**Test 8: Cost Tags (15s timeout)**
```python
# Verify all resources tagged with TenantID, Tier, CostCenter
resources = boto3.client('resourcegroupstaggingapi').get_resources(
    TagFilters=[
        {'Key': 'TenantID', 'Values': [tenant_id]},
        {'Key': 'Tier', 'Values': ['Gold']},
        {'Key': 'CostCenter', 'Values': [f'CC_{tenant_id.upper()}']}
    ]
)
assert len(resources['ResourceTagMappingList']) == expected_count
```
**Critical:** No | **Failure Action:** Log warning, continue (chargeback may fail)

---

## Multi-Tenant at GCC Scale

### Real-World Complexity (50-200 Tenants)

**Multi-Layer Approval Workflows:**
```
Budget Decision Tree:
├─ <₹10L: Auto-approved (5s)
├─ ₹10L-₹50L: CFO approval (1-3 days)
├─ >₹50L: CFO + CTO + Legal (5-10 days)
│
├─ Sensitive Data (PII/PHI): +Legal +Compliance (2-5 days)
├─ Cross-Border Transfer: +Data Protection Officer (3-7 days)
└─ Gold Tier: +CTO approval (1-2 days)
```

**Cost Attribution Mechanisms:**
```python
# Regional multipliers for chargeback
REGION_MULTIPLIERS = {
    "us-east-1": 1.0,
    "us-west-2": 1.1,
    "eu-west-1": 1.2,
    "ap-south-1": 0.9
}

# Tier pricing (relative to Bronze baseline)
TIER_MULTIPLIERS = {
    "Gold": 3.0,
    "Silver": 2.0,
    "Bronze": 1.0
}

# Monthly chargeback calculation
monthly_cost = base_cost * REGION_MULTIPLIERS[region] * TIER_MULTIPLIERS[tier]
```

**Three-Layer Compliance Stack:**
1. **Parent Company:** SOX (audit trails), GDPR (EU data residency)
2. **India Operations:** DPDPA (data localization), IT Act
3. **Client-Specific:** HIPAA (healthcare), PCI-DSS (payments), FedRAMP (government)

---

## Next Module

**M11.5: Cost Allocation & Chargeback**
- Resource tagging strategies for accurate cost attribution
- Chargeback report generation per tenant
- Budget alerts and cost anomaly detection
- Cost optimization recommendations (rightsizing, reserved instances)

---

## Further Learning

**Terraform:**
- Official docs: https://developer.hashicorp.com/terraform/docs
- AWS provider: https://registry.terraform.io/providers/hashicorp/aws/latest/docs
- Best practices: https://www.terraform-best-practices.com/

**Multi-Tenancy:**
- AWS SaaS architecture: https://aws.amazon.com/blogs/architecture/saas-architecture-fundamentals/
- PostgreSQL RLS: https://www.postgresql.org/docs/current/ddl-rowsecurity.html
- Tenant isolation patterns: https://docs.microsoft.com/en-us/azure/architecture/guide/multitenant/overview

**Cost Optimization:**
- AWS Cost Management: https://aws.amazon.com/aws-cost-management/
- Cost allocation tags: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/cost-alloc-tags.html
- Rightsizing: https://aws.amazon.com/compute-optimizer/

---

## License

MIT License - See [LICENSE](LICENSE) file for details.

---

## Support

- **Issues:** https://github.com/yesvisare/gcc_multi_tenant_ai_pra_l2/issues
- **Discussions:** https://github.com/yesvisare/gcc_multi_tenant_ai_pra_l2/discussions
- **Documentation:** See `notebooks/L3_M11_Multi_Tenant_Foundations.ipynb` for interactive walkthrough

---

**Built with ❤️ for Global Capability Centers scaling multi-tenant RAG systems**
