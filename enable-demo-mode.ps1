# Enable demo mode for all Lambda functions to bypass Bedrock rate limits

Write-Host "Enabling demo mode for all Lambda functions..." -ForegroundColor Cyan

$functions = @(
    "ai-learning-assistant-quiz-generation-dev",
    "ai-learning-assistant-flashcard-generation-dev",
    "ai-learning-assistant-code-analysis-dev",
    "ai-learning-assistant-text-processing-dev"
)

foreach ($func in $functions) {
    Write-Host "Updating $func..." -ForegroundColor Yellow
    aws lambda update-function-configuration `
        --function-name $func `
        --environment "Variables={DEMO_MODE=true,ENVIRONMENT=dev}" `
        --region ap-south-1 `
        --no-cli-pager | Out-Null
    Write-Host "✅ $func" -ForegroundColor Green
}

Write-Host "`n✅ Demo mode enabled! Your app will now work without Bedrock." -ForegroundColor Green
Write-Host "Note: Responses will be pre-generated demo data." -ForegroundColor Yellow
