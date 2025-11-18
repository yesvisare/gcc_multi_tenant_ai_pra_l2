# Run pytest test suite for L3 M14.1
# Multi-Tenant Monitoring & Observability Tests

Write-Host "Running L3 M14.1 Test Suite..." -ForegroundColor Green
Write-Host ""

# Set environment variables
$env:PYTHONPATH = $PWD
$env:PROMETHEUS_ENABLED = "false"
$env:OFFLINE = "true"

Write-Host "Test Configuration:" -ForegroundColor Cyan
Write-Host "  PROMETHEUS_ENABLED = false (tests use in-memory storage)" -ForegroundColor Yellow
Write-Host "  OFFLINE = true" -ForegroundColor Yellow
Write-Host ""

# Run pytest
pytest -v tests/

Write-Host ""
Write-Host "Test run completed!" -ForegroundColor Green
