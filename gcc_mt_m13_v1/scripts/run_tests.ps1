# Run tests with pytest
# All tests run in OFFLINE mode (no Redis required)

Write-Host "Running L3 M13.1 Performance Patterns Tests..." -ForegroundColor Green

# Set environment variables
$env:PYTHONPATH = $PWD
$env:REDIS_ENABLED = "False"
$env:OFFLINE = "True"

Write-Host "Environment:" -ForegroundColor Yellow
Write-Host "  PYTHONPATH: $env:PYTHONPATH" -ForegroundColor Cyan
Write-Host "  OFFLINE: $env:OFFLINE" -ForegroundColor Cyan
Write-Host ""

# Run pytest
Write-Host "Executing pytest..." -ForegroundColor Green
pytest -v tests/

# Show summary
Write-Host ""
Write-Host "Tests complete!" -ForegroundColor Green
