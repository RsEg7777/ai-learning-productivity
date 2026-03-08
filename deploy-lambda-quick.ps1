# Quick Lambda deployment script - updates all functions with demo mode
Write-Host "🚀 Quick Lambda Deployment with Demo Mode" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Step 1: Package Lambda code
Write-Host "`n📦 Packaging Lambda code..." -ForegroundColor Yellow
if (Test-Path "lambda-code.zip") {
    Remove-Item "lambda-code.zip" -Force
}

Compress-Archive -Path src -DestinationPath lambda-code.zip -Force
Write-Host "✅ Package created: lambda-code.zip" -ForegroundColor Green

# Step 2: Update Lambda functions
$functions = @(
    "ai-learning-assistant-quiz-generation-dev",
    "ai-learning-assistant-flashcard-generation-dev",
    "ai-learning-assistant-code-analysis-dev",
    "ai-learning-assistant-text-processing-dev"
)

Write-Host "`n🔄 Updating Lambda functions..." -ForegroundColor Yellow

foreach ($func in $functions) {
    Write-Host "  Updating $func..." -ForegroundColor Cyan
    
    # Update function code
    aws lambda update-function-code `
        --function-name $func `
        --zip-file fileb://lambda-code.zip `
        --region ap-south-1 `
        --no-cli-pager | Out-Null
    
    # Enable demo mode
    aws lambda update-function-configuration `
        --function-name $func `
        --environment "Variables={DEMO_MODE=true,ENVIRONMENT=dev}" `
        --region ap-south-1 `
        --no-cli-pager | Out-Null
    
    Write-Host "  ✅ $func updated" -ForegroundColor Green
    Start-Sleep -Seconds 2
}

Write-Host "`n✅ All Lambda functions updated with demo mode!" -ForegroundColor Green
Write-Host "🎉 Your app should now work without Bedrock rate limits" -ForegroundColor Cyan
Write-Host "`nTest your endpoints:" -ForegroundColor Yellow
Write-Host "  Quiz: https://qtyf9c08b4.execute-api.ap-south-1.amazonaws.com/dev/quiz/generate" -ForegroundColor White
Write-Host "  Flashcards: https://qtyf9c08b4.execute-api.ap-south-1.amazonaws.com/dev/flashcards/generate" -ForegroundColor White
Write-Host "  Code Analysis: https://qtyf9c08b4.execute-api.ap-south-1.amazonaws.com/dev/code/analyze" -ForegroundColor White
