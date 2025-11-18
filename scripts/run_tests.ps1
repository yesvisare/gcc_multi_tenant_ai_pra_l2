# Run pytest test suite
# L3 M14.3: Tenant Lifecycle & Migrations
#
# This script runs all tests in offline mode (no external infrastructure required)

Write-Host "Running L3 M14.3 Test Suite..." -ForegroundColor Cyan

# Set PYTHONPATH to include project root
$env:PYTHONPATH = $PWD

# Force OFFLINE mode for tests
$env:OFFLINE = "True"

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  OFFLINE mode: $env:OFFLINE (forced for tests)" -ForegroundColor Yellow
Write-Host "  PYTHONPATH: $env:PYTHONPATH" -ForegroundColor Yellow
Write-Host ""

# Run pytest with verbose output
Write-Host "Executing pytest..." -ForegroundColor Green
pytest -v tests/

# Check exit code
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ All tests passed!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "✗ Some tests failed. See output above for details." -ForegroundColor Red
    exit $LASTEXITCODE
}
