# Create Complete Lambda Layer with All Dependencies
Write-Host "🔧 Creating Complete Lambda Layer" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

$LAYER_NAME = "ai-learning-complete-dependencies"
$REGION = "ap-south-1"

# Create layer directory
$layerDir = "lambda-layer-complete"
$pythonDir = "$layerDir/python"

Write-Host "`n📁 Creating layer directory..." -ForegroundColor Yellow
if (Test-Path $layerDir) {
    Remove-Item $layerDir -Recurse -Force
}
New-Item -ItemType Directory -Path $pythonDir -Force | Out-Null

# Create requirements for Lambda (excluding uvicorn which is not needed in Lambda)
$requirements = @"
boto3>=1.34.0
botocore>=1.34.0
aws-lambda-powertools>=2.30.0
fastapi>=0.104.0
pydantic>=2.5.0
pydantic[email]
pydantic-settings>=2.1.0
PyPDF2>=3.0.0
pypdf>=3.17.0
requests>=2.31.0
urllib3>=2.1.0
python-dateutil>=2.8.2
orjson>=3.9.10
structlog>=23.2.0
typing-extensions>=4.9.0
pyyaml>=6.0.1
python-dotenv>=1.0.0
mangum>=0.17.0
"@

Set-Content -Path "$layerDir/requirements.txt" -Value $requirements

Write-Host "`n📦 Installing all dependencies (this will take a few minutes)..." -ForegroundColor Yellow
Write-Host "  Target platform: Linux x86_64, Python 3.11" -ForegroundColor Gray

pip install -r "$layerDir/requirements.txt" -t $pythonDir `
    --platform manylinux2014_x86_64 `
    --implementation cp `
    --python-version 3.11 `
    --only-binary=:all: `
    --upgrade `
    --no-cache-dir

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Failed to install dependencies!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ All dependencies installed" -ForegroundColor Green

# Verify key modules
$keyModules = @("pydantic_core", "structlog", "PyPDF2", "fastapi", "mangum")
foreach ($module in $keyModules) {
    if (Test-Path "$pythonDir/$module*") {
        Write-Host "  ✓ $module" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $module NOT FOUND!" -ForegroundColor Red
    }
}

# Create ZIP
Write-Host "`n📦 Creating layer ZIP..." -ForegroundColor Yellow
$layerZip = "complete-layer.zip"
if (Test-Path $layerZip) {
    Remove-Item $layerZip -Force
}

Push-Location $layerDir
Compress-Archive -Path python -DestinationPath "../$layerZip" -Force
Pop-Location

$layerSize = (Get-Item $layerZip).Length / 1MB
Write-Host "✅ Layer created: $layerZip ($([math]::Round($layerSize, 2)) MB)" -ForegroundColor Green

if ($layerSize -gt 50) {
    Write-Host "⚠️  Layer is larger than 50MB, will need S3 upload" -ForegroundColor Yellow
}

# Upload to S3 if needed
if ($layerSize -gt 50) {
    Write-Host "`n📤 Uploading to S3..." -ForegroundColor Yellow
    $bucketName = "ai-learning-lambda-layers"
    
    # Create bucket if needed
    aws s3 mb "s3://$bucketName" --region $REGION 2>$null
    
    # Upload
    aws s3 cp $layerZip "s3://$bucketName/$layerZip" --region $REGION
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ S3 upload failed!" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ Uploaded to S3" -ForegroundColor Green
    
    # Publish from S3
    Write-Host "`n🚀 Publishing layer from S3..." -ForegroundColor Yellow
    $layerResult = aws lambda publish-layer-version `
        --layer-name $LAYER_NAME `
        --description "Complete dependencies for AI Learning Assistant" `
        --content S3Bucket=$bucketName,S3Key=$layerZip `
        --compatible-runtimes python3.11 `
        --region $REGION `
        --output json
} else {
    # Publish directly
    Write-Host "`n🚀 Publishing layer..." -ForegroundColor Yellow
    $layerResult = aws lambda publish-layer-version `
        --layer-name $LAYER_NAME `
        --description "Complete dependencies for AI Learning Assistant" `
        --zip-file fileb://$layerZip `
        --compatible-runtimes python3.11 `
        --region $REGION `
        --output json
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to publish layer!" -ForegroundColor Red
    exit 1
}

$layer = $layerResult | ConvertFrom-Json
$layerArn = $layer.LayerVersionArn

Write-Host "✅ Layer published!" -ForegroundColor Green
Write-Host "  ARN: $layerArn" -ForegroundColor Cyan

# Update Lambda function
Write-Host "`n🔗 Updating Lambda function..." -ForegroundColor Yellow
$FUNCTION_NAME = "ai-learning-app-fastapi"

aws lambda update-function-configuration `
    --function-name $FUNCTION_NAME `
    --layers $layerArn `
    --region $REGION `
    --no-cli-pager | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Function updated!" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to update function!" -ForegroundColor Red
    exit 1
}

# Wait and test
Write-Host "`n⏳ Waiting for function to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 25

Write-Host "`n🧪 Testing Code Playground..." -ForegroundColor Cyan

$testBody = @{
    code = "print('Hello from Code Playground!')\nprint('2 + 2 =', 2 + 2)"
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
    Write-Host "Checking logs..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
    aws logs tail /aws/lambda/$FUNCTION_NAME --region $REGION --since 1m --format short | Select-Object -Last 20
}

# Clean up
Remove-Item $layerDir -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "`n✅ Done!" -ForegroundColor Green
