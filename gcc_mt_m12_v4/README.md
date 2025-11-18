# L3 M12.4: Compliance Boundaries & Data Governance

Production-ready multi-tenant compliance management system for RAG applications. Implements per-tenant compliance configuration and automated data deletion across 7 systems to meet GDPR Article 17, CCPA, DPDPA, and other regulatory requirements.

**Part of:** TechVoyageHub L3 Production RAG Engineering Track
**Prerequisites:** L3 M11 (Data Security & Encryption), L3 M10 (Multi-Tenancy & Access Control)
**Services:** PINECONE (vector DB), AWS (S3/CloudFront) - auto-detected from script

---

## What You'll Build

A production compliance system that handles the challenge of managing per-tenant data retention policies across different regulations when each tenant has unique requirements. Imagine a GCC (Global Capability Center) serving 50 business units, each with different regulatory needs:

- **Tenant A (EU)**: GDPR requires 90-day retention with Right to Erasure
- **Tenant B (US)**: SOX mandates 7-year retention for financial records
- **Tenant C (India)**: DPDPA requires 180-day retention with data localization

When a GDPR Article 17 deletion request arrives, you have **30 days** to delete data across:
- Vector database (Pinecone)
- Object storage (S3)
- Primary database (PostgreSQL)
- Cache (Redis)
- Logs (anonymized, not deleted)
- Backups (marked for deletion)
- CDN (CloudFront invalidation)

**This module solves that problem.**

---

## Key Capabilities

✅ **Per-Tenant Compliance Configuration**
- Configure retention policies per tenant (1-3650 days / 10 years max)
- Support for 7 regulatory frameworks: GDPR, CCPA, DPDPA, SOX, HIPAA, PCI-DSS, FINRA
- Data residency constraints (EU, US, IN, GLOBAL)
- Encryption requirements (AES-256, RSA-4096)

✅ **Automated Scheduled Deletion**
- Daily execution at 2am UTC across all tenants
- Multi-system cascade deletion (7 systems)
- Legal hold protection (prevents evidence destruction)
- Retry logic with exponential backoff (1 min → 5 min → 15 min)
- Per-system status tracking (prevents partial deletion issues)

✅ **GDPR Article 17 Workflow**
- 30-day SLA compliance
- Triple-check legal hold (3 independent sources)
- User deletion request API endpoint
- Automated cascade across all systems
- Verification testing 48 hours post-deletion

✅ **Immutable Audit Trail**
- 7-10 year retention (regulatory requirement)
- Append-only log (never deleted)
- Detailed deletion counts per system
- Audit-ready evidence (< 24 hours to produce)
- Compliance Officer review support

✅ **Legal Hold Protection**
- Litigation/investigation freeze on deletion
- Triple-source verification (config, tracking DB, external legal API)
- Unauthorized deactivation prevention
- Evidence preservation for legal proceedings

✅ **Multi-System Verification**
- Independent verification job (48 hours post-deletion)
- Separate checks per system (not reusing deletion code)
- Verification failure alerts
- Pass/Fail audit trail logging

---

## Success Criteria

✓ **Deletion Completion**: 3-5 days typical (vs. 30-day GDPR SLA)
✓ **Verification Window**: 48 hours post-deletion
✓ **Scheduled Job Runtime**: 30-60 minutes for 50 tenants
✓ **Success Rate**: 99.5% (0.5% failures retry next day)
✓ **Audit Evidence**: < 24 hours to produce compliance proof
✓ **Audit Trail Retention**: 7-10 years (immutable append-only log)
✓ **System Availability**: Low-traffic 2am UTC window (minimal impact)

---

## How It Works

```
┌────────────────────────────────────────────────────────────────────┐
│                    SCHEDULED DELETION JOB (2am UTC)                │
└────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │ For Each Tenant Config  │
                    └─────────────────────────┘
                                  │
                                  ▼
            ┌─────────────────────────────────────┐
            │ STEP 1: Triple-Check Legal Hold    │
            │ ✓ Compliance config table           │
            │ ✓ Legal holds tracking DB           │
            │ ✓ External legal system API         │
            │ IF ANY = TRUE → SKIP (⚠️  Critical) │
            └─────────────────────────────────────┘
                                  │
                                  ▼
            ┌─────────────────────────────────────┐
            │ STEP 2: Check Auto-Delete Enabled  │
            │ IF FALSE → SKIP (manual approval)   │
            └─────────────────────────────────────┘
                                  │
                                  ▼
            ┌─────────────────────────────────────┐
            │ STEP 3: Calculate Cutoff Date       │
            │ cutoff = NOW() - retention_days     │
            └─────────────────────────────────────┘
                                  │
                                  ▼
┌───────────────────────────────────────────────────────────────────┐
│         STEP 4: CASCADE DELETE (7 SYSTEMS INDEPENDENTLY)          │
├───────────────────────────────────────────────────────────────────┤
│ 1. Vector DB (Pinecone)                                           │
│    └─ Delete namespace: tenant_{tenant_id}                        │
│    └─ Filter: created_at < cutoff_date                            │
│                                                                   │
│ 2. S3 (AWS)                                                       │
│    └─ List prefix: tenant_{tenant_id}/                            │
│    └─ Batch delete: 1,000 objects/API call                        │
│                                                                   │
│ 3. PostgreSQL                                                     │
│    └─ CASCADE delete with FK constraints                          │
│    └─ Related tables: document_chunks, embeddings                 │
│                                                                   │
│ 4. Redis                                                          │
│    └─ Pattern match: tenant_{tenant_id}:*                         │
│    └─ Bulk delete matched keys                                    │
│                                                                   │
│ 5. Logs                                                           │
│    └─ ANONYMIZE (replace PII with <REDACTED>)                     │
│    └─ Don't delete (regulatory requirement)                       │
│                                                                   │
│ 6. Backups                                                        │
│    └─ Mark for deletion in next backup cycle                      │
│    └─ Verification job checks backup_metadata                     │
│                                                                   │
│ 7. CDN (CloudFront)                                               │
│    └─ Invalidate path: /tenant_{tenant_id}/*                      │
│    └─ Cache purge                                                 │
└───────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
            ┌─────────────────────────────────────┐
            │ STEP 5: Log to Audit Trail          │
            │ ✓ Deletion counts per system         │
            │ ✓ Cutoff date                        │
            │ ✓ Retention policy used              │
            │ ✓ NEVER DELETED (7-10 years)         │
            └─────────────────────────────────────┘
                                  │
                                  ▼
            ┌─────────────────────────────────────┐
            │ STEP 6: Verification (48 hrs later) │
            │ ✓ Independent checks per system      │
            │ ✓ Don't reuse deletion code          │
            │ ✓ Alert on failures                  │
            │ ✓ Log Pass/Fail to audit trail       │
            └─────────────────────────────────────┘
```

---

## Quick Start

### 1. Clone and Setup

```bash
cd gcc_mt_m12_v4
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env and configure:
# - PINECONE_ENABLED=true (if using Pinecone)
# - PINECONE_API_KEY=your_api_key
# - AWS_ENABLED=true (if using AWS S3/CloudFront)
# - AWS_ACCESS_KEY_ID=your_access_key
# - AWS_SECRET_ACCESS_KEY=your_secret_key
```

**Note:** System runs in degraded mode without credentials (offline mode for testing).

### 4. Run Tests

```bash
# Windows PowerShell
$env:PYTHONPATH=$PWD; pytest -v tests/

# Or use script
./scripts/run_tests.ps1
```

All tests run in **OFFLINE mode** (no external services required).

### 5. Start API

```bash
# Windows PowerShell (offline mode)
$env:PYTHONPATH=$PWD; uvicorn app:app --reload

# Or use script
./scripts/run_api.ps1

# With services enabled
$env:PINECONE_ENABLED='True'; $env:AWS_ENABLED='True'; $env:PYTHONPATH=$PWD; uvicorn app:app --reload
```

API Documentation: `http://localhost:8000/docs`

### 6. Explore Notebook

```bash
jupyter lab notebooks/L3_M12_Data_Isolation_Security.ipynb
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PINECONE_ENABLED` | No | `false` | Enable Pinecone vector database integration |
| `PINECONE_API_KEY` | If enabled | - | Pinecone API key |
| `PINECONE_ENVIRONMENT` | No | `us-west1-gcp` | Pinecone environment |
| `PINECONE_INDEX_NAME` | No | `compliance-rag` | Pinecone index name |
| `AWS_ENABLED` | No | `false` | Enable AWS S3/CloudFront integration |
| `AWS_ACCESS_KEY_ID` | If enabled | - | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | If enabled | - | AWS secret key |
| `AWS_REGION` | No | `us-east-1` | AWS region |
| `S3_BUCKET_NAME` | No | `compliance-documents` | S3 bucket for documents |
| `CLOUDFRONT_DISTRIBUTION_ID` | No | - | CloudFront distribution ID |
| `REDIS_HOST` | No | `localhost` | Redis host |
| `REDIS_PORT` | No | `6379` | Redis port |
| `POSTGRES_HOST` | No | `localhost` | PostgreSQL host |
| `POSTGRES_PORT` | No | `5432` | PostgreSQL port |
| `POSTGRES_DB` | No | `compliance_db` | PostgreSQL database name |
| `POSTGRES_USER` | No | `postgres` | PostgreSQL username |
| `POSTGRES_PASSWORD` | No | - | PostgreSQL password |
| `OFFLINE` | No | `false` | Run in offline mode (notebook/testing) |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) |

---

## Common Failures & Fixes

| Failure | Cause | Fix |
|---------|-------|-----|
| **Partial Deletion** | Vector DB deleted, S3 deleted, PostgreSQL down → partial deletion logged as success | Track per-system status in `deletion_status` table; mark failed systems, retry tomorrow; don't mark deletion "complete" until ALL systems succeed |
| **Legal Hold Not Checked** | Litigation active (legal hold = TRUE), scheduled job deletes anyway → evidence destruction | Triple-check legal hold from 3 sources: (1) `tenant_compliance_config.legal_hold_active`, (2) `legal_holds` table, (3) External legal system API. If ANY = TRUE, skip deletion and alert Legal Counsel |
| **Backup Restore Brings Data Back** | Data deleted from production; backup restore brings deleted data back → GDPR violation | (1) Mark backups for deletion in same workflow, (2) Verification job checks `backup_metadata.marked_for_deletion = TRUE`, (3) Alert if backups not marked |
| **Third-Party Systems Not Notified** | Data deleted from your systems, but Mixpanel/Segment still have it → GDPR violation | (1) Maintain inventory of third-party systems + deletion APIs, (2) Automated deletion notifications via API, (3) Manual tickets for systems without API, (4) Track third-party deletion status in audit trail |
| **No Verification (False Confidence)** | Deletion job logs success, but data still exists (bug in deletion logic). Auditor finds data → compliance failure | (1) Separate verification job runs 48 hours post-deletion, (2) Independent checks (don't reuse deletion code), (3) Verification failures trigger ops alert, (4) Log verification results (PASS/FAIL) to audit trail |
| **Import Errors** | `ModuleNotFoundError: No module named 'src.l3_m12_compliance_boundaries'` | Set PYTHONPATH: `$env:PYTHONPATH=$PWD` (PowerShell) or `export PYTHONPATH=$PWD` (Bash) |
| **Pinecone Not Available** | API calls fail or return "skipped - offline mode" | Set `PINECONE_ENABLED=true` and `PINECONE_API_KEY` in `.env`, restart API |
| **AWS S3 Not Available** | S3 deletion returns "skipped - offline mode" | Set `AWS_ENABLED=true`, `AWS_ACCESS_KEY_ID`, and `AWS_SECRET_ACCESS_KEY` in `.env`, restart API |
| **Redis Connection Failed** | Warning: "Redis connection failed" | Start Redis: `redis-server` or use Docker: `docker run -d -p 6379:6379 redis:5.0.1` |

---

## Decision Card

### ✅ When to Use This System

1. **10-50+ multi-tenant customers** with different regulatory needs (GDPR, CCPA, DPDPA, SOX, HIPAA, etc.)
2. **GDPR/CCPA/DPDPA compliance required** with 30-day deletion SLA
3. **Budget-conscious** (₹7.5K-50K/month vs. ₹2L-10L/month vendor solutions like OneTrust, BigID)
4. **GCC environment** serving parent company + global clients with varying compliance needs
5. **Technical team available** for implementation/maintenance (2-4 week implementation)
6. **Audit-ready evidence required** (< 24 hours to produce compliance proof for auditors)
7. **Multi-system RAG** (vector DB + S3 + PostgreSQL + Redis + logs + backups + CDN - need coordinated deletion)
8. **Established legal hold process** (Legal Counsel workflows in place for litigation/investigation)

### ❌ Choose Alternative When

1. **< 5 tenants** → Use manual deletion (DPO-driven, no automation needed - ₹60K/month labor only)
2. **Real-time compliance required** (< 1 hour SLA) → Use event-driven deletion (7-15x more cost due to constant polling)
3. **No tenant isolation** (mixed data, no tenant_id tags) → First implement tenant isolation (4-8 week project prerequisite)
4. **Fortune 500 with full data governance platform** → Consider vendor (OneTrust ₹2L-10L/month, BigID, Collibra - enterprise budget)
5. **No legal hold process** → Establish Legal Counsel workflows first (2-4 weeks) to prevent evidence destruction
6. **Third-party systems unaudited** → Review Data Processing Agreements (DPAs) first - ensure processors contractually obligate deletion
7. **Retroactive compliance needed** (existing data without tenant tags) → Requires data migration project (8-12 weeks) before implementing this system

### Trade-offs

- **Cost**: ₹15K-50K/month (GCC) vs. ₹2L-10L/month (vendor) - **savings: ₹1.2L-9.5L/year**
- **Latency**: 3-5 days typical deletion (vs. 30-day SLA) - **well within compliance**
- **Complexity**: 2-4 week implementation + ongoing maintenance vs. vendor turnkey (4-6 months vendor onboarding)
- **Control**: Full control over deletion logic and audit trail vs. vendor black box
- **Risk**: Self-managed compliance responsibility vs. vendor shared responsibility
- **Scalability**: Linear scaling (₹750-1,000/tenant) vs. vendor tiered pricing (fixed cost up to thresholds)

---

## Regulatory Frameworks & Requirements

### GDPR (European Union)

- **Article 17 (Right to Erasure)**: User can request all data deleted; **30-day response deadline**
- **Article 5(e)**: Storage limitation principle (don't keep data longer than necessary)
- **Article 30**: Records of processing (audit trail) retained **7 years**
- **Article 44**: Cross-border transfer restrictions (EU data → non-adequate countries requires mechanism like SCCs/BCRs)
- **Fine**: **€20 million OR 4% of global annual revenue**, whichever higher

### CCPA (California)

- **Right to Delete**: Consumer can request deletion; **"without undue delay"** requirement (typically 45 days)
- **Opt-Out Rights**: Consumers can opt out of data sales
- **Fine**: **$7,500 per violation** (can accumulate rapidly with multiple users)

### DPDPA (India)

- **Data Localization**: Some personal data must be stored in India
- **Consent Management**: Explicit consent required for processing
- **Maximum Fine**: **₹250 crore (approximately $30 million USD)**

### SOX (Sarbanes-Oxley, US)

- **Section 404**: Financial controls documentation
- **Record Retention**: **7 years** for financial records (SEC Rule 17a-4)
- **Audit Trail**: Immutable logs of financial data access/modification

### HIPAA (Healthcare, US)

- **PHI Protection**: Strict controls on personal health information
- **Breach Notification**: **60-day** notification requirement
- **Retention**: **6 years** for medical records (varies by context)

### PCI-DSS (Payment Card Industry)

- **Cardholder Data**: Strict protection and retention limits
- **Maximum Retention**: **90 days** for transaction data unless longer retention justified

### FINRA (Financial Industry, US)

- **Rule 17a-4**: Electronic records retention
- **Retention**: **7 years** for financial communications and transactions

---

## Cost Breakdown

### Small GCC (20 tenants)

- Celery workers: **₹2,000/month**
- Audit log storage: **₹3,000/month**
- Deletion API calls (Pinecone, S3): **₹500/month**
- DPO time (20% FTE): **₹10,000/month**
- **Total: ₹15,000/month** (₹750 per tenant)

### Medium GCC (50 tenants)

- Celery workers: **₹5,000/month**
- Audit log storage: **₹10,000/month**
- Deletion API calls: **₹2,000/month**
- DPO time (100% FTE): **₹35,000/month**
- **Total: ₹50,000/month** (₹1,000 per tenant)

### ROI Comparison

- Manual deletion (DPO only): **₹60,000/month**
- Automated (medium GCC): **₹50,000/month**
- **Savings: ₹10,000/month** (₹1.2L annually)
- **Additional benefit**: Audit-ready evidence in < 24 hours (vs. 3-5 days manual compilation)

---

## API Endpoints

### Health Check

```bash
GET /
GET /health
```

Returns service status and enabled/disabled services.

### Create Tenant Compliance Config

```bash
POST /api/v1/compliance/tenants
```

**Request Body:**
```json
{
  "tenant_id": "tenant_a_eu",
  "tenant_name": "ACME Corp EU Division",
  "tenant_email": "dpo@acme.eu",
  "regulations": ["GDPR", "SOX"],
  "retention_days": 90,
  "data_residency": "EU",
  "encryption_required": true,
  "encryption_standard": "AES-256",
  "audit_retention_days": 2555,
  "auto_delete_enabled": true,
  "compliance_metadata": {
    "gdpr_dpo_contact": "dpo@acme.eu"
  }
}
```

### Get Tenant Compliance Config

```bash
GET /api/v1/compliance/tenants/{tenant_id}
```

### Update Legal Hold

```bash
PATCH /api/v1/compliance/tenants/{tenant_id}/legal-hold
```

**Request Body:**
```json
{
  "legal_hold_active": true,
  "legal_hold_reason": "SEC Investigation: Case #2024-SEC-98765"
}
```

**⚠️  CRITICAL:** Consult Legal Counsel before activating/deactivating legal holds.

### Initiate Data Deletion Request (GDPR Article 17)

```bash
POST /api/v1/tenants/{tenant_id}/data/delete
```

**Request Body:**
```json
{
  "user_id": "user_123456",
  "request_type": "gdpr_article_17"
}
```

**Response:**
```json
{
  "request_id": "del_tenant_a_eu_user_123456_1699920000",
  "tenant_id": "tenant_a_eu",
  "user_id": "user_123456",
  "request_type": "gdpr_article_17",
  "requested_at": "2024-11-18T10:00:00Z",
  "status": "completed",
  "message": "Deletion completed successfully across all systems"
}
```

### Get Deletion Request Status

```bash
GET /api/v1/deletion-requests/{request_id}
```

---

## Troubleshooting

### Service Disabled Mode

The module runs without external service integration if `PINECONE_ENABLED` and `AWS_ENABLED` are not set to `true` in `.env`. The `config.py` file will skip client initialization, and API endpoints will return skipped responses. This is the **default behavior** and is useful for local development or testing.

**To enable services:**
1. Copy `.env.example` to `.env`
2. Set `PINECONE_ENABLED=true` and/or `AWS_ENABLED=true`
3. Add API keys (`PINECONE_API_KEY`, `AWS_ACCESS_KEY_ID`, etc.)
4. Restart the API

### Import Errors

If you see `ModuleNotFoundError: No module named 'src.l3_m12_compliance_boundaries'`, ensure:

```bash
# Windows PowerShell
$env:PYTHONPATH=$PWD

# Linux/Mac Bash
export PYTHONPATH=$PWD
```

### Tests Failing

Run tests with verbose output to see which test is failing:

```bash
pytest -v tests/

# Run specific test
pytest -v tests/test_m12_compliance_boundaries.py::test_create_compliance_config_gdpr

# Run with coverage
pytest --cov=src --cov-report=html tests/
```

### API Not Starting

Check that all dependencies are installed:

```bash
pip install -r requirements.txt
```

Verify no port conflicts (8000 already in use):

```bash
# Change port
uvicorn app:app --reload --port 8001
```

---

## Important Warnings

### ⚠️  Consult Legal Team Before Implementing Retention Policies

Retention policies have legal implications. Wrong retention = regulatory violation. This module provides technical implementation only - **not legal advice**.

### ⚠️  GDPR Compliance Requires Professional Legal Review

GDPR is complex. 95% automated compliance requires 5% legal review. Consult Data Protection Officer (DPO) or Legal Counsel before deploying to production.

### ⚠️  Consult DevOps Team Before Implementing Deletion Automation

Test deletion across all systems in UAT environment first. Production systems are complex - verify deletion logic thoroughly before scheduling.

### ⚠️  Data Deletion Must Be Tested Across All Systems

Verification is non-negotiable. Don't automate what you can't verify. The 48-hour verification job is **critical** for compliance.

### ⚠️  Legal Holds Prevent Evidence Destruction

Unauthorized deactivation of legal holds during litigation may constitute obstruction of justice (federal crime). Always consult Legal Counsel before modifying legal hold status.

---

## Production Checklist

✅ Tenant compliance config stored (per-tenant regulations, retention, residency)
✅ Scheduled deletion job runs daily (2am UTC, processes all tenants)
✅ Multi-system cascade implemented (vector DB, S3, PostgreSQL, Redis, logs, backups, CDN)
✅ Legal hold triple-check (3 independent sources prevent evidence destruction)
✅ Verification testing automated (48 hours post-deletion, alerts on failures)
✅ Audit trail immutable (7-10 year retention, never deleted)
✅ Third-party systems inventoried (Mixpanel, Segment, Snowflake, others)
✅ Backup integration complete (marked for deletion, verified in next backup cycle)
✅ CFO chargeback reports monthly (per-tenant cost allocation, ±2% accuracy)
✅ DPO approval workflow (high-stakes tenants require manual sign-off before deletion)
✅ Cross-border transfer mechanisms (SCCs or BCRs documented for EU↔India)
✅ Regulatory inventory maintained (updated quarterly, reviewed by Compliance Officer)

---

## Technology Stack

**Tested Versions:**
- PostgreSQL 15 (ACID guarantees, native UUID, JSONB)
- Celery 5.3.4 (distributed task queue, exponential backoff retries)
- Redis 5.0.1 (cache + Celery broker)
- FastAPI 0.104.0 (async REST API)
- SQLAlchemy 2.0.23 (ORM with cascade deletes)
- Pydantic 2.4.2 (validation)
- Pinecone 3.0.0 (vector DB with namespace isolation)
- Boto3 1.34.0 (AWS S3 + CloudFront)
- Pytest 7.4.4 (testing)

---

## Next Module

**L3 M13: Cost Optimization & Monitoring** - Learn how to optimize RAG costs with caching, batching, and usage tracking across multi-tenant systems.

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Contributing

This is a learning module from TechVoyageHub L3 Production RAG Engineering Track. For issues or improvements, please consult the track documentation or contact your instructor.

---

**⚠️  Disclaimer:** This software is provided for educational purposes. Regulatory compliance requires professional legal review. Consult your Data Protection Officer (DPO), Legal Counsel, and Compliance team before deploying to production.
