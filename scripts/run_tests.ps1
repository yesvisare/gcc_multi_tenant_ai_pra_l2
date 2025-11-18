# Run test suite for L3 M11.4: Tenant Provisioning
# Windows PowerShell script

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "L3 M11.4: Tenant Provisioning Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set Python path to include src directory
$env:PYTHONPATH = $PWD
Write-Host "✓ PYTHONPATH set to: $PWD" -ForegroundColor Green

# Force offline mode for tests
$env:PROVISIONING_ENABLED = "false"
$env:OFFLINE = "true"
Write-Host "✓ Test environment configured (offline mode)" -ForegroundColor Green
Write-Host ""

# Check if pytest is installed
$pytestVersion = & pytest --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ pytest found: $pytestVersion" -ForegroundColor Green
} else {
    Write-Host "✗ pytest not found. Install with: pip install pytest pytest-asyncio" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Running test suite..." -ForegroundColor Cyan
Write-Host ""

# Run pytest with verbose output and summary
pytest -v tests/ --tb=short --color=yes

# Check exit code
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✓ All tests passed!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "✗ Some tests failed" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    exit 1
}
