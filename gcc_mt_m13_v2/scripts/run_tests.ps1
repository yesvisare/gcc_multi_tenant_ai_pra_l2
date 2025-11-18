# Run tests with pytest
# Auto-Scaling Multi-Tenant Infrastructure Test Suite

Write-Host "Running L3 M13.2 Auto-Scaling Tests..." -ForegroundColor Green

# Set environment variables
$env:PYTHONPATH = $PWD
$env:REDIS_ENABLED = "False"
$env:PROMETHEUS_ENABLED = "False"
$env:OFFLINE = "True"

Write-Host "Test environment configuration:" -ForegroundColor Cyan
Write-Host "  PYTHONPATH: $env:PYTHONPATH"
Write-Host "  OFFLINE: $env:OFFLINE"
Write-Host ""

# Run pytest with verbose output
Write-Host "Executing pytest..." -ForegroundColor Green
pytest -v tests/
