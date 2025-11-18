# Start FastAPI server for L3 M11.4: Tenant Provisioning API
# Windows PowerShell script

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "L3 M11.4: Tenant Provisioning API" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set Python path to include src directory
$env:PYTHONPATH = $PWD
Write-Host "✓ PYTHONPATH set to: $PWD" -ForegroundColor Green

# Check if .env file exists
if (Test-Path ".env") {
    Write-Host "✓ Found .env file" -ForegroundColor Green
} else {
    Write-Host "⚠ No .env file found. Using defaults (PROVISIONING_ENABLED=false)" -ForegroundColor Yellow
    Write-Host "  → Copy .env.example to .env and configure for production use" -ForegroundColor Yellow
}

# Set provisioning mode
$provisioningEnabled = $env:PROVISIONING_ENABLED
if (-not $provisioningEnabled) {
    $env:PROVISIONING_ENABLED = "false"
    Write-Host "⚠ PROVISIONING_ENABLED not set - running in SIMULATION mode" -ForegroundColor Yellow
} elseif ($provisioningEnabled -eq "true") {
    Write-Host "✓ PROVISIONING_ENABLED=true - running in PRODUCTION mode" -ForegroundColor Green
    Write-Host "  → Infrastructure changes will be applied via Terraform" -ForegroundColor Yellow
} else {
    Write-Host "⚠ PROVISIONING_ENABLED=$provisioningEnabled - running in SIMULATION mode" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Starting FastAPI server..." -ForegroundColor Cyan
Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Interactive docs at: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""

# Start uvicorn server with hot reload
uvicorn app:app --reload --host 0.0.0.0 --port 8000
