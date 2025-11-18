# Start API server with environment setup
# SERVICE: REDIS (caching infrastructure)

Write-Host "Starting L3 M13.1 Multi-Tenant Performance Patterns API..." -ForegroundColor Green

# Set environment variables
$env:PYTHONPATH = $PWD
$env:REDIS_ENABLED = "False"  # Set to "True" if Redis is available
$env:OFFLINE = "True"          # Set to "False" if Redis is available
$env:LOG_LEVEL = "INFO"

Write-Host "Environment:" -ForegroundColor Yellow
Write-Host "  PYTHONPATH: $env:PYTHONPATH" -ForegroundColor Cyan
Write-Host "  REDIS_ENABLED: $env:REDIS_ENABLED" -ForegroundColor Cyan
Write-Host "  OFFLINE: $env:OFFLINE" -ForegroundColor Cyan
Write-Host ""

# Start Uvicorn server
Write-Host "Starting Uvicorn server on http://0.0.0.0:8000" -ForegroundColor Green
uvicorn app:app --reload --host 0.0.0.0 --port 8000
