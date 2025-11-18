# Run pytest test suite
# Forces offline mode for tests

Write-Host "Running L3 M12.3 Test Suite..." -ForegroundColor Green
Write-Host ""

# Set PYTHONPATH to include project root
$env:PYTHONPATH = $PWD

# Force offline mode for tests
$env:OFFLINE = "true"
$env:REDIS_ENABLED = "false"
$env:POSTGRES_ENABLED = "false"
$env:PROMETHEUS_ENABLED = "false"

Write-Host "Test Environment:" -ForegroundColor Cyan
Write-Host "  Offline Mode: $($env:OFFLINE)" -ForegroundColor Yellow
Write-Host "  Using in-memory fallbacks for all services" -ForegroundColor Yellow
Write-Host ""

# Run tests with pytest
Write-Host "Executing pytest..." -ForegroundColor Green
pytest -v tests/

# Display test summary
Write-Host ""
Write-Host "Test run completed!" -ForegroundColor Green
Write-Host ""
Write-Host "To run specific tests:" -ForegroundColor Cyan
Write-Host "  pytest tests/test_m12_data_isolation_security.py::TestTenantRateLimiter -v" -ForegroundColor Gray
Write-Host ""
Write-Host "To run with coverage:" -ForegroundColor Cyan
Write-Host "  pytest --cov=src tests/ --cov-report=html" -ForegroundColor Gray
