# PowerShell script to start FastAPI server with environment setup
# L3 M14.2: Incident Management & Blast Radius

Write-Host "Starting L3 M14.2 Incident Management API..." -ForegroundColor Green

# Set Python path
$env:PYTHONPATH = $PWD.Path

# Set Prometheus configuration (change these values as needed)
$env:PROMETHEUS_ENABLED = "True"
$env:PROMETHEUS_URL = "http://prometheus:9090"

# Set detection parameters
$env:ERROR_THRESHOLD = "0.50"
$env:CHECK_INTERVAL_SECONDS = "10"

# Set circuit breaker parameters
$env:FAILURE_THRESHOLD = "5"
$env:TIMEOUT_SECONDS = "60"

# Set logging
$env:LOG_LEVEL = "INFO"

Write-Host "Environment configured:" -ForegroundColor Cyan
Write-Host "  PYTHONPATH: $env:PYTHONPATH" -ForegroundColor Gray
Write-Host "  PROMETHEUS_ENABLED: $env:PROMETHEUS_ENABLED" -ForegroundColor Gray
Write-Host "  PROMETHEUS_URL: $env:PROMETHEUS_URL" -ForegroundColor Gray
Write-Host ""

# Check if Prometheus is enabled
if ($env:PROMETHEUS_ENABLED -eq "True") {
    Write-Host "WARNING: Prometheus is ENABLED" -ForegroundColor Yellow
    Write-Host "  Make sure Prometheus is running at $env:PROMETHEUS_URL" -ForegroundColor Yellow
    Write-Host "  Or set PROMETHEUS_ENABLED=false in .env for offline mode" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "INFO: Running in OFFLINE mode (Prometheus disabled)" -ForegroundColor Cyan
    Write-Host ""
}

# Start uvicorn server
Write-Host "Starting uvicorn on http://0.0.0.0:8000..." -ForegroundColor Green
Write-Host "API documentation: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Health check: http://localhost:8000/" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

try {
    uvicorn app:app --reload --host 0.0.0.0 --port 8000
} catch {
    Write-Host "Error starting server: $_" -ForegroundColor Red
    exit 1
}
