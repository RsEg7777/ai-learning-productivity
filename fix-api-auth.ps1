# Script to remove Cognito authorization from API Gateway endpoints

$API_ID = "qtyf9c08b4"

# List of resources with POST methods that need auth removed
$resources = @(
    @{id="bproyj"; path="/quiz/generate"},
    @{id="uvjaf9"; path="/quiz/submit"},
    @{id="h44jxn"; path="/flashcards/generate"},
    @{id="5bxbhx"; path="/code/analyze"},
    @{id="1sdhvk"; path="/code/explain-algorithm"},
    @{id="a4efw2"; path="/content/upload"},
    @{id="m4g810"; path="/content/process-text"},
    @{id="g9l616"; path="/voice/transcribe"},
    @{id="gx6dn5"; path="/voice/synthesize"}
)

Write-Host "Removing Cognito authorization from API Gateway endpoints..." -ForegroundColor Cyan

foreach ($resource in $resources) {
    Write-Host "Updating $($resource.path)..." -ForegroundColor Yellow
    
    try {
        # Update the POST method to remove authorization
        aws apigateway update-method `
            --rest-api-id $API_ID `
            --resource-id $resource.id `
            --http-method POST `
            --patch-operations "op=replace,path=/authorizationType,value=NONE" `
            2>&1 | Out-Null
        
        Write-Host "  ✅ Updated $($resource.path)" -ForegroundColor Green
    } catch {
        Write-Host "  ❌ Failed to update $($resource.path): $_" -ForegroundColor Red
    }
}

Write-Host "`nCreating new deployment..." -ForegroundColor Cyan

# Create a new deployment to apply changes
$deployment = aws apigateway create-deployment `
    --rest-api-id $API_ID `
    --stage-name dev `
    --description "Removed Cognito authorization" `
    --output json | ConvertFrom-Json

if ($deployment) {
    Write-Host "✅ Deployment created successfully!" -ForegroundColor Green
    Write-Host "API URL: https://$API_ID.execute-api.ap-south-1.amazonaws.com/dev" -ForegroundColor Cyan
} else {
    Write-Host "❌ Deployment failed" -ForegroundColor Red
}

Write-Host "`nTesting health endpoint..." -ForegroundColor Cyan
curl https://$API_ID.execute-api.ap-south-1.amazonaws.com/dev/health
