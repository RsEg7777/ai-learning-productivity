# Create Lambda Layer with FastAPI and Pydantic Dependencies
Write-Host "🔧 Creating Lambda Layer for FastAPI Dependencies" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

$LAYER_NAME = "fastapi-pydantic-dependencies"
$REGION = "ap-south-1"
$PYTHON_VERSION = "python3.11"

# Create layer directory structure
$layerDir = "lambda-layer-build"
$pythonDir = "$layerDir/python"

Write-Host "`n📁 Creating layer directory structure..." -ForegroundColor Yellow
if (Test-Path $layerDir) {
    Remove-Item $layerDir -Recurse -Force
}
New-Item -ItemType Directory -Path $pythonDir -Force | Out-Null

# Create requirements file with all necessary dependencies
# Using compatible versions without pinning pydantic-core (let pip resolve it)
$requirements = @"
fastapi==0.104.1
pydantic==2.5.0
mangum==0.17.0
starlette==0.27.0
typing-extensions>=4.8.0
annotated-types>=0.6.0
anyio>=3.7.1
idna>=3.6
sniffio>=1.3.0
"@

Write-Host "📝 Creating requirements.txt..." -ForegroundColor Cyan
Set-Content -Path "$layerDir/requirements.txt" -Value $requirements

# Install dependencies into the python directory
Write-Host "`n📦 Installing dependencies (this may take a few minutes)..." -ForegroundColor Yellow
Write-Host "  Target: $pythonDir" -ForegroundColor Gray

pip install -r "$layerDir/requirements.txt" -t $pythonDir --platform manylinux2014_x86_64 --only-binary=:all: --upgrade --no-cache-dir

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Failed to install dependencies!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Dependencies installed" -ForegroundColor Green

# Create ZIP file for the layer
Write-Host "`n📦 Creating layer ZIP file..." -ForegroundColor Yellow
$layerZip = "fastapi-layer.zip"
if (Test-Path $layerZip) {
    Remove-Item $layerZip -Force
}

Push-Location $layerDir
Compress-Archive -Path python -DestinationPath "../$layerZip" -Force
Pop-Location

$layerSize = (Get-Item $layerZip).Length / 1MB
Write-Host "✅ Layer package created: $layerZip ($([math]::Round($layerSize, 2)) MB)" -ForegroundColor Green

# Publish the layer to AWS Lambda
Write-Host "`n🚀 Publishing Lambda Layer to AWS..." -ForegroundColor Yellow

$layerResult = aws lambda publish-layer-version `
    --layer-name $LAYER_NAME `
    --description "FastAPI, Pydantic, and Mangum dependencies for Lambda" `
    --zip-file fileb://$layerZip `
    --compatible-runtimes python3.11 python3.10 python3.9 `
    --region $REGION `
    --output json

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Failed to publish layer!" -ForegroundColor Red
    Write-Host "  The layer might be too large. Trying S3 upload method..." -ForegroundColor Yellow
    
    # Try uploading to S3 first
    $bucketName = "ai-learning-lambda-layers"
    
    # Create bucket if it doesn't exist
    aws s3 mb "s3://$bucketName" --region $REGION 2>$null
    
    # Upload to S3
    aws s3 cp $layerZip "s3://$bucketName/$layerZip" --region $REGION
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Uploaded to S3" -ForegroundColor Green
        
        # Publish from S3
        $layerResult = aws lambda publish-layer-version `
            --layer-name $LAYER_NAME `
            --description "FastAPI, Pydantic, and Mangum dependencies for Lambda" `
            --content S3Bucket=$bucketName,S3Key=$layerZip `
            --compatible-runtimes python3.11 python3.10 python3.9 `
            --region $REGION `
            --output json
    } else {
        Write-Host "❌ S3 upload failed!" -ForegroundColor Red
        exit 1
    }
}

$layer = $layerResult | ConvertFrom-Json
$layerArn = $layer.LayerVersionArn

Write-Host "✅ Layer published successfully!" -ForegroundColor Green
Write-Host "  Layer ARN: $layerArn" -ForegroundColor Cyan

# Attach the layer to the Lambda function
Write-Host "`n🔗 Attaching layer to Lambda function..." -ForegroundColor Yellow
$FUNCTION_NAME = "ai-learning-app-fastapi"

# Get current function configuration
$currentConfig = aws lambda get-function-configuration `
    --function-name $FUNCTION_NAME `
    --region $REGION `
    --output json | ConvertFrom-Json

# Get existing layers (if any)
$existingLayers = @()
if ($currentConfig.Layers) {
    $existingLayers = $currentConfig.Layers | ForEach-Object { $_.Arn }
}

# Add new layer (avoid duplicates)
$allLayers = @($existingLayers | Where-Object { $_ -notlike "*$LAYER_NAME*" }) + @($layerArn)

# Update function with layers
aws lambda update-function-configuration `
    --function-name $FUNCTION_NAME `
    --layers $allLayers `
    --region $REGION `
    --no-cli-pager | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Layer attached to function successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to attach layer to function!" -ForegroundColor Red
    Write-Host "  You can manually attach it using the ARN: $layerArn" -ForegroundColor Yellow
    exit 1
}

# Wait for function to update
Write-Host "`n⏳ Waiting for function to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Clean up
Write-Host "`n🧹 Cleaning up temporary files..." -ForegroundColor Gray
Remove-Item $layerDir -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "`n✅ Lambda Layer setup complete!" -ForegroundColor Green
Write-Host "`n📋 Summary:" -ForegroundColor Cyan
Write-Host "  Layer Name: $LAYER_NAME" -ForegroundColor White
Write-Host "  Layer ARN: $layerArn" -ForegroundColor White
Write-Host "  Function: $FUNCTION_NAME" -ForegroundColor White
Write-Host "  Region: $REGION" -ForegroundColor White

# Test the endpoint
Write-Host "`n🧪 Testing Code Playground endpoint..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

if (Test-Path "test-playground-endpoint.ps1") {
    ./test-playground-endpoint.ps1
} else {
    Write-Host "  Test script not found. Testing manually..." -ForegroundColor Yellow
    
    $testBody = @{
        code = "print('Hello from Lambda Layer!')"
        language = "python"
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "https://qtyf9c08b4.execute-api.ap-south-1.amazonaws.com/dev/playground/execute" `
            -Method Post `
            -Headers @{"Content-Type"="application/json"; "Authorization"="Bearer test-token"} `
            -Body $testBody
        
        Write-Host "✅ SUCCESS! Endpoint is working!" -ForegroundColor Green
        $response | ConvertTo-Json -Depth 5
    } catch {
        Write-Host "❌ Test failed. Check logs:" -ForegroundColor Red
        Write-Host "  aws logs tail /aws/lambda/$FUNCTION_NAME --region $REGION --follow" -ForegroundColor Yellow
    }
}

Write-Host "`n🎉 Done! Your Code Playground should now work!" -ForegroundColor Green
