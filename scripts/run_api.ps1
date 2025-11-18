# Start Tenant Registry API Server
# This module uses local databases only (no external API keys required)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "L3 M11.2: Tenant Registry API" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set environment variables
$env:PYTHONPATH = $PWD
$env:DATABASE_URL = "postgresql://localhost:5432/tenant_registry"
$env:REDIS_URL = "redis://localhost:6379/0"
$env:LOG_LEVEL = "INFO"

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Database: PostgreSQL + Redis (demo mode)" -ForegroundColor Gray
Write-Host "  Service: OFFLINE (no external APIs)" -ForegroundColor Gray
Write-Host "  Port: 8000" -ForegroundColor Gray
Write-Host ""

Write-Host "Note: Database connections are optional for demo purposes" -ForegroundColor Yellow
Write-Host "      The API demonstrates tenant registry patterns" -ForegroundColor Yellow
Write-Host ""

Write-Host "Starting API server..." -ForegroundColor Green
Write-Host "  Endpoint: http://localhost:8000" -ForegroundColor Gray
Write-Host "  Docs: http://localhost:8000/docs" -ForegroundColor Gray
Write-Host ""

# Start the server
uvicorn app:app --reload --host 0.0.0.0 --port 8000
