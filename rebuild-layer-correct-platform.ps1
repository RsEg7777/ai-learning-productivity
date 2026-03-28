# Rebuild Lambda Layer with Correct Platform for Python 3.11
Write-Host "🔧 Rebuilding Lambda Layer with Correct Platform" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

$LAYER_NAME = "fastapi-pydantic-dependencies"
$REGION = "ap-south-1"

# Create layer directory structure
$layerDir = "lambda-layer-rebuild"
$pythonDir = "$layerDir/python"

Write-Host "`n📁 Creating layer directory structure..." -ForegroundColor Yellow
if (Test-Path $layerDir) {
    Remove-Item $layerDir -Recurse -Force
}
New-Item -ItemType Directory -Path $pythonDir -Force | Out-Null

# Create requirements file
$requirements = @"
fastapi==0.104.1
pydantic==2.5.0
pydantic[email]
mangum==0.17.0
structlog
boto3
"@

Set-Content -Path "$layerDir/requirements.txt" -Value $requirements

# Install with correct platform and Python version
Write-Host "`n📦 Installing dependencies for Lambda (Python 3.11, Linux x86_64)..." -ForegroundColor Yellow
Write-Host "  This ensures compatibility with AWS Lambda runtime" -ForegroundColor Gray

# Use Docker if available for better compatibility, otherwise use pip with platform flags
$useDocker = $false
try {
    docker --version | Out-Null
    $useDocker = $true
    Write-Host "  Using Docker for maximum compatibility..." -ForegroundColor Cyan
} catch {
    Write-Host "  Docker not available, using pip with platform flags..." -ForegroundColor Yellow
}

if ($useDocker) {
    # Use Docker to build in Lambda-like environment
    docker run --rm -v "${PWD}/${layerDir}:/var/task" -w /var/task public.ecr.aws/lambda/python:3.11 `
        pip install -r requirements.txt -t python --platform manylinux2014_x86_64 --only-binary=:all: --upgrade --no-cache-dir
} else {
    # Fallback to pip with platform specification
    pip install -r "$layerDir/requirements.txt" -t $pythonDir `
        --platform manylinux2014_x86_64 `
        --implementation cp `
        --python-version 3.11 `
        --only-binary=:all: `
        --upgrade `
        --no-cache-dir
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Failed to install dependencies!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Dependencies installed" -ForegroundColor Green

# Verify pydantic_core is present
if (Test-Path "$pythonDir/pydantic_core") {
    Write-Host "✅ pydantic_core found in layer" -ForegroundColor Green
    $pydanticCoreFiles = Get-ChildItem "$pythonDir/pydantic_core" -Recurse | Measure-Object
    Write-Host "  Files in pydantic_core: $($pydanticCoreFiles.Count)" -ForegroundColor Gray
} else {
    Write-Host "⚠️  WARNING: pydantic_core not found!" -ForegroundColor Yellow
}

# Create ZIP
Write-Host "`n📦 Creating layer ZIP..." -ForegroundColor Yellow
$layerZip = "fastapi-layer-v2.zip"
if (Test-Path $layerZip) {
    Remove-Item $layerZip -Force
}

Push-Location $layerDir
Compress-Archive -Path python -DestinationPath "../$layerZip" -Force
Pop-Location

$layerSize = (Get-Item $layerZip).Length / 1MB
Write-Host "✅ Layer package created: $layerZip ($([math]::Round($layerSize, 2)) MB)" -ForegroundColor Green

# Publish new version
Write-Host "`n🚀 Publishing new layer version..." -ForegroundColor Yellow

$layerResult = aws lambda publish-layer-version `
    --layer-name $LAYER_NAME `
    --description "FastAPI, Pydantic dependencies for Lambda (Python 3.11 compatible)" `
    --zip-file fileb://$layerZip `
    --compatible-runtimes python3.11 `
    --region $REGION `
    --output json

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to publish layer!" -ForegroundColor Red
    exit 1
}

$layer = $layerResult | ConvertFrom-Json
$layerArn = $layer.LayerVersionArn
$layerVersion = $layer.Version

Write-Host "✅ Layer version $layerVersion published!" -ForegroundColor Green
Write-Host "  ARN: $layerArn" -ForegroundColor Cyan

# Update Lambda function with new layer
Write-Host "`n🔗 Updating Lambda function with new layer..." -ForegroundColor Yellow
$FUNCTION_NAME = "ai-learning-app-fastapi"

aws lambda update-function-configuration `
    --function-name $FUNCTION_NAME `
    --layers $layerArn `
    --region $REGION `
    --no-cli-pager | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Function updated with new layer!" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to update function!" -ForegroundColor Red
    exit 1
}

# Wait and test
Write-Host "`n⏳ Waiting for function to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 20

Write-Host "`n🧪 Testing endpoint..." -ForegroundColor Cyan

$testBody = @{
    code = "print('Hello World!')\nprint(2 + 2)"
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
    Write-Host "❌ Still failing. Checking logs..." -ForegroundColor Red
    Start-Sleep -Seconds 3
    aws logs tail /aws/lambda/$FUNCTION_NAME --region $REGION --since 1m --format short
}

# Clean up
Remove-Item $layerDir -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "`n✅ Done!" -ForegroundColor Green
