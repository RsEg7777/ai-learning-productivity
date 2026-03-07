# Start the AI Learning Assistant API Server
# This script starts the FastAPI server with proper configuration

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "AI Learning Assistant - Starting Server" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

Write-Host "Python version:" -ForegroundColor Yellow
python --version
Write-Host ""

# Check if virtual environment exists
if (!(Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Install/upgrade dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet

Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Green
Write-Host ("=" * 59) -ForegroundColor Green
Write-Host "Server Configuration" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Green
Write-Host ("=" * 59) -ForegroundColor Green

# Set environment variables
$env:AWS_REGION = if ($env:AWS_REGION) { $env:AWS_REGION } else { "us-east-1" }
$env:TABLE_PREFIX = if ($env:TABLE_PREFIX) { $env:TABLE_PREFIX } else { "ai-learning-" }
$env:STRICT_MODE = if ($env:STRICT_MODE) { $env:STRICT_MODE } else { "false" }

Write-Host "AWS Region:     $env:AWS_REGION" -ForegroundColor Cyan
Write-Host "Table Prefix:   $env:TABLE_PREFIX" -ForegroundColor Cyan
Write-Host "Strict Mode:    $env:STRICT_MODE" -ForegroundColor Cyan
Write-Host ""

# Check AWS credentials
Write-Host "Checking AWS credentials..." -ForegroundColor Yellow
if ($env:AWS_ACCESS_KEY_ID -and $env:AWS_SECRET_ACCESS_KEY) {
    Write-Host "✓ AWS credentials found in environment" -ForegroundColor Green
} elseif (Test-Path "$env:USERPROFILE\.aws\credentials") {
    Write-Host "✓ AWS credentials file found" -ForegroundColor Green
} else {
    Write-Host "⚠ WARNING: No AWS credentials found!" -ForegroundColor Yellow
    Write-Host "  The server will start but AWS services will not work." -ForegroundColor Yellow
    Write-Host "  Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY or configure ~/.aws/credentials" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Green
Write-Host ("=" * 59) -ForegroundColor Green
Write-Host "Starting Server" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Green
Write-Host ("=" * 59) -ForegroundColor Green
Write-Host ""
Write-Host "Server will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Health check: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the server
python -m uvicorn app:app --reload --port 8000 --host 0.0.0.0
