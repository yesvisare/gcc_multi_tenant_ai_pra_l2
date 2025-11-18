# Start API server with environment setup
# Multi-Tenant Isolation API for L3 M11.3

Write-Host "Starting L3 M11.3 Multi-Tenant Isolation API..." -ForegroundColor Green

# Set Python path
$env:PYTHONPATH = $PWD

# Enable services (set to "True" to enable, "False" to run offline)
# PostgreSQL - Strategy 1: RLS
$env:POSTGRES_ENABLED = "False"

# Pinecone - Strategy 2: Namespace Isolation
$env:PINECONE_ENABLED = "False"

# Redis - Cache Isolation
$env:REDIS_ENABLED = "False"

# AWS - S3 Prefix Isolation
$env:AWS_ENABLED = "False"

# Offline mode (set to "False" to enable external services)
$env:OFFLINE = "True"

Write-Host "`nService Configuration:" -ForegroundColor Yellow
Write-Host "  PostgreSQL: $env:POSTGRES_ENABLED"
Write-Host "  Pinecone: $env:PINECONE_ENABLED"
Write-Host "  Redis: $env:REDIS_ENABLED"
Write-Host "  AWS: $env:AWS_ENABLED"
Write-Host "  Offline Mode: $env:OFFLINE"
Write-Host ""

Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""

# Start server
uvicorn app:app --reload --host 0.0.0.0 --port 8000
