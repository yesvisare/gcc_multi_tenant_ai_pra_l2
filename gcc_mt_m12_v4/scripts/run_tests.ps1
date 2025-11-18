# Run tests with pytest
# L3 M12.4: Compliance Boundaries & Data Governance
# All tests run in OFFLINE mode (no external services required)

Write-Host "Running L3 M12.4 Compliance Boundaries Tests..." -ForegroundColor Green

# Set PYTHONPATH to project root
$env:PYTHONPATH = $PWD

# Force offline mode for tests (no external API calls)
$env:PINECONE_ENABLED = "false"
$env:AWS_ENABLED = "false"
$env:OFFLINE = "true"

Write-Host "Test configuration: OFFLINE mode (no external services)" -ForegroundColor Yellow
Write-Host ""

# Run pytest with verbose output
pytest -v tests/

Write-Host ""
Write-Host "✓ Tests completed!" -ForegroundColor Green
Write-Host ""
Write-Host "To run specific test:" -ForegroundColor Cyan
Write-Host "  pytest -v tests/test_m12_compliance_boundaries.py::test_create_compliance_config_gdpr"
Write-Host ""
Write-Host "To run with coverage:" -ForegroundColor Cyan
Write-Host "  pytest --cov=src --cov-report=html tests/"
