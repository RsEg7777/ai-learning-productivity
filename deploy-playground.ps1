# Deploy Code Playground Lambda Function
Write-Host "🚀 Deploying Code Playground Lambda Function" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

$FUNCTION_NAME = "ai-learning-assistant-code-playground-dev"
$REGION = "ap-south-1"
$API_ID = "qtyf9c08b4"

# Step 1: Check if function exists
Write-Host "`n🔍 Checking if Lambda function exists..." -ForegroundColor Yellow
$functionExists = aws lambda get-function --function-name $FUNCTION_NAME --region $REGION 2>$null

if ($functionExists) {
    Write-Host "✅ Function exists, updating..." -ForegroundColor Green
    
    # Package code
    Write-Host "`n📦 Packaging Lambda code..." -ForegroundColor Yellow
    if (Test-Path "lambda-code.zip") {
        Remove-Item "lambda-code.zip" -Force
    }
    Compress-Archive -Path src -DestinationPath lambda-code.zip -Force
    
    # Update function code
    aws lambda update-function-code `
        --function-name $FUNCTION_NAME `
        --zip-file fileb://lambda-code.zip `
        --region $REGION `
        --no-cli-pager
    
    Write-Host "✅ Function code updated" -ForegroundColor Green
} else {
    Write-Host "❌ Function does not exist. Creating new function..." -ForegroundColor Yellow
    Write-Host "⚠️  This requires IAM role ARN. Please create the function manually or use the full deployment script." -ForegroundColor Red
    Write-Host "`nAlternative: Add playground endpoint to existing Lambda function" -ForegroundColor Yellow
    exit 1
}

# Step 2: Add API Gateway route
Write-Host "`n🔗 Adding API Gateway route..." -ForegroundColor Yellow

# Get API Gateway integrations
$integrations = aws apigatewayv2 get-integrations --api-id $API_ID --region $REGION --output json | ConvertFrom-Json

# Check if integration exists
$playgroundIntegration = $integrations.Items | Where-Object { $_.IntegrationUri -like "*$FUNCTION_NAME*" }

if (-not $playgroundIntegration) {
    Write-Host "Creating new integration..." -ForegroundColor Cyan
    
    $integration = aws apigatewayv2 create-integration `
        --api-id $API_ID `
        --integration-type AWS_PROXY `
        --integration-uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:${REGION}:$(aws sts get-caller-identity --query Account --output text):function:${FUNCTION_NAME}/invocations" `
        --payload-format-version 2.0 `
        --region $REGION `
        --output json | ConvertFrom-Json
    
    $integrationId = $integration.IntegrationId
    Write-Host "✅ Integration created: $integrationId" -ForegroundColor Green
} else {
    $integrationId = $playgroundIntegration.IntegrationId
    Write-Host "✅ Integration already exists: $integrationId" -ForegroundColor Green
}

# Create route
Write-Host "Creating route for POST /playground/execute..." -ForegroundColor Cyan
$route = aws apigatewayv2 create-route `
    --api-id $API_ID `
    --route-key "POST /playground/execute" `
    --target "integrations/$integrationId" `
    --region $REGION `
    --output json 2>$null

if ($route) {
    Write-Host "✅ Route created successfully" -ForegroundColor Green
} else {
    Write-Host "⚠️  Route might already exist or creation failed" -ForegroundColor Yellow
}

# Step 3: Deploy API
Write-Host "`n🚀 Deploying API Gateway..." -ForegroundColor Yellow
aws apigatewayv2 create-deployment `
    --api-id $API_ID `
    --stage-name dev `
    --region $REGION `
    --no-cli-pager

Write-Host "`n✅ Deployment complete!" -ForegroundColor Green
Write-Host "`nTest the endpoint:" -ForegroundColor Yellow
Write-Host "  curl -X POST https://$API_ID.execute-api.$REGION.amazonaws.com/dev/playground/execute -H 'Content-Type: application/json' -d '{\"code\":\"print('Hello')\",\"language\":\"python\"}'" -ForegroundColor White
