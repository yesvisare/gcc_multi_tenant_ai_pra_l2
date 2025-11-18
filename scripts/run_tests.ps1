# Run Tests for L3 M11.2: Tenant Registry

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "L3 M11.2: Running Test Suite" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set environment variables
$env:PYTHONPATH = $PWD
$env:LOG_LEVEL = "ERROR"  # Reduce log noise during tests

Write-Host "Running pytest..." -ForegroundColor Green
Write-Host ""

# Run tests with verbose output
pytest -v tests/

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Coverage Report" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Run tests with coverage
pytest --cov=src --cov-report=term-missing tests/

Write-Host ""
Write-Host "Tests complete!" -ForegroundColor Green
