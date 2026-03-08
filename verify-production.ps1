# Production Verification Script
# Verifies all production requirements are met

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Production Verification" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

$allPassed = $true

# Check 1: Demo files removed
Write-Host "1. Checking demo files removed..." -ForegroundColor Yellow
$demoFiles = @("demo_app.py", "demo-responses.json", "enable-demo-mode.ps1")
$demoFilesExist = $false
foreach ($file in $demoFiles) {
    if (Test-Path $file) {
        Write-Host "   ❌ Demo file still exists: $file" -ForegroundColor Red
        $demoFilesExist = $true
        $allPassed = $false
    }
}
if (-not $demoFilesExist) {
    Write-Host "   ✅ All demo files removed" -ForegroundColor Green
}

# Check 2: Required files exist
Write-Host "2. Checking required files..." -ForegroundColor Yellow
$requiredFiles = @(
    "app.py",
    "requirements.txt",
    "README.md",
    "PRODUCTION_READY.md",
    "PRODUCTION_FIXES.md",
    "DEPLOYMENT_GUIDE.md",
    "CHANGES_SUMMARY.md",
    "test_production_features.py"
)
$missingFiles = @()
foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        Write-Host "   ❌ Missing required file: $file" -ForegroundColor Red
        $missingFiles += $file
        $allPassed = $false
    }
}
if ($missingFiles.Count -eq 0) {
    Write-Host "   ✅ All required files present" -ForegroundColor Green
}

# Check 3: Service files exist
Write-Host "3. Checking service files..." -ForegroundColor Yellow
$serviceFiles = @(
    "src/services/ai_tutor/conversational_tutor.py",
    "src/services/quiz_generation/quiz_generator.py",
    "src/services/quiz_generation/flashcard_generator.py",
    "src/services/code_analysis/code_analyzer.py",
    "src/shared/aws_clients/bedrock_client.py"
)
$missingServices = @()
foreach ($file in $serviceFiles) {
    if (-not (Test-Path $file)) {
        Write-Host "   ❌ Missing service file: $file" -ForegroundColor Red
        $missingServices += $file
        $allPassed = $false
    }
}
if ($missingServices.Count -eq 0) {
    Write-Host "   ✅ All service files present" -ForegroundColor Green
}

# Check 4: Python dependencies
Write-Host "4. Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python 3\.1[1-9]") {
        Write-Host "   ✅ Python version: $pythonVersion" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Python version: $pythonVersion (3.11+ recommended)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Python not found" -ForegroundColor Red
    $allPassed = $false
}

# Check 5: AWS CLI
Write-Host "5. Checking AWS CLI..." -ForegroundColor Yellow
try {
    $awsVersion = aws --version 2>&1
    Write-Host "   ✅ AWS CLI installed: $awsVersion" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  AWS CLI not found (optional but recommended)" -ForegroundColor Yellow
}

# Check 6: Frontend directory
Write-Host "6. Checking frontend..." -ForegroundColor Yellow
if (Test-Path "frontend") {
    if (Test-Path "frontend/package.json") {
        Write-Host "   ✅ Frontend directory present" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Frontend directory exists but package.json missing" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ⚠️  Frontend directory not found" -ForegroundColor Yellow
}

# Check 7: Documentation completeness
Write-Host "7. Checking documentation..." -ForegroundColor Yellow
$docFiles = @(
    "PRODUCTION_READY.md",
    "PRODUCTION_FIXES.md",
    "DEPLOYMENT_GUIDE.md",
    "CHANGES_SUMMARY.md"
)
$missingDocs = @()
foreach ($file in $docFiles) {
    if (-not (Test-Path $file)) {
        $missingDocs += $file
    }
}
if ($missingDocs.Count -eq 0) {
    Write-Host "   ✅ All documentation present" -ForegroundColor Green
} else {
    Write-Host "   ❌ Missing documentation: $($missingDocs -join ', ')" -ForegroundColor Red
    $allPassed = $false
}

# Summary
Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Verification Summary" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

if ($allPassed) {
    Write-Host "✅ ALL CHECKS PASSED" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your project is production-ready!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Start server: python -m uvicorn app:app --reload --port 8000" -ForegroundColor White
    Write-Host "  2. Run tests: python test_production_features.py" -ForegroundColor White
    Write-Host "  3. Read guide: PRODUCTION_READY.md" -ForegroundColor White
} else {
    Write-Host "❌ SOME CHECKS FAILED" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please review the errors above and fix them." -ForegroundColor Yellow
}

Write-Host ""
