# L3 M14.2: Incident Management & Blast Radius

This module implements incident management with automatic blast radius containment for multi-tenant RAG systems, detecting failing tenants within 60 seconds and isolating them automatically using circuit breaker patterns.

**Part of:** TechVoyageHub L3 Production RAG Engineering Track
**Prerequisites:** M11-M14.1 (Multi-tenant fundamentals, monitoring)
**SERVICE:** PROMETHEUS (monitoring/metrics system)

## What You'll Build

A production-grade incident management system that prevents platform-wide outages by detecting and isolating failing tenants automatically.

**Key Capabilities:**
- **Blast radius detection within 60 seconds** - Continuous monitoring with 10-second polling
- **Circuit breaker isolation** - Automatic tenant isolation using three-state pattern (Closed/Open/Half-Open)
- **Incident priority framework** - P0/P1/P2 classification based on tenant tier and impact
- **Automated notifications** - PagerDuty, Slack, and email alerts
- **Blameless postmortem generation** - Five Whys analysis and action item tracking
- **Cost impact tracking** - Estimated financial impact per incident

**Success Criteria:**
- ✓ Failing tenant detected within 60 seconds
- ✓ Circuit breaker isolates tenant automatically (5 consecutive failures)
- ✓ Other 49 tenants remain operational
- ✓ P0 incidents trigger within 15-minute SLA
- ✓ Cost contained to single-tenant impact (₹15 lakh vs ₹5.5 crore platform outage)

## How It Works

```
Prometheus Monitoring → Blast Radius Detector → Circuit Breaker → Tenant Isolation
                              ↓                       ↓                  ↓
                     Error Rate Analysis    State Transitions    Notification System
                     (50% threshold)        (Closed/Open/Half)   (PagerDuty/Slack)
```

**Architecture:**
1. **BlastRadiusDetector** polls Prometheus every 10 seconds
2. Queries `rag_queries_total` and `rag_queries_errors` metrics over 5-minute window
3. Calculates error rate per tenant: `error_rate = errors / total`
4. If error_rate ≥ 50%, records failure in CircuitBreaker
5. After 5 consecutive failures, circuit breaker opens (tenant isolated)
6. Incident created with priority based on tenant tier
7. Notifications sent to ops team and tenant admins
8. After 60-second timeout, circuit breaker attempts recovery (Half-Open)
9. Successful requests close circuit breaker; failures reopen it

## Quick Start

### 1. Clone and Setup
```bash
git clone https://github.com/your-org/gcc_mt_m14_v2
cd gcc_mt_m14_v2
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env and configure Prometheus settings
```

**Required Configuration:**
```bash
PROMETHEUS_ENABLED=true
PROMETHEUS_URL=http://prometheus:9090
ERROR_THRESHOLD=0.50
CHECK_INTERVAL_SECONDS=10
```

**Optional Configuration:**
```bash
PAGERDUTY_ENABLED=true
PAGERDUTY_API_KEY=your_key
SLACK_ENABLED=true
SLACK_WEBHOOK_URL=your_webhook
```

### 4. Run Tests
```bash
# Windows PowerShell
$env:PYTHONPATH=$PWD; pytest -q

# Or use script
./scripts/run_tests.ps1
```

Expected output:
```
...........................  [100%]
27 passed in 2.1s
```

### 5. Start API
```bash
# Windows PowerShell
$env:PROMETHEUS_ENABLED='True'; $env:PYTHONPATH=$PWD; uvicorn app:app --reload

# Or use script
./scripts/run_api.ps1
```

Access API documentation: http://localhost:8000/docs

### 6. Explore Notebook
```bash
jupyter lab notebooks/L3_M14_Operations_Governance.ipynb
```

## API Usage Examples

### Configure Tenant Tier
```bash
curl -X POST http://localhost:8000/tenants/configure \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "tenant-A", "tier": "platinum"}'
```

### Check Tenant Health
```bash
curl http://localhost:8000/tenants/tenant-A/health
```

### Scan Blast Radius
```bash
curl -X POST http://localhost:8000/blast-radius/scan
```

### Create Incident
```bash
curl -X POST http://localhost:8000/incidents/create
```

### Generate Postmortem
```bash
curl http://localhost:8000/incidents/INC-20250118-120000/postmortem
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PROMETHEUS_ENABLED` | No | `false` | Enable Prometheus integration |
| `PROMETHEUS_URL` | If enabled | `http://prometheus:9090` | Prometheus server URL |
| `ERROR_THRESHOLD` | No | `0.50` | Error rate threshold (0.0-1.0) |
| `CHECK_INTERVAL_SECONDS` | No | `10` | Polling interval in seconds |
| `CHECK_WINDOW` | No | `5m` | Prometheus time window |
| `FAILURE_THRESHOLD` | No | `5` | Failures before circuit opens |
| `TIMEOUT_SECONDS` | No | `60` | Timeout before recovery attempt |
| `PAGERDUTY_ENABLED` | No | `false` | Enable PagerDuty notifications |
| `PAGERDUTY_API_KEY` | If PD enabled | - | PagerDuty API key |
| `SLACK_ENABLED` | No | `false` | Enable Slack notifications |
| `SLACK_WEBHOOK_URL` | If Slack enabled | - | Slack webhook URL |
| `OFFLINE` | No | `false` | Run in offline mode (notebook) |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |

## Common Failures & Fixes

Based on production experience with 50-tenant multi-tenant RAG systems:

| Failure | Cause | Impact | Fix |
|---------|-------|--------|-----|
| **Detection too slow (>60s)** | Polling interval too long | Platform-wide outage before isolation | Reduce CHECK_INTERVAL_SECONDS to 10 seconds |
| **Circuit breaker bypassed** | Error threshold too high | Failing tenant affects others | Lower ERROR_THRESHOLD to 0.30-0.50 |
| **False positives** | Failure threshold too low | Healthy tenants isolated unnecessarily | Increase FAILURE_THRESHOLD to 5-7 |
| **Recovery loops** | Timeout too short | Circuit thrashes between Open/Half-Open | Increase TIMEOUT_SECONDS to 60-120 |
| **Database connection pool exhaustion** | No per-tenant limits | Cascade failure to all tenants | Implement per-tenant connection limits |
| **Query timeout too long** | No query timeout configured | Slow queries block all tenants | Set query_timeout=30s per tenant |
| **Shared circuit breaker trips** | All tenants share one breaker | One bad tenant kills platform | Implement per-tenant circuit breakers |
| **Message queue saturation** | No per-tenant queue limits | One tenant floods queue | Partition queues by tenant_id |
| **No incident runbooks** | Ops team doesn't know response | Delayed incident response | Create P0/P1/P2 runbooks with escalation paths |
| **Blame culture** | Postmortems focus on individuals | Engineers hide failures | Switch to blameless postmortems with Five Whys |

**Cost Impact (Based on GCC Production Data):**
- **Without containment**: ₹5.5 crore (50 tenants × 3 hours × ₹36.6K/hour)
- **With containment**: ₹15 lakh (1 tenant × 3 hours × ₹5K/hour)
- **Savings ratio**: 36x cost reduction

## Decision Card

Decision framework for implementing blast radius containment in multi-tenant RAG systems:

### When to Use

✅ **Use blast radius containment when:**
- Managing 10+ tenants on shared infrastructure
- Platform-wide outages cause severe business impact (₹1 crore+ losses)
- Tenants have different SLA tiers (Platinum/Gold/Silver/Bronze)
- Need for automatic incident response without manual intervention
- Cannot afford 3+ hour platform outages
- Running production RAG systems with shared resources (DB, queue, compute)

### When NOT to Use

❌ **Do NOT use when:**
- Managing <5 tenants (manual isolation is simpler)
- Single-tenant deployments (no blast radius to contain)
- Development/staging environments (overhead not justified)
- Tenants are fully isolated (separate DB, compute, network)
- Platform outages have minimal business impact (<₹10 lakh)
- Team lacks incident response processes (fix processes first)

### Trade-offs

**Cost:**
- Self-hosted: ₹50K/month (Prometheus + monitoring infrastructure)
- Managed SaaS: ₹155K/month (Datadog + PagerDuty)
- Hybrid (recommended): ₹75K/month (self-hosted Prometheus + PagerDuty)
- ROI: First prevented outage pays for 73 months of infrastructure

**Latency:**
- Detection overhead: 10-second polling adds <5ms avg latency
- Circuit breaker: <1ms per request
- False positive risk: 2-5% of tenants may be isolated unnecessarily

**Complexity:**
- Monitoring setup: 4-8 hours initial setup
- Circuit breaker integration: 2-4 hours per service
- Incident runbook creation: 8-16 hours
- Ongoing maintenance: 4-8 hours/month

**Operational Impact:**
- Reduces MTTR (Mean Time To Recovery): 3 hours → 10 minutes
- Increases MTTD (Mean Time To Detection): Manual → 60 seconds
- Reduces affected users: 50 tenants → 1 tenant
- Requires 24/7 on-call rotation for P0 incidents

### Alternative Approaches

| Approach | When to Use | Trade-off |
|----------|-------------|-----------|
| **Manual isolation** | <5 tenants, low traffic | Slower (15+ min response), requires manual intervention |
| **Full tenant isolation** | High-security requirements | 3-5x infrastructure cost, eliminates shared resources |
| **Rate limiting only** | Cost-constrained environments | Doesn't stop infinite loops or bad queries |
| **Load shedding** | Temporary traffic spikes | Drops requests (bad UX), doesn't fix root cause |
| **Kubernetes pod isolation** | Container-based deployments | Requires k8s expertise, 30-60s detection delay |

### Tenant Tier System

| Tier | Contract Value | SLA | Incident Priority | Response SLA | Escalation |
|------|----------------|-----|-------------------|--------------|------------|
| **Platinum** | ₹2 crore+ | 99.99% | P0 (Critical) | 15 minutes | CTO + VP Eng |
| **Gold** | ₹50 lakh+ | 99.9% | P1 (High) | 60 minutes | Platform Lead |
| **Silver** | ₹10 lakh+ | 99% | P2 (Medium) | 4 hours | On-call Engineer |
| **Bronze** | <₹10 lakh | Best-effort | P2 (Medium) | 8 hours | On-call Engineer |

### Incident Priority Rules

- **P0 (Critical)**: Any Platinum tenant OR 10+ tenants affected
  - Response SLA: 15 minutes
  - Escalation: War room with CTO
  - Notification: PagerDuty + SMS + phone calls

- **P1 (High)**: Gold tenant OR 5-9 tenants affected
  - Response SLA: 60 minutes
  - Escalation: Platform lead + on-call
  - Notification: PagerDuty + Slack

- **P2 (Medium)**: Silver/Bronze tenant, <5 tenants affected
  - Response SLA: 4 hours
  - Escalation: On-call engineer only
  - Notification: Slack + email

## Troubleshooting

### Prometheus Disabled Mode

The module will run without Prometheus if `PROMETHEUS_ENABLED` is not set to `true` in `.env`. The API will return skipped responses for detection endpoints. This is useful for local development or testing.

```bash
# API response when Prometheus disabled
{
  "status": "healthy",
  "prometheus_enabled": false,
  "notification_config": {
    "pagerduty_enabled": false,
    "slack_enabled": false
  }
}
```

### Import Errors

If you see `ModuleNotFoundError: No module named 'src.l3_m14_operations_governance'`, ensure:
```bash
# Windows PowerShell
$env:PYTHONPATH=$PWD

# Linux/macOS
export PYTHONPATH=$(pwd)
```

### Tests Failing

Run tests with verbose output:
```bash
pytest -v tests/
```

All tests use mocked Prometheus responses, so they should pass without actual Prometheus instance.

### Circuit Breaker Not Tripping

Check configuration:
```python
# In Python console
from config import ERROR_THRESHOLD, FAILURE_THRESHOLD
print(f"Threshold: {ERROR_THRESHOLD}, Failures: {FAILURE_THRESHOLD}")
```

Common issues:
- ERROR_THRESHOLD too high (increase to 0.7+)
- FAILURE_THRESHOLD too high (reduce to 3-5)
- Polling interval too long (reduce to 10s)

### Prometheus Connection Failed

Verify Prometheus is accessible:
```bash
curl http://prometheus:9090/api/v1/status/config
```

If using Docker:
```bash
docker run -p 9090:9090 prom/prometheus
```

## Blameless Postmortem Template

Incidents generate automatic postmortem templates focused on system improvements:

**Five Why Analysis Example:**
1. **Why did the incident occur?** Bad query deployed to tenant-A
2. **Why was bad query deployed?** No validation tool for queries
3. **Why no validation tool?** Deprioritized for feature work
4. **Why deprioritized?** No incident history to justify cost
5. **Why no incident history?** First major incident (root cause)

**Action Items (Blameless):**
- [ ] **Owner**: Platform team | **Deadline**: 2 weeks | **Action**: Implement query validation tool
- [ ] **Owner**: DevOps | **Deadline**: 1 week | **Action**: Add pre-deployment testing for queries
- [ ] **Owner**: SRE | **Deadline**: 3 days | **Action**: Update runbook with detection steps
- [ ] **Owner**: Engineering | **Deadline**: 1 week | **Action**: Review circuit breaker thresholds

Focus: System improvements, not individual blame.

## Technology Stack

**Detection:**
- Prometheus: Metrics collection and querying
- Grafana: Visualization (optional)
- PromQL: Query language for metric aggregation

**Isolation:**
- Circuit breaker pattern (native Python implementation)
- Alternative: pybreaker library

**Notification:**
- PagerDuty: P0/P1 incident alerting
- Slack: Team notifications
- Email: Tenant admin notifications

**Logging:**
- PostgreSQL: Audit log storage
- ELK Stack: Log correlation (optional)
- Python logging: Structured logs

**Orchestration:**
- FastAPI: REST API endpoints
- uvicorn: ASGI server
- Background tasks: Async notification processing

## Cost Estimates

**Infrastructure Costs (50-tenant deployment):**

| Component | Self-Hosted | Managed SaaS | Notes |
|-----------|-------------|--------------|-------|
| **Prometheus** | ₹15K/month | ₹80K/month (Datadog) | 3-node cluster, 90-day retention |
| **Grafana** | ₹5K/month | Included | Visualization dashboards |
| **PagerDuty** | - | ₹45K/month | 10-user plan, P0/P1 alerting |
| **ELK Stack** | ₹25K/month | ₹30K/month (Splunk) | Log correlation (optional) |
| **Compute** | ₹5K/month | - | Detector + API (2 vCPU, 4GB RAM) |
| **Total** | ₹50K/month | ₹155K/month | Hybrid: ₹75K/month |

**ROI Calculation:**
- First prevented outage: ₹5.5 crore saved
- Infrastructure cost: ₹75K/month
- Payback period: First incident (73 months of infrastructure)

## Next Steps

After completing this module, proceed to:
- **M14.3**: Tenant lifecycle management
- **M15**: Advanced monitoring and observability
- **Practathon**: Implement full incident response system

## Resources

- [Prometheus Query Documentation](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Blameless Postmortems](https://sre.google/sre-book/postmortem-culture/)
- [PagerDuty Incident Response](https://response.pagerduty.com/)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

For issues or questions:
- GitHub Issues: https://github.com/your-org/gcc_mt_m14_v2/issues
- Documentation: See `notebooks/` for interactive walkthrough
- Tests: See `tests/` for usage examples

---

**Built with ❤️ by TechVoyageHub**
