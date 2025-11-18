# Start API server with environment setup
# Auto-Scaling Multi-Tenant Infrastructure API

Write-Host "Starting L3 M13.2 Auto-Scaling API..." -ForegroundColor Green

# Set environment variables
$env:PYTHONPATH = $PWD
$env:REDIS_ENABLED = "False"
$env:PROMETHEUS_ENABLED = "False"

Write-Host "Environment configuration:" -ForegroundColor Cyan
Write-Host "  PYTHONPATH: $env:PYTHONPATH"
Write-Host "  REDIS_ENABLED: $env:REDIS_ENABLED"
Write-Host "  PROMETHEUS_ENABLED: $env:PROMETHEUS_ENABLED"
Write-Host ""

Write-Host "Note: Redis and Prometheus are disabled by default." -ForegroundColor Yellow
Write-Host "To enable, set REDIS_ENABLED=True and PROMETHEUS_ENABLED=True in .env file" -ForegroundColor Yellow
Write-Host ""

# Start uvicorn server
Write-Host "Starting uvicorn server on http://0.0.0.0:8000..." -ForegroundColor Green
uvicorn app:app --reload --host 0.0.0.0 --port 8000
