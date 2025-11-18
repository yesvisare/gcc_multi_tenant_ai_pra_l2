# L3 M14.3: Tenant Lifecycle & Migrations

Zero-downtime tenant migrations, GDPR-compliant data deletion workflows, backup/restore services, and tenant cloning for multi-tenant RAG systems. This module implements production-grade orchestration across PostgreSQL, Redis, Pinecone, S3, and CloudWatch with sub-second rollback capability.

**Part of:** TechVoyageHub L3 Production RAG Engineering Track
**Prerequisites:** L3 M14.1 (Multi-Tenant Architecture), L3 M14.2 (Tenant Isolation & Security)
**SERVICE:** Infrastructure Orchestration (Multi-service: PostgreSQL, Redis, Celery, Pinecone, S3)
**Default Mode:** OFFLINE (runs without external dependencies for local development)

## What You'll Build

This module teaches you to build enterprise-grade tenant lifecycle management systems that handle:

- **Zero-downtime migrations** using blue-green deployment patterns with gradual traffic cutover
- **GDPR Article 17 compliance** with systematic deletion across 7+ systems and cryptographic certificates
- **Per-tenant backup/restore** with point-in-time recovery and cross-region replication
- **Tenant cloning** for staging/testing environments with data anonymization
- **Sub-second rollback** capability for failed migrations
- **Multi-system orchestration** coordinating PostgreSQL, Redis, Pinecone, S3, CloudWatch, and analytics

**Key Capabilities:**
- Blue-green migration with 6-phase orchestration (provision, sync, dual-write, catchup, cutover, validate)
- GDPR deletion verification across databases, caches, vector stores, object storage, logs, backups, and analytics
- Backup automation with configurable retention policies and disaster recovery
- Data consistency verification using multi-system checksums
- Legal hold checks preventing accidental deletion during litigation
- Cryptographically signed deletion certificates for compliance audit trails

**Success Criteria:**
- Migration duration: 6-8 hours (first attempt), improving to 3-4 hours with experience
- Rollback time: <60 seconds from detection to traffic restoration
- Data consistency: 100% checksum match across all systems
- GDPR deletion completeness: 0 residual records in verification scan
- Success rate: 98%+ after 3-5 initial migrations
- Cost efficiency: ₹50K-80K per migration (vs ₹10-20 lakh for parallel infrastructure)

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                   Tenant Lifecycle Orchestrator                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────┼─────────────────────┐
        ↓                     ↓                     ↓
┌───────────────┐   ┌──────────────────┐   ┌──────────────────┐
│  Blue-Green   │   │  GDPR Deletion   │   │ Backup/Restore/  │
│  Migration    │   │   Workflow       │   │     Clone        │
└───────────────┘   └──────────────────┘   └──────────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ↓
        ┌────────────────────────────────────────────┐
        │         Multi-System Coordination           │
        ├────────────────────────────────────────────┤
        │  PostgreSQL │ Redis │ Pinecone │ S3        │
        │  CloudWatch │ Backups │ Analytics          │
        └────────────────────────────────────────────┘
                              ↓
        ┌────────────────────────────────────────────┐
        │      Verification & Certificate Engine     │
        │  • Checksum validation                     │
        │  • Multi-system deletion verification      │
        │  • Cryptographic signing                   │
        │  • Legal hold checks                       │
        └────────────────────────────────────────────┘

Blue-Green Migration Flow:
1. Provision green environment (parallel infrastructure)
2. Full data sync (initial bulk transfer)
3. Enable dual-write mode (writes go to both blue and green)
4. Incremental catchup sync (close replication lag)
5. Gradual traffic cutover (10% → 25% → 50% → 100%)
6. Decommission blue environment (after stability validation)

GDPR Deletion Flow:
1. Validate request (check legal holds and retention exceptions)
2. Multi-system deletion (parallel workers across 7+ systems)
3. Verification scan (ensure complete erasure)
4. Log anonymization (where deletion impossible)
5. Certificate generation (cryptographically signed proof)
6. Backup exclusion (prevent restoration of deleted data)
```

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
# Edit .env - default OFFLINE=true (no infrastructure needed)
# To enable real infrastructure, set OFFLINE=false and configure services
```

### 4. Run Tests
```bash
# Windows PowerShell
$env:PYTHONPATH=$PWD; pytest -v tests/

# Or use script
./scripts/run_tests.ps1
```

### 5. Start API
```bash
# Windows PowerShell
$env:OFFLINE='True'; $env:PYTHONPATH=$PWD; uvicorn app:app --reload

# Or use script
./scripts/run_api.ps1
```

API will be available at http://localhost:8000 with interactive docs at http://localhost:8000/docs

### 6. Explore Notebook
```bash
jupyter lab notebooks/L3_M14_Operations_Governance.ipynb
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OFFLINE` | No | `true` | Run without external infrastructure (simulated operations) |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) |
| `POSTGRES_ENABLED` | No | `false` | Enable PostgreSQL tenant registry |
| `POSTGRES_HOST` | If enabled | `localhost` | PostgreSQL server hostname |
| `POSTGRES_PORT` | If enabled | `5432` | PostgreSQL server port |
| `POSTGRES_DB` | If enabled | `tenant_registry` | Database name |
| `POSTGRES_USER` | If enabled | `postgres` | Database username |
| `POSTGRES_PASSWORD` | If enabled | - | Database password |
| `REDIS_ENABLED` | No | `false` | Enable Redis distributed locks and caching |
| `REDIS_HOST` | If enabled | `localhost` | Redis server hostname |
| `REDIS_PORT` | If enabled | `6379` | Redis server port |
| `CELERY_ENABLED` | No | `false` | Enable Celery async task distribution |
| `CELERY_BROKER_URL` | If enabled | `redis://localhost:6379/0` | Celery message broker |
| `CELERY_RESULT_BACKEND` | If enabled | `redis://localhost:6379/0` | Celery result backend |
| `PINECONE_ENABLED` | No | `false` | Enable Pinecone vector database operations |
| `PINECONE_API_KEY` | If enabled | - | Pinecone API key |
| `PINECONE_ENVIRONMENT` | If enabled | - | Pinecone environment |
| `AWS_ENABLED` | No | `false` | Enable AWS S3 for backups and object storage |
| `AWS_ACCESS_KEY_ID` | If enabled | - | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | If enabled | - | AWS secret key |
| `AWS_REGION` | If enabled | `us-east-1` | AWS region |
| `AWS_S3_BUCKET` | If enabled | `tenant-backups` | S3 bucket for backups |

## Common Failures & Fixes

| Failure | Cause | Fix |
|---------|-------|-----|
| **Data Inconsistency** | Checksum mismatch between source and target after migration | Full re-sync with parallel workers. Increase sync workers from 4 to 16, extend sync window by 2x. Verify network throughput >1Gbps between environments. |
| **Rollback Failure** | Load balancer configuration drift prevents traffic recovery | Manual DNS update to source IP. Verify load balancer health checks are enabled. Test rollback in staging quarterly. Keep load balancer config in version control. |
| **Incomplete GDPR Deletion** | Residual data found in undocumented systems during verification | Multi-system verification scan across ALL data stores. Document every system storing tenant data. Run discovery scan: `grep -r tenant_id /var/log/*`. Add missing systems to deletion checklist. |
| **Migration Timeout** | High write rates (>10K writes/sec) outpace incremental sync | Scale parallel sync workers. Enable dual-write mode earlier. Increase sync frequency from 5min to 1min intervals. Consider maintenance window for write-heavy tenants. |
| **Backup Restoration Failure** | Schema version incompatibility between backup and current system | Schema migration before restore. Maintain schema version metadata in backups. Test restore compatibility monthly. Keep schema migration scripts in backup manifest. |
| **Traffic Cutover Spike** | Sudden 100% cutover causes target environment overload | Use gradual cutover stages (10% → 25% → 50% → 100%). Monitor CPU/memory at each stage. Wait 30-60s between stages for autoscaling. Have rollback playbook ready. |
| **Legal Hold Violation** | Deletion executed despite active court order | Pre-deletion legal hold check. Maintain legal_holds table in PostgreSQL. Require legal team approval for high-value tenants. Log all deletion requests with requestor identity. |
| **Cross-Region Sync Lag** | Network latency causes replication delays >5 minutes | Use AWS DataSync or Transfer Family for bulk data. Enable S3 Transfer Acceleration. Consider staged migration: sync data first, then cutover DNS. Monitor replication lag metrics. |
| **Dual-Write Conflict** | Concurrent writes to blue and green cause race conditions | Implement distributed locking with Redis. Use timestamp-based conflict resolution. Enable transaction logs for rollback. Test dual-write under load in staging. |
| **Certificate Generation Failure** | Verification incomplete but certificate requested | Block certificate generation until verification=100%. Require manual review if any system shows residual data. Store verification logs for audit. Retry verification before cert generation. |

## Decision Card

### When to Use Zero-Downtime Migration

**Use this approach when:**
- Tenant has strict SLA requirements with 0% acceptable downtime
- Revenue impact >₹1 lakh/hour of downtime
- Tenant tier is Platinum/Enterprise with premium support
- Migration window spans business hours or peak usage times
- Regulatory compliance requires continuous availability (financial services, healthcare)
- Previous migrations caused customer escalations or churn risk
- Multi-region deployment with gradual geographic rollout needed
- Testing new infrastructure version before full cutover (canary deployment)

**Do NOT use this approach when:**
- Tenant accepts scheduled maintenance windows (Bronze/Silver tiers)
- Off-peak migration window available (nights/weekends for B2B tenants)
- Same-region updates compatible with rolling Kubernetes deployment
- Budget constraints: development cost ₹40-60 lakh too high for ROI
- Small tenant with <10K queries/day (simple backup-restore is faster)
- Infrastructure change is backward-compatible (no data migration needed)
- First-time migration (20% rollback rate too risky - use maintenance window)

### Trade-offs

**Cost:**
- Development: ₹40-60 lakh one-time (orchestrator, verification, monitoring)
- Operational: ₹50K-80K per migration (parallel infrastructure for 6-8 hours)
- Staging testing: ₹10-15 lakh annually (quarterly rollback drills)
- Total 3-year TCO: ₹1.2-1.8 crore for 50 migrations/year

**Latency:**
- Migration duration: 6-8 hours (vs 2-3 hours maintenance window)
- Rollback time: <60 seconds (vs 2-4 hours full restore)
- Dual-write overhead: +5-10ms per write operation during cutover

**Complexity:**
- Lines of code: 5000+ (orchestration, verification, rollback logic)
- Systems coordinated: 7+ (PostgreSQL, Redis, Pinecone, S3, CloudWatch, etc.)
- Team expertise required: Senior DevOps + SRE + DBA
- Quarterly testing burden: Rollback drills, verification audits, schema compatibility tests

**Reliability:**
- Success rate: 98%+ after 3-5 initial migrations
- First-migration rollback rate: 15-20%
- Data consistency guarantee: 99.99%+ (checksum verification)
- GDPR deletion verification: Manual audit required for first 5 deletions

### Performance Metrics

| Metric | Target | Platinum | Gold | Bronze |
|--------|--------|----------|------|--------|
| Migration Duration | 6-8 hours | 4-6 hours | 8-12 hours | Maintenance window |
| Rollback Time | <60 seconds | <30 seconds | <2 minutes | <30 minutes |
| Data Consistency | 100% | 100% | 99.9% | 99% |
| Cost per Migration | ₹50K-80K | ₹80K-120K | ₹30K-50K | ₹5K-15K |

## Alternative Approaches

### 1. Maintenance Window Migration
**When:** Acceptable downtime, off-peak hours available
**Cost:** ₹2-5 lakh (vs ₹40-60 lakh for zero-downtime)
**Duration:** 2-3 hours total (vs 6-8 hours parallel infra)
**Downside:** Revenue loss during window, customer notification required

### 2. Rolling Kubernetes Updates
**When:** Same-region, backward-compatible changes
**Cost:** Minimal (native K8s feature)
**Duration:** 30-60 minutes
**Downside:** Only works for code/config updates, not data migrations

### 3. Hybrid Tiered Approach
**When:** Multiple tenant tiers with different SLAs
**Platinum:** Zero-downtime migration
**Gold:** Short maintenance window (1-2 hours)
**Bronze:** Extended maintenance window (4-8 hours)
**Cost:** Optimized per tier
**Downside:** Multiple migration strategies to maintain

## Troubleshooting

### Offline/Disabled Mode (Default)
By default, the module runs in **OFFLINE mode** where all infrastructure calls are simulated. This allows local development and testing without PostgreSQL, Redis, Celery, Pinecone, or AWS credentials.

**To enable real infrastructure:**
1. Set `OFFLINE=false` in `.env`
2. Configure service-specific variables (e.g., `POSTGRES_ENABLED=true`, `POSTGRES_PASSWORD=...`)
3. Ensure services are running and accessible
4. Restart the API server

**To test individual services:**
```bash
# Test PostgreSQL connection
$env:POSTGRES_ENABLED='True'; python -c "from config import CLIENTS; print(CLIENTS['postgres'])"

# Test Redis connection
$env:REDIS_ENABLED='True'; python -c "from config import CLIENTS; print(CLIENTS['redis'])"
```

### Import Errors
If you see `ModuleNotFoundError: No module named 'src.l3_m14_tenant_lifecycle'`, ensure:
```bash
# Windows PowerShell
$env:PYTHONPATH=$PWD

# Linux/Mac
export PYTHONPATH=$(pwd)
```

### Tests Failing
Run tests with verbose output and detailed assertions:
```bash
pytest -vv tests/ --tb=short
```

### API 500 Errors
Check logs for detailed error messages:
```bash
# In the terminal where uvicorn is running, look for:
# ERROR - Migration failed: ...
# ERROR - GDPR deletion failed: ...
```

Most errors in OFFLINE mode are expected (simulated failures for testing). In production mode with real infrastructure, check:
- Service connectivity (PostgreSQL, Redis, Pinecone, S3)
- API key validity
- Network firewall rules
- Schema compatibility

### Migration Consistency Issues
If verification shows checksum mismatches:
1. Run full re-sync with increased parallelism
2. Check network throughput between environments
3. Verify no writes bypassing dual-write mode
4. Review application logs for write errors
5. Consider extending sync window before cutover

### GDPR Deletion Incomplete
If verification finds residual data:
1. Run discovery scan: `grep -r tenant_id /var/log/* /backups/* /analytics/*`
2. Document all systems storing tenant data
3. Add missing systems to `GDPR_CONFIG.systems_to_delete`
4. Re-run deletion workflow
5. Manual verification for first 5 deletions (build confidence)

## Architecture Details

### Blue-Green Migration Pattern
Six-phase orchestration ensuring zero data loss:

1. **Provision:** Spin up green environment (Terraform/K8s)
2. **Full Sync:** Bulk data transfer (AWS DataSync for S3, pg_dump for PostgreSQL)
3. **Dual-Write:** Application writes to both blue and green
4. **Incremental Sync:** Close replication gap (catchup from transaction logs)
5. **Cutover:** Gradual traffic shift (10% → 25% → 50% → 100%)
6. **Decommission:** Destroy blue after 24-hour stability period

### GDPR Deletion Workflow
Six-phase compliance orchestration:

1. **Validation:** Check legal_holds table, retention policies
2. **Deletion:** Parallel workers across 7 systems (PostgreSQL, Redis, Pinecone, S3, CloudWatch, backups, analytics)
3. **Verification:** Multi-system scan for residual data
4. **Anonymization:** Logs where deletion is impossible (immutable audit trails)
5. **Certificate:** Cryptographic signing with SHA-256
6. **Backup Exclusion:** Add to exclusion list, scheduled purge

### Systems Coordinated

| System | Purpose | Deletion Method | Verification |
|--------|---------|-----------------|--------------|
| PostgreSQL | Tenant registry, metadata, deletion logs | `DELETE FROM tenants WHERE tenant_id='...'` | `SELECT COUNT(*) FROM tenants WHERE tenant_id='...'` |
| Redis | Distributed locks, session cache | `DEL tenant:{tenant_id}:*` | `KEYS tenant:{tenant_id}:*` |
| Pinecone | Vector embeddings | `delete(namespace=tenant_id)` | `query(namespace=tenant_id, top_k=1)` |
| S3 | Documents, backups | `s3.delete_objects(Prefix=tenant_id/)` | `s3.list_objects_v2(Prefix=tenant_id/)` |
| CloudWatch | Application logs | Log anonymization (PII masking) | Grep scan for tenant_id |
| Backups | Point-in-time snapshots | Add to exclusion list | Backup manifest check |
| Analytics | Event streams, dashboards | `DELETE FROM events WHERE tenant_id='...'` | Aggregation query verification |

## Next Module

**L3 M14.4: Operating Model & Governance**
Learn to build multi-GCC operating models with cost allocation, SLA management, incident response, and compliance frameworks for enterprise RAG systems.

---

## License

MIT License - Copyright (c) 2025 yesvisare

## Support

For issues and questions:
- GitHub Issues: https://github.com/yesvisare/gcc_multi_tenant_ai_pra_l2/issues
- Documentation: See `notebooks/L3_M14_Operations_Governance.ipynb` for interactive walkthrough

## Contributors

TechVoyageHub L3 Production RAG Engineering Track
