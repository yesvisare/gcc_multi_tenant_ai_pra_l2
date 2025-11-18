# Start FastAPI server for L3 M12.1: Vector Database Multi-Tenancy Patterns
# SERVICE: Pinecone (auto-detected from script Section 4)

Write-Host "Starting L3 M12.1 API Server..." -ForegroundColor Green
Write-Host "Service: Pinecone Vector Database" -ForegroundColor Cyan
Write-Host ""

# Set environment variables
$env:PYTHONPATH = $PWD
$env:PINECONE_ENABLED = "True"

# Check if .env file exists
if (Test-Path ".env") {
    Write-Host "âœ" Found .env file - loading configuration" -ForegroundColor Green
} else {
    Write-Host "âš ï¸ No .env file found - using .env.example defaults" -ForegroundColor Yellow
    Write-Host "   Copy .env.example to .env and configure PINECONE_API_KEY" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start uvicorn server
uvicorn app:app --reload --host 0.0.0.0 --port 8000
