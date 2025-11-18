# Run tests with pytest
# L3 M11.3 Multi-Tenant Isolation Tests

Write-Host "Running L3 M11.3 tests..." -ForegroundColor Green

# Set Python path
$env:PYTHONPATH = $PWD

# Force offline mode for tests
$env:OFFLINE = "True"
$env:POSTGRES_ENABLED = "False"
$env:PINECONE_ENABLED = "False"
$env:REDIS_ENABLED = "False"
$env:AWS_ENABLED = "False"

Write-Host "Running tests in offline mode (no external services required)" -ForegroundColor Yellow
Write-Host ""

# Run tests
pytest -v tests/

Write-Host ""
Write-Host "Tests complete!" -ForegroundColor Green
