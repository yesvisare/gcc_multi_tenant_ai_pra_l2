# Start API server with environment setup
# L3 M13.3: Cost Optimization Strategies

Write-Host "Starting L3 M13.3 Cost Optimization API..." -ForegroundColor Green

# Set Python path
$env:PYTHONPATH = $PWD

# Optional: Enable infrastructure services (defaults to false)
# Uncomment to enable Prometheus, StatsD, or PostgreSQL
# $env:PROMETHEUS_ENABLED = "true"
# $env:STATSD_ENABLED = "true"
# $env:POSTGRES_ENABLED = "true"

# Set log level
$env:LOG_LEVEL = "INFO"

Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  PYTHONPATH: $env:PYTHONPATH" -ForegroundColor Gray
Write-Host "  LOG_LEVEL: $env:LOG_LEVEL" -ForegroundColor Gray
Write-Host "  Infrastructure: In-memory mode (no external services)" -ForegroundColor Gray
Write-Host ""

Write-Host "Starting uvicorn server..." -ForegroundColor Yellow
Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Green
Write-Host "Interactive docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""

uvicorn app:app --reload --host 0.0.0.0 --port 8000
