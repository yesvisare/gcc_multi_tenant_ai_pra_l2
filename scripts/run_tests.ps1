# Run tests with pytest
# For L3 M14.4: Platform Governance & Operating Model

Write-Host "Running L3 M14.4 Platform Governance Tests..." -ForegroundColor Green
Write-Host ""

# Set PYTHONPATH to project root
$env:PYTHONPATH = $PWD
Write-Host "✓ PYTHONPATH set to: $PWD" -ForegroundColor Gray

# Force OFFLINE mode for tests (no external services needed)
$env:OFFLINE = "true"
Write-Host "✓ OFFLINE mode enabled" -ForegroundColor Gray

Write-Host ""
Write-Host "Running pytest..." -ForegroundColor Cyan
Write-Host ""

# Run pytest with verbose output and coverage
pytest -v tests/ --tb=short

Write-Host ""
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ All tests passed!" -ForegroundColor Green
} else {
    Write-Host "✗ Some tests failed. Check output above." -ForegroundColor Red
}
