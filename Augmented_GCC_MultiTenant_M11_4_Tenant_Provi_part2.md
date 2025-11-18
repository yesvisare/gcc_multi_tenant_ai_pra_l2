## SECTION 5: REALITY CHECK (3-4 minutes, 600-800 words)

### [18:00-20:00] Honest Limitations of Automation

[SLIDE: "Reality Check" - Balance scale showing automation benefits vs. challenges:
- Left side (Benefits): Speed, consistency, cost savings
- Right side (Challenges): Complexity, debugging difficulty, edge cases
- Center: "Automation is NOT Magic"]

**NARRATION:**
"Let's be honest about automated provisioning. It's powerful, but not magic.

**Reality #1: Terraform Can Provision Incorrectly**

Terraform successfully completing doesn't mean infrastructure works correctly:

**Example: Missing RLS Policy**
```hcl
# Bug in Terraform module: RLS policy commented out during testing
# resource "postgresql_policy" "tenant_rls" {
#   name = "tenant_${var.tenant_id}_rls_policy"
#   ...
# }
```

**Result:**
- Terraform apply succeeds ✓
- PostgreSQL schema created ✓
- **But: No row-level security!** ✗
- Tenant A can query Tenant B's data via SQL injection

**Impact:** Security breach, regulatory violation, P0 incident

**Mitigation:**
- Validation tests catch this (test_cross_tenant_isolation fails)
- Automated rollback prevents broken tenant activation
- Code review on Terraform modules (peer review required)

**Lesson:** Always validate, never trust provisioning success alone

---

**Reality #2: Validation Tests Don't Catch Everything**

Our 8 validation tests catch common issues, but edge cases slip through:

**Example: Regional Performance**
```python
# Validation test checks latency in us-east-1
async def test_query_performance():
    # This test runs from us-east-1
    # But tenant's users are in ap-south-1 (Mumbai)
    latency = measure_query_latency()  # 100ms (looks good!)
    assert latency < 500  # Passes ✓

# In production:
# Mumbai users experience 800ms latency (crosses region)
# Validation test didn't catch this
```

**Impact:** SLA violation, angry users, reputation damage

**Mitigation:**
- Multi-region validation testing (test from user's region)
- Real user monitoring (post-activation)
- Performance testing with load (not just single query)

**Lesson:** Validation is insurance, not guarantee

---

**Reality #3: Rollback Isn't Always Perfect**

Terraform destroy usually works, but partial state happens:

**Example: S3 Bucket with Objects**
```bash
# Terraform destroy attempts to delete S3 bucket
# But: Bucket contains objects (uploaded during validation)
# AWS blocks deletion: "Bucket must be empty"

Error: Error deleting S3 bucket: BucketNotEmpty
```

**Result:**
- Rollback fails mid-way
- PostgreSQL schema deleted ✓
- Vector DB namespace deleted ✓
- **S3 bucket remains** ✗ (orphaned resource)
- Manual cleanup required (SRE spends 30 minutes)

**Mitigation:**
- Force empty bucket before destroy:
```python
async def rollback_s3_bucket(bucket_name):
    # Delete all objects first
    s3 = boto3.client('s3')
    objects = s3.list_objects_v2(Bucket=bucket_name)
    
    if 'Contents' in objects:
        delete_keys = [{'Key': obj['Key']} for obj in objects['Contents']]
        s3.delete_objects(
            Bucket=bucket_name,
            Delete={'Objects': delete_keys}
        )
    
    # Now Terraform destroy will succeed
```

**Lesson:** Rollback needs pre-destroy cleanup logic

---

**Reality #4: Automation Requires Expertise**

Automated provisioning is complex - requires multiple skillsets:

**Required Skills:**
- **Terraform:** HCL syntax, state management, modules, providers (20+ hours)
- **Python:** Async programming, subprocess management, error handling (intermediate level)
- **AWS:** IAM policies, S3, RDS, ElastiCache, CloudWatch (AWS Certified level)
- **PostgreSQL:** Schema design, RLS policies, RBAC (DBA-level knowledge)
- **Vector Databases:** Pinecone/Weaviate multi-tenancy (emerging skill)
- **CI/CD:** Celery, Redis, async task queues (DevOps expertise)

**Learning Curve:**
- Junior engineer: 3-6 months to build production system
- Mid-level engineer: 1-2 months
- Senior engineer: 2-4 weeks

**Team Requirement:**
- Not a solo project (too complex for one person)
- Minimum 2-3 engineers for production system
- On-call rotation for incident response

**Lesson:** Budget for learning time and team size

---

**Reality #5: Monitoring is Non-Negotiable**

Without monitoring, automated provisioning becomes a black box:

**What You Can't See:**
- Provisioning duration trending up (performance degradation)
- Failure rate spiking (infrastructure issues)
- Validation tests passing but tenants still broken
- Cost per tenant increasing (resource leak)

**Consequences:**
- CFO: 'Why did our platform costs jump 40% last month?' (No visibility)
- CTO: 'How many tenants are failing provisioning?' (No metrics)
- Platform team: 'Why is provisioning suddenly slow?' (No alerts)

**Required Monitoring:**
```python
# Prometheus metrics (minimum required)
provisioning_duration_seconds{tier, region}
provisioning_success_total{tier}
provisioning_failures_total{tier, step}
validation_test_duration_seconds{test_name}
rollback_success_total
rollback_failures_total
terraform_execution_duration_seconds{command}
```

**Lesson:** Invest in monitoring early (Day 1, not Day 100)

---

**Reality #6: Cost Optimization is Ongoing**

Initial provisioning cost: ₹5K per tenant (automated)

**But:**
- Terraform Cloud: ₹8K/month (Team plan)
- Celery + Redis: ₹6K/month (t3.medium EC2)
- Monitoring: ₹4K/month (Prometheus + Grafana)
- **Total: ₹18K/month platform overhead**

For 10 tenants: ₹18K platform overhead + (₹5K × 10) = ₹68K/month

**ROI Calculation:**
- Manual provisioning: 10 tenants × ₹50K = ₹5 lakh
- Automated provisioning: ₹68K
- **Savings: ₹4.32 lakh (86% cost reduction)**

**At 50 tenants:**
- Manual: 50 × ₹50K = ₹25 lakh
- Automated: ₹18K + (₹5K × 50) = ₹2.68 lakh
- **Savings: ₹22.32 lakh (89% cost reduction)**

**Lesson:** Automation ROI improves with scale (break-even at ~5 tenants)

---

**Reality #7: Edge Cases Require Manual Intervention**

Not all provisioning can be automated:

**Manual Required:**
- Special compliance requirements (healthcare tenants: HIPAA-specific configs)
- Custom integrations (tenant wants Snowflake integration)
- Non-standard regions (tenant needs ap-southeast-3, not supported yet)
- Budget exceptions (enterprise tenant: ₹1 crore annual contract)

**Hybrid Model:**
```python
if tenant.requires_manual_provisioning():
    # Create IT ticket for manual setup
    await create_jira_ticket(
        title=f'Manual provisioning: {tenant.name}',
        assignee='platform-team',
        details=tenant.special_requirements
    )
    await update_status(tenant_id, 'pending_manual_setup')
else:
    # Standard automated path
    await trigger_provisioning_async(tenant_id)
```

**Percentage:**
- 80-90% of tenants: Fully automated
- 10-20% of tenants: Require manual steps

**Lesson:** Design for 'mostly automated', not '100% automated'

---

**Reality #8: Regulatory Compliance Adds Complexity**

Multi-region tenants face complex compliance:

**Example: EU Tenant (GDPR)**
- Must provision in eu-west-1 (data residency)
- Cannot use us-east-1 vector DB namespace (cross-border data transfer)
- Must enable encryption at rest (GDPR Article 32)
- Must implement right-to-deletion (GDPR Article 17)

**Provisioning Complexity:**
```hcl
# Conditional resource creation based on region
resource "aws_kms_key" "tenant_encryption" {
  # KMS key required for EU tenants only
  count = var.region == "eu-west-1" ? 1 : 0
  
  description = "Encryption key for tenant ${var.tenant_id} (GDPR)"
}

# Different S3 configuration for EU
resource "aws_s3_bucket" "tenant_storage" {
  bucket = "${local.resource_prefix}-documents"
  
  # Server-side encryption required for EU
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm     = var.region == "eu-west-1" ? "aws:kms" : "AES256"
        kms_master_key_id = var.region == "eu-west-1" ? aws_kms_key.tenant_encryption[0].id : null
      }
    }
  }
}
```

**Impact:**
- 2x Terraform module complexity
- Region-specific validation tests
- Compliance audits per region

**Lesson:** Regional compliance increases provisioning complexity significantly

---

**Honest Summary:**

**What Automated Provisioning Solves:**
- ✓ Eliminates 2-week manual delays
- ✓ Reduces cost from ₹50K to ₹5K per tenant
- ✓ Scales to 50+ tenants without hiring more SREs
- ✓ Provides consistent, reproducible infrastructure

**What It Doesn't Solve:**
- ✗ Doesn't eliminate all manual work (10-20% edge cases)
- ✗ Doesn't guarantee bug-free provisioning (validation catches issues)
- ✗ Doesn't remove complexity (requires expertise to build)
- ✗ Doesn't work without monitoring (black box otherwise)

**Production Readiness Checklist:**
- [ ] Validation tests cover security, isolation, performance
- [ ] Rollback tested and handles edge cases (S3 cleanup)
- [ ] Monitoring metrics defined and dashboards created
- [ ] Team trained on Terraform, Python orchestration
- [ ] On-call rotation for incident response
- [ ] Regional compliance mapped (GDPR, DPDPA, etc.)
- [ ] Cost monitoring per tenant enabled
- [ ] Documentation for manual edge cases

**Measure Twice, Cut Once:**
Building automated provisioning takes 3-6 months. But benefits last for years. Invest in validation, monitoring, and documentation - they pay dividends."

**INSTRUCTOR GUIDANCE:**
- Be brutally honest about limitations (builds trust)
- Use real failure examples (not hypothetical)
- Quantify everything (time, cost, effort)
- End on practical checklist (production readiness)

---

## SECTION 6: ALTERNATIVE APPROACHES (3-4 minutes, 600-800 words)

### [20:00-23:00] Comparison: Terraform vs. Alternatives

[SLIDE: Alternative Provisioning Approaches Matrix:
- **Approach:** Terraform | Pulumi | CloudFormation | Crossplane | Manual Scripts
- **Complexity:** Medium | High | Low | High | Very Low
- **Multi-Cloud:** Yes | Yes | AWS Only | K8s Only | Depends
- **Cost:** Free | Free | Free | Free | Free
- **Learning Curve:** 20h | 30h | 15h | 40h | 5h
- **GCC Fit:** ★★★★★ | ★★★★☆ | ★★★☆☆ | ★★★★☆ | ★☆☆☆☆]

**NARRATION:**
"Terraform isn't the only way to automate provisioning. Let's compare alternatives.

---

**Alternative #1: Pulumi (Code-Based IaC)**

**Description:**
Infrastructure as Code using Python/TypeScript instead of HCL:

```python
# Pulumi version (Python)
import pulumi
import pulumi_aws as aws

# Create S3 bucket
bucket = aws.s3.Bucket(
    f'rag-tenant-{tenant_id}',
    tags={
        'TenantID': tenant_id,
        'Tier': tier
    }
)

# Create IAM policy
policy = aws.iam.Policy(
    f'tenant-{tenant_id}-s3-access',
    policy=bucket.arn.apply(lambda arn: f'''{{
        "Version": "2012-10-17",
        "Statement": [{{
            "Effect": "Allow",
            "Action": ["s3:*"],
            "Resource": ["{arn}", "{arn}/*"]
        }}]
    }}''')
)

pulumi.export('bucket_name', bucket.id)
```

**Pros:**
- **Familiar Language:** Use Python (same as orchestration service)
- **Type Safety:** IDE autocomplete, type checking (fewer bugs)
- **Testing:** Unit test infrastructure code with pytest
- **Dynamic Logic:** Complex conditionals easier than HCL

**Cons:**
- **Learning Curve:** 30 hours (Pulumi concepts + cloud APIs)
- **Community:** Smaller than Terraform (fewer modules, Stack Overflow answers)
- **State Management:** Pulumi Cloud required (or self-host state backend)

**Cost Comparison:**
- Free tier: 1 stack (equivalent to 1 Terraform workspace)
- Team plan: $75/month (unlimited stacks)

**When to Use:**
- Team already proficient in Python/TypeScript
- Complex provisioning logic (easier in code than HCL)
- Existing CI/CD in Python ecosystem

**When NOT to Use:**
- Team new to IaC (Terraform has better learning resources)
- Multi-cloud required (Terraform has broader provider support)
- Need maximum community support (Terraform wins)

**GCC Fit:** ★★★★☆ (4/5) - Excellent if team is Python-first

---

**Alternative #2: AWS CloudFormation (AWS-Native)**

**Description:**
AWS's native IaC tool using JSON/YAML templates:

```yaml
# CloudFormation template (YAML)
Resources:
  TenantBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub 'rag-tenant-${TenantId}'
      Tags:
        - Key: TenantID
          Value: !Ref TenantId
        - Key: Tier
          Value: !Ref Tier

  TenantBucketPolicy:
    Type: AWS::S3::BucketPolicy
    Properties:
      Bucket: !Ref TenantBucket
      PolicyDocument:
        Statement:
          - Effect: Allow
            Principal:
              AWS: !GetAtt TenantRole.Arn
            Action: 's3:*'
            Resource:
              - !GetAtt TenantBucket.Arn
              - !Sub '${TenantBucket.Arn}/*'
```

**Pros:**
- **No Installation:** Built into AWS (no separate tool)
- **AWS Integration:** Deep integration with AWS services
- **Stack Policies:** Prevent accidental deletion of resources
- **ChangeS

ets:** Preview changes before apply (like Terraform plan)

**Cons:**
- **AWS Only:** Cannot provision non-AWS resources (Pinecone, etc.)
- **YAML Verbosity:** Templates can be very long (100+ lines for simple resources)
- **Limited Logic:** No loops, limited conditionals (complex provisioning hard)
- **State Management:** Stack state locked to AWS (can't move to other providers)

**Cost:**
- Free (built into AWS)

**When to Use:**
- 100% AWS infrastructure (no Pinecone, no GCP)
- Team already familiar with CloudFormation
- Deep AWS integration needed (IAM, Service Catalog)

**When NOT to Use:**
- Multi-cloud required (Terraform/Pulumi better)
- Complex provisioning logic (code-based IaC better)
- Non-AWS resources (vector DB, third-party APIs)

**GCC Fit:** ★★★☆☆ (3/5) - Works but limited to AWS

---

**Alternative #3: Crossplane (Kubernetes-Native)**

**Description:**
Kubernetes Operator that provisions cloud resources via CRDs:

```yaml
# Crossplane CompositeResourceDefinition
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata:
  name: tenant-composition
spec:
  resources:
    - name: tenant-bucket
      base:
        apiVersion: s3.aws.crossplane.io/v1beta1
        kind: Bucket
        spec:
          forProvider:
            region: us-east-1
            tagging:
              tagSet:
                - key: TenantID
                  value: {{ .tenant_id }}
```

**Pros:**
- **Kubernetes Native:** If using K8s, native integration
- **GitOps:** Works seamlessly with ArgoCD, Flux
- **Declarative:** True Kubernetes declarative style
- **RBAC:** Leverage K8s RBAC for infrastructure access control

**Cons:**
- **K8s Required:** Must run Kubernetes cluster (adds complexity)
- **Learning Curve:** 40 hours (K8s + Crossplane + cloud provider CRDs)
- **Maturity:** Less mature than Terraform (fewer providers, edge cases)
- **Debugging:** K8s debugging skills required (more complex)

**Cost:**
- Crossplane: Free (open source)
- K8s cluster: ₹15-30K/month (EKS/GKE)

**When to Use:**
- Already running Kubernetes platform
- GitOps workflow established (ArgoCD)
- Team proficient in Kubernetes

**When NOT to Use:**
- No Kubernetes expertise (too much complexity)
- Simple provisioning needs (overkill)
- Cost-sensitive (K8s cluster overhead)

**GCC Fit:** ★★★★☆ (4/5) - Excellent IF already on K8s

---

**Alternative #4: Manual Bash Scripts**

**Description:**
Simple shell scripts calling cloud CLIs:

```bash
#!/bin/bash
# provision_tenant.sh

TENANT_ID=$1
TIER=$2

# Create S3 bucket
aws s3api create-bucket   --bucket "rag-tenant-${TENANT_ID}"   --region us-east-1

# Tag bucket
aws s3api put-bucket-tagging   --bucket "rag-tenant-${TENANT_ID}"   --tagging "TagSet=[{Key=TenantID,Value=${TENANT_ID}},{Key=Tier,Value=${TIER}}]"

# Create PostgreSQL schema
psql -h $DB_HOST -U admin -d rag_platform <<EOF
CREATE SCHEMA tenant_${TENANT_ID};
GRANT USAGE ON SCHEMA tenant_${TENANT_ID} TO tenant_${TENANT_ID}_user;
EOF
```

**Pros:**
- **Simple:** Easy to understand (no new language)
- **Quick Start:** 5-hour learning curve (basic bash)
- **No Dependencies:** Just bash + cloud CLIs
- **Easy Debugging:** Step through commands manually

**Cons:**
- **Not Idempotent:** Running twice creates errors (duplicate resources)
- **No State Management:** Can't track what was created
- **Error Handling:** Manual (easy to miss failures)
- **Rollback:** Manual (no automatic cleanup)
- **No Validation:** Must manually test provisioning

**Cost:**
- Free (no tooling costs)

**When to Use:**
- Proof of concept (quickly test provisioning flow)
- Learning exercise (understand provisioning steps)
- One-off tenant (won't scale, but quick)

**When NOT to Use:**
- Production use (too error-prone)
- Multiple tenants (no idempotency = chaos)
- Team collaboration (no shared state)

**GCC Fit:** ★☆☆☆☆ (1/5) - Only for POC, not production

---

**Decision Matrix:**

| **Criteria** | **Terraform** | **Pulumi** | **CloudFormation** | **Crossplane** | **Bash Scripts** |
|---|---|---|---|---|---|
| **Multi-Cloud** | ✓ | ✓ | AWS Only | ✓ | Depends |
| **Idempotency** | ✓ | ✓ | ✓ | ✓ | ✗ |
| **State Management** | ✓ | ✓ | ✓ | ✓ (K8s) | ✗ |
| **Learning Curve** | 20h | 30h | 15h | 40h | 5h |
| **Community Size** | Large | Medium | Large | Small | N/A |
| **GCC Production** | ✓ | ✓ | Partial | ✓ (if K8s) | ✗ |
| **ROI Breakeven** | 5 tenants | 5 tenants | 8 tenants | 10 tenants | Never |

**Recommendation:**

**For Most GCCs:** Use **Terraform**
- Industry standard (easiest to hire for)
- Multi-cloud (AWS + Pinecone + GCP if needed)
- Large community (Stack Overflow, modules)
- Break-even at 5 tenants (ROI proven)

**If Python-First Team:** Use **Pulumi**
- Leverage existing Python skills
- Type safety reduces bugs
- Better for complex provisioning logic

**If 100% AWS:** Consider **CloudFormation**
- No additional tools required
- Deep AWS integration
- Simpler deployment (built-in)

**If Already on K8s:** Consider **Crossplane**
- Native K8s integration
- GitOps workflows
- Unified infrastructure management

**Never for Production:** **Bash Scripts**
- Use only for POC or learning
- Not production-ready"

**INSTRUCTOR GUIDANCE:**
- Present alternatives fairly (no FUD)
- Provide clear decision criteria
- Acknowledge team context matters (Python vs. HCL skills)
- End with actionable recommendation

---

## SECTION 7: ANTI-PATTERNS (2-3 minutes, 400-600 words)

### [23:00-25:00] When NOT to Automate Provisioning

[SLIDE: "Red Flags" - Warning signs with X marks:
- ⛔ Tenant count < 5 (manual faster)
- ⛔ No Terraform expertise (3-month learning curve)
- ⛔ Frequent custom requirements (80%+ manual exceptions)
- ⛔ No monitoring infrastructure (blind automation)
- ⛔ Single-tenant platform (overkill)]

**NARRATION:**
"Not every platform needs automated provisioning. Here's when NOT to automate.

---

**Anti-Pattern #1: Premature Automation**

**Scenario:**
Startup GCC with 3 tenants, planning for 'future scale'

**Problem:**
- Automation investment: 3 months dev time (₹15 lakh person-hours)
- Manual provisioning: 3 tenants × 2 weeks = 6 weeks (₹3 lakh)
- **Automation costs 5x more than just doing it manually**

**Red Flags:**
- 'We might have 100 tenants someday' (speculative)
- Current tenant count < 5
- Growth trajectory uncertain

**Better Approach:**
1. Start with documented manual provisioning (runbook)
2. Automate at 8-10 tenants (proven demand)
3. Use runbook as spec for automation

**Lesson:** Automate when pain is real, not hypothetical

---

**Anti-Pattern #2: No Validation Testing**

**Scenario:**
Team builds Terraform automation, skips validation suite to 'ship faster'

**Problem:**
```python
# No validation - just provision and activate
async def provision_tenant(tenant_id, tier, region):
    await run_terraform(['apply', '-auto-approve'])
    await update_status(tenant_id, 'active')  # Hope it works!
```

**Consequences:**
- Tenant 1: PostgreSQL RLS missing → Security breach
- Tenant 2: S3 bucket wrong region → Compliance violation
- Tenant 3: Vector DB namespace not created → System completely broken

**Reality:**
- 15-20% of provisioned tenants are broken
- Users discover bugs in production
- Platform team reputation destroyed

**Lesson:** Validation is NOT optional, it's the core value of automation

---

**Anti-Pattern #3: No Rollback Mechanism**

**Scenario:**
Provisioning fails mid-way, leaves orphaned resources

**Problem:**
```python
# No rollback - just fail and give up
try:
    await run_terraform(['apply'])
except TerraformError:
    logger.error('Provisioning failed')
    # Orphaned: PostgreSQL schema, S3 bucket, IAM roles
    return {'success': False}
```

**Consequences:**
- Orphaned resources consume cost (₹5K/month per failed tenant)
- Manual cleanup required (SRE spends 2 hours per incident)
- Terraform state corrupted (thinks resources exist)

**Cost Impact:**
- 10 failed provisionings × ₹5K/month = ₹50K/month wasted
- Annualized: ₹6 lakh/year in leaked resources

**Lesson:** Rollback is as important as provisioning itself

---

**Anti-Pattern #4: Automation Without Monitoring**

**Scenario:**
Black-box automation - no visibility into what's happening

**Problem:**
- CTO: 'How long does provisioning take?' (No metrics)
- CFO: 'Why are costs up 30%?' (No cost tracking)
- Platform team: 'Why is failure rate spiking?' (No alerts)

**Reality:**
```python
# No monitoring - just hope it works
async def provision_tenant(tenant_id):
    result = await run_terraform(['apply'])
    return result
```

**Consequences:**
- Can't detect degradation (provisioning time: 15 min → 45 min)
- Can't measure ROI (no baseline vs. manual)
- Can't debug failures (no visibility into what broke)

**Lesson:** Monitor first, automate second

---

**Anti-Pattern #5: Single-Tenant Mindset**

**Scenario:**
Team builds 'automated provisioning' that requires manual config per tenant

**Problem:**
```python
# Hardcoded tenant config (not scalable)
if tenant_id == 'tenant-001':
    tier = 'Gold'
    region = 'us-east-1'
elif tenant_id == 'tenant-002':
    tier = 'Silver'
    region = 'eu-west-1'
# ... Must update code for every new tenant!
```

**Why This Fails:**
- Adding tenant requires code change + deployment
- Not truly automated (still manual step)
- Doesn't scale beyond 10 tenants

**Correct Approach:**
```python
# Data-driven: Config from database
tenant_config = await db.get_tenant_config(tenant_id)
await provision(tenant_id, tier=tenant_config.tier, region=tenant_config.region)
```

**Lesson:** Automation means zero code changes for new tenants

---

**Anti-Pattern #6: Ignoring Regulatory Complexity**

**Scenario:**
Team builds simple automation, ignores regional compliance

**Problem:**
```hcl
# Same infrastructure for all regions (non-compliant)
resource "aws_s3_bucket" "tenant_storage" {
  bucket = "rag-tenant-${var.tenant_id}"
  # No encryption, no region-specific rules
}
```

**Consequences:**
- EU tenants: GDPR violation (no encryption at rest)
- Healthcare tenants: HIPAA violation (no access logs)
- Financial tenants: SOX violation (no audit trail)

**Reality:**
- Compliance audit fails
- Fines: ₹50 lakh to ₹5 crore
- Reputational damage

**Correct Approach:**
```hcl
# Region-aware compliance
resource "aws_s3_bucket" "tenant_storage" {
  bucket = "rag-tenant-${var.tenant_id}"
  
  # EU: KMS encryption (GDPR Article 32)
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = var.region == "eu-west-1" ? "aws:kms" : "AES256"
      }
    }
  }
  
  # Healthcare: Access logging (HIPAA)
  logging {
    target_bucket = var.tier == "Healthcare" ? aws_s3_bucket.audit_logs.id : null
  }
}
```

**Lesson:** Compliance is NOT an afterthought, it's core architecture

---

**Anti-Pattern #7: No Approval Workflow**

**Scenario:**
Self-service portal without governance (anyone can create tenant)

**Problem:**
```python
# No approval - instant provisioning
async def create_tenant_request(request):
    # No checks, no approval, just provision
    await provision_tenant(request.tenant_id, request.tier, request.region)
```

**Consequences:**
- Rogue tenants: Unauthorized ₹50L tenant created
- Budget overrun: CFO discovers ₹1 crore annual cost surprise
- No accountability: Can't track who approved what

**Correct Approach:**
```python
# Approval workflow (governance)
if request.budget > 1000000:  # > ₹10L
    # Large budget → CFO approval required
    await notify_cfo_for_approval(request)
    status = 'pending_approval'
else:
    # Small budget → Auto-approved
    await provision_tenant_async(request.tenant_id)
    status = 'provisioning'
```

**Lesson:** Self-service needs guardrails (approval workflow)

---

**When Automation Makes Sense:**
- ✓ Tenant count ≥ 8-10 (proven demand)
- ✓ Terraform expertise on team (or willing to learn)
- ✓ Monitoring infrastructure in place
- ✓ Validation tests designed before provisioning
- ✓ Rollback mechanism tested
- ✓ Compliance requirements mapped

**When Manual is Better:**
- ✗ Tenant count < 5 (automation overhead too high)
- ✗ No IaC expertise (3-6 month learning curve)
- ✗ Frequent custom requirements (80%+ exceptions)
- ✗ Single-tenant platform (overkill)
- ✗ Regulatory complexity unknown (need mapping first)"

**INSTRUCTOR GUIDANCE:**
- Use specific anti-pattern examples (not generic)
- Quantify consequences (cost, time, risk)
- Provide clear when-to-automate criteria
- End on checklist (actionable)

---

## SECTION 8: COMMON FAILURES (3-4 minutes, 600-800 words)

### [25:00-28:00] Production Failure Scenarios & Fixes

[SLIDE: "Common Failures" - Troubleshooting guide with 5 failure modes:
1. Terraform State Corruption
2. Validation Test Failures
3. Partial Rollback (Orphaned Resources)
4. Cross-Tenant Data Leak
5. Regional Provisioning Errors]

**NARRATION:**
"Let's walk through real production failures and how to fix them.

---

**Failure #1: Terraform State Corruption**

**Symptom:**
```bash
$ terraform apply
Error: resource already exists
  AWS S3 bucket 'rag-tenant-001-documents' already exists
  but is not in Terraform state
```

**What Happened:**
- Someone manually deleted S3 bucket via AWS console
- Or: Terraform state file corrupted (S3 backend failure)
- Terraform thinks resource doesn't exist
- AWS says resource exists

**Impact:**
- Cannot provision new tenants (Terraform refuses to run)
- Cannot update existing tenants (state mismatch)
- Manual intervention required

**Root Cause:**
- Manual changes outside Terraform (console clicks)
- Or: Terraform state backend failure (S3 outage)

**Fix #1: Import Existing Resource**
```bash
# Import S3 bucket into Terraform state
terraform import aws_s3_bucket.tenant_storage rag-tenant-001-documents

# Verify state matches reality
terraform plan  # Should show no changes
```

**Fix #2: Recreate Resource (If Import Fails)**
```bash
# 1. Manually delete resource in AWS console
aws s3 rb s3://rag-tenant-001-documents --force

# 2. Run Terraform apply (will recreate)
terraform apply -auto-approve
```

**Prevention:**
```python
# Prevent manual changes - enable Terraform Cloud workspace locking
# Only automation service can run Terraform
async def run_terraform_with_lock(command):
    # Acquire distributed lock (Redis)
    async with redis_lock(f'terraform-{tenant_id}'):
        result = subprocess.run(['terraform'] + command)
    return result
```

**Lesson:** Never make manual changes to Terraform-managed resources

---

**Failure #2: Validation Test Failures (Isolation Breach)**

**Symptom:**
```python
# Validation test fails
ValidationError: Cross-tenant isolation test FAILED
  Tenant A can access Tenant B's data!
  Leaked rows: 150
```

**What Happened:**
- Terraform provisioned resources successfully
- But: PostgreSQL RLS policy missing (bug in Terraform module)
- Tenant A queries Tenant B's documents via SQL

**Impact:**
- **P0 Security Incident:** Cross-tenant data leak
- Regulatory violation (GDPR, HIPAA)
- Must notify affected tenants
- Potential fines: ₹50 lakh to ₹5 crore

**Root Cause:**
```hcl
# Bug: RLS policy commented out during testing
# resource "postgresql_policy" "tenant_rls" {
#   name = "tenant_${var.tenant_id}_rls_policy"
#   ...
# }
```

**Fix:**
```python
# 1. Rollback immediately (don't activate tenant)
await rollback_provisioning(tenant_id, failed_step='validation')

# 2. Fix Terraform module
# Uncomment RLS policy in modules/tenant/main.tf

# 3. Add test to catch this earlier
async def test_rls_policy_exists():
    conn = await get_tenant_db_connection(tenant_id)
    policies = await conn.fetch('''
        SELECT policyname 
        FROM pg_policies 
        WHERE schemaname = 'tenant_${tenant_id}'
    ''')
    
    # Must have at least one RLS policy
    assert len(policies) > 0, 'No RLS policies found!'

# 4. Re-provision tenant
await provision_tenant(tenant_id, tier, region)
```

**Prevention:**
```python
# Make validation tests comprehensive
validation_tests = [
    test_database_connection,
    test_cross_tenant_isolation,  # CRITICAL
    test_rls_policy_exists,        # NEW TEST
    test_vector_search,
    test_authentication,
    test_performance,
    test_s3_permissions,
    test_monitoring,
    test_cost_tags
]

# All tests must pass before activation
for test in validation_tests:
    result = await test(tenant_id)
    if not result['passed']:
        # STOP - do not activate
        await rollback_provisioning(tenant_id)
        raise ValidationError(f'{test.__name__} failed')
```

**Lesson:** Validation catches provisioning bugs before production

---

**Failure #3: Partial Rollback (Orphaned S3 Bucket)**

**Symptom:**
```bash
$ terraform destroy
Error: Error deleting S3 bucket: BucketNotEmpty
  Bucket 'rag-tenant-002-documents' contains objects

Rollback status: FAILED
  PostgreSQL schema: DELETED ✓
  Vector DB namespace: DELETED ✓
  S3 bucket: FAILED ✗ (contains objects)
```

**What Happened:**
- Provisioning failed, triggered rollback
- Terraform deleted PostgreSQL schema successfully
- Terraform deleted vector DB namespace successfully
- **Terraform FAILED to delete S3 bucket** (contains objects)
- Orphaned bucket consuming cost (₹500/month)

**Impact:**
- Cost leak: ₹500/month per failed provisioning
- Manual cleanup required (SRE spends 30 minutes)
- Terraform state corrupted (thinks bucket deleted)

**Root Cause:**
- S3 bucket lifecycle: Must be empty before deletion
- Validation tests uploaded documents during testing
- Terraform doesn't force-empty bucket before destroy

**Fix:**
```python
async def rollback_s3_bucket(tenant_id):
    """
    Force-empty S3 bucket before Terraform destroy.
    
    This ensures Terraform destroy succeeds.
    """
    import boto3
    
    bucket_name = f'rag-tenant-{tenant_id}-documents'
    s3 = boto3.client('s3')
    
    try:
        # List all objects (including versions if versioning enabled)
        response = s3.list_objects_v2(Bucket=bucket_name)
        
        if 'Contents' in response:
            # Delete all objects
            objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
            s3.delete_objects(
                Bucket=bucket_name,
                Delete={'Objects': objects_to_delete}
            )
            
            logger.info(f'Deleted {len(objects_to_delete)} objects from {bucket_name}')
        
        # If versioning enabled, delete all versions
        versions = s3.list_object_versions(Bucket=bucket_name)
        if 'Versions' in versions:
            versions_to_delete = [
                {'Key': v['Key'], 'VersionId': v['VersionId']} 
                for v in versions['Versions']
            ]
            s3.delete_objects(
                Bucket=bucket_name,
                Delete={'Objects': versions_to_delete}
            )
        
        # Now Terraform destroy will succeed
        await run_terraform(['destroy', '-auto-approve'])
        
    except Exception as e:
        logger.error(f'Failed to empty bucket {bucket_name}: {str(e)}')
        # Alert SRE for manual cleanup
        await alert_sre(f'Manual cleanup needed: {bucket_name}')
```

**Prevention:**
```python
# Add force-empty logic to rollback
async def rollback_provisioning(tenant_id, failed_step):
    try:
        # STEP 1: Force-empty S3 bucket (before Terraform destroy)
        await rollback_s3_bucket(tenant_id)
        
        # STEP 2: Run Terraform destroy
        await run_terraform(['destroy', '-auto-approve'])
        
        # STEP 3: Clean up database records
        await db.delete_tenant(tenant_id)
        
    except Exception as e:
        # Rollback failed - escalate
        await alert_sre(f'Rollback FAILED for {tenant_id}: {str(e)}')
```

**Lesson:** Rollback needs pre-destroy cleanup for stateful resources

---

**Failure #4: Cross-Tenant Data Leak (JWT Spoofing)**

**Symptom:**
```
SECURITY ALERT: Cross-tenant access detected
  Tenant A accessed Tenant B's documents
  Method: Spoofed JWT claim (tenant_id altered)
```

**What Happened:**
- Attacker captured Tenant A's JWT
- Modified `tenant_id` claim from 'tenant-A' to 'tenant-B'
- API accepted spoofed JWT (didn't verify signature)
- Attacker accessed Tenant B's data

**Impact:**
- **P0 Security Incident:** Data breach
- Must notify both tenants
- Regulatory fines: ₹50 lakh+
- Reputation damage

**Root Cause:**
```python
# Bug: JWT validation doesn't verify signature
async def authenticate_request(request):
    token = request.headers.get('Authorization').replace('Bearer ', '')
    
    # WRONG: Just decode, don't verify signature
    payload = jwt.decode(token, verify=False)  # ⚠️ DANGEROUS
    tenant_id = payload['tenant_id']
    
    # Attacker can forge any tenant_id!
    return tenant_id
```

**Fix:**
```python
# Correct: ALWAYS verify JWT signature
async def authenticate_request(request):
    token = request.headers.get('Authorization').replace('Bearer ', '')
    
    try:
        # VERIFY signature with secret key
        # This ensures token was issued by our auth service
        payload = jwt.decode(
            token,
            os.environ['JWT_SECRET'],  # Secret key
            algorithms=['HS256']        # Algorithm verification
        )
        
        tenant_id = payload['tenant_id']
        
        # Additional validation: Check tenant exists
        tenant = await db.get_tenant(tenant_id)
        if not tenant or tenant.status != 'active':
            raise HTTPException(401, 'Invalid tenant')
        
        return tenant_id
        
    except jwt.InvalidTokenError:
        # Signature verification failed
        raise HTTPException(401, 'Invalid JWT signature')
    except jwt.ExpiredSignatureError:
        # Token expired
        raise HTTPException(401, 'Token expired')
```

**Prevention:**
```python
# Automated security testing (from M11.3)
async def test_spoofed_jwt():
    """
    Test: Can attacker spoof JWT tenant_id claim?
    
    This should FAIL (JWT signature verification should reject).
    """
    # Create valid JWT for Tenant A
    valid_token = create_jwt(tenant_id='tenant-A')
    
    # Decode and modify tenant_id (attacker simulation)
    payload = jwt.decode(valid_token, verify=False)  # Don't verify for testing
    payload['tenant_id'] = 'tenant-B'  # Spoof different tenant
    
    # Re-encode without proper signature
    spoofed_token = jwt.encode(payload, 'wrong_secret', algorithm='HS256')
    
    # Try to access API with spoofed token
    response = await api_client.get(
        '/api/documents',
        headers={'Authorization': f'Bearer {spoofed_token}'}
    )
    
    # MUST be rejected
    assert response.status_code == 401, 'JWT spoofing attack succeeded!'
```

**Lesson:** Always verify JWT signatures (never `verify=False` in production)

---

**Failure #5: Regional Provisioning Errors (Data Residency)**

**Symptom:**
```
ProvisioningError: Cannot provision in eu-west-1
  Pinecone namespace not available in EU region
  Data residency violation (GDPR)
```

**What Happened:**
- EU tenant requested (GDPR compliance required)
- Terraform successfully provisioned AWS resources in eu-west-1
- **But: Pinecone doesn't have EU region**
- Vector DB data stored in us-east-1 (data residency violation)

**Impact:**
- **GDPR Violation:** Cross-border data transfer
- Fines: Up to 4% of global revenue
- Must provision separate vector DB in EU

**Root Cause:**
```python
# Bug: No region validation before provisioning
async def provision_tenant(tenant_id, tier, region):
    # Assumes all providers support all regions
    await run_terraform(['apply'])
    # But Pinecone only in us-east-1, ap-southeast-1
```

**Fix:**
```python
# Add region validation
SUPPORTED_REGIONS = {
    'aws': ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-south-1'],
    'pinecone': ['us-east-1', 'ap-southeast-1']  # Limited regions
}

async def validate_region(region, providers):
    """
    Validate region supported by all providers.
    
    Prevents data residency violations.
    """
    for provider in providers:
        if region not in SUPPORTED_REGIONS[provider]:
            raise ValidationError(
                f'Region {region} not supported by {provider}. '
                f'Supported: {SUPPORTED_REGIONS[provider]}'
            )

# Before provisioning
async def provision_tenant(tenant_id, tier, region):
    # Validate region first
    await validate_region(region, providers=['aws', 'pinecone'])
    
    # If EU region but Pinecone unavailable, use alternative
    if region == 'eu-west-1' and 'pinecone' not in get_available_providers(region):
        # Use Weaviate (supports EU)
        vector_db_provider = 'weaviate'
    else:
        vector_db_provider = 'pinecone'
    
    # Provision with correct provider
    await run_terraform(['apply'], vector_db=vector_db_provider)
```

**Prevention:**
```python
# Regional compliance validation
async def validate_compliance(tenant_id, region):
    """
    Validate regional compliance requirements.
    
    EU: GDPR (data residency, encryption at rest)
    Healthcare: HIPAA (access logs, encryption)
    Financial: SOX (audit trail, immutability)
    """
    if region.startswith('eu-'):
        # GDPR requirements
        assert vector_db_region == region, 'GDPR: Data must stay in EU'
        assert encryption_at_rest_enabled, 'GDPR Article 32: Encryption required'
    
    if tier == 'Healthcare':
        # HIPAA requirements
        assert access_logging_enabled, 'HIPAA: Access logs required'
        assert encryption_in_transit_enabled, 'HIPAA: Encryption required'
```

**Lesson:** Validate regional compliance before provisioning (not after)

---

**Debugging Checklist:**

When provisioning fails:
1. **Check Terraform logs:** Look for resource creation errors
2. **Check validation test results:** Which test failed?
3. **Check Terraform state:** Does it match AWS reality?
4. **Check regional compliance:** Is region supported by all providers?
5. **Check JWT validation:** Is signature verification enabled?
6. **Check rollback logs:** Did rollback complete successfully?
7. **Check monitoring:** Are metrics showing degradation?

**Prevention is Better Than Cure:**
- Write comprehensive validation tests BEFORE provisioning
- Test rollback in staging environment
- Run security tests (JWT spoofing, isolation)
- Validate regional compliance before provisioning
- Monitor provisioning metrics (duration, failure rate)"

**INSTRUCTOR GUIDANCE:**
- Use real failure scenarios (not hypothetical)
- Show actual error messages (makes it concrete)
- Provide complete fix code (not just theory)
- End with debugging checklist (actionable)

---

**[End of Part 2]**

This completes Sections 5-8 (Reality Check, Alternatives, Anti-patterns, Failures). The script will continue with Part 3.
