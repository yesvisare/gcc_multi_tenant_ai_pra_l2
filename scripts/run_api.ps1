# Start API server with environment setup
# For L3 M14.4: Platform Governance & Operating Model
# No external service needed - runs entirely offline

Write-Host "Starting L3 M14.4 Platform Governance API..." -ForegroundColor Green
Write-Host ""

# Set PYTHONPATH to project root
$env:PYTHONPATH = $PWD
Write-Host "✓ PYTHONPATH set to: $PWD" -ForegroundColor Gray

# Set OFFLINE mode (always true - no external services needed)
$env:OFFLINE = "true"
Write-Host "✓ OFFLINE mode enabled (no external services required)" -ForegroundColor Gray

# Set log level (can be overridden)
if (-not $env:LOG_LEVEL) {
    $env:LOG_LEVEL = "INFO"
}
Write-Host "✓ LOG_LEVEL: $env:LOG_LEVEL" -ForegroundColor Gray

Write-Host ""
Write-Host "Launching uvicorn server..." -ForegroundColor Cyan
Write-Host "API will be available at:" -ForegroundColor Yellow
Write-Host "  - http://localhost:8000" -ForegroundColor White
Write-Host "  - Swagger docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - Health check: http://localhost:8000/health" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host ""

# Start uvicorn with hot reload
uvicorn app:app --reload --host 0.0.0.0 --port 8000
