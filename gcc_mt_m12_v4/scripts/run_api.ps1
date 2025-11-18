# Start API server with environment setup
# L3 M12.4: Compliance Boundaries & Data Governance
# Services: Pinecone (vector DB), AWS (S3/CloudFront)

Write-Host "Starting L3 M12.4 Compliance Boundaries API..." -ForegroundColor Green

# Set PYTHONPATH to project root
$env:PYTHONPATH = $PWD

# SERVICE configuration (auto-detected from script Section 4)
# Set to "True" to enable external services, "False" for offline mode

# Option 1: Enable Pinecone + AWS (requires API keys in .env)
# $env:PINECONE_ENABLED = "True"
# $env:AWS_ENABLED = "True"

# Option 2: Offline mode (default - no external services)
$env:PINECONE_ENABLED = "False"
$env:AWS_ENABLED = "False"

Write-Host "Service configuration:" -ForegroundColor Yellow
Write-Host "  PINECONE_ENABLED=$env:PINECONE_ENABLED"
Write-Host "  AWS_ENABLED=$env:AWS_ENABLED"
Write-Host ""

if ($env:PINECONE_ENABLED -eq "False" -and $env:AWS_ENABLED -eq "False") {
    Write-Host "⚠️  WARNING: Running in OFFLINE mode" -ForegroundColor Yellow
    Write-Host "   External services disabled. To enable:" -ForegroundColor Yellow
    Write-Host "   1. Copy .env.example to .env" -ForegroundColor Yellow
    Write-Host "   2. Set PINECONE_ENABLED=true and/or AWS_ENABLED=true" -ForegroundColor Yellow
    Write-Host "   3. Add API keys (PINECONE_API_KEY, AWS_ACCESS_KEY_ID, etc.)" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "Starting FastAPI server on http://localhost:8000" -ForegroundColor Green
Write-Host "API docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

# Start uvicorn server
uvicorn app:app --reload --host 0.0.0.0 --port 8000
