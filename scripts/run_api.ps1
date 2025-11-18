# Start API server with environment setup
# Services: Redis, PostgreSQL, Prometheus (all optional - defaults to offline mode)

Write-Host "Starting L3 M12.3 API Server..." -ForegroundColor Green
Write-Host ""

# Set PYTHONPATH to include project root
$env:PYTHONPATH = $PWD

# Check if .env exists, otherwise use offline mode
if (Test-Path ".env") {
    Write-Host "✓ Using .env configuration" -ForegroundColor Green
} else {
    Write-Host "⚠️  No .env file found - using offline mode defaults" -ForegroundColor Yellow
    Write-Host "   Copy .env.example to .env and configure services if needed" -ForegroundColor Yellow
    Write-Host ""

    # Set offline defaults
    $env:OFFLINE = "true"
    $env:REDIS_ENABLED = "false"
    $env:POSTGRES_ENABLED = "false"
    $env:PROMETHEUS_ENABLED = "false"
}

# Display service status
Write-Host "Service Status:" -ForegroundColor Cyan
Write-Host "  Redis: $($env:REDIS_ENABLED)" -ForegroundColor $(if ($env:REDIS_ENABLED -eq "true") { "Green" } else { "Yellow" })
Write-Host "  PostgreSQL: $($env:POSTGRES_ENABLED)" -ForegroundColor $(if ($env:POSTGRES_ENABLED -eq "true") { "Green" } else { "Yellow" })
Write-Host "  Prometheus: $($env:PROMETHEUS_ENABLED)" -ForegroundColor $(if ($env:PROMETHEUS_ENABLED -eq "true") { "Green" } else { "Yellow" })
Write-Host "  Offline Mode: $($env:OFFLINE)" -ForegroundColor $(if ($env:OFFLINE -eq "true") { "Yellow" } else { "Green" })
Write-Host ""

Write-Host "Starting uvicorn server..." -ForegroundColor Green
Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API docs available at: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host ""

# Start the API server
uvicorn app:app --reload --host 0.0.0.0 --port 8000
