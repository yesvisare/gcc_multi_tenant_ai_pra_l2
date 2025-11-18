# Start API server with environment setup
# L3 M14.3: Tenant Lifecycle & Migrations
#
# This script starts the FastAPI server with proper environment configuration.
# Default mode: OFFLINE (can run without external infrastructure)

Write-Host "Starting L3 M14.3 Tenant Lifecycle & Migrations API..." -ForegroundColor Cyan

# Set PYTHONPATH to include project root
$env:PYTHONPATH = $PWD

# Default to OFFLINE mode (change to 'False' to enable real infrastructure)
if (-not $env:OFFLINE) {
    $env:OFFLINE = "True"
}

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  OFFLINE mode: $env:OFFLINE" -ForegroundColor Yellow
Write-Host "  PYTHONPATH: $env:PYTHONPATH" -ForegroundColor Yellow
Write-Host ""

if ($env:OFFLINE -eq "True") {
    Write-Host "⚠️  Running in OFFLINE mode - infrastructure calls will be simulated" -ForegroundColor Yellow
    Write-Host "   To enable real infrastructure, set OFFLINE=False in .env or environment" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "Starting FastAPI server on http://localhost:8000" -ForegroundColor Green
Write-Host "API documentation available at http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""

# Start uvicorn server
uvicorn app:app --reload --host 0.0.0.0 --port 8000
