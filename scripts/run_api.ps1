# Start FastAPI server with Prometheus metrics enabled
# Multi-Tenant Monitoring & Observability API

Write-Host "Starting L3 M14.1: Multi-Tenant Monitoring & Observability API..." -ForegroundColor Green
Write-Host ""

# Set environment variables
$env:PYTHONPATH = $PWD
$env:PROMETHEUS_ENABLED = "True"
$env:PROMETHEUS_PORT = "8000"

Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  PROMETHEUS_ENABLED = True" -ForegroundColor Yellow
Write-Host "  PROMETHEUS_PORT = 8000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Endpoints:" -ForegroundColor Cyan
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "  Metrics:  http://localhost:8000/metrics" -ForegroundColor Yellow
Write-Host ""

# Start uvicorn server
uvicorn app:app --reload --host 0.0.0.0 --port 8000
