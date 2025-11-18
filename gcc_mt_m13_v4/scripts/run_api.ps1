# Start API server with environment setup
# L3 M13.4: Capacity Planning & Forecasting

Write-Host "Starting L3 M13.4 Capacity Planning API..." -ForegroundColor Cyan

# Set Python path for imports
$env:PYTHONPATH = $PWD

# Optional: Enable database connection (set to True if PostgreSQL is configured)
# $env:DB_ENABLED = "True"
# $env:DB_PASSWORD = "your_password_here"

# Start FastAPI server with auto-reload
Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Green
Write-Host "API docs available at: http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

uvicorn app:app --reload --host 0.0.0.0 --port 8000
