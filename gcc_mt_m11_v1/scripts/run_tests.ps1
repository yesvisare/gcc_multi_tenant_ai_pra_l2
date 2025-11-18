# Run pytest test suite for Multi-Tenant RAG Architecture
# Tests run in OFFLINE mode (no external API calls)

Write-Host "Running Multi-Tenant RAG Test Suite..." -ForegroundColor Green

# Set PYTHONPATH to include src directory
$env:PYTHONPATH = $PWD

# Force offline mode for tests
$env:OFFLINE = "true"
$env:PINECONE_ENABLED = "false"
$env:OPENAI_ENABLED = "false"

Write-Host "Test Configuration:" -ForegroundColor Cyan
Write-Host "  OFFLINE: $env:OFFLINE" -ForegroundColor Cyan
Write-Host "  PINECONE_ENABLED: $env:PINECONE_ENABLED" -ForegroundColor Cyan
Write-Host "  OPENAI_ENABLED: $env:OPENAI_ENABLED" -ForegroundColor Cyan
Write-Host ""

# Run pytest with quiet mode (-q) for concise output
# Use -v for verbose output, -vv for very verbose
pytest -q tests/

Write-Host ""
Write-Host "Test run complete!" -ForegroundColor Green
