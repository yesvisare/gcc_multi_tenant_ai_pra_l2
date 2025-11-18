# Start Multi-Tenant RAG API server with environment setup
# Services: PINECONE (vector DB) + OPENAI (embeddings/LLM)

Write-Host "Starting Multi-Tenant RAG API..." -ForegroundColor Green

# Set PYTHONPATH to include src directory
$env:PYTHONPATH = $PWD

# Enable services (set to "True" if you have API keys configured in .env)
# Default: False for offline development mode
$env:PINECONE_ENABLED = "False"
$env:OPENAI_ENABLED = "False"

# Optional: Enable services if .env file exists with keys
if (Test-Path ".env") {
    Write-Host "Loading environment from .env file..." -ForegroundColor Yellow
    # PowerShell will load .env via python-dotenv in app
}

Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  PINECONE_ENABLED: $env:PINECONE_ENABLED" -ForegroundColor Cyan
Write-Host "  OPENAI_ENABLED: $env:OPENAI_ENABLED" -ForegroundColor Cyan

Write-Host ""
Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Green
Write-Host "API docs available at: http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start Uvicorn server with hot reload
uvicorn app:app --reload --host 0.0.0.0 --port 8000
