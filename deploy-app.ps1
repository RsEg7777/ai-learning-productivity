# Deploy app.py to AWS Lambda using Mangum adapter

Write-Host "Creating Lambda deployment package..." -ForegroundColor Cyan

# Create deployment directory
$deployDir = "lambda-deploy"
if (Test-Path $deployDir) { Remove-Item $deployDir -Recurse -Force }
New-Item -ItemType Directory -Path $deployDir | Out-Null

# Copy only essential files
Write-Host "Copying app.py..." -ForegroundColor Yellow
Copy-Item app.py $deployDir/

# Create a minimal requirements file
@"
fastapi==0.104.1
mangum==0.17.0
boto3==1.34.0
pydantic==2.5.0
"@ | Out-File -FilePath "$deployDir/requirements.txt" -Encoding utf8

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r "$deployDir/requirements.txt" -t $deployDir --quiet

# Create Lambda handler
@"
from mangum import Mangum
from app import app

handler = Mangum(app, lifespan="off")
"@ | Out-File -FilePath "$deployDir/lambda_handler.py" -Encoding utf8

# Create zip
Write-Host "Creating deployment package..." -ForegroundColor Yellow
$zipFile = "app-lambda.zip"
if (Test-Path $zipFile) { Remove-Item $zipFile -Force }

Push-Location $deployDir
Compress-Archive -Path * -DestinationPath "../$zipFile" -CompressionLevel Optimal
Pop-Location

Write-Host "Deployment package created: $zipFile" -ForegroundColor Green
Write-Host "Size: $((Get-Item $zipFile).Length / 1MB) MB" -ForegroundColor Cyan

# Check if Lambda function exists
$functionName = "ai-learning-app-fastapi"
$functionExists = aws lambda get-function --function-name $functionName 2>&1 | Select-String "FunctionName"

if ($functionExists) {
    Write-Host "Updating existing Lambda function..." -ForegroundColor Yellow
    aws lambda update-function-code `
        --function-name $functionName `
        --zip-file "fileb://$zipFile"
} else {
    Write-Host "Creating new Lambda function..." -ForegroundColor Yellow
    
    # Create execution role if needed
    $roleName = "ai-learning-app-lambda-role"
    $roleArn = aws iam get-role --role-name $roleName --query "Role.Arn" --output text 2>$null
    
    if (-not $roleArn) {
        Write-Host "Creating IAM role..." -ForegroundColor Yellow
        
        $trustPolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "lambda.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
"@
        
        $trustPolicy | Out-File -FilePath "trust-policy.json" -Encoding utf8
        
        aws iam create-role `
            --role-name $roleName `
            --assume-role-policy-document file://trust-policy.json
        
        # Attach policies
        aws iam attach-role-policy `
            --role-name $roleName `
            --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        
        aws iam attach-role-policy `
            --role-name $roleName `
            --policy-arn "arn:aws:iam::aws:policy/AmazonBedrockFullAccess"
        
        aws iam attach-role-policy `
            --role-name $roleName `
            --policy-arn "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
        
        Start-Sleep -Seconds 10
        $roleArn = aws iam get-role --role-name $roleName --query "Role.Arn" --output text
    }
    
    aws lambda create-function `
        --function-name $functionName `
        --runtime python3.11 `
        --role $roleArn `
        --handler lambda_handler.handler `
        --zip-file "fileb://$zipFile" `
        --timeout 30 `
        --memory-size 512 `
        --environment "Variables={AWS_REGION=ap-south-1}"
}

Write-Host "`n✅ Deployment complete!" -ForegroundColor Green
Write-Host "Function name: $functionName" -ForegroundColor Cyan

# Clean up
Remove-Item $deployDir -Recurse -Force
Remove-Item trust-policy.json -ErrorAction SilentlyContinue

Write-Host "`nNext: Add this Lambda to your API Gateway" -ForegroundColor Yellow
