# Test Code Playground Endpoint
Write-Host "🧪 Testing Code Playground Endpoint" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

$API_URL = "https://qtyf9c08b4.execute-api.ap-south-1.amazonaws.com/dev"
$headers = @{
    "Content-Type" = "application/json"
    "Authorization" = "Bearer test-token"
}

$body = @{
    code = "print('Hello, World!')"
    language = "python"
} | ConvertTo-Json

Write-Host "`n📤 Sending request to: $API_URL/playground/execute" -ForegroundColor Yellow
Write-Host "Body: $body" -ForegroundColor Gray

try {
    $response = Invoke-WebRequest -Uri "$API_URL/playground/execute" `
        -Method Post `
        -Headers $headers `
        -Body $body `
        -UseBasicParsing
    
    Write-Host "`n✅ SUCCESS!" -ForegroundColor Green
    Write-Host "Status Code: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Cyan
    $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
} catch {
    Write-Host "`n❌ ERROR!" -ForegroundColor Red
    Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    Write-Host "Error Message:" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host $responseBody -ForegroundColor Yellow
    } else {
        Write-Host $_.Exception.Message -ForegroundColor Yellow
    }
}

Write-Host "`n🔍 Checking Lambda function logs..." -ForegroundColor Cyan
Write-Host "Run this command to see recent logs:" -ForegroundColor Yellow
Write-Host "aws logs tail /aws/lambda/ai-learning-app-fastapi --region ap-south-1 --follow" -ForegroundColor White
