# L3 M14.1: Multi-Tenant Monitoring & Observability

**Production-grade tenant-aware metrics collection and observability for multi-tenant RAG systems.**

Global dashboards lie by averaging. When 9 tenants operate at 50ms latency and 1 tenant runs at 5000ms, the platform average shows ~545ms—masking the failing tenant completely. This module solves the critical challenge of tenant-aware monitoring using Prometheus, Grafana, and OpenTelemetry.

**Part of:** TechVoyageHub L3 Production RAG Engineering Track
**Prerequisites:** L3 M13 (Multi-Tenant Architecture Patterns)
**SERVICE:** Prometheus (self-hosted metrics collection)

## What You'll Build

A complete observability infrastructure that:
- Tracks metrics per tenant using label-based multi-tenancy
- Prevents "averaging blindness" that hides failing tenants
- Detects resource monopolization and latency outliers
- Manages cardinality to avoid metric explosion
- Provides drill-down dashboards for tenant isolation

**Key Capabilities:**
- Tenant-aware metrics with Prometheus (counters, histograms, gauges)
- Drill-down Grafana dashboards with per-tenant filtering
- Distributed trace context propagation with tenant_id labels
- SLA budget tracking and alerting per tenant
- Quota usage monitoring (queries, tokens, storage)
- Graceful degradation when Prometheus is unavailable (in-memory fallback)

**Success Criteria:**
- Detect individual tenant SLA violations within 3 minutes (vs. 45+ minutes without tenant-aware monitoring)
- Identify resource monopolization (one tenant consuming 40% CPU while appearing as healthy 60% utilization)
- Track per-tenant query success rates, latency percentiles, and token consumption
- Maintain <1000 unique label values per metric (cardinality management)

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. INSTRUMENTATION                                              │
│    RAG services emit Prometheus metrics with tenant_id labels   │
│    rag_queries_total{tenant_id="finance", status="success"}     │
│    rag_query_duration_seconds{tenant_id="finance"} 2.0          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. COLLECTION                                                    │
│    Prometheus scrapes /metrics endpoint every 15 seconds        │
│    OpenTelemetry Collector ingests traces with tenant context   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. STORAGE                                                       │
│    Prometheus time-series DB (15-day retention)                 │
│    Jaeger stores distributed traces                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. VISUALIZATION                                                 │
│    Grafana queries: rate(rag_queries[5m]) by (tenant_id)       │
│    Drill-down: Click tenant → see per-tenant latency histogram │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. ALERTING                                                      │
│    AlertManager evaluates: quota_usage{tenant_id} > 90%         │
│    Routes alerts to tenant-specific Slack channels              │
└─────────────────────────────────────────────────────────────────┘
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
# Edit .env:
# - Set PROMETHEUS_ENABLED=true to enable metrics server
# - Set PROMETHEUS_PORT=8000 (or your preferred port)
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
$env:PROMETHEUS_ENABLED='True'; $env:PYTHONPATH=$PWD; uvicorn app:app --reload

# Or use script
./scripts/run_api.ps1
```

### 6. Explore Notebook
```bash
jupyter lab notebooks/L3_M14_Operations_Governance.ipynb
```

### 7. View Metrics
```bash
# After starting API with PROMETHEUS_ENABLED=true
curl http://localhost:8000/metrics

# Expected output:
# rag_queries_total{tenant_id="finance-team",status="success"} 10250
# rag_query_duration_seconds{tenant_id="finance-team"} 2.0
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PROMETHEUS_ENABLED` | No | `false` | Enable Prometheus metrics server |
| `PROMETHEUS_PORT` | No | `8000` | Port for /metrics endpoint |
| `OFFLINE` | No | `false` | Run in offline mode (notebook/testing) |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) |

## API Endpoints

The FastAPI application provides the following endpoints:

### Health & Configuration
- `GET /` - Health check and system status
- `GET /config` - Current configuration and Prometheus status

### Query Tracking
- `POST /tracking/start` - Start tracking a query (returns context)
- `POST /tracking/end` - End tracking and record metrics
- `POST /track` - Track a completed query in one call

### Quota Management
- `POST /quota/update` - Update tenant quota usage

### Metrics Retrieval
- `GET /metrics/{tenant_id}` - Get metrics for a specific tenant
- `GET /metrics` - Prometheus exposition format (when PROMETHEUS_ENABLED=true)

## Common Failures & Fixes

| Failure | Cause | Fix |
|---------|-------|-----|
| **Averaging Blindness** | Platform shows 99% success; one tenant at 80% success (others at 100%) | Use per-tenant success rate query: `sum(rate(rag_queries_total{status="success"}[5m])) by (tenant_id) / sum(rate(rag_queries_total[5m])) by (tenant_id)` |
| **Resource Monopolization** | One tenant consuming 40% CPU, causing slowness for 49 others (appears as healthy 60% utilization) | Alert on per-tenant resource consumption: `sum(rate(rag_active_queries[1m])) by (tenant_id) > 100` |
| **Latency Masking** | Global 545ms average hides 5000ms outlier tenant | Use per-tenant p99 latency: `histogram_quantile(0.99, rate(rag_query_duration_seconds_bucket[5m]))` |
| **Cardinality Explosion** | Labeling by `{tenant_id, user_id, query_id}` creates billions of time series | Limit labels to `tenant_id` only; use logging for high-cardinality data |
| **SLA Violation Detection Delay** | Without per-tenant error budgets, discovering violation takes 45+ minutes | Implement per-tenant alerts: `rag_quota_usage_percent{resource_type="queries"} > 90` fires within 3 minutes |

## Decision Card

### When to Use Multi-Tenant Monitoring

**Use this pattern when:**
- You have 10+ tenants with different SLA targets
- Individual tenant failures are hidden by platform averages
- You need to attribute costs (tokens, queries) per tenant
- Regulatory compliance requires tenant data isolation
- You're experiencing "noisy neighbor" resource contention
- You need drill-down capabilities from platform → tenant → user

**When NOT to use:**
- Single-tenant system (use standard Prometheus metrics)
- Fewer than 5 tenants (overhead exceeds benefit)
- All tenants have identical SLAs and resource limits
- You can't manage label cardinality (risk of metric explosion)
- Your monitoring infrastructure can't handle 50-500 time series per tenant

**Trade-offs:**

| Aspect | Single-Tenant Monitoring | Multi-Tenant Monitoring (This Module) |
|--------|-------------------------|--------------------------------------|
| **Cost** | Low (1 metric set) | Medium (50 tenants × 10 metrics = 500 series) |
| **Latency** | No additional overhead | Minimal (label filtering in PromQL) |
| **Complexity** | Simple (one dashboard) | Higher (per-tenant dashboards + cardinality management) |
| **Visibility** | Global only | Global + per-tenant drill-down |
| **SLA Detection** | Slow (45+ minutes) | Fast (3 minutes per-tenant alerts) |
| **Cardinality Risk** | None | Manage to <1000 unique labels |

## Architecture Patterns

### Label-Based Multi-Tenancy

All metrics include `tenant_id` as a label:
```prometheus
rag_queries_total{tenant_id="finance", status="success"} 10250
rag_queries_total{tenant_id="marketing", status="success"} 8900
```

**Benefits:**
- Single metric definition serves all tenants
- PromQL can aggregate or filter by tenant
- Cardinality: 50 tenants × 2 statuses = 100 time series (manageable)

**Cardinality Management Rule:**
- ✅ Safe: `{tenant_id}` with 50 tenants
- ❌ Unsafe: `{tenant_id, user_id, query_id}` = 50 × 10K × 100K = 50 billion series

### In-Memory Fallback

When Prometheus is unavailable (or `PROMETHEUS_ENABLED=false`), the module:
1. Records metrics to in-memory storage
2. Provides aggregated metrics via `/metrics/{tenant_id}` endpoint
3. Logs warnings clearly

This ensures the application remains functional for development and testing.

## Grafana Dashboard Examples

### Per-Tenant Query Rate
```promql
rate(rag_queries_total{tenant_id="finance-team"}[5m])
```

### Per-Tenant Success Rate
```promql
sum(rate(rag_queries_total{status="success"}[5m])) by (tenant_id)
/
sum(rate(rag_queries_total[5m])) by (tenant_id)
```

### Per-Tenant p99 Latency
```promql
histogram_quantile(0.99, rate(rag_query_duration_seconds_bucket[5m]))
```

### Tenants Exceeding 90% Quota
```promql
rag_quota_usage_percent > 90
```

## Troubleshooting

### Prometheus Server Not Starting
If you see `⚠️ Cannot start Prometheus server - client library not installed`:
```bash
pip install prometheus-client
```

### Service Disabled Mode
The module will run without Prometheus if `PROMETHEUS_ENABLED` is not set to `true` in `.env`. The `config.py` file will skip server startup, and metrics will be recorded in-memory. This is the default behavior and is useful for local development or testing.

To enable Prometheus:
```bash
# In .env file:
PROMETHEUS_ENABLED=true
```

### Import Errors
If you see `ModuleNotFoundError: No module named 'src.l3_m14_monitoring_observability'`, ensure:
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

All tests use in-memory storage (Prometheus disabled) to ensure they pass without dependencies.

### Metrics Not Appearing
1. Check PROMETHEUS_ENABLED is true: `http://localhost:8000/config`
2. Verify metrics server started: Check API startup logs for `✅ Prometheus metrics server started`
3. Test /metrics endpoint: `curl http://localhost:8000/metrics`

## Example Usage

### Python SDK
```python
from src.l3_m14_monitoring_observability import (
    start_query_tracking,
    end_query_tracking,
    track_query,
    update_quota_usage
)

# Track a query with start/end pattern
context = start_query_tracking("finance-team")
# ... perform RAG query ...
end_query_tracking(context, "success", docs_retrieved=5, llm_tokens=1200)

# Or track in one call
track_query("marketing-team", "success", duration=1.5, docs_retrieved=3, llm_tokens=800)

# Update quota usage
update_quota_usage("finance-team", "queries", 75.0)  # 75% of monthly quota used
```

### REST API
```bash
# Start tracking
curl -X POST http://localhost:8000/tracking/start \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "finance-team"}'

# Returns: {"context": {"tenant_id": "finance-team", "start_time": 1699999999.123, ...}}

# End tracking
curl -X POST http://localhost:8000/tracking/end \
  -H "Content-Type: application/json" \
  -d '{
    "context": {"tenant_id": "finance-team", "start_time": 1699999999.123},
    "status": "success",
    "docs_retrieved": 5,
    "llm_tokens": 1200
  }'

# Track in one call
curl -X POST http://localhost:8000/track \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "marketing-team",
    "status": "success",
    "duration": 1.5,
    "docs_retrieved": 3,
    "llm_tokens": 800
  }'
```

## Project Structure

```
gcc_multi_tenant_ai_pra_l2/
├── app.py                              # FastAPI entrypoint
├── config.py                           # Environment & Prometheus config
├── requirements.txt                    # Python dependencies
├── .env.example                        # Environment variable template
├── .gitignore                          # Git ignore rules
├── LICENSE                             # MIT License
├── README.md                           # This file
├── example_data.json                   # Sample metrics data
├── example_data.txt                    # Sample Prometheus exposition format
│
├── src/                                # Source code package
│   └── l3_m14_monitoring_observability/
│       └── __init__.py                 # Core business logic
│
├── notebooks/                          # Jupyter notebooks
│   └── L3_M14_Operations_Governance.ipynb  # Interactive walkthrough
│
├── tests/                              # Test suite
│   └── test_m14_monitoring_observability.py  # Pytest tests
│
├── configs/                            # Configuration files
│   └── example.json                    # Sample tenant configuration
│
└── scripts/                            # Automation scripts
    ├── run_api.ps1                     # Start API (Windows PowerShell)
    └── run_tests.ps1                   # Run tests (Windows PowerShell)
```

## Next Steps

After completing this module, continue to:
- **L3 M14.2:** Incident Response & Runbooks
- **L3 M14.3:** Cost Attribution & Chargeback

## Additional Resources

- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
- [Grafana Dashboard Design](https://grafana.com/docs/grafana/latest/dashboards/)
- [OpenTelemetry Multi-Tenancy](https://opentelemetry.io/docs/concepts/signals/traces/)
- [Cardinality Management](https://www.robustperception.io/cardinality-is-key)

## License

MIT License - See LICENSE file for details

## Contributing

This module is part of the TechVoyageHub L3 Production RAG Engineering Track. For questions or improvements, please open an issue or submit a pull request.
