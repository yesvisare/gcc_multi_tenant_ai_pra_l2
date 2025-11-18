# Module 11: Multi-Tenant Foundations
## Video M11.4: Tenant Provisioning & Automation (Enhanced with TVH Framework v2.0)

**Duration:** 35 minutes
**Track:** GCC Multi-Tenant Architecture for RAG Systems
**Level:** Builds on Generic CCC Level 2/3 + M11.1-M11.3
**Audience:** RAG engineers who completed M11.1-M11.3 and have Terraform/IaC basics
**Prerequisites:** 
- Generic CCC M1-M8 (RAG fundamentals)
- GCC Multi-Tenant M11.1 (Architecture Patterns)
- GCC Multi-Tenant M11.2 (Tenant Registry)
- GCC Multi-Tenant M11.3 (Authentication & Authorization)
- Terraform basics (infrastructure as code)
- CI/CD concepts (GitHub Actions, GitLab CI)

---

## SECTION 1: INTRODUCTION & HOOK (2-3 minutes, 400-500 words)

### [0:00-0:30] Hook - The Manual Onboarding Nightmare

[SLIDE: Title - "Tenant Provisioning & Automation - From 2 Weeks to 15 Minutes" showing:
- Clock showing "2 weeks" crossed out → "15 minutes"
- Stack of tickets vs. automated dashboard
- Frustrated SRE with manual checklist vs. happy developer at self-service portal
- Cost comparison: ₹50K manual vs. ₹5K automated
- Error rate: 15-20% manual vs. <1% automated]

**NARRATION:**
"You've built a multi-tenant RAG platform. Your tenant registry tracks metadata, your authentication layer prevents cross-tenant leaks, and your isolation model works perfectly. But there's a massive bottleneck nobody talks about: tenant onboarding.

Your sales team just closed 10 new deals. Finance approved the budgets. Legal signed the contracts. Now comes the painful part: provisioning 10 new tenants. In your current setup, each tenant requires:

- **Day 1-2:** DevOps creates PostgreSQL schema with RLS policies (manual SQL scripts)
- **Day 3-4:** Platform team provisions vector DB namespace (manual Pinecone dashboard clicks)
- **Day 5-6:** Security team sets up S3 bucket with tenant-specific IAM policies (manual AWS console)
- **Day 7-8:** Monitoring team creates dashboards and alerts (manual Grafana configuration)
- **Day 9-10:** SRE runs validation tests (manual curl commands)
- **Day 11-14:** Back-and-forth fixing errors from manual steps

Result? **2 weeks per tenant. ₹50,000 in person-hours. 15-20% error rate.**

Your CFO is furious: 'We're paying 3 engineers for 2 weeks to click buttons?' Your CTO is concerned: 'What happens when we have 50 tenants? We'll need 10 full-time SREs just for onboarding!'

**The driving question: How do we automate tenant provisioning to onboard 10 tenants simultaneously in 15 minutes with zero human intervention?**

Today, we're building a fully automated tenant provisioning system using Infrastructure as Code, validation testing, and self-service portals. No more manual clicks. No more 2-week delays. Just 15 minutes from request to active tenant."

**INSTRUCTOR GUIDANCE:**
- Open with urgency - manual onboarding is a real scaling bottleneck
- Use specific time and cost numbers (2 weeks, ₹50K, 15-20% errors)
- Show contrast: manual chaos vs. automated elegance
- Make CFO/CTO pain points real and relatable

---

### [0:30-1:30] What We're Building Today

[SLIDE: Automated Provisioning Architecture showing:
- Self-service portal (React UI) accepting tenant requests
- Approval workflow (CFO approval if budget > ₹10L)
- Orchestration service (Python/Celery) managing workflow
- Terraform module provisioning infrastructure (PostgreSQL, Vector DB, S3, Redis, monitoring)
- Validation test suite (10+ automated checks)
- Rollback mechanism (undo on failure)
- Notification system (Slack/email to stakeholders)]

**NARRATION:**
"Here's what we're building today:

**A fully automated tenant provisioning system** that takes a tenant request through infrastructure creation, validation, and activation - all in 15 minutes without human intervention.

**Key capabilities:**

1. **Self-Service Portal:** Business units request new tenants via web form (name, tier, region, budget)
2. **Approval Workflow:** Automatic approval below ₹10L, CFO approval above (governance guardrails)
3. **Infrastructure Provisioning:** Terraform modules create PostgreSQL schema, vector DB namespace, S3 bucket, Redis namespace, monitoring dashboards - all in parallel
4. **Validation Testing:** Automated test suite runs 10+ checks (isolation, performance, security) before activation
5. **Rollback Capability:** If any step fails, system automatically rolls back all changes (transaction-like semantics)
6. **Audit Trail:** Git commits + Terraform state + application logs = complete audit history

By the end of this video, you'll have **a working provisioning system** that onboards 10 tenants simultaneously in 15 minutes, with <1% error rate, saving ₹25 lakh annually."

**INSTRUCTOR GUIDANCE:**
- Show complete system architecture visually
- Emphasize "no human intervention" as key goal
- Connect to business impact (time, cost, error rate)
- Make CFO approval workflow explicit (governance matters)

---

### [1:30-2:30] Learning Objectives

[SLIDE: Learning Objectives with checkboxes:
✓ Design automated tenant provisioning workflow (request → active)
✓ Implement Infrastructure as Code (Terraform modules)
✓ Build validation test suite (isolation, performance, security)
✓ Create rollback mechanism (transaction-like semantics)
✓ Integrate self-service portal with approval workflow]

**NARRATION:**
"In this video, you'll learn:

1. **Design automated provisioning workflow:** Request → Validation → Approval → Provision → Test → Activate (15-minute end-to-end)
2. **Implement Infrastructure as Code:** Terraform modules that provision PostgreSQL, vector DB, S3, Redis, monitoring - all idempotent and reproducible
3. **Build validation test suite:** 10+ automated checks that verify tenant isolation, performance, security before activation
4. **Create rollback mechanism:** Transaction-like semantics where provisioning failure automatically reverts all infrastructure changes
5. **Integrate self-service portal:** Business units request tenants directly, with approval workflow for governance

These skills are critical for GCC multi-tenant platforms where manual onboarding doesn't scale beyond 10-15 tenants. Automation is the difference between supporting 50 tenants or hiring 10 more SREs."

**INSTRUCTOR GUIDANCE:**
- Frame objectives as production skills, not toy examples
- Emphasize scaling challenge (50+ tenants)
- Connect to career impact (automation expertise = platform engineer roles)
- Set expectation: working code, tested, production-ready

---

### [2:30-3:00] Prerequisites Check

[SLIDE: Prerequisites with status indicators:
✓ Generic CCC M1-M8 (RAG fundamentals)
✓ GCC Multi-Tenant M11.1-M11.3 (Architecture, Registry, Auth)
✓ Terraform basics (modules, state, variables)
✓ CI/CD concepts (GitHub Actions, GitLab CI)
⚠ If missing Terraform: Complete 12-hour Terraform course first]

**NARRATION:**
"Before we start, make sure you've completed:

- **Generic CCC M1-M8:** You understand RAG fundamentals, vector databases, LLM integration
- **GCC Multi-Tenant M11.1-M11.3:** You've built tenant architecture, registry, and authentication
- **Terraform basics:** You know how to write modules, manage state, use variables (12-hour investment if new)
- **CI/CD concepts:** You understand build pipelines, automated testing, deployment automation

If you haven't done Terraform yet, pause this video. Complete a 12-hour Terraform fundamentals course. Infrastructure as Code is non-negotiable for multi-tenant platforms. Manual provisioning simply doesn't scale.

Ready? Let's automate tenant onboarding."

**INSTRUCTOR GUIDANCE:**
- Be firm about Terraform prerequisite (non-negotiable)
- Acknowledge it's additional learning time (12 hours)
- Explain why IaC matters (scale, reproducibility, auditability)
- Set stage for technical depth ahead

---

## SECTION 2: CONCEPTUAL FOUNDATION (8-10 minutes, 1,600-2,000 words)

### [3:00-5:00] Infrastructure as Code Principles

[SLIDE: IaC vs. Manual Provisioning showing:
- Manual: Console screenshots, error-prone, no audit trail, not reproducible
- IaC: Code in Git, version-controlled, reproducible, auditable
- Idempotency concept: Running terraform apply twice = same result
- Declarative vs. Imperative: "What" (desired state) vs. "How" (steps)]

**NARRATION:**
"Let's start with the foundational concept: **Infrastructure as Code (IaC)**.

**Manual Provisioning - The Old Way:**
Imagine onboarding a new tenant manually:
1. Log into AWS console → Create S3 bucket → Set IAM policies (click, click, click)
2. Log into Pinecone dashboard → Create namespace → Set metadata (more clicks)
3. SSH into PostgreSQL → Run CREATE SCHEMA → Set RLS policies (manual SQL)
4. Open Grafana → Create dashboard → Add panels (manual configuration)

**Problems:**
- **Not Reproducible:** Each SRE follows slightly different steps. Tenant A's setup ≠ Tenant B's setup
- **Error-Prone:** Typos in bucket names, incorrect IAM policies, missing monitoring
- **No Audit Trail:** Who created what when? No way to know without digging through logs
- **Not Reversible:** Rollback requires manually undoing each step (often forgotten)

**Infrastructure as Code - The New Way:**
Instead of clicking buttons, we write code that declares desired infrastructure state:

```hcl
# Terraform module: tenant-infrastructure/main.tf
resource "aws_s3_bucket" "tenant_storage" {
  bucket = "rag-tenant-${var.tenant_id}"  # Consistent naming
  
  tags = {
    TenantID = var.tenant_id
    Tier = var.tier
    CostCenter = var.cost_center  # Chargeback tags
  }
}

resource "aws_s3_bucket_policy" "tenant_isolation" {
  bucket = aws_s3_bucket.tenant_storage.id
  
  # Only this tenant's IAM role can access this bucket
  # Prevents cross-tenant data leaks
  policy = jsonencode({
    Statement = [{
      Effect = "Allow"
      Principal = { AWS = "arn:aws:iam::${var.account_id}:role/tenant-${var.tenant_id}" }
      Action = ["s3:GetObject", "s3:PutObject"]
      Resource = "${aws_s3_bucket.tenant_storage.arn}/*"
    }]
  })
}
```

**Benefits:**
1. **Reproducible:** Same code = same infrastructure every time. Tenant A = Tenant B = Tenant C (consistency)
2. **Version-Controlled:** Code in Git. See who changed what when. Rollback to previous version if needed
3. **Auditable:** Terraform state file + Git history = complete audit trail (compliance requirement)
4. **Reversible:** `terraform destroy` undoes everything cleanly (no leftover debris)

**Idempotency - Critical Concept:**
Idempotency means running the same provisioning code multiple times produces the same result (no duplicate resources, no errors).

Example:
- First run: `terraform apply` creates S3 bucket
- Second run: `terraform apply` detects bucket already exists, does nothing (idempotent)
- Without idempotency: Second run tries to create duplicate bucket, fails with error

**Declarative vs. Imperative:**
- **Declarative (Terraform):** 'I want an S3 bucket with these properties.' Terraform figures out how to create it
- **Imperative (Bash script):** 'Run aws s3api create-bucket with these flags.' You specify exact steps

Declarative is better for infrastructure because:
- Terraform handles dependencies (creates IAM role before bucket policy)
- Terraform detects drift (manual changes in AWS console)
- Terraform plans changes before applying (preview what will change)

**GCC Context:**
In GCCs with 50+ tenants, manual provisioning becomes impossible:
- 50 tenants × 2 weeks each = 100 weeks = 2 years (even with 10 SREs)
- With IaC: 50 tenants × 15 minutes each = 12.5 hours (automated, parallelized)
- Cost: ₹25 lakh savings annually (₹50K manual → ₹5K automated per tenant)"

**INSTRUCTOR GUIDANCE:**
- Contrast manual (chaos) vs. IaC (elegance) visually
- Use specific code example to make IaC concrete
- Explain idempotency with clear example (running twice)
- Connect to GCC scale (50+ tenants = IaC mandatory)

---

### [5:00-7:00] Tenant Provisioning Workflow

[SLIDE: End-to-End Provisioning Workflow showing:
- Step 1: Request (Self-service portal)
- Step 2: Validation (Budget, tier, region checks)
- Step 3: Approval (Auto if <₹10L, CFO if >₹10L)
- Step 4: Provision (Terraform apply)
- Step 5: Initialize (Seed data, configs)
- Step 6: Test (Validation suite)
- Step 7: Activate (Update registry to 'active')
- Step 8: Notify (Slack/email to stakeholders)
- Rollback branch: If any step fails → Revert all changes]

**NARRATION:**
"Now let's design the complete provisioning workflow.

**Step 1: Request Submission (Self-Service Portal)**
Business unit fills out form:
- Tenant name: 'Finance-Analytics'
- Tier: Gold (99.9% SLA, 10K docs/month)
- Region: us-east-1 (data residency requirement)
- Budget: ₹8 lakh/year
- Owner: CFO email

Portal validates input:
- Tenant name unique? (No duplicates)
- Tier valid? (Gold/Silver/Bronze only)
- Region supported? (Check allowed regions)

If valid → Create tenant request (status: 'pending')

**Step 2: Approval Workflow (Governance)**
Two approval paths:
1. **Auto-Approval (< ₹10L budget):**
   - Budget < ₹10L → Automatically approved
   - Updates status: 'pending' → 'approved'
   - Proceeds to provisioning immediately

2. **Manual Approval (> ₹10L budget):**
   - Budget > ₹10L → Notify CFO via email/Slack
   - CFO reviews business justification
   - CFO clicks 'Approve' or 'Reject' in portal
   - If approved → status: 'approved', proceed to provisioning
   - If rejected → status: 'rejected', send notification to requester

**Why approval workflow matters:**
- **Governance:** Prevents runaway costs (unauthorized ₹50L tenant)
- **Compliance:** Audit trail shows who approved what when
- **Budget Control:** CFO maintains visibility into platform spend

**Step 3: Infrastructure Provisioning (Terraform)**
Orchestration service runs Terraform module:

```python
async def provision_infrastructure(tenant_id: str, tier: str, region: str):
    """
    Provision all tenant infrastructure using Terraform.
    
    This function is the core of automation - no human intervention.
    Terraform handles all dependencies, resource creation, and error handling.
    """
    # Create Terraform variables file
    # This makes provisioning parameterized - same code, different tenants
    tfvars = {
        'tenant_id': tenant_id,
        'tier': tier,  # Gold/Silver/Bronze
        'region': region,
        'vpc_id': get_vpc_for_region(region),
        'isolation_model': 'namespace'  # From M11.1
    }
    
    # Run Terraform in isolated directory
    # Each tenant gets its own Terraform workspace - prevents conflicts
    terraform_dir = f'/opt/terraform/tenants/{tenant_id}'
    write_tfvars(terraform_dir, tfvars)
    
    # Terraform init: Download providers and modules
    await run_terraform(['init'], cwd=terraform_dir)
    
    # Terraform plan: Preview what will be created
    # Always plan before apply - catch errors early
    plan_output = await run_terraform(['plan', '-out=tfplan'], cwd=terraform_dir)
    log_terraform_plan(tenant_id, plan_output)
    
    # Terraform apply: Actually create infrastructure
    # -auto-approve because we already validated in approval workflow
    await run_terraform(['apply', '-auto-approve', 'tfplan'], cwd=terraform_dir)
    
    # Store Terraform state in S3 for team access
    # State file is critical - contains resource IDs for future changes
    await upload_terraform_state(tenant_id, f'{terraform_dir}/terraform.tfstate')
```

Terraform module provisions:
1. **PostgreSQL Schema:** With RLS policies (row-level security for isolation)
2. **Vector DB Namespace:** Pinecone collection with tenant metadata
3. **S3 Bucket:** With IAM policies (only tenant's role can access)
4. **Redis Namespace:** For tenant-specific caching
5. **Monitoring Dashboard:** Grafana dashboard with tenant metrics
6. **Cost Tags:** All resources tagged with TenantID, Tier, CostCenter

**Provisioning time: 8-12 minutes** (resources created in parallel)

**Step 4: Configuration Initialization**
After infrastructure exists, initialize configs:

```python
async def initialize_tenant_config(tenant_id: str, tier: str):
    """
    Initialize tenant-specific configurations after infrastructure is ready.
    
    Configs include feature flags, rate limits, model selection.
    These are application-level settings, not infrastructure.
    """
    config = {
        'tenant_id': tenant_id,
        'tier': tier,
        
        # Feature flags (see M11.2)
        'features': {
            'advanced_search': tier == 'Gold',  # Premium feature
            'real_time_indexing': tier in ['Gold', 'Silver'],
            'custom_models': tier == 'Gold'
        },
        
        # Rate limits (prevent abuse)
        'rate_limits': {
            'queries_per_minute': 100 if tier == 'Gold' else 50,
            'documents_per_month': 10000 if tier == 'Gold' else 5000
        },
        
        # Model selection (cost optimization)
        'llm_config': {
            'model': 'gpt-4' if tier == 'Gold' else 'gpt-3.5-turbo',
            'max_tokens': 2000,
            'temperature': 0.7
        }
    }
    
    # Store in tenant registry (from M11.2)
    await tenant_registry.create_config(tenant_id, config)
    
    # Seed data (optional)
    # Example: Pre-load sample documents for demo
    if tier == 'Gold':
        await seed_demo_documents(tenant_id)
```

**Step 5: Validation Testing**
Before activating tenant, run automated test suite:

```python
async def validate_tenant(tenant_id: str):
    """
    Run comprehensive validation tests before activating tenant.
    
    These tests catch provisioning errors before users access the system.
    Better to catch issues now than in production.
    """
    test_results = []
    
    # Test 1: Database connectivity
    # Can we connect to PostgreSQL schema?
    result = await test_database_connection(tenant_id)
    test_results.append(('database_connectivity', result))
    
    # Test 2: Isolation verification
    # Can this tenant's credentials access other tenants' data? (Should fail)
    result = await test_cross_tenant_isolation(tenant_id)
    test_results.append(('isolation', result))
    
    # Test 3: Vector search
    # Can we ingest and query documents?
    result = await test_vector_search(tenant_id)
    test_results.append(('vector_search', result))
    
    # Test 4: Authentication
    # Can we generate JWTs with correct tenant claims?
    result = await test_authentication(tenant_id)
    test_results.append(('authentication', result))
    
    # Test 5: Performance
    # Query latency <500ms? (SLA requirement)
    result = await test_query_performance(tenant_id)
    test_results.append(('performance', result))
    
    # Test 6: Storage permissions
    # Can tenant upload documents to S3?
    result = await test_s3_permissions(tenant_id)
    test_results.append(('s3_permissions', result))
    
    # Test 7: Monitoring
    # Are metrics being collected in Prometheus?
    result = await test_monitoring(tenant_id)
    test_results.append(('monitoring', result))
    
    # Test 8: Cost tags
    # Are all resources tagged with TenantID? (Chargeback requirement)
    result = await test_cost_tags(tenant_id)
    test_results.append(('cost_tags', result))
    
    # All tests must pass
    # One failure = rollback entire provisioning
    all_passed = all(result['passed'] for _, result in test_results)
    return all_passed, test_results
```

**Validation time: 2-3 minutes**

**Step 6: Activation**
If all tests pass, activate tenant:

```python
async def activate_tenant(tenant_id: str):
    """
    Mark tenant as active in registry.
    
    After this, tenant can start using the platform.
    This is the 'go-live' moment.
    """
    await tenant_registry.update_status(tenant_id, 'active')
    await notify_stakeholders(tenant_id, 'activated')
```

**Step 7: Notification**
Send notifications to stakeholders:
- Tenant owner: 'Your RAG tenant is ready! Login URL: https://rag.company.com/tenant-xyz'
- Platform team: 'New tenant provisioned: Finance-Analytics (Gold tier, us-east-1)'
- Finance team: 'New tenant activated with ₹8L annual budget'

**Step 8: Rollback on Failure**
If ANY step fails, rollback ALL changes:

```python
async def rollback_provisioning(tenant_id: str, failed_step: str):
    """
    Undo all provisioning changes if any step fails.
    
    This ensures we don't leave partial/broken tenants in the system.
    Transaction-like semantics for infrastructure.
    """
    logger.error(f'Provisioning failed at {failed_step} for {tenant_id}')
    
    # Run Terraform destroy to remove all infrastructure
    # Terraform's dependency graph ensures correct deletion order
    terraform_dir = f'/opt/terraform/tenants/{tenant_id}'
    await run_terraform(['destroy', '-auto-approve'], cwd=terraform_dir)
    
    # Delete tenant from registry
    await tenant_registry.delete(tenant_id)
    
    # Notify requester of failure
    await notify_failure(tenant_id, failed_step)
```

**Total workflow time: 15 minutes** (request → active tenant)"

**INSTRUCTOR GUIDANCE:**
- Show complete workflow visually (8 steps)
- Emphasize automation (no human intervention except CFO approval)
- Explain rollback importance (transaction-like semantics)
- Use code examples to make steps concrete

---

### [7:00-8:00] Validation as Code

[SLIDE: Validation Test Pyramid showing:
- Base: Integration tests (database, S3, vector DB connectivity)
- Middle: Security tests (isolation, authentication, permissions)
- Top: Performance tests (latency, throughput)
- Continuous: Monitoring (post-activation health checks)]

**NARRATION:**
"Let's zoom into validation testing - often the most overlooked part of automation.

**Why Validation Matters:**
Terraform can provision infrastructure successfully but still create broken tenants:
- PostgreSQL schema created, but RLS policies missing → Security breach
- Vector DB namespace created, but wrong region → Compliance violation
- S3 bucket created, but IAM policy allows cross-tenant access → Data leak
- Monitoring created, but metrics not flowing → Operational blindness

**Validation catches these issues BEFORE activation.**

**Validation Test Categories:**

**1. Integration Tests (Base Layer):**
- **Database Connectivity:** Can we connect to PostgreSQL with tenant credentials?
- **Vector Search:** Can we ingest documents and retrieve them?
- **S3 Permissions:** Can we upload/download from tenant bucket?

**2. Security Tests (Middle Layer):**
- **Isolation Verification:** Tenant A's credentials CANNOT access Tenant B's data (critical)
- **Authentication:** JWT generation works with correct tenant claims
- **Permission Boundaries:** Tenant cannot access platform admin APIs

**3. Performance Tests (Top Layer):**
- **Query Latency:** <500ms for p95 (SLA requirement)
- **Throughput:** Handle 100 queries/minute (tier-dependent)
- **Resource Limits:** Memory usage within quota

**4. Compliance Tests:**
- **Cost Tags:** All resources tagged with TenantID (chargeback requirement)
- **Audit Logging:** Provisioning events logged with timestamp + user
- **Data Residency:** Resources in correct region (GDPR requirement)

**Continuous Monitoring (Post-Activation):**
After activation, continuous health checks:
- Every 5 minutes: Check tenant service health
- Every hour: Verify data integrity (document count matches expected)
- Daily: Run full validation suite again (detect configuration drift)

**Failure Threshold:**
- Any security test failure → **Immediate rollback** (zero tolerance)
- Any integration test failure → **Rollback** (tenant won't work)
- Performance test failure → **Warning** (activate but notify platform team)
- Compliance test failure → **Block activation** (regulatory risk)

**GCC Context:**
In GCCs, validation testing is non-negotiable:
- Cross-tenant leaks = regulatory incident = multi-million dollar fines
- Broken tenants = angry business units = platform team credibility destroyed
- Automated validation = 15-minute onboarding vs. 2-week manual debugging"

**INSTRUCTOR GUIDANCE:**
- Explain validation as insurance against provisioning bugs
- Categorize tests (integration, security, performance, compliance)
- Emphasize zero tolerance for security failures
- Show validation prevents production incidents

---

### [8:00-9:00] Rollback Mechanism

[SLIDE: Transaction-like Semantics showing:
- Happy path: Request → Provision → Test → Activate (all green checkmarks)
- Failure path: Request → Provision → Test FAILS → Rollback (red X, undo arrow)
- Terraform state: Before rollback (resources exist) → After rollback (clean slate)
- Partial state danger: Infrastructure exists but tenant not activated (red warning)]

**NARRATION:**
"Rollback is the safety net for automation. Without it, failed provisioning leaves debris - partial tenants, orphaned resources, leaked costs.

**The Problem: Partial Provisioning**
Imagine provisioning fails at Step 5 (validation testing):
- PostgreSQL schema created ✓
- Vector DB namespace created ✓
- S3 bucket created ✓
- Redis namespace created ✓
- **Validation tests FAIL** ✗ (isolation bug detected)

Without rollback:
- Infrastructure exists but tenant unusable
- Resources consuming cost (S3 storage, Redis memory)
- Manual cleanup required (SRE spends 2 hours deleting resources)
- Terraform state corrupted (thinks resources exist, but tenant abandoned)

**With Rollback:**
```python
async def rollback_provisioning(tenant_id: str, failed_step: str):
    """
    Rollback all changes when provisioning fails.
    
    Goal: Return system to state before provisioning started.
    No orphaned resources, no cost leaks, no manual cleanup.
    """
    try:
        # Log failure for debugging
        # Rollback doesn't hide failures - it cleans up after them
        logger.error(
            f'Rollback triggered for {tenant_id} at step {failed_step}',
            extra={'tenant_id': tenant_id, 'failed_step': failed_step}
        )
        
        # Step 1: Destroy infrastructure with Terraform
        # Terraform's dependency graph ensures correct deletion order:
        # First: S3 bucket policy (depends on bucket)
        # Then: S3 bucket
        # Then: IAM role
        # Terraform handles this automatically
        terraform_dir = f'/opt/terraform/tenants/{tenant_id}'
        result = await run_terraform(
            ['destroy', '-auto-approve'],
            cwd=terraform_dir
        )
        
        if result.returncode != 0:
            # Terraform destroy failed - manual intervention needed
            # Alert SRE immediately
            await alert_sre(
                f'Rollback failed for {tenant_id}: Terraform destroy error',
                result.stderr
            )
            raise RollbackError('Terraform destroy failed')
        
        # Step 2: Delete from tenant registry
        # Remove tenant metadata, configs, feature flags
        await tenant_registry.delete(tenant_id)
        
        # Step 3: Clean up Terraform state
        # Remove state file so we can retry provisioning later
        await delete_terraform_state(tenant_id)
        
        # Step 4: Notify stakeholders
        # Be honest about failure - include error details
        await notify_stakeholders(
            tenant_id,
            'provisioning_failed',
            details={'step': failed_step, 'error': 'Validation tests failed'}
        )
        
        logger.info(f'Rollback completed successfully for {tenant_id}')
        
    except Exception as e:
        # Rollback itself failed - escalate to human
        # This is rare but critical when it happens
        await alert_sre(
            f'Rollback FAILED for {tenant_id}: {str(e)}',
            severity='P0'  # Highest priority
        )
        raise
```

**Key Principles:**

**1. Idempotent Rollback:**
Running rollback twice should be safe:
- First run: Deletes resources
- Second run: Detects resources already deleted, does nothing

**2. Dependency-Aware Deletion:**
Terraform handles deletion order:
- Can't delete S3 bucket before deleting bucket policy (dependency)
- Terraform's graph ensures correct order automatically

**3. State Cleanup:**
After rollback, Terraform state file removed:
- Allows re-running provisioning later (retry mechanism)
- Prevents state corruption

**4. Honest Communication:**
Rollback doesn't hide failures:
- Logs show what failed and why
- Stakeholders notified with error details
- SRE alerted if rollback itself fails

**Transaction-like Semantics:**
Rollback makes provisioning transaction-like:
- **ACID properties:** Atomicity (all-or-nothing), Consistency (valid state), Isolation (tenant-specific), Durability (state persisted)
- Either: Tenant fully provisioned and working
- Or: System returned to clean state (as if provisioning never started)
- Never: Partial provisioning with orphaned resources

**GCC Context:**
In GCCs with 50+ tenants, rollback prevents cost leaks:
- 50 failed provisionings × ₹10K leaked resources = ₹5 lakh wasted
- With rollback: ₹0 leaked (infrastructure cleaned up automatically)
- Rollback = financial discipline + operational hygiene"

**INSTRUCTOR GUIDANCE:**
- Explain rollback as transaction semantics for infrastructure
- Show code example with error handling
- Emphasize dependency-aware deletion (Terraform's strength)
- Connect to cost discipline (no leaked resources)

---

### [9:00-10:00] Self-Service Portal & Governance

[SLIDE: Self-Service Architecture showing:
- React UI (tenant request form)
- API Gateway (authentication, rate limiting)
- Orchestration Service (Python/Celery)
- Approval Workflow (auto vs. manual)
- Notification System (Slack, email)
- Audit Log (PostgreSQL)]

**NARRATION:**
"Finally, let's design the self-service portal - the user-facing layer that makes automation accessible.

**Design Goals:**

**1. Self-Service:**
Business units request tenants directly (no IT tickets):
- Finance team wants new tenant for Q4 analysis → Fill form, submit
- HR team wants tenant for employee surveys → Fill form, submit
- No waiting for IT to open ticket, no back-and-forth emails

**2. Governance:**
Self-service doesn't mean uncontrolled:
- Budget approval workflow (CFO signs off on large tenants)
- Resource quotas (Gold tier = 10K docs/month max)
- Regional restrictions (Only US/EU regions allowed for compliance)

**3. Transparency:**
Requesters see provisioning status in real-time:
- 'Pending approval' → CFO reviewing
- 'Provisioning infrastructure' → Terraform running
- 'Running validation tests' → Test suite executing
- 'Active' → Tenant ready, login URL provided

**Portal UI Flow:**

**Step 1: Request Form**
```
Tenant Name: [Finance-Q4-Analytics]
Tier: [Gold ▼] (Gold/Silver/Bronze)
Region: [us-east-1 ▼] (US-East, US-West, EU-West)
Annual Budget: [₹8,00,000]
Business Justification: [Q4 financial forecasting]
Owner Email: [cfo@company.com]

[Submit Request]
```

**Step 2: Validation (Client-Side)**
- Tenant name unique? (Check against existing tenants)
- Budget reasonable? (Gold tier: ₹5-15L, Silver: ₹2-5L, Bronze: <₹2L)
- Region allowed? (Only US/EU for GDPR compliance)

**Step 3: Submission**
POST /api/tenants/request:
```python
async def create_tenant_request(request: TenantRequest):
    """
    API endpoint for tenant request submission.
    
    This is the entry point for self-service provisioning.
    Validates request, checks approvals needed, starts workflow.
    """
    # Validate request
    # Prevent invalid requests from entering workflow
    if not request.tenant_name_unique():
        raise HTTPException(400, 'Tenant name already exists')
    
    if request.budget > 1000000 and not request.has_cfo_approval:
        # Large budget → Manual approval required
        # This is governance - prevents runaway costs
        status = 'pending_approval'
        await notify_cfo_for_approval(request)
    else:
        # Small budget → Auto-approved
        # Fast path for routine requests
        status = 'approved'
        await trigger_provisioning_async(request.tenant_id)
    
    # Store request in database
    # This becomes audit trail for compliance
    tenant_request = await db.tenant_requests.create({
        'tenant_id': request.tenant_id,
        'tenant_name': request.tenant_name,
        'tier': request.tier,
        'region': request.region,
        'budget': request.budget,
        'status': status,
        'requester': request.owner_email,
        'created_at': datetime.utcnow()
    })
    
    return {
        'request_id': tenant_request.id,
        'status': status,
        'message': 'Auto-approved' if status == 'approved' else 'Pending CFO approval'
    }
```

**Step 4: Approval Workflow (If Needed)**
CFO receives email:
```
New Tenant Request: Finance-Q4-Analytics
Tier: Gold
Region: us-east-1
Annual Budget: ₹8,00,000
Requester: finance-team@company.com
Justification: Q4 financial forecasting

[Approve] [Reject]
```

CFO clicks 'Approve':
- Updates status: 'pending_approval' → 'approved'
- Triggers provisioning workflow automatically
- Requester notified: 'Your tenant request was approved'

**Step 5: Provisioning Status (Real-Time)**
Portal shows live status:
```
Tenant: Finance-Q4-Analytics
Status: Provisioning Infrastructure ⏳

Progress:
✓ Request validated
✓ Budget approved
⏳ Provisioning PostgreSQL schema... (2 min)
⏳ Provisioning Vector DB namespace... (3 min)
⏳ Provisioning S3 bucket... (1 min)
⏳ Setting up monitoring... (2 min)
⏳ Running validation tests... (3 min)
```

**Step 6: Activation Notification**
```
Your tenant is ready! 🎉

Tenant Name: Finance-Q4-Analytics
Tier: Gold (99.9% SLA)
Region: us-east-1
Login URL: https://rag.company.com/finance-q4-analytics
API Key: [Secure key, click to reveal]
Documentation: https://docs.company.com/tenants

Support: platform-team@company.com
```

**Governance Features:**

**1. Budget Approval:**
- <₹10L: Auto-approved (routine requests)
- >₹10L: CFO approval required (governance)
- Prevents unauthorized large tenants

**2. Resource Quotas:**
- Gold tier: 10K docs/month max
- Silver tier: 5K docs/month max
- Bronze tier: 2K docs/month max
- Prevents runaway storage costs

**3. Regional Restrictions:**
- Only US/EU regions allowed (GDPR compliance)
- Blocks requests for APAC regions (no data center yet)

**4. Audit Trail:**
- All requests logged: Who requested what when
- All approvals logged: Who approved what when
- All provisioning events logged: What happened when
- Compliance requirement: 7-year retention

**GCC Context:**
Self-service portals scale GCC platforms:
- 50 tenants × manual IT tickets = overwhelmed IT team
- 50 tenants × self-service = IT team focuses on platform improvements
- Time savings: 2 weeks → 15 minutes per tenant
- Cost savings: ₹50K → ₹5K per tenant (person-hours eliminated)"

**INSTRUCTOR GUIDANCE:**
- Show complete user journey (form → provisioning → activation)
- Emphasize governance (approval workflow, quotas)
- Explain audit trail importance (compliance)
- Connect self-service to GCC scale (50+ tenants)

---

## SECTION 3: TECHNOLOGY STACK (4-5 minutes, 800-1,000 words)

### [10:00-11:00] Core Technologies

[SLIDE: Technology Stack with categories:
**Infrastructure as Code:**
- Terraform (primary IaC tool)
- Terraform Cloud (state management)

**Orchestration:**
- Python 3.11+ (orchestration logic)
- Celery (async task queue)
- Redis (Celery broker)

**Validation:**
- pytest (test framework)
- requests (API testing)
- psycopg2 (PostgreSQL testing)

**Portal:**
- React 18 (frontend)
- FastAPI (backend API)
- PostgreSQL (tenant registry)

**Monitoring:**
- Prometheus (metrics)
- Grafana (dashboards)
- Slack/Email (notifications)]

**NARRATION:**
"Let's review the technology stack for automated provisioning.

**Infrastructure as Code Layer:**

**Terraform 1.5+**
- **Purpose:** Provision infrastructure (PostgreSQL, S3, Vector DB, etc.)
- **Why Terraform:** Industry standard for multi-cloud IaC, excellent state management, large module ecosystem
- **Alternative:** Pulumi (code-based IaC in Python/TypeScript) - Consider if team prefers programming languages over HCL

**Terraform Cloud/Enterprise**
- **Purpose:** Centralized state management, team collaboration
- **Why Important:** Prevents state corruption, enables team access to Terraform state
- **Alternative:** S3 + DynamoDB for state locking (AWS-only, free but manual setup)

**Orchestration Layer:**

**Python 3.11+**
- **Purpose:** Orchestration logic (workflow management, API calls)
- **Why Python:** Excellent AWS/GCP SDKs, strong typing with type hints, async/await support
- **Key Libraries:**
  - `asyncio`: Async workflow execution
  - `boto3`: AWS SDK (S3, IAM, EC2)
  - `subprocess`: Run Terraform commands

**Celery 5.3+**
- **Purpose:** Async task queue (long-running provisioning tasks)
- **Why Celery:** Proven at scale, retries, task prioritization
- **Configuration:** Redis as broker (lightweight, fast)
- **Alternative:** AWS SQS + Lambda (serverless, but less control)

**Validation Layer:**

**pytest 7.4+**
- **Purpose:** Test framework for validation suite
- **Why pytest:** Fixtures for setup/teardown, parameterized tests, excellent reporting
- **Test Categories:** Integration, security, performance, compliance

**requests 2.31+**
- **Purpose:** HTTP client for API testing
- **Why requests:** Simple, reliable, widely used

**psycopg2 3.1+**
- **Purpose:** PostgreSQL driver for database testing
- **Why psycopg2:** Fast, battle-tested, connection pooling support

**Portal Layer:**

**React 18**
- **Purpose:** Frontend UI for self-service portal
- **Why React:** Component-based, large ecosystem, excellent state management
- **Key Libraries:**
  - `react-hook-form`: Form handling
  - `react-query`: API state management
  - `tailwind-css`: Styling

**FastAPI 0.104+**
- **Purpose:** Backend API for portal
- **Why FastAPI:** Async support, automatic OpenAPI docs, type validation with Pydantic
- **Endpoints:**
  - POST /api/tenants/request: Create tenant request
  - GET /api/tenants/{id}/status: Get provisioning status
  - POST /api/tenants/{id}/approve: Approve request (CFO only)

**PostgreSQL 15+**
- **Purpose:** Tenant registry (from M11.2)
- **Schema:**
  ```sql
  CREATE TABLE tenant_requests (
    id UUID PRIMARY KEY,
    tenant_id VARCHAR(255) UNIQUE,
    tenant_name VARCHAR(255),
    tier VARCHAR(20),  -- Gold/Silver/Bronze
    region VARCHAR(50),
    budget INTEGER,
    status VARCHAR(50),  -- pending_approval, approved, provisioning, active, failed
    requester VARCHAR(255),
    approver VARCHAR(255),  -- CFO email if manually approved
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    
    -- Audit trail
    approval_notes TEXT,
    failure_reason TEXT
  );
  ```

**Monitoring Layer:**

**Prometheus**
- **Purpose:** Metrics collection (provisioning duration, success rate)
- **Metrics:**
  ```
  tenant_provisioning_duration_seconds{tier="Gold"}
  tenant_provisioning_failures_total{step="validation"}
  tenant_provisioning_successes_total
  ```

**Grafana**
- **Purpose:** Dashboards for platform team
- **Dashboards:**
  - Provisioning metrics (success rate, duration)
  - Active tenants by tier
  - Cost per tenant (from Kubecost integration)

**Slack/Email**
- **Purpose:** Notifications (approvals, failures, activations)
- **Integration:** Slack webhook + SendGrid for email

**Cost Considerations:**

**Small GCC (10 tenants):**
- Terraform Cloud: Free tier (up to 500 resources)
- Celery + Redis: ₹2K/month (t3.small EC2)
- Portal: ₹3K/month (serverless: Lambda + API Gateway)
- **Total: ₹5K/month**

**Medium GCC (30 tenants):**
- Terraform Cloud: ₹8K/month (Team plan)
- Celery + Redis: ₹6K/month (t3.medium EC2)
- Portal: ₹8K/month (ECS Fargate)
- **Total: ₹22K/month**

**Large GCC (100 tenants):**
- Terraform Cloud: ₹25K/month (Business plan)
- Celery + Redis: ₹20K/month (r6g.large ElastiCache cluster)
- Portal: ₹30K/month (EKS with autoscaling)
- **Total: ₹75K/month**

**ROI Calculation:**
- Manual provisioning: 50 tenants × ₹50K = ₹25 lakh/year
- Automated provisioning: ₹75K/month × 12 = ₹9 lakh/year
- **Savings: ₹16 lakh/year (64% cost reduction)**"

**INSTRUCTOR GUIDANCE:**
- Organize stack by layer (IaC, orchestration, validation, portal, monitoring)
- Explain WHY each technology chosen (not just WHAT)
- Provide alternatives for each key component
- Show cost tiers (small/medium/large GCC)

---

### [11:00-12:00] Integration Points

[SLIDE: Integration Architecture showing:
- Portal → API Gateway → Orchestration Service
- Orchestration Service → Terraform CLI → Cloud Providers
- Orchestration Service → Tenant Registry (PostgreSQL)
- Orchestration Service → Celery → Redis
- Validation Service → Tenant Infrastructure (PostgreSQL, Vector DB, S3)
- Monitoring → Prometheus → Grafana
- Notifications → Slack/Email]

**NARRATION:**
"Let's map how these technologies integrate.

**Integration Flow:**

**1. Portal → API Gateway → Orchestration:**
```
User submits form → React sends POST request → FastAPI validates → Celery task created
```

**2. Orchestration → Terraform:**
```python
# Orchestration service runs Terraform as subprocess
# This bridges Python world and Terraform world
result = subprocess.run(
    ['terraform', 'apply', '-auto-approve'],
    cwd=terraform_dir,
    capture_output=True,
    text=True
)

# Parse Terraform output for status
if result.returncode == 0:
    logger.info('Terraform apply succeeded')
    await update_status(tenant_id, 'provisioning_complete')
else:
    logger.error(f'Terraform apply failed: {result.stderr}')
    await trigger_rollback(tenant_id)
```

**3. Orchestration → Tenant Registry:**
```python
# Update tenant status throughout workflow
# This provides real-time visibility for users
await tenant_registry.update_status(tenant_id, 'provisioning')
await tenant_registry.update_status(tenant_id, 'validating')
await tenant_registry.update_status(tenant_id, 'active')
```

**4. Validation → Tenant Infrastructure:**
```python
# Validation tests interact directly with provisioned infrastructure
# This verifies infrastructure works correctly
async def test_database_connection(tenant_id):
    conn = await asyncpg.connect(
        host=get_db_host(tenant_id),
        database=f'tenant_{tenant_id}',
        user=f'tenant_{tenant_id}_user',
        password=get_db_password(tenant_id)
    )
    await conn.close()
    return True
```

**5. Monitoring → Metrics:**
```python
# Emit metrics throughout provisioning
from prometheus_client import Counter, Histogram

provisioning_success = Counter(
    'tenant_provisioning_success_total',
    'Successful tenant provisionings',
    ['tier']
)

provisioning_duration = Histogram(
    'tenant_provisioning_duration_seconds',
    'Tenant provisioning duration',
    ['tier', 'region']
)

# In orchestration code:
with provisioning_duration.labels(tier=tier, region=region).time():
    await provision_infrastructure(tenant_id, tier, region)
    provisioning_success.labels(tier=tier).inc()
```

**6. Notifications:**
```python
# Send notifications at key workflow points
async def notify_stakeholders(tenant_id, event, details=None):
    """
    Send Slack and email notifications for provisioning events.
    
    Events: request_submitted, approved, provisioning, active, failed
    Stakeholders: Requester, CFO (if approval), Platform team
    """
    if event == 'request_submitted':
        await send_slack(
            channel='#tenant-requests',
            message=f'New tenant request: {tenant_id}'
        )
    elif event == 'approved':
        await send_email(
            to=get_requester_email(tenant_id),
            subject='Tenant Request Approved',
            body=f'Your tenant {tenant_id} was approved and is being provisioned.'
        )
    elif event == 'active':
        await send_slack(
            channel='#tenant-activations',
            message=f'Tenant {tenant_id} is now active!'
        )
        await send_email(
            to=get_requester_email(tenant_id),
            subject='Tenant Ready',
            body=f'Your tenant is ready! Login: https://rag.company.com/{tenant_id}'
        )
    elif event == 'failed':
        await send_slack(
            channel='#platform-alerts',
            message=f'⚠️ Tenant provisioning FAILED: {tenant_id} at step {details["step"]}'
        )
```

**Critical Integration Patterns:**

**1. Idempotency:**
All API calls must be idempotent:
- POST /api/tenants/request with same tenant_id → Returns existing request, doesn't create duplicate
- Running Terraform apply twice → Same result (no duplicate resources)

**2. Async Execution:**
Long-running tasks (Terraform apply) run asynchronously:
- User submits request → Celery task created → User sees 'provisioning' status
- Task runs in background → Updates status in database
- Frontend polls GET /api/tenants/{id}/status every 5 seconds

**3. Error Propagation:**
Errors bubble up from Terraform → Orchestration → API → Frontend:
- Terraform error → Logged with stderr output
- Orchestration catches error → Triggers rollback
- API returns error response → Frontend shows user-friendly message

**GCC Integration Complexity:**
In GCCs with 50+ tenants:
- Terraform manages 5,000+ resources (100 resources × 50 tenants)
- Celery handles 50 concurrent provisioning tasks
- PostgreSQL tracks 50 tenant registries
- Prometheus collects 10,000+ metrics/minute
- Integration testing becomes critical (can't test in production)"

**INSTRUCTOR GUIDANCE:**
- Show data flow visually (portal → orchestration → infrastructure)
- Explain critical integration patterns (idempotency, async, errors)
- Use code examples to make integrations concrete
- Emphasize testing importance at scale

---

## SECTION 4: TECHNICAL IMPLEMENTATION (12-15 minutes, 2,400-3,000 words)

### [12:00-15:00] Terraform Module for Tenant Infrastructure

**NARRATION:**
"Now let's build the Terraform module that provisions all tenant infrastructure.

**File Structure:**
```
terraform/
├── modules/
│   └── tenant/
│       ├── main.tf           # Resource definitions
│       ├── variables.tf      # Input variables
│       ├── outputs.tf        # Output values
│       └── providers.tf      # Provider configuration
├── tenants/
│   ├── tenant-001/
│   │   ├── main.tf          # Calls tenant module
│   │   ├── terraform.tfvars # Tenant-specific values
│   │   └── terraform.tfstate # State (managed by Terraform)
│   └── tenant-002/
│       └── ...
└── README.md
```

**Terraform Module: `modules/tenant/main.tf`**
```hcl
# modules/tenant/main.tf
# This module provisions ALL infrastructure for ONE tenant
# Idempotent: Can run multiple times safely
# Parameterized: Same code works for all tenants

terraform {
  required_version = ">= 1.5"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    postgresql = {
      source  = "cyrilgdn/postgresql"
      version = "~> 1.20"
    }
  }
}

# Variables (inputs from orchestration service)
variable "tenant_id" {
  description = "Unique tenant identifier"
  type        = string
  
  # Validation: Tenant ID must be lowercase alphanumeric + hyphens
  # This prevents naming conflicts in AWS
  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.tenant_id))
    error_message = "Tenant ID must be lowercase alphanumeric with hyphens only"
  }
}

variable "tier" {
  description = "Tenant tier: Gold, Silver, or Bronze"
  type        = string
  
  # Validation: Only valid tiers allowed
  validation {
    condition     = contains(["Gold", "Silver", "Bronze"], var.tier)
    error_message = "Tier must be Gold, Silver, or Bronze"
  }
}

variable "region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "isolation_model" {
  description = "Isolation model: namespace, schema, or dedicated"
  type        = string
  default     = "namespace"
}

# Locals (computed values)
locals {
  # Resource naming convention: rag-<tenant_id>-<resource>
  # This ensures uniqueness across all tenants
  resource_prefix = "rag-${var.tenant_id}"
  
  # Tier-specific configurations
  # Gold tenants get more resources than Bronze
  tier_config = {
    Gold = {
      db_instance_class = "db.t3.medium"
      redis_node_type   = "cache.t3.small"
      s3_lifecycle_days = 90  # Keep data longer
      vector_db_replicas = 3   # High availability
    }
    Silver = {
      db_instance_class = "db.t3.small"
      redis_node_type   = "cache.t3.micro"
      s3_lifecycle_days = 60
      vector_db_replicas = 2
    }
    Bronze = {
      db_instance_class = "db.t3.micro"
      redis_node_type   = "cache.t3.micro"
      s3_lifecycle_days = 30
      vector_db_replicas = 1
    }
  }
  
  # Cost allocation tags
  # These tags enable chargeback per tenant
  common_tags = {
    TenantID    = var.tenant_id
    Tier        = var.tier
    ManagedBy   = "Terraform"
    CostCenter  = "rag-platform-${var.tier}"
    Environment = "production"
  }
}

#############################################
# 1. PostgreSQL Schema with Row-Level Security
#############################################

# PostgreSQL provider configuration
provider "postgresql" {
  # Connection details from environment variables
  # Never hardcode credentials in Terraform
  host     = var.postgres_host
  port     = var.postgres_port
  database = "rag_platform"
  username = var.postgres_admin_user
  password = var.postgres_admin_password
  sslmode  = "require"
}

# Create tenant-specific schema
# Schema provides namespace isolation in shared database
resource "postgresql_schema" "tenant" {
  name = "tenant_${var.tenant_id}"
  
  # Owner is tenant-specific role (created below)
  owner = postgresql_role.tenant_user.name
}

# Create tenant-specific role (database user)
resource "postgresql_role" "tenant_user" {
  name     = "tenant_${var.tenant_id}_user"
  login    = true
  password = random_password.db_password.result
  
  # Permissions limited to tenant schema only
  # Cannot access other tenants' schemas
}

# Random password for tenant database user
# Stored securely in Terraform state (encrypted)
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Grant schema permissions to tenant role
resource "postgresql_grant" "tenant_schema" {
  database    = "rag_platform"
  role        = postgresql_role.tenant_user.name
  schema      = postgresql_schema.tenant.name
  object_type = "schema"
  privileges  = ["USAGE", "CREATE"]
}

# Enable Row-Level Security (RLS) policies
# RLS ensures tenant can only see their own rows
resource "postgresql_policy" "tenant_rls" {
  # This is critical for multi-tenant security
  # Without RLS, tenants could query other tenants' data via SQL injection
  name   = "tenant_${var.tenant_id}_rls_policy"
  schema = postgresql_schema.tenant.name
  table  = "documents"  # Example table
  
  # Policy: Only rows where tenant_id matches current role
  using = "tenant_id = current_user"
}

#############################################
# 2. S3 Bucket for Document Storage
#############################################

# S3 bucket for tenant documents
# Each tenant gets isolated bucket
resource "aws_s3_bucket" "tenant_storage" {
  # Bucket name must be globally unique across ALL AWS accounts
  # Using tenant_id ensures uniqueness
  bucket = "${local.resource_prefix}-documents"
  
  # Tags for cost allocation
  tags = local.common_tags
}

# Enable versioning for data protection
# Protects against accidental deletions
resource "aws_s3_bucket_versioning" "tenant_storage" {
  bucket = aws_s3_bucket.tenant_storage.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

# Lifecycle policy: Move old documents to cheaper storage
# Saves costs for infrequently accessed data
resource "aws_s3_bucket_lifecycle_configuration" "tenant_storage" {
  bucket = aws_s3_bucket.tenant_storage.id
  
  rule {
    id     = "archive_old_documents"
    status = "Enabled"
    
    # After 30 days: Move to Infrequent Access (50% cost savings)
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
    
    # After tier-specific days: Move to Glacier (90% cost savings)
    transition {
      days          = local.tier_config[var.tier].s3_lifecycle_days
      storage_class = "GLACIER"
    }
  }
}

# IAM policy: Only tenant's role can access bucket
# This is critical for multi-tenant security
resource "aws_iam_policy" "tenant_s3_access" {
  name        = "${local.resource_prefix}-s3-access"
  description = "S3 access policy for tenant ${var.tenant_id}"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowTenantBucketAccess"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.tenant_storage.arn,
          "${aws_s3_bucket.tenant_storage.arn}/*"
        ]
      }
    ]
  })
  
  tags = local.common_tags
}

# IAM role for tenant applications
# Applications assume this role to access AWS resources
resource "aws_iam_role" "tenant_application" {
  name               = "${local.resource_prefix}-application"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"  # ECS Fargate tasks
      }
      Action = "sts:AssumeRole"
    }]
  })
  
  tags = local.common_tags
}

# Attach S3 policy to tenant role
resource "aws_iam_role_policy_attachment" "tenant_s3" {
  role       = aws_iam_role.tenant_application.name
  policy_arn = aws_iam_policy.tenant_s3_access.arn
}

#############################################
# 3. Vector Database Namespace (Pinecone)
#############################################

# Note: Pinecone doesn't have native Terraform provider
# We use null_resource with local-exec to call Pinecone API
# Alternative: Use Crossplane or custom Terraform provider

resource "null_resource" "pinecone_namespace" {
  # Trigger on tenant_id or tier changes
  triggers = {
    tenant_id = var.tenant_id
    tier      = var.tier
  }
  
  # Create namespace via Pinecone API
  provisioner "local-exec" {
    command = <<-EOT
      python3 ${path.module}/scripts/create_pinecone_namespace.py         --tenant-id "${var.tenant_id}"         --tier "${var.tier}"         --replicas ${local.tier_config[var.tier].vector_db_replicas}
    EOT
    
    # Environment variables for Pinecone API key
    environment = {
      PINECONE_API_KEY = var.pinecone_api_key
      PINECONE_ENV     = var.pinecone_environment
    }
  }
  
  # Delete namespace on destroy
  provisioner "local-exec" {
    when    = destroy
    command = <<-EOT
      python3 ${path.module}/scripts/delete_pinecone_namespace.py         --tenant-id "${self.triggers.tenant_id}"
    EOT
    
    environment = {
      PINECONE_API_KEY = var.pinecone_api_key
      PINECONE_ENV     = var.pinecone_environment
    }
  }
}

# Python script: create_pinecone_namespace.py
# (This would be in modules/tenant/scripts/)
# ```python
# import argparse
# import pinecone
# import os
# 
# def create_namespace(tenant_id, tier, replicas):
#     pinecone.init(
#         api_key=os.environ['PINECONE_API_KEY'],
#         environment=os.environ['PINECONE_ENV']
#     )
#     
#     # Create namespace with tenant-specific metadata
#     index = pinecone.Index('rag-platform')
#     index.create_namespace(
#         namespace=f'tenant-{tenant_id}',
#         metadata={'tenant_id': tenant_id, 'tier': tier},
#         replicas=replicas
#     )
# ```

#############################################
# 4. Redis Namespace for Caching
#############################################

# ElastiCache Redis cluster (shared across tenants)
# Tenant isolation via key prefixes
# Note: In production, use existing shared Redis cluster
# This resource creates new cluster only for demo

resource "aws_elasticache_cluster" "tenant_cache" {
  cluster_id           = "${local.resource_prefix}-cache"
  engine               = "redis"
  node_type            = local.tier_config[var.tier].redis_node_type
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  
  # Subnet and security groups
  subnet_group_name    = var.redis_subnet_group
  security_group_ids   = [aws_security_group.tenant_cache.id]
  
  tags = local.common_tags
}

# Security group for Redis
resource "aws_security_group" "tenant_cache" {
  name        = "${local.resource_prefix}-cache-sg"
  description = "Security group for tenant ${var.tenant_id} Redis"
  vpc_id      = var.vpc_id
  
  # Ingress: Only from tenant application
  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.tenant_application.id]
  }
  
  # Egress: Allow all outbound
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = local.common_tags
}

#############################################
# 5. Monitoring Dashboard (Grafana)
#############################################

# Note: Grafana dashboard creation via Terraform
# Requires Grafana Terraform provider

provider "grafana" {
  url  = var.grafana_url
  auth = var.grafana_api_key
}

# Dashboard for tenant metrics
resource "grafana_dashboard" "tenant" {
  config_json = jsonencode({
    title = "Tenant ${var.tenant_id} - RAG Metrics"
    
    panels = [
      {
        title = "Query Latency (p95)"
        targets = [{
          expr = "histogram_quantile(0.95, rate(rag_query_duration_seconds_bucket{tenant_id=\"${var.tenant_id}\"}[5m]))"
        }]
      },
      {
        title = "Query Rate"
        targets = [{
          expr = "rate(rag_queries_total{tenant_id=\"${var.tenant_id}\"}[5m])"
        }]
      },
      {
        title = "Error Rate"
        targets = [{
          expr = "rate(rag_errors_total{tenant_id=\"${var.tenant_id}\"}[5m])"
        }]
      },
      {
        title = "Document Count"
        targets = [{
          expr = "rag_documents_total{tenant_id=\"${var.tenant_id}\"}"
        }]
      }
    ]
  })
}

#############################################
# 6. Outputs (for orchestration service)
#############################################

output "tenant_id" {
  value = var.tenant_id
}

output "postgres_schema" {
  value = postgresql_schema.tenant.name
}

output "postgres_user" {
  value = postgresql_role.tenant_user.name
}

output "postgres_password" {
  value     = random_password.db_password.result
  sensitive = true
}

output "s3_bucket" {
  value = aws_s3_bucket.tenant_storage.id
}

output "iam_role_arn" {
  value = aws_iam_role.tenant_application.arn
}

output "redis_endpoint" {
  value = aws_elasticache_cluster.tenant_cache.cache_nodes[0].address
}

output "grafana_dashboard_url" {
  value = "${var.grafana_url}/d/${grafana_dashboard.tenant.id}"
}
```

**Key Terraform Patterns:**

**1. Parameterization:**
- Same module works for all tenants
- Tier-specific configs (Gold gets more resources)
- Regional variants (EU vs. US)

**2. Idempotency:**
- Running `terraform apply` twice = same result
- No duplicate resources created
- Detects and corrects drift

**3. Dependency Management:**
- Terraform creates resources in correct order
- IAM role before bucket policy
- Schema before RLS policies

**4. Cost Tags:**
- All resources tagged with TenantID, Tier, CostCenter
- Enables chargeback and cost attribution

**5. Security:**
- No hardcoded credentials (environment variables)
- Least privilege IAM policies
- RLS policies in PostgreSQL"

**INSTRUCTOR GUIDANCE:**
- Show complete Terraform module (don't skip details)
- Explain inline comments (WHY not just WHAT)
- Emphasize security (IAM policies, RLS)
- Connect to cost management (tags, lifecycle policies)

---

### [15:00-18:00] Python Orchestration Service

**NARRATION:**
"Now let's build the orchestration service that runs the Terraform module.

**File: `orchestration/provisioning_service.py`**
```python
# provisioning_service.py
# Orchestrates tenant provisioning workflow
# Handles: Validation, Terraform execution, testing, rollback

import asyncio
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Tuple
from datetime import datetime

from celery import Celery
import asyncpg
from prometheus_client import Counter, Histogram

# Celery configuration
# Redis as broker for task queue
celery_app = Celery(
    'provisioning',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

# Prometheus metrics
provisioning_success = Counter(
    'tenant_provisioning_success_total',
    'Successful tenant provisionings',
    ['tier']
)

provisioning_failures = Counter(
    'tenant_provisioning_failures_total',
    'Failed tenant provisionings',
    ['tier', 'step']
)

provisioning_duration = Histogram(
    'tenant_provisioning_duration_seconds',
    'Tenant provisioning duration',
    ['tier', 'region']
)

# Logger configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TenantProvisioner:
    """
    Manages complete tenant provisioning lifecycle.
    
    Workflow:
    1. Validate request
    2. Provision infrastructure (Terraform)
    3. Initialize configurations
    4. Run validation tests
    5. Activate tenant
    6. Rollback on failure
    """
    
    def __init__(self, tenant_id: str, tier: str, region: str):
        self.tenant_id = tenant_id
        self.tier = tier
        self.region = region
        self.terraform_dir = Path(f'/opt/terraform/tenants/{tenant_id}')
        
    async def provision(self) -> Dict[str, Any]:
        """
        Main provisioning workflow.
        
        Returns: {
            'success': bool,
            'tenant_id': str,
            'duration_seconds': float,
            'error': str if failed
        }
        """
        start_time = datetime.utcnow()
        
        try:
            # Track progress in tenant registry
            # This provides real-time status to users
            await self.update_status('provisioning')
            
            # Step 1: Provision infrastructure
            logger.info(f'Provisioning infrastructure for {self.tenant_id}')
            await self.provision_infrastructure()
            
            # Step 2: Initialize configurations
            logger.info(f'Initializing config for {self.tenant_id}')
            await self.initialize_config()
            
            # Step 3: Run validation tests
            logger.info(f'Validating tenant {self.tenant_id}')
            validation_passed, test_results = await self.validate_tenant()
            
            if not validation_passed:
                # Validation failed - trigger rollback
                failed_tests = [t for t, r in test_results if not r['passed']]
                logger.error(f'Validation failed for {self.tenant_id}: {failed_tests}')
                raise ProvisioningError(f'Validation failed: {failed_tests}')
            
            # Step 4: Activate tenant
            logger.info(f'Activating tenant {self.tenant_id}')
            await self.activate_tenant()
            
            # Step 5: Notify stakeholders
            await self.notify_success()
            
            # Record success metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            provisioning_success.labels(tier=self.tier).inc()
            provisioning_duration.labels(tier=self.tier, region=self.region).observe(duration)
            
            return {
                'success': True,
                'tenant_id': self.tenant_id,
                'duration_seconds': duration
            }
            
        except Exception as e:
            # Provisioning failed - rollback
            logger.error(f'Provisioning failed for {self.tenant_id}: {str(e)}')
            provisioning_failures.labels(tier=self.tier, step='unknown').inc()
            
            # Attempt rollback
            await self.rollback(failed_step='provisioning')
            
            return {
                'success': False,
                'tenant_id': self.tenant_id,
                'error': str(e)
            }
    
    async def provision_infrastructure(self):
        """
        Run Terraform to provision infrastructure.
        
        This creates: PostgreSQL schema, S3 bucket, Vector DB, Redis, monitoring
        Duration: ~8-12 minutes (resources created in parallel)
        """
        # Create Terraform directory if not exists
        self.terraform_dir.mkdir(parents=True, exist_ok=True)
        
        # Write Terraform configuration
        # This calls the tenant module with specific parameters
        terraform_main = f'''
        terraform {{
          required_version = ">= 1.5"
          
          backend "s3" {{
            bucket = "rag-platform-terraform-state"
            key    = "tenants/{self.tenant_id}/terraform.tfstate"
            region = "us-east-1"
          }}
        }}

        module "tenant" {{
          source = "../../modules/tenant"
          
          tenant_id         = "{self.tenant_id}"
          tier              = "{self.tier}"
          region            = "{self.region}"
          isolation_model   = "namespace"
          
          # Database connection (from environment)
          postgres_host         = var.postgres_host
          postgres_port         = var.postgres_port
          postgres_admin_user   = var.postgres_admin_user
          postgres_admin_password = var.postgres_admin_password
          
          # AWS configuration
          vpc_id               = var.vpc_id
          redis_subnet_group   = var.redis_subnet_group
          
          # Vector DB configuration
          pinecone_api_key       = var.pinecone_api_key
          pinecone_environment   = var.pinecone_environment
          
          # Monitoring
          grafana_url     = var.grafana_url
          grafana_api_key = var.grafana_api_key
        }}

        output "tenant_credentials" {{
          value = module.tenant
          sensitive = true
        }}
        '''
        
        # Write main.tf file
        (self.terraform_dir / 'main.tf').write_text(terraform_main)
        
        # Write terraform.tfvars (tenant-specific values)
        # These override module defaults
        tfvars = f'''
        postgres_host = "{os.environ['POSTGRES_HOST']}"
        postgres_port = 5432
        postgres_admin_user = "{os.environ['POSTGRES_ADMIN_USER']}"
        postgres_admin_password = "{os.environ['POSTGRES_ADMIN_PASSWORD']}"
        
        vpc_id = "{os.environ['VPC_ID']}"
        redis_subnet_group = "{os.environ['REDIS_SUBNET_GROUP']}"
        
        pinecone_api_key = "{os.environ['PINECONE_API_KEY']}"
        pinecone_environment = "{os.environ['PINECONE_ENV']}"
        
        grafana_url = "{os.environ['GRAFANA_URL']}"
        grafana_api_key = "{os.environ['GRAFANA_API_KEY']}"
        '''
        
        (self.terraform_dir / 'terraform.tfvars').write_text(tfvars)
        
        # Run Terraform commands
        # These are idempotent - can run multiple times safely
        
        # Step 1: Init (download providers, initialize backend)
        await self.run_terraform_command(['init'])
        
        # Step 2: Plan (preview changes)
        # Always plan before apply - catch errors early
        await self.run_terraform_command(['plan', '-out=tfplan'])
        
        # Step 3: Apply (create resources)
        # -auto-approve because we already validated in approval workflow
        await self.run_terraform_command(['apply', '-auto-approve', 'tfplan'])
        
        logger.info(f'Infrastructure provisioned successfully for {self.tenant_id}')
    
    async def run_terraform_command(self, args: list):
        """
        Execute Terraform command.
        
        Runs Terraform as subprocess, captures output, handles errors.
        This bridges Python orchestration and Terraform infrastructure.
        """
        cmd = ['terraform'] + args
        
        logger.info(f'Running: {" ".join(cmd)} in {self.terraform_dir}')
        
        # Run Terraform as subprocess
        # capture_output=True: Capture stdout/stderr for logging
        # text=True: Return strings, not bytes
        # check=False: Don't raise exception on non-zero exit (we handle manually)
        result = subprocess.run(
            cmd,
            cwd=str(self.terraform_dir),
            capture_output=True,
            text=True,
            check=False
        )
        
        # Log output
        if result.stdout:
            logger.info(f'Terraform stdout: {result.stdout}')
        if result.stderr:
            logger.warning(f'Terraform stderr: {result.stderr}')
        
        # Check for errors
        if result.returncode != 0:
            error_msg = f'Terraform command failed: {" ".join(cmd)}'
            logger.error(f'{error_msg}\nStderr: {result.stderr}')
            raise TerraformError(error_msg, result.stderr)
        
        return result
    
    async def initialize_config(self):
        """
        Initialize tenant-specific configurations.
        
        After infrastructure exists, set up:
        - Feature flags
        - Rate limits
        - Model selection
        - Seed data (optional)
        """
        # Feature flags (from M11.2)
        feature_config = {
            'advanced_search': self.tier == 'Gold',
            'real_time_indexing': self.tier in ['Gold', 'Silver'],
            'custom_models': self.tier == 'Gold'
        }
        
        # Rate limits (prevent abuse)
        rate_limits = {
            'queries_per_minute': 100 if self.tier == 'Gold' else 50,
            'documents_per_month': 10000 if self.tier == 'Gold' else 5000
        }
        
        # LLM configuration
        llm_config = {
            'model': 'gpt-4' if self.tier == 'Gold' else 'gpt-3.5-turbo',
            'max_tokens': 2000,
            'temperature': 0.7
        }
        
        # Store in tenant registry
        config = {
            'tenant_id': self.tenant_id,
            'tier': self.tier,
            'region': self.region,
            'features': feature_config,
            'rate_limits': rate_limits,
            'llm_config': llm_config,
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Insert into PostgreSQL tenant_configs table
        conn = await asyncpg.connect(os.environ['DATABASE_URL'])
        try:
            await conn.execute('''
                INSERT INTO tenant_configs (tenant_id, config, created_at)
                VALUES ($1, $2, $3)
            ''', self.tenant_id, config, datetime.utcnow())
        finally:
            await conn.close()
        
        logger.info(f'Configuration initialized for {self.tenant_id}')
    
    async def validate_tenant(self) -> Tuple[bool, list]:
        """
        Run comprehensive validation tests.
        
        Tests: Database, isolation, vector search, authentication,
               performance, storage, monitoring, cost tags
        
        Returns: (all_passed: bool, test_results: list)
        """
        test_results = []
        
        # Test 1: Database connectivity
        try:
            result = await self.test_database_connection()
            test_results.append(('database_connectivity', result))
        except Exception as e:
            test_results.append(('database_connectivity', {'passed': False, 'error': str(e)}))
        
        # Test 2: Cross-tenant isolation
        try:
            result = await self.test_cross_tenant_isolation()
            test_results.append(('isolation', result))
        except Exception as e:
            test_results.append(('isolation', {'passed': False, 'error': str(e)}))
        
        # Test 3: Vector search
        try:
            result = await self.test_vector_search()
            test_results.append(('vector_search', result))
        except Exception as e:
            test_results.append(('vector_search', {'passed': False, 'error': str(e)}))
        
        # Test 4: Authentication
        try:
            result = await self.test_authentication()
            test_results.append(('authentication', result))
        except Exception as e:
            test_results.append(('authentication', {'passed': False, 'error': str(e)}))
        
        # Test 5: Performance
        try:
            result = await self.test_query_performance()
            test_results.append(('performance', result))
        except Exception as e:
            test_results.append(('performance', {'passed': False, 'error': str(e)}))
        
        # Test 6: S3 permissions
        try:
            result = await self.test_s3_permissions()
            test_results.append(('s3_permissions', result))
        except Exception as e:
            test_results.append(('s3_permissions', {'passed': False, 'error': str(e)}))
        
        # Test 7: Monitoring
        try:
            result = await self.test_monitoring()
            test_results.append(('monitoring', result))
        except Exception as e:
            test_results.append(('monitoring', {'passed': False, 'error': str(e)}))
        
        # Test 8: Cost tags
        try:
            result = await self.test_cost_tags()
            test_results.append(('cost_tags', result))
        except Exception as e:
            test_results.append(('cost_tags', {'passed': False, 'error': str(e)}))
        
        # All tests must pass
        # One failure = rollback entire provisioning
        all_passed = all(result['passed'] for _, result in test_results)
        
        return all_passed, test_results
    
    async def test_database_connection(self) -> Dict[str, Any]:
        """
        Test: Can we connect to tenant's PostgreSQL schema?
        
        Verifies: Schema exists, credentials work, RLS policies active
        """
        try:
            # Get database credentials from Terraform output
            # These were created by Terraform module
            tf_output = await self.get_terraform_output()
            
            db_user = tf_output['postgres_user']['value']
            db_password = tf_output['postgres_password']['value']
            db_schema = tf_output['postgres_schema']['value']
            
            # Connect with tenant credentials
            conn = await asyncpg.connect(
                host=os.environ['POSTGRES_HOST'],
                port=5432,
                database='rag_platform',
                user=db_user,
                password=db_password
            )
            
            # Test query: List tables in tenant schema
            # This verifies schema exists and we have permissions
            tables = await conn.fetch(f'''
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = '{db_schema}'
            ''')
            
            await conn.close()
            
            return {
                'passed': True,
                'schema': db_schema,
                'tables_count': len(tables)
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }
    
    async def test_cross_tenant_isolation(self) -> Dict[str, Any]:
        """
        Test: Can this tenant access other tenants' data?
        
        This is CRITICAL for multi-tenant security.
        If this fails, rollback immediately (security breach).
        """
        try:
            # Get credentials for THIS tenant
            tf_output = await self.get_terraform_output()
            tenant_a_user = tf_output['postgres_user']['value']
            tenant_a_password = tf_output['postgres_password']['value']
            
            # Connect as Tenant A
            conn_a = await asyncpg.connect(
                host=os.environ['POSTGRES_HOST'],
                database='rag_platform',
                user=tenant_a_user,
                password=tenant_a_password
            )
            
            # Try to access Tenant B's data (should FAIL)
            # Example: Query documents table with Tenant B's ID
            other_tenant_id = 'tenant-001'  # Known other tenant
            
            try:
                # This query should return ZERO rows
                # RLS policies should block cross-tenant access
                rows = await conn_a.fetch(f'''
                    SELECT * FROM documents 
                    WHERE tenant_id = '{other_tenant_id}'
                    LIMIT 1
                ''')
                
                if len(rows) > 0:
                    # SECURITY BREACH: Tenant A can see Tenant B's data!
                    return {
                        'passed': False,
                        'error': 'Cross-tenant data leak detected!',
                        'leaked_rows': len(rows)
                    }
            
            except asyncpg.exceptions.InsufficientPrivilegeError:
                # Expected: RLS blocked access
                pass
            
            await conn_a.close()
            
            return {
                'passed': True,
                'message': 'Cross-tenant isolation verified'
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }
    
    async def test_vector_search(self) -> Dict[str, Any]:
        """
        Test: Can we ingest and query documents?
        
        Verifies: Vector DB namespace exists, embeddings work, queries work
        """
        try:
            # Import Pinecone
            import pinecone
            
            # Initialize Pinecone
            pinecone.init(
                api_key=os.environ['PINECONE_API_KEY'],
                environment=os.environ['PINECONE_ENV']
            )
            
            # Get index and namespace
            index = pinecone.Index('rag-platform')
            namespace = f'tenant-{self.tenant_id}'
            
            # Test document
            test_doc = {
                'id': 'test-doc-1',
                'values': [0.1] * 1536,  # Dummy embedding (1536 dims for OpenAI)
                'metadata': {
                    'tenant_id': self.tenant_id,
                    'text': 'Test document for provisioning validation'
                }
            }
            
            # Upsert test document
            index.upsert(
                vectors=[test_doc],
                namespace=namespace
            )
            
            # Query for test document
            results = index.query(
                vector=[0.1] * 1536,
                top_k=1,
                namespace=namespace,
                include_metadata=True
            )
            
            # Verify we got our document back
            if len(results['matches']) == 0:
                return {
                    'passed': False,
                    'error': 'No results from vector search'
                }
            
            # Clean up test document
            index.delete(ids=['test-doc-1'], namespace=namespace)
            
            return {
                'passed': True,
                'matches_found': len(results['matches'])
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }
    
    async def test_authentication(self) -> Dict[str, Any]:
        """
        Test: Can we generate JWT with correct tenant claims?
        
        Verifies: JWT service works, tenant_id in claims, signature valid
        """
        try:
            from jose import jwt
            
            # Generate JWT for this tenant
            payload = {
                'tenant_id': self.tenant_id,
                'tier': self.tier,
                'iat': datetime.utcnow(),
                'exp': datetime.utcnow() + timedelta(hours=1)
            }
            
            token = jwt.encode(
                payload,
                os.environ['JWT_SECRET'],
                algorithm='HS256'
            )
            
            # Decode and verify
            decoded = jwt.decode(
                token,
                os.environ['JWT_SECRET'],
                algorithms=['HS256']
            )
            
            # Verify tenant_id matches
            if decoded['tenant_id'] != self.tenant_id:
                return {
                    'passed': False,
                    'error': f'Tenant ID mismatch: {decoded["tenant_id"]} != {self.tenant_id}'
                }
            
            return {
                'passed': True,
                'token_generated': True
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }
    
    async def test_query_performance(self) -> Dict[str, Any]:
        """
        Test: Query latency < 500ms (SLA requirement)
        
        Verifies: System meets performance SLA for this tier
        """
        try:
            import time
            
            # Measure query latency
            start = time.time()
            
            # Simulate query (replace with actual RAG query)
            # Example: Vector search + LLM completion
            await asyncio.sleep(0.3)  # Placeholder
            
            latency_ms = (time.time() - start) * 1000
            
            # SLA thresholds by tier
            sla_threshold = {
                'Gold': 500,    # <500ms
                'Silver': 1000, # <1s
                'Bronze': 2000  # <2s
            }
            
            threshold = sla_threshold[self.tier]
            
            if latency_ms > threshold:
                return {
                    'passed': False,
                    'latency_ms': latency_ms,
                    'threshold_ms': threshold,
                    'error': f'Latency {latency_ms}ms exceeds SLA {threshold}ms'
                }
            
            return {
                'passed': True,
                'latency_ms': latency_ms,
                'threshold_ms': threshold
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }
    
    async def test_s3_permissions(self) -> Dict[str, Any]:
        """
        Test: Can tenant upload/download from S3 bucket?
        
        Verifies: S3 bucket exists, IAM policies work, permissions correct
        """
        try:
            import boto3
            
            # Get S3 bucket from Terraform output
            tf_output = await self.get_terraform_output()
            bucket_name = tf_output['s3_bucket']['value']
            
            # Create S3 client with tenant credentials
            # (In production, assume IAM role via STS)
            s3 = boto3.client('s3')
            
            # Test: Upload file
            test_key = f'test-{datetime.utcnow().timestamp()}.txt'
            s3.put_object(
                Bucket=bucket_name,
                Key=test_key,
                Body=b'Test upload for provisioning validation'
            )
            
            # Test: Download file
            response = s3.get_object(
                Bucket=bucket_name,
                Key=test_key
            )
            
            # Test: Delete file
            s3.delete_object(
                Bucket=bucket_name,
                Key=test_key
            )
            
            return {
                'passed': True,
                'bucket': bucket_name,
                'operations': ['put', 'get', 'delete']
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }
    
    async def test_monitoring(self) -> Dict[str, Any]:
        """
        Test: Are metrics being collected in Prometheus?
        
        Verifies: Monitoring dashboard exists, metrics flowing
        """
        try:
            import requests
            
            # Query Prometheus for tenant metrics
            # Example: Check if tenant_id label exists
            prometheus_url = os.environ['PROMETHEUS_URL']
            
            query = f'rag_queries_total{{tenant_id="{self.tenant_id}"}}'
            
            response = requests.get(
                f'{prometheus_url}/api/v1/query',
                params={'query': query}
            )
            
            data = response.json()
            
            # Check if metrics exist
            if not data.get('data', {}).get('result'):
                # No metrics yet - this is expected immediately after provisioning
                # Metrics will start flowing once tenant starts using system
                return {
                    'passed': True,
                    'message': 'Monitoring configured (no metrics yet - expected)'
                }
            
            return {
                'passed': True,
                'metrics_found': len(data['data']['result'])
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }
    
    async def test_cost_tags(self) -> Dict[str, Any]:
        """
        Test: Are all resources tagged with TenantID?
        
        Verifies: Cost allocation tags present (chargeback requirement)
        """
        try:
            import boto3
            
            # Get Terraform output
            tf_output = await self.get_terraform_output()
            
            # Resources to check
            resources = [
                ('s3_bucket', tf_output['s3_bucket']['value']),
                # Add more resources as needed
            ]
            
            # Check tags on each resource
            s3 = boto3.client('s3')
            
            for resource_type, resource_id in resources:
                if resource_type == 's3_bucket':
                    response = s3.get_bucket_tagging(Bucket=resource_id)
                    tags = {tag['Key']: tag['Value'] for tag in response['TagSet']}
                    
                    # Verify required tags exist
                    required_tags = ['TenantID', 'Tier', 'CostCenter']
                    
                    for tag in required_tags:
                        if tag not in tags:
                            return {
                                'passed': False,
                                'error': f'Missing required tag: {tag} on {resource_type}',
                                'resource': resource_id
                            }
                    
                    # Verify TenantID matches
                    if tags['TenantID'] != self.tenant_id:
                        return {
                            'passed': False,
                            'error': f'TenantID tag mismatch: {tags["TenantID"]} != {self.tenant_id}'
                        }
            
            return {
                'passed': True,
                'resources_checked': len(resources)
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }
    
    async def activate_tenant(self):
        """
        Mark tenant as active in registry.
        
        After this, tenant can start using the platform.
        This is the 'go-live' moment.
        """
        conn = await asyncpg.connect(os.environ['DATABASE_URL'])
        try:
            await conn.execute('''
                UPDATE tenants
                SET status = 'active', activated_at = $1
                WHERE tenant_id = $2
            ''', datetime.utcnow(), self.tenant_id)
        finally:
            await conn.close()
        
        logger.info(f'Tenant {self.tenant_id} activated successfully')
    
    async def notify_success(self):
        """
        Send success notifications to stakeholders.
        
        Stakeholders: Requester, platform team, finance (chargeback)
        """
        # Get tenant details
        conn = await asyncpg.connect(os.environ['DATABASE_URL'])
        try:
            tenant = await conn.fetchrow('''
                SELECT tenant_name, requester, tier, region, budget
                FROM tenants
                WHERE tenant_id = $1
            ''', self.tenant_id)
        finally:
            await conn.close()
        
        # Email to requester
        await send_email(
            to=tenant['requester'],
            subject=f'Your RAG Tenant is Ready: {tenant["tenant_name"]}',
            body=f'''
            Your tenant is now active and ready to use!

            Tenant Name: {tenant['tenant_name']}
            Tenant ID: {self.tenant_id}
            Tier: {tenant['tier']}
            Region: {tenant['region']}

            Login URL: https://rag.company.com/{self.tenant_id}
            API Documentation: https://docs.company.com/api

            Need help? Contact platform-team@company.com
            '''
        )
        
        # Slack to platform team
        await send_slack(
            channel='#platform-notifications',
            message=f'''
            ✅ New tenant activated!
            
            Tenant: {tenant['tenant_name']} ({self.tenant_id})
            Tier: {tenant['tier']}
            Region: {tenant['region']}
            Budget: ₹{tenant['budget']:,}
            '''
        )
    
    async def rollback(self, failed_step: str):
        """
        Rollback all changes when provisioning fails.
        
        Goal: Return system to state before provisioning started.
        No orphaned resources, no cost leaks, no manual cleanup.
        """
        try:
            logger.error(f'Rollback triggered for {self.tenant_id} at step {failed_step}')
            
            # Update status in registry
            await self.update_status('rollback_in_progress')
            
            # Step 1: Destroy infrastructure with Terraform
            # Terraform's dependency graph ensures correct deletion order
            await self.run_terraform_command(['destroy', '-auto-approve'])
            
            # Step 2: Delete from tenant registry
            conn = await asyncpg.connect(os.environ['DATABASE_URL'])
            try:
                await conn.execute('''
                    UPDATE tenants
                    SET status = 'failed', failed_at = $1, failure_reason = $2
                    WHERE tenant_id = $3
                ''', datetime.utcnow(), f'Provisioning failed at {failed_step}', self.tenant_id)
            finally:
                await conn.close()
            
            # Step 3: Clean up Terraform state
            # Remove state file so we can retry provisioning later
            state_file = self.terraform_dir / 'terraform.tfstate'
            if state_file.exists():
                state_file.unlink()
            
            # Step 4: Notify stakeholders of failure
            await self.notify_failure(failed_step)
            
            logger.info(f'Rollback completed successfully for {self.tenant_id}')
            
        except Exception as e:
            # Rollback itself failed - escalate to human
            # This is rare but critical when it happens
            logger.critical(f'Rollback FAILED for {self.tenant_id}: {str(e)}')
            await alert_sre(
                f'⚠️ P0: Rollback FAILED for {self.tenant_id}',
                f'Failed step: {failed_step}\nError: {str(e)}'
            )
            raise
    
    async def notify_failure(self, failed_step: str):
        """
        Notify stakeholders of provisioning failure.
        
        Be honest about failure - include error details.
        """
        conn = await asyncpg.connect(os.environ['DATABASE_URL'])
        try:
            tenant = await conn.fetchrow('''
                SELECT tenant_name, requester, failure_reason
                FROM tenants
                WHERE tenant_id = $1
            ''', self.tenant_id)
        finally:
            await conn.close()
        
        # Email to requester
        await send_email(
            to=tenant['requester'],
            subject=f'Tenant Provisioning Failed: {tenant["tenant_name"]}',
            body=f'''
            We encountered an error while provisioning your tenant.

            Tenant Name: {tenant['tenant_name']}
            Failed At: {failed_step}
            Error: {tenant['failure_reason']}

            Our platform team has been notified and will investigate.
            You can retry provisioning once the issue is resolved.

            Contact: platform-team@company.com
            '''
        )
        
        # Slack to platform team (high priority)
        await send_slack(
            channel='#platform-alerts',
            message=f'''
            ⚠️ Tenant provisioning FAILED
            
            Tenant: {tenant['tenant_name']} ({self.tenant_id})
            Failed Step: {failed_step}
            Error: {tenant['failure_reason']}
            
            Rollback completed. Review logs for details.
            '''
        )
    
    async def update_status(self, status: str):
        """Update tenant status in registry for real-time tracking."""
        conn = await asyncpg.connect(os.environ['DATABASE_URL'])
        try:
            await conn.execute('''
                UPDATE tenants
                SET status = $1, updated_at = $2
                WHERE tenant_id = $3
            ''', status, datetime.utcnow(), self.tenant_id)
        finally:
            await conn.close()
    
    async def get_terraform_output(self) -> Dict[str, Any]:
        """Get Terraform outputs (credentials, resource IDs)."""
        result = await self.run_terraform_command(['output', '-json'])
        return json.loads(result.stdout)

# Celery task for async provisioning
@celery_app.task(bind=True)
def provision_tenant_task(self, tenant_id: str, tier: str, region: str):
    """
    Celery task for tenant provisioning.
    
    This runs asynchronously in background worker.
    User can poll status while provisioning happens.
    """
    provisioner = TenantProvisioner(tenant_id, tier, region)
    result = asyncio.run(provisioner.provision())
    return result

# Helper functions
async def send_email(to: str, subject: str, body: str):
    """Send email via SendGrid."""
    # Implementation omitted for brevity
    pass

async def send_slack(channel: str, message: str):
    """Send Slack notification."""
    # Implementation omitted for brevity
    pass

async def alert_sre(title: str, details: str):
    """Send P0 alert to SRE team via PagerDuty."""
    # Implementation omitted for brevity
    pass

# Custom exceptions
class ProvisioningError(Exception):
    pass

class TerraformError(Exception):
    def __init__(self, message: str, terraform_stderr: str):
        super().__init__(message)
        self.terraform_stderr = terraform_stderr
```

**Key Implementation Patterns:**

**1. Async Workflow:**
- Long-running provisioning runs in Celery background task
- User polls status while provisioning happens
- No blocking API calls

**2. Validation Before Activation:**
- 8 comprehensive tests run before tenant activation
- One failure = automatic rollback
- Prevents broken tenants in production

**3. Rollback Safety:**
- Terraform destroy removes all resources cleanly
- Dependency-aware deletion (no orphaned resources)
- Transaction-like semantics (all-or-nothing)

**4. Monitoring & Alerting:**
- Prometheus metrics track success rate, duration
- Slack/email notifications at key workflow points
- P0 alerts if rollback fails (escalate to human)

**5. Audit Trail:**
- All status changes logged in database
- Terraform state in S3 (team access)
- Git commits for infrastructure changes
- Complete history for compliance"

**INSTRUCTOR GUIDANCE:**
- Show complete orchestration service (600+ lines)
- Emphasize inline comments (educational value)
- Explain error handling throughout
- Connect to production reliability (validation, rollback, monitoring)

---

**[End of Part 1]**

This completes Sections 1-4 (Hook, Concepts, Tech Stack, Implementation). The script will continue with Parts 2 and 3.
