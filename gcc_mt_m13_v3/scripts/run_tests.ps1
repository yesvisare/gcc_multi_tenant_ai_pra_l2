# Run tests with pytest
# L3 M13.3: Cost Optimization Strategies

Write-Host "Running L3 M13.3 Test Suite..." -ForegroundColor Green
Write-Host ""

# Set Python path
$env:PYTHONPATH = $PWD

Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  PYTHONPATH: $env:PYTHONPATH" -ForegroundColor Gray
Write-Host ""

Write-Host "Executing pytest..." -ForegroundColor Yellow
pytest -v tests/

Write-Host ""
Write-Host "Test run complete!" -ForegroundColor Green
