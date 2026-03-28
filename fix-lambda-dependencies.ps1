# Fix Lambda Dependencies for FastAPI App
Write-Host "🔧 Fixing Lambda Dependencies" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan

$FUNCTION_NAME = "ai-learning-app-fastapi"
$REGION = "ap-south-1"

Write-Host "`n📦 Creating deployment package with dependencies..." -ForegroundColor Yellow

# Create a temporary directory for packaging
$tempDir = "lambda-package-temp"
if (Test-Path $tempDir) {
    Remove-Item $tempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

# Copy source code
Write-Host "  Copying source code..." -ForegroundColor Cyan
Copy-Item -Path "app.py" -Destination $tempDir -Force
if (Test-Path "src") {
    Copy-Item -Path "src" -Destination $tempDir -Recurse -Force
}

# Create requirements file for Lambda
$requirements = @"
fastapi==0.104.1
mangum==0.17.0
pydantic==2.5.0
boto3==1.34.0
"@

Set-Content -Path "$tempDir/requirements.txt" -Value $requirements

# Install dependencies
Write-Host "  Installing Python dependencies..." -ForegroundColor Cyan
Push-Location $tempDir
pip install -r requirements.txt -t . --platform manylinux2014_x86_64 --only-binary=:all: --upgrade
Pop-Location

# Create lambda_handler.py wrapper
$lambdaHandler = @"
from mangum import Mangum
from app import app

# Wrap FastAPI app with Mangum for Lambda
lambda_handler = Mangum(app, lifespan="off")
"@

Set-Content -Path "$tempDir/lambda_handler.py" -Value $lambdaHandler

# Create deployment package
Write-Host "  Creating ZIP file..." -ForegroundColor Cyan
if (Test-Path "lambda-fastapi-fixed.zip") {
    Remove-Item "lambda-fastapi-fixed.zip" -Force
}

Push-Location $tempDir
Compress-Archive -Path * -DestinationPath "../lambda-fastapi-fixed.zip" -Force
Pop-Location

# Clean up temp directory
Remove-Item $tempDir -Recurse -Force

Write-Host "✅ Package created: lambda-fastapi-fixed.zip" -ForegroundColor Green

# Check package size
$packageSize = (Get-Item "lambda-fastapi-fixed.zip").Length / 1MB
Write-Host "  Package size: $([math]::Round($packageSize, 2)) MB" -ForegroundColor Gray

if ($packageSize -gt 50) {
    Write-Host "`n⚠️  WARNING: Package is larger than 50MB!" -ForegroundColor Yellow
    Write-Host "  You'll need to use S3 or Lambda Layers for deployment." -ForegroundColor Yellow
    Write-Host "  Uploading to S3..." -ForegroundColor Cyan
    
    $bucketName = "ai-learning-lambda-deployments"
    $s3Key = "lambda-fastapi-fixed.zip"
    
    # Try to upload to S3
    aws s3 cp lambda-fastapi-fixed.zip "s3://$bucketName/$s3Key" --region $REGION 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Uploaded to S3" -ForegroundColor Green
        
        # Update Lambda from S3
        Write-Host "`n🚀 Updating Lambda function from S3..." -ForegroundColor Yellow
        aws lambda update-function-code `
            --function-name $FUNCTION_NAME `
            --s3-bucket $bucketName `
            --s3-key $s3Key `
            --region $REGION `
            --no-cli-pager
    } else {
        Write-Host "❌ S3 upload failed. Package is too large for direct upload." -ForegroundColor Red
        Write-Host "  Please use Lambda Layers instead." -ForegroundColor Yellow
        exit 1
    }
} else {
    # Update Lambda function directly
    Write-Host "`n🚀 Updating Lambda function..." -ForegroundColor Yellow
    aws lambda update-function-code `
        --function-name $FUNCTION_NAME `
        --zip-file fileb://lambda-fastapi-fixed.zip `
        --region $REGION `
        --no-cli-pager
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Lambda function updated successfully!" -ForegroundColor Green
    Write-Host "`n⏳ Waiting for function to be ready..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    Write-Host "`n🧪 Testing the endpoint..." -ForegroundColor Cyan
    ./test-playground-endpoint.ps1
} else {
    Write-Host "`n❌ Lambda update failed!" -ForegroundColor Red
}
