# Update Lambda Function Code with Proper Handler
Write-Host "🚀 Updating Lambda Function Code" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

$FUNCTION_NAME = "ai-learning-app-fastapi"
$REGION = "ap-south-1"

# Create deployment package
Write-Host "`n📦 Creating deployment package..." -ForegroundColor Yellow

$packageDir = "lambda-deploy-temp"
if (Test-Path $packageDir) {
    Remove-Item $packageDir -Recurse -Force
}
New-Item -ItemType Directory -Path $packageDir | Out-Null

# Copy necessary files
Write-Host "  Copying application files..." -ForegroundColor Cyan
Copy-Item -Path "app.py" -Destination $packageDir -Force
Copy-Item -Path "lambda_handler.py" -Destination $packageDir -Force

if (Test-Path "src") {
    Copy-Item -Path "src" -Destination $packageDir -Recurse -Force
}

if (Test-Path "config") {
    Copy-Item -Path "config" -Destination $packageDir -Recurse -Force
}

# Create ZIP
Write-Host "  Creating ZIP file..." -ForegroundColor Cyan
$zipFile = "lambda-app-code.zip"
if (Test-Path $zipFile) {
    Remove-Item $zipFile -Force
}

Push-Location $packageDir
Compress-Archive -Path * -DestinationPath "../$zipFile" -Force
Pop-Location

# Clean up temp directory
Remove-Item $packageDir -Recurse -Force

$zipSize = (Get-Item $zipFile).Length / 1MB
Write-Host "✅ Package created: $zipFile ($([math]::Round($zipSize, 2)) MB)" -ForegroundColor Green

# Update Lambda function
Write-Host "`n🚀 Updating Lambda function code..." -ForegroundColor Yellow

aws lambda update-function-code `
    --function-name $FUNCTION_NAME `
    --zip-file fileb://$zipFile `
    --region $REGION `
    --no-cli-pager

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Lambda function code updated!" -ForegroundColor Green
    
    # Update handler configuration
    Write-Host "`n⚙️  Updating function configuration..." -ForegroundColor Yellow
    aws lambda update-function-configuration `
        --function-name $FUNCTION_NAME `
        --handler "lambda_handler.lambda_handler" `
        --region $REGION `
        --no-cli-pager | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Handler configuration updated!" -ForegroundColor Green
    }
    
    # Wait for function to be ready
    Write-Host "`n⏳ Waiting for function to be ready..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
    
    # Test the endpoint
    Write-Host "`n🧪 Testing Code Playground endpoint..." -ForegroundColor Cyan
    
    $testBody = @{
        code = "print('Hello from fixed Lambda!')"
        language = "python"
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "https://qtyf9c08b4.execute-api.ap-south-1.amazonaws.com/dev/playground/execute" `
            -Method Post `
            -Headers @{"Content-Type"="application/json"; "Authorization"="Bearer test-token"} `
            -Body $testBody `
            -TimeoutSec 30
        
        Write-Host "✅ SUCCESS! Code Playground is working!" -ForegroundColor Green
        Write-Host "`nResponse:" -ForegroundColor Cyan
        $response | ConvertTo-Json -Depth 5
    } catch {
        Write-Host "❌ Test failed!" -ForegroundColor Red
        Write-Host "Status: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Yellow
        
        Write-Host "`n🔍 Checking logs for errors..." -ForegroundColor Cyan
        Start-Sleep -Seconds 3
        aws logs tail /aws/lambda/$FUNCTION_NAME --region $REGION --since 1m --format short
    }
} else {
    Write-Host "❌ Failed to update Lambda function!" -ForegroundColor Red
}

Write-Host "`n✅ Done!" -ForegroundColor Green
