# L3 M13.4: Capacity Planning & Forecasting

Forecasts tenant capacity needs for multi-tenant platforms using time-series analysis and linear regression. Analyzes 6 months of historical usage data to predict capacity requirements 3 months ahead with a 20% headroom buffer to absorb quarter-end spikes.

**Part of:** TechVoyageHub L3 Production RAG Engineering Track
**Prerequisites:** M13.1-M13.3 (Performance Optimization Fundamentals)
**Technology Stack:** PostgreSQL, NumPy, scikit-learn, FastAPI

## What You'll Build

This module teaches you to implement proactive capacity management for 50+ tenant platforms. You'll learn to analyze historical usage patterns, forecast future capacity needs using linear regression, implement multi-threshold alerting (70%, 80%, 90% utilization), and design tenant rebalancing strategies for uneven load distribution.

**Key Capabilities:**
- Analyze historical usage patterns from PostgreSQL time-series data
- Forecast capacity needs 3 months ahead using linear regression
- Apply 20% headroom buffer to absorb quarter-end spikes
- Implement graduated alert thresholds (CAUTION, WARNING, CRITICAL)
- Recommend tenant rebalancing to address "noisy neighbor" problems
- Batch process forecasts for 50+ tenants × 3 metrics efficiently
- Store forecast results for dashboard visualization and auditing

**Success Criteria:**
- Forecast accuracy within ±10% of actual usage
- Alert triggers at 70%, 80%, and 90% utilization thresholds
- Batch processing completes within 5 minutes for 150+ forecasts
- Rebalancing recommendations reduce node imbalance below 30%
- All forecasts stored in PostgreSQL with confidence scores

## How It Works

```
Historical Data (PostgreSQL)
         â†"
[6 months of monthly-aggregated usage]
         â†"
Linear Regression Modeling
         â†"
[Predict 3 months ahead]
         â†"
Apply Headroom Factor (1.2x)
         â†"
Alert Level Classification
         â†"
[Store Results + Dashboard Display]
```

**Algorithm Steps:**
1. Query PostgreSQL for 6 months of monthly-aggregated usage data
2. Fit linear regression model to historical trend
3. Predict usage N months ahead (default: 3 months)
4. Multiply prediction by headroom factor (default: 1.2 for 20% buffer)
5. Classify into alert levels: OK (<70%), CAUTION (70-80%), WARNING (80-90%), CRITICAL (≥90%)
6. Generate actionable recommendations based on alert level
7. Store forecast results for Grafana dashboard visualization

## Quick Start

### 1. Clone and Setup
```bash
cd gcc_mt_m13_v4
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env to set database credentials (optional for testing)
```

**Database Setup (Optional):**
If you want to connect to a real PostgreSQL database:
```bash
# Edit .env and set:
DB_ENABLED=true
DB_HOST=localhost
DB_PORT=5432
DB_NAME=capacity_planning
DB_USER=postgres
DB_PASSWORD=your_password_here
```

**Offline Mode (Default):**
The module works without a database by generating synthetic data for testing.

### 4. Run Tests
```bash
# Windows PowerShell
$env:PYTHONPATH=$PWD; pytest -q

# Or use script
./scripts/run_tests.ps1
```

Expected output:
```
....................  [100%]
20 passed in 2.5s
```

### 5. Start API
```bash
# Windows PowerShell
$env:PYTHONPATH=$PWD; uvicorn app:app --reload

# Or use script
./scripts/run_api.ps1
```

API will be available at:
- Main endpoint: http://localhost:8000
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/

### 6. Explore Notebook
```bash
jupyter lab notebooks/L3_M13_Scale_Performance_Optimization.ipynb
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DB_ENABLED` | No | `false` | Enable PostgreSQL database integration |
| `DB_HOST` | If enabled | `localhost` | Database host address |
| `DB_PORT` | If enabled | `5432` | Database port |
| `DB_NAME` | If enabled | `capacity_planning` | Database name |
| `DB_USER` | If enabled | `postgres` | Database username |
| `DB_PASSWORD` | If enabled | - | Database password |
| `HEADROOM_FACTOR` | No | `1.2` | Safety buffer multiplier (1.2 = 20% headroom) |
| `HISTORY_MONTHS` | No | `6` | Number of historical months to analyze |
| `FORECAST_MONTHS` | No | `3` | Number of months to forecast ahead |
| `THRESHOLD_CAUTION` | No | `70.0` | CAUTION alert threshold (%) |
| `THRESHOLD_WARNING` | No | `80.0` | WARNING alert threshold (%) |
| `THRESHOLD_CRITICAL` | No | `90.0` | CRITICAL alert threshold (%) |
| `OFFLINE` | No | `false` | Run in offline mode (notebook) |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |

## API Endpoints

### GET /
Health check and service status
```bash
curl http://localhost:8000/
```

### POST /forecast
Forecast capacity for a single tenant and metric
```bash
curl -X POST http://localhost:8000/forecast \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "tenant-ecommerce-001",
    "metric_name": "cpu_usage",
    "months_back": 6,
    "months_ahead": 3
  }'
```

### POST /forecast/batch
Batch forecast for multiple tenants
```bash
curl -X POST http://localhost:8000/forecast/batch \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_ids": ["tenant-1", "tenant-2", "tenant-3"],
    "metrics": ["cpu_usage", "memory_usage", "storage_usage"]
  }'
```

### POST /rebalancing
Get tenant rebalancing recommendations
```bash
curl -X POST http://localhost:8000/rebalancing \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_usage": {
      "tenant-1": 90.0,
      "tenant-2": 55.0,
      "tenant-3": 30.0
    },
    "imbalance_threshold": 0.3
  }'
```

### GET /alert-level/{usage}
Check alert level for a usage percentage
```bash
curl http://localhost:8000/alert-level/85.5
```

## Common Failures & Fixes

| Failure | Cause | Fix |
|---------|-------|-----|
| **Insufficient Historical Data** | New tenant with < 3 months of data | Wait for minimum data collection period or use conservative defaults (assume linear growth at 5%/month) |
| **Seasonal Anomaly Not Captured** | Holiday spike not in 6-month window | Extend history to 12 months or apply seasonal adjustment factor (1.3x for Q4) |
| **Unexpected Spike Absorption** | 20% headroom insufficient for 35% spike | Increase headroom factor to 1.35 for high-volatility tenants (e-commerce, retail) |
| **Tenant Imbalance Degradation** | "Noisy neighbor" consuming 80%+ of node resources | Run rebalancing recommendations and migrate high-usage tenants to dedicated nodes |
| **Lead Time Mismatch** | Forecast shows 90% in 1 month, but procurement takes 3 months | Increase forecast window to 6 months for hardware procurement, use 3 months for software scaling |
| **Low Confidence Score** | R² < 0.5 indicating poor model fit | Check for data quality issues (missing values, outliers), or switch to seasonal decomposition |
| **False Positive Alerts** | CAUTION alerts triggered by temporary spikes | Smooth data with moving average (3-month window) before forecasting |
| **Database Connection Timeout** | PostgreSQL query takes > 30 seconds | Add indexes on `(tenant_id, metric_name, timestamp)` columns |
| **Batch Processing Timeout** | 150+ forecasts exceed API timeout | Process in chunks of 50 tenants, or increase timeout to 10 minutes |
| **Alert Fatigue** | Too many CAUTION alerts ignored by ops team | Raise CAUTION threshold to 75% and focus on WARNING/CRITICAL only |

## Decision Card

**When to use Linear Regression for Capacity Forecasting:**

**Use When:**
- Historical usage shows linear or near-linear growth trend
- You need explainable forecasts for CFO/budget discussions
- Platform is mature with stable tenant base (< 10% churn)
- Forecast horizon is short-term (1-6 months)
- Data collection is monthly-aggregated (not real-time)
- Acceptable accuracy: ±10-15% prediction error
- Team lacks ML expertise for advanced models
- CFO requires transparent cost projections

**Do NOT Use When:**
- Usage patterns are highly seasonal (use Prophet or SARIMA instead)
- Exponential growth expected (use exponential smoothing)
- Real-time capacity decisions needed (use streaming analytics)
- Platform is new with < 3 months data (insufficient history)
- Tenant churn > 25% (invalidates historical trends)
- Budget requires ±5% accuracy (use ensemble methods)
- Complex interactions between metrics (use multivariate models)
- Compliance requires worst-case planning (use percentile-based forecasting)

**Trade-offs:**

| Dimension | Linear Regression | Advanced ML (Prophet, LSTM) |
|-----------|-------------------|------------------------------|
| **Accuracy** | 85-90% for linear trends | 90-95% with seasonal patterns |
| **Explainability** | High (clear coefficient interpretation) | Low (black-box models) |
| **Implementation Complexity** | Low (scikit-learn, 50 lines) | High (hyperparameter tuning, 500+ lines) |
| **Training Time** | Milliseconds | Minutes to hours |
| **Forecast Latency** | < 1 second | 1-10 seconds |
| **Data Requirements** | 3 months minimum | 12+ months for seasonality |
| **Maintenance Overhead** | Minimal (stable algorithm) | High (drift detection, retraining) |
| **Cost** | Free (open-source) | Cloud GPU for LSTM ($50-200/month) |

**Why 20% Headroom?**
Industry standard based on empirical data: quarter-end spikes typically 15-25% above baseline. 20% buffer absorbs most spikes without excessive waste. Adjust to 30% for high-volatility workloads (retail, finance) or 10% for stable workloads (healthcare, government).

**Why 6 Months History?**
Captures two full quarterly cycles without including stale data. Too short (< 3 months) misses seasonal patterns. Too long (> 12 months) includes irrelevant trends (e.g., pre-migration usage).

**Why 3 Alert Thresholds?**
Graduated responses prevent alert fatigue:
- **70% CAUTION:** Plan ahead (3+ months lead time)
- **80% WARNING:** Initiate procurement (1-3 months lead time)
- **90% CRITICAL:** Emergency expansion (< 1 month lead time)

## Architecture

```
┌─────────────────────┐
│  PostgreSQL DB      │
│  (Historical Data)  │
└──────────┬──────────┘
           â†"
┌─────────────────────┐
│ TenantCapacity      │
│ Forecaster          │
│                     │
│ • get_historical    │
│ • forecast_capacity │
│ • forecast_all      │
│ • store_forecast    │
└──────────┬──────────┘
           â†"
┌─────────────────────┐
│  FastAPI Server     │
│  (REST Endpoints)   │
└──────────┬──────────┘
           â†"
┌─────────────────────┐
│  Grafana Dashboard  │
│  (Visualization)    │
└─────────────────────┘
```

## Troubleshooting

### Database Disabled Mode
The module runs without PostgreSQL integration by default (`DB_ENABLED=false`). It generates synthetic time-series data for testing. This is useful for:
- Local development without database setup
- Running tests in CI/CD pipelines
- Exploring the notebook without credentials

To enable database integration:
1. Set up PostgreSQL with required schema (see `docs/database_schema.sql` - not included in basic setup)
2. Set `DB_ENABLED=true` in `.env`
3. Provide database credentials

### Import Errors
If you see `ModuleNotFoundError: No module named 'src.l3_m13_capacity_planning'`, ensure:
```bash
# Windows PowerShell
$env:PYTHONPATH=$PWD

# Linux/Mac
export PYTHONPATH=$PWD
```

### Tests Failing
Run tests with verbose output to see details:
```bash
pytest -v tests/
```

Common test failures:
- **Database tests skipped:** Expected when `DB_ENABLED=false` (default)
- **Synthetic data variation:** Acceptable if confidence score > 0.7
- **Import errors:** Check PYTHONPATH is set correctly

### API Startup Errors
**Error:** `psycopg2 not installed`
**Fix:** Install with `pip install psycopg2-binary`

**Error:** `Database connection failed`
**Fix:** Check PostgreSQL is running and credentials are correct, or set `DB_ENABLED=false`

**Error:** `ModuleNotFoundError: No module named 'src'`
**Fix:** Set `PYTHONPATH=$PWD` before starting API

### Low Forecast Confidence
If confidence scores (R²) are consistently < 0.5:
1. Check historical data quality (missing values, outliers)
2. Ensure at least 3-6 months of data available
3. Verify data is monthly-aggregated (not daily spikes)
4. Consider using moving average smoothing
5. Switch to seasonal decomposition for highly seasonal data

## Project Structure

```
gcc_mt_m13_v4/
├── app.py                              ← FastAPI entrypoint
├── config.py                           ← Database & environment config
├── requirements.txt                    ← Python dependencies
├── .env.example                        ← Environment variable template
├── .gitignore                          ← Git ignore rules
├── LICENSE                             ← MIT License
├── README.md                           ← This file
├── example_data.json                   ← Sample tenant data
├── example_data.txt                    ← Usage scenarios
│
├── src/                                ← Source code package
│   └── l3_m13_capacity_planning/      ← Main Python package
│       └── __init__.py                 ← Core business logic
│
├── notebooks/                          ← Jupyter notebooks
│   └── L3_M13_Scale_Performance_Optimization.ipynb
│
├── tests/                              ← Test suite
│   └── test_m13_capacity_planning.py  ← Pytest tests
│
├── configs/                            ← Configuration files
│   └── example.json                    ← Sample config
│
└── scripts/                            ← Automation scripts
    ├── run_api.ps1                     ← Start API (PowerShell)
    └── run_tests.ps1                   ← Run tests (PowerShell)
```

## Next Steps

After completing this module, proceed to:
- **M13.5:** Auto-scaling Implementation (horizontal scaling triggers)
- **M13.6:** Cost Optimization Strategies (right-sizing recommendations)
- **M14:** Advanced RAG Optimization (query optimization, caching strategies)

## Learning Resources

**Core Concepts:**
- Linear Regression: [scikit-learn documentation](https://scikit-learn.org/stable/modules/linear_model.html)
- Time-Series Forecasting: [Practical Time Series Analysis](https://www.oreilly.com/library/view/practical-time-series/9781492041641/)
- Capacity Planning: [Google SRE Book - Chapter 25](https://sre.google/sre-book/software-engineering-in-sre/)

**Alternative Approaches:**
- Facebook Prophet (seasonal forecasting)
- TimescaleDB (time-series database)
- Prometheus + Grafana (real-time monitoring)
- Apache Airflow (workflow orchestration)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

This module is part of the TechVoyageHub L3 curriculum. For issues or improvements, contact the course maintainers.

---

**Production-Ready Checklist:**
- ✅ Implements linear regression forecasting with 20% headroom
- ✅ Multi-threshold alerting (70%, 80%, 90%)
- ✅ Batch processing for 50+ tenants
- ✅ PostgreSQL integration (optional)
- ✅ FastAPI REST endpoints
- ✅ Comprehensive test suite
- ✅ Offline mode for testing
- ✅ Rebalancing recommendations
- ✅ Type hints and docstrings
- ✅ Error handling for all failure scenarios
- ✅ Windows PowerShell automation scripts
- ✅ Jupyter notebook walkthrough
