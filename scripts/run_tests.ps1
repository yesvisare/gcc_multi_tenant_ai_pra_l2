# Run pytest test suite for L3 M12.1: Vector Database Multi-Tenancy Patterns
# All tests run in offline mode (no Pinecone connection required)

Write-Host "Running L3 M12.1 Test Suite..." -ForegroundColor Green
Write-Host "Module: Vector Database Multi-Tenancy Patterns" -ForegroundColor Cyan
Write-Host ""

# Set environment variables
$env:PYTHONPATH = $PWD
$env:PINECONE_ENABLED = "false"
$env:OFFLINE = "true"

Write-Host "âœ" Environment configured for offline testing" -ForegroundColor Green
Write-Host "   PINECONE_ENABLED=false (tests will use mocked/offline mode)" -ForegroundColor Gray
Write-Host ""

# Run pytest with verbose output
Write-Host "Executing tests..." -ForegroundColor Cyan
Write-Host ""

pytest tests/ -v --tb=short

# Check test results
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "âœ" All tests passed!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "âŒ Some tests failed. Review output above." -ForegroundColor Red
    exit 1
}
