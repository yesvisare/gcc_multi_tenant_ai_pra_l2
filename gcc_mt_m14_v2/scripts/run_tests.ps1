# PowerShell script to run pytest tests
# L3 M14.2: Incident Management & Blast Radius

Write-Host "Running L3 M14.2 Tests..." -ForegroundColor Green
Write-Host ""

# Set Python path
$env:PYTHONPATH = $PWD.Path

# Force offline mode for tests (no Prometheus required)
$env:PROMETHEUS_ENABLED = "false"
$env:OFFLINE = "true"

Write-Host "Environment configured:" -ForegroundColor Cyan
Write-Host "  PYTHONPATH: $env:PYTHONPATH" -ForegroundColor Gray
Write-Host "  PROMETHEUS_ENABLED: $env:PROMETHEUS_ENABLED (tests use mocked data)" -ForegroundColor Gray
Write-Host ""

# Run pytest with coverage
Write-Host "Running pytest..." -ForegroundColor Green
Write-Host ""

try {
    # Run tests with verbose output
    pytest -v tests/

    $exitCode = $LASTEXITCODE

    if ($exitCode -eq 0) {
        Write-Host ""
        Write-Host "All tests passed!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "Some tests failed (exit code: $exitCode)" -ForegroundColor Red
        exit $exitCode
    }
} catch {
    Write-Host "Error running tests: $_" -ForegroundColor Red
    exit 1
}
