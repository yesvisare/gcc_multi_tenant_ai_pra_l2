# Run tests with pytest
# L3 M13.4: Capacity Planning & Forecasting

Write-Host "Running L3 M13.4 Capacity Planning Tests..." -ForegroundColor Cyan
Write-Host ""

# Set Python path for imports
$env:PYTHONPATH = $PWD

# Force offline mode for tests
$env:DB_ENABLED = "false"
$env:OFFLINE = "true"

# Run pytest with verbose output
pytest -v tests/

Write-Host ""
Write-Host "Tests complete!" -ForegroundColor Green
