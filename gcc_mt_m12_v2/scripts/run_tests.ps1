# Run tests with pytest
# SERVICE: AWS_S3 (tests run in offline mode)

Write-Host "Running L3 M12.2 Test Suite..." -ForegroundColor Green

# Set environment variables
$env:PYTHONPATH = $PWD
$env:AWS_S3_ENABLED = "false"  # Force offline mode for tests
$env:OFFLINE = "true"

# Run pytest
Write-Host "Executing tests..." -ForegroundColor Cyan
pytest -v tests/

# Check exit code
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "All tests passed! ✓" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Some tests failed. Check output above." -ForegroundColor Red
    exit $LASTEXITCODE
}
