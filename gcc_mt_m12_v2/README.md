# L3 M12.2: Document Storage & Access Control

Multi-tenant document storage with S3 isolation models, presigned URLs with tenant validation, data residency enforcement, and comprehensive audit logging for GCC RAG systems.

**Part of:** TechVoyageHub L3 Production RAG Engineering Track
**Prerequisites:** L3 M12.1 (Multi-Tenant Architecture Foundations)
**SERVICE:** AWS_S3 (auto-detected from script)

## What You'll Build

Application-layer validation alone is insufficient for multi-tenant security. Even with tenant ID checks in code, vulnerabilities exist through bugs, accidental code removal, direct S3 Console access, leaked credentials, and third-party tools. This module teaches you to architect document storage so tenant isolation is enforced at the storage layer, not just the application layer.

**Central Question:** How do you architect document storage so tenant isolation is enforced at the storage layer, not just the application layer?

**Key Capabilities:**
- Implement three distinct S3 isolation models (Bucket-Per-Tenant, Shared Bucket + IAM, Hybrid)
- Design tenant-aware presigned URLs that enforce boundaries with validation gates
- Build data residency enforcement for multi-region compliance (GDPR, DPDPA, HIPAA)
- Create comprehensive audit logging for storage access using CloudTrail patterns
- Analyze cost trade-offs between isolation models (₹20L vs ₹8L annually for 50 tenants)
- Prevent cross-tenant document access through wrapper-based prefix enforcement
- Generate short-lived presigned URLs (5 minutes) with tag validation
- Implement TenantS3Client wrapper to prevent direct boto3 bypass

**Success Criteria:**
- Zero cross-tenant document access attempts in audit logs
- All documents properly tagged with tenant_id within 48 hours of upload
- Presigned URL generation completes in <200ms (Redis cache hit rate >80%)
- Data residency violations = 0 (enforcement active at upload time)
- Cost per GB/month = ₹1.75 standard storage + ₹0.05 for tagging overhead
- Tenant A cannot download Tenant B's documents (prefix validation enforced)
- Presigned URLs expire after 5 minutes maximum
- Cross-region upload attempts blocked before S3 API call

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                    Multi-Tenant Storage Architecture             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Application Layer                                               │
│  ┌────────────────┐        ┌──────────────────┐                │
│  │  TenantS3Client │───────▶│ Prefix Validator │                │
│  │   (Wrapper)     │        │  tenant-{id}/    │                │
│  └────────┬───────┘        └──────────────────┘                │
│           │                                                      │
│           ▼                                                      │
│  ┌──────────────────────────────────────┐                       │
│  │   DataResidencyValidator             │                       │
│  │   - EU → eu-west-1                   │                       │
│  │   - US → us-east-1                   │                       │
│  │   - India → ap-south-1               │                       │
│  └──────────────┬───────────────────────┘                       │
│                 │                                                │
├─────────────────┼────────────────────────────────────────────────┤
│                 ▼                                                │
│  Storage Layer (S3)                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │  rag-docs-us   │  │  rag-docs-eu   │  │ rag-docs-india │   │
│  │  (us-east-1)   │  │  (eu-west-1)   │  │  (ap-south-1)  │   │
│  │                │  │                │  │                │   │
│  │ tenant-A/      │  │ tenant-B/      │  │ tenant-C/      │   │
│  │   doc1.pdf     │  │   doc2.pdf     │  │   doc3.pdf     │   │
│  │   doc2.pdf     │  │   doc3.pdf     │  │   doc4.pdf     │   │
│  └────────────────┘  └────────────────┘  └────────────────┘   │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│  Security Controls                                               │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ - Prefix Enforcement: tenant-{id}/ (immutable)             │ │
│  │ - Object Tagging: tenant_id tag validated on presigned URL│ │
│  │ - KMS Encryption: Tenant-specific keys                     │ │
│  │ - IAM Policies: Deny unless tag matches                    │ │
│  │ - Presigned URLs: 5-minute expiration, audit logged        │ │
│  │ - CloudTrail: Immutable audit trail of all access          │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

**Data Flow:**
1. User uploads document via FastAPI endpoint with `X-Tenant-ID` header
2. TenantS3Client validates data residency (region matches tenant requirement)
3. Document key prefixed with `tenant-{id}/` automatically
4. Upload to S3 with tenant_id tag and KMS encryption
5. Audit log records upload with timestamp, tenant, document key
6. Presigned URL generation validates prefix and tags before creating URL
7. URL expires in 5 minutes, access logged to CloudTrail

## Three S3 Isolation Models

### Model 1: Bucket-Per-Tenant
**Structure:** Each tenant receives dedicated S3 bucket (tenant-a, tenant-b, tenant-c)

**Pros:**
- Maximum isolation (bucket-level security boundary)
- Simplest IAM policies (one policy per bucket)
- Clear cost attribution (per-bucket billing)
- Distinct audit trails (per-bucket CloudTrail)

**Cons:**
- AWS bucket limits (100 default, 1,000 with request)
- Management overhead for 50+ tenants
- Per-bucket provisioning complexity
- Per-bucket logging costs

**Cost:** ₹20L annually for 50 tenants
**Recommendation:** Premium GCCs with <100 tenants

### Model 2: Shared Bucket + IAM Policies
**Structure:** One bucket with tenant-specific IAM roles; isolation via bucket policies and object tagging

**IAM Policy Pattern:**
```json
{
  "Effect": "Deny",
  "Principal": "*",
  "Action": "s3:GetObject",
  "Resource": "arn:aws:s3:::rag-docs-shared/*",
  "Condition": {
    "StringNotEquals": {
      "aws:PrincipalTag/tenant_id": "${s3:ExistingObjectTag/tenant_id}"
    }
  }
}
```

**Pros:**
- Scales to 1000+ tenants
- Single management point
- Lower storage costs
- Easier backup/restore

**Cons:**
- Complex IAM policies (human error risk)
- Requires strict object tagging discipline
- Harder cost attribution
- One misconfigured policy enables data breach

**Cost:** ₹8L annually
**Recommendation:** Large GCCs (100+ tenants), cost-conscious organizations with strong IAM expertise

### Model 3: Hybrid (Shared Bucket + Tenant Prefixes + Application Wrapper) **RECOMMENDED**
**Structure:** Shared bucket with mandatory prefix isolation + TenantS3Client wrapper that prevents direct boto3 access

**Security Layers:**
- Prefix validation (tenant-{id}/)
- Metadata checks (tenant_id tag)
- Audit logging (all operations)
- Short expiration times (5 minutes)

**Pros:**
- Scales to 1000+ tenants
- Simpler IAM than Model 2
- Cost-effective (₹8L annually)
- Wrapper prevents S3 bypass

**Cons:**
- Requires disciplined code (never use boto3 directly)
- Wrapper must be bulletproof
- Still needs IAM policies as backup

**Cost:** ₹8L annually
**Recommendation:** MOST GCCs (50-500 tenants) - balances security, scale, cost

## Quick Start

### 1. Clone and Setup
```bash
git clone https://github.com/yesvisare/gcc_multi_tenant_ai_pra_l2.git
cd gcc_mt_m12_v2
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env and set AWS_S3_ENABLED=true and AWS credentials
```

**Required environment variables:**
```bash
AWS_S3_ENABLED=true
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
AWS_DEFAULT_BUCKET=rag-docs-shared
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
$env:AWS_S3_ENABLED='True'; $env:PYTHONPATH=$PWD; uvicorn app:app --reload

# Or use script
./scripts/run_api.ps1
```

**API will be available at:**
- Health check: http://localhost:8000/
- API docs: http://localhost:8000/docs
- Upload: POST http://localhost:8000/documents/upload
- Download: GET http://localhost:8000/documents/{doc_key}/download
- List: GET http://localhost:8000/documents/list
- Presigned URL: POST http://localhost:8000/documents/presigned-url

### 6. Explore Notebook
```bash
jupyter lab notebooks/L3_M12_Data_Isolation_Security.ipynb
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AWS_S3_ENABLED` | No | `false` | Enable AWS S3 integration (set to `true` for production) |
| `AWS_ACCESS_KEY_ID` | If enabled | - | AWS access key for S3 authentication |
| `AWS_SECRET_ACCESS_KEY` | If enabled | - | AWS secret key for S3 authentication |
| `AWS_REGION` | No | `us-east-1` | Default AWS region for S3 operations |
| `AWS_DEFAULT_BUCKET` | No | `rag-docs-shared` | Default S3 bucket name |
| `REDIS_ENABLED` | No | `false` | Enable Redis for presigned URL caching |
| `REDIS_HOST` | If Redis enabled | `localhost` | Redis server hostname |
| `REDIS_PORT` | If Redis enabled | `6379` | Redis server port |
| `DATABASE_URL` | No | - | PostgreSQL connection string for audit logging |
| `OFFLINE` | No | `false` | Run in offline mode (notebook testing) |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) |

## Common Failures & Fixes

| Failure | Cause | Fix |
|---------|-------|-----|
| Tenant A downloads Tenant B's file | Missing prefix validation before presigned URL generation | Add `doc_key.startswith(f"tenant-{tenant_id}/")` check in `PresignedURLService.generate_url()` |
| Wrong S3 region used (GDPR violation) | No region enforcement at upload time | Implement `DataResidencyValidator` in `TenantS3Client.__init__()` to validate region before upload |
| Presigned URLs valid for hours | Expiration set to 3600s instead of 300s | Change `ExpiresIn=300` (5 minutes) in `generate_presigned_url()` call |
| Objects uploaded without tenant tags | Tagging not mandatory in wrapper | Use try-except to enforce tagging in `TenantS3Client.upload()`, fail upload without tags |
| CloudTrail logs show all access as "system" user | IAM role lacks proper tagging | Add tenant_id tags to IAM roles, audit with `aws:PrincipalTag` condition |
| S3 costs 3x expected (from cross-region transfer) | Engineers uploading from wrong region | Block cross-region uploads at application layer with `DataResidencyValidator` |
| Presigned URL forwarded to external party, then accessed | No expiration enforcement by frontend | Return URL + explicit 5-minute TTL message to frontend, audit URL generation |
| Database query for tenant metadata times out | N+1 queries during bulk document upload | Cache tenant metadata in Redis with 1-hour TTL |

## Decision Card

### When to Use

✅ **50+ tenants** with varied data residency requirements (GDPR, DPDPA, HIPAA)
✅ **Documents >100MB** requiring efficient download (presigned URLs avoid proxy overhead)
✅ **Multi-region compliance mandatory** (EU, US, India with separate buckets)
✅ **Cost optimization critical** (shared infrastructure reduces costs by 60%)
✅ **Audit trail required** for regulatory compliance (CloudTrail + database logging)
✅ **Team has AWS expertise** (IAM, KMS, S3 bucket policies)
✅ **Asynchronous document access** (uploads/downloads don't block application flow)
✅ **Large document corpus** (>10GB total storage across all tenants)

### When NOT to Use

❌ **<10GB total storage** across all tenants (database BYTEA simpler)
❌ **Simple row-level database security sufficient** (no regulatory compliance needs)
❌ **Team lacks AWS expertise** and can't hire (IAM misconfiguration risks)
❌ **Budget for managed solutions** like Dropbox Business (₹10-50/GB/month)
❌ **Synchronous document access required** (<100ms latency needed)
❌ **Write-heavy patterns** (>10K uploads/day incur high S3 PUT request costs)
❌ **Single-region deployment** (multi-region overhead unnecessary)
❌ **Documents <100MB** accessed frequently (database storage more efficient)

### Trade-offs

**Cost:**
- **Bucket-Per-Tenant:** ₹20L/year for 50 tenants (higher isolation, higher cost)
- **Shared Bucket (Hybrid):** ₹8L/year for 50 tenants (60% savings)
- **Cross-region transfer:** ₹6/GB for data movement
- **KMS encryption:** ₹75/key/month + ₹0.24/10K API calls
- **CloudTrail:** ₹0.75/100K events

**Latency:**
- **Presigned URL generation:** <200ms (with Redis cache)
- **Direct S3 download:** 50-500ms (depends on region proximity)
- **Cross-region access:** +100-300ms (if user far from bucket region)

**Complexity:**
- **Bucket-Per-Tenant:** Low (simple IAM, easy to understand)
- **Shared Bucket + IAM:** High (complex policies, tag discipline required)
- **Hybrid (TenantS3Client wrapper):** Medium (wrapper must be used consistently)

**Security:**
- **Best:** Bucket-Per-Tenant (physical isolation)
- **Good:** Hybrid with wrapper enforcement (application-level isolation)
- **Risk:** Shared Bucket + IAM (policy misconfiguration vulnerability)

## Troubleshooting

### AWS S3 Disabled Mode
The module will run without AWS S3 integration if `AWS_S3_ENABLED` is not set to `true` in `.env`. The `config.py` file will skip S3 client initialization, and API endpoints will return offline responses. This is the default behavior and is useful for local development or testing.

**To enable AWS S3:**
```bash
# In .env file
AWS_S3_ENABLED=true
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
```

### Import Errors
If you see `ModuleNotFoundError: No module named 'src.l3_m12_document_storage'`, ensure:
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

Check that `AWS_S3_ENABLED=false` for offline testing:
```bash
$env:AWS_S3_ENABLED='false'
pytest -v tests/
```

### Presigned URL Errors
**Error:** "Cross-tenant access denied"
**Cause:** Document key doesn't start with tenant prefix
**Fix:** Ensure document key format is `tenant-{tenant_id}/{filename}`

**Error:** "Document not found"
**Cause:** Document doesn't exist in S3 bucket
**Fix:** Upload document first, then generate presigned URL

### Data Residency Violations
**Error:** "Data residency violation"
**Cause:** Upload attempted to wrong region
**Fix:** Ensure tenant metadata specifies correct `data_residency_region`

Example:
```python
metadata = TenantMetadata(
    tenant_id="tenant-eu-001",
    data_residency="EU",
    data_residency_region="eu-west-1",  # Must match upload region
    encryption_key_id="key-eu"
)
```

## API Usage Examples

### Upload Document
```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -H "X-Tenant-ID: tenant-123" \
  -F "file=@invoice.pdf"
```

**Response:**
```json
{
  "filename": "invoice.pdf",
  "s3_location": "s3://rag-docs-shared/tenant-tenant-123/invoice.pdf",
  "tenant_id": "tenant-123",
  "status": "uploaded"
}
```

### Download Document
```bash
curl -X GET "http://localhost:8000/documents/invoice.pdf/download" \
  -H "X-Tenant-ID: tenant-123" \
  --output invoice.pdf
```

### List Documents
```bash
curl -X GET "http://localhost:8000/documents/list" \
  -H "X-Tenant-ID: tenant-123"
```

**Response:**
```json
{
  "tenant_id": "tenant-123",
  "documents": [
    "invoice.pdf",
    "contract.pdf",
    "report.pdf"
  ],
  "count": 3
}
```

### Generate Presigned URL
```bash
curl -X POST "http://localhost:8000/documents/presigned-url" \
  -H "X-Tenant-ID: tenant-123" \
  -H "Content-Type: application/json" \
  -d '{"doc_key": "invoice.pdf", "expiration": 300}'
```

**Response:**
```json
{
  "presigned_url": "https://rag-docs-shared.s3.us-east-1.amazonaws.com/tenant-tenant-123/invoice.pdf?...",
  "expires_in": 300,
  "tenant_id": "tenant-123"
}
```

## Architecture Details

### TenantS3Client Wrapper
The `TenantS3Client` class wraps boto3 S3 client and enforces tenant isolation:

```python
from src.l3_m12_document_storage import TenantS3Client

client = TenantS3Client("tenant-123")

# Upload - automatically prefixes with tenant-tenant-123/
s3_url = client.upload("invoice.pdf", file_data)

# Download - validates prefix
data = client.download("invoice.pdf")

# List - only shows tenant's documents
docs = client.list_documents()
```

**Security guarantees:**
- All operations automatically scoped to tenant prefix
- Data residency validated before upload
- Audit logged for all operations
- Cannot access other tenants' documents

### Presigned URL Generation
Presigned URLs enable temporary, direct S3 downloads without exposing AWS credentials:

```python
from src.l3_m12_document_storage import PresignedURLService

service = PresignedURLService(redis_client)

# Generate URL with security checks
url = service.generate_url(
    tenant_id="tenant-123",
    doc_key="tenant-tenant-123/invoice.pdf",
    expiration=300  # 5 minutes
)

# Returns: https://rag-docs-shared.s3.amazonaws.com/...?X-Amz-Expires=300
```

**Security checks before generation:**
1. Validate doc_key starts with tenant prefix
2. Verify document exists in S3
3. Check object tags match tenant_id
4. Generate short-lived URL (5 minutes max)
5. Audit log URL generation

### Data Residency Enforcement
Multi-region architecture for regulatory compliance:

```python
from src.l3_m12_document_storage import DataResidencyValidator

validator = DataResidencyValidator()

# Validate upload region matches tenant requirement
region = validator.validate_upload(
    tenant_id="tenant-eu-001",
    region_override="us-east-1"  # Will raise DataResidencyViolation
)
```

**Region mapping:**
- **EU tenants** → `eu-west-1` (GDPR compliance)
- **US tenants** → `us-east-1` (HIPAA/CCPA compliance)
- **India tenants** → `ap-south-1` (DPDPA/RBI compliance)

## GCC Enterprise Context

### Typical 50-Tenant GCC Scenario

**Tenant Distribution:**
- 25 US healthcare providers (HIPAA: must stay in us-east-1)
- 15 EU logistics companies (GDPR: must stay in eu-west-1)
- 10 India financial services (RBI: must stay in ap-south-1)

**Implementation Decisions:**

1. **Use Hybrid Model** (shared bucket + tenant prefixes + wrapper)
   - Scales to 1000+ tenants without bucket limits
   - Cost ₹8L/year vs ₹20L for bucket-per-tenant
   - Still achieves high isolation through wrapper enforcement

2. **Multi-Region Bucket Strategy**
   - Create 3 separate S3 buckets in 3 regions
   - TenantS3Client routes based on tenant.data_residency_region
   - Each region has independent lifecycle, encryption, logging

3. **Encryption Strategy**
   - Create 50 individual KMS keys (one per tenant)
   - Cost: 50 × ₹75 = ₹3,750/month
   - Enables key rotation per tenant independently
   - Audit trail per key

4. **Cost Attribution**
   - Tag all objects with tenant_id and team (for chargeback)
   - Use AWS Cost Explorer to drill down by tag
   - Report monthly storage costs per tenant
   - Implement S3 lifecycle: Standard → Intelligent-Tiering → Glacier after 90 days

5. **Compliance Reporting**
   - CloudTrail logs all access (immutable audit)
   - Monthly audit reports: who accessed what, when
   - Automated anomaly detection: >100 API calls/hour per tenant flags alert
   - GDPR Data Subject Access Requests: query CloudTrail + object list for citizen data

6. **Disaster Recovery**
   - Enable cross-region replication for each region
   - us-east-1 → us-west-2 (₹0.02/1K requests)
   - eu-west-1 → eu-central-1
   - ap-south-1 → ap-southeast-1
   - RTO: <1 hour, RPO: <15 minutes

## Alternative Solutions

### Option 1: Database-Backed File Storage
- Store documents in PostgreSQL BYTEA field
- **Pros:** Full control, single consistency model, ACID guarantees
- **Cons:** Database not optimized for binary objects, expensive scaling, performance bottleneck
- **When to use:** <1GB total storage, simplicity over scale
- **Cost:** ₹50/month single-tenant DB → ₹500/month multi-tenant

### Option 2: Third-Party Storage (Dropbox, OneDrive)
- Offload storage to managed service
- **Pros:** Managed security, compliance certifications, disaster recovery
- **Cons:** Vendor lock-in, cross-tenant data isolation responsibility remains, API rate limits
- **When to use:** Non-regulated industries, budget-constrained
- **Cost:** ₹10-50/GB/month (expensive at scale)

### Option 3: MinIO (Self-Hosted S3-Compatible)
- Run S3-compatible storage on-premises or Kubernetes
- **Pros:** Full control, no vendor lock-in, cost-effective at scale
- **Cons:** Operational burden, security ownership, no managed compliance features
- **When to use:** Regulated industries requiring on-prem, cost optimization
- **Cost:** ₹20L infrastructure + ₹50L ops annually

### Option 4: Azure Blob Storage + RBAC
- Similar to AWS S3 but with different access control model
- **Pros:** Azure ecosystem integration, HIPAA/HITRUST certified
- **Cons:** Less mature IAM model, fewer isolation options
- **When to use:** Microsoft-centric organizations
- **Cost:** ₹2/GB/month (competitive)

## Next Module

**L3 M12.3:** Query Isolation (vector DB + traditional DB separation)
**L3 M12.4:** Compliance Automation (GDPR/HIPAA audit trails)
**L3 M13:** Scaling to 500+ tenants (performance optimization)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

This is a learning module from TechVoyageHub L3 Production RAG Engineering Track. For questions or improvements, please open an issue at the main repository.

---

**Production-ready multi-tenant document storage with storage-layer isolation enforcement** ✓
