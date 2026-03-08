# Quick Start Script for Production Testing
# Run this to verify all features are working

Write-Host "================================" -ForegroundColor Cyan
Write-Host "AI Learning Platform - Quick Start" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if server is running
Write-Host "Checking if server is running..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ Server is running!" -ForegroundColor Green
    Write-Host ""
    
    # Display health status
    $health = $response.Content | ConvertFrom-Json
    Write-Host "Health Status:" -ForegroundColor Cyan
    Write-Host "  Status: $($health.status)" -ForegroundColor White
    Write-Host "  Services:" -ForegroundColor White
    $health.services.PSObject.Properties | ForEach-Object {
        Write-Host "    - $($_.Name): $($_.Value)" -ForegroundColor White
    }
    Write-Host ""
    
    # Ask if user wants to run tests
    Write-Host "Would you like to run the full test suite? (Y/N)" -ForegroundColor Yellow
    $runTests = Read-Host
    
    if ($runTests -eq "Y" -or $runTests -eq "y") {
        Write-Host ""
        Write-Host "Running production tests..." -ForegroundColor Cyan
        python test_production_features.py
    } else {
        Write-Host ""
        Write-Host "Skipping tests. You can run them manually with:" -ForegroundColor Yellow
        Write-Host "  python test_production_features.py" -ForegroundColor White
    }
    
    Write-Host ""
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host "Quick Links:" -ForegroundColor Cyan
    Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor White
    Write-Host "  Health: http://localhost:8000/health" -ForegroundColor White
    Write-Host "  Frontend: cd frontend && npm start" -ForegroundColor White
    Write-Host "================================" -ForegroundColor Cyan
    
} catch {
    Write-Host "❌ Server is not running!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Start the server with:" -ForegroundColor Yellow
    Write-Host "  python -m uvicorn app:app --reload --port 8000" -ForegroundColor White
    Write-Host ""
    Write-Host "Or use the start script:" -ForegroundColor Yellow
    Write-Host "  .\start-server.ps1" -ForegroundColor White
    Write-Host ""
    
    # Ask if user wants to start server
    Write-Host "Would you like to start the server now? (Y/N)" -ForegroundColor Yellow
    $startServer = Read-Host
    
    if ($startServer -eq "Y" -or $startServer -eq "y") {
        Write-Host ""
        Write-Host "Starting server..." -ForegroundColor Cyan
        python -m uvicorn app:app --reload --port 8000
    }
}
