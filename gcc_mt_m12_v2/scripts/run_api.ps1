# Start API server with environment setup
# SERVICE: AWS_S3 (auto-detected from script Section 4)

Write-Host "Starting L3 M12.2 API Server..." -ForegroundColor Green

# Set environment variables
$env:PYTHONPATH = $PWD
$env:AWS_S3_ENABLED = "False"  # Set to "True" to enable S3 operations

# Check if .env file exists
if (Test-Path .env) {
    Write-Host "Loading environment from .env file..." -ForegroundColor Yellow
} else {
    Write-Host "No .env file found. Using default configuration (offline mode)." -ForegroundColor Yellow
    Write-Host "Copy .env.example to .env and configure AWS credentials to enable S3." -ForegroundColor Yellow
}

# Start Uvicorn server
Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API docs at: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow

uvicorn app:app --reload --host 0.0.0.0 --port 8000
