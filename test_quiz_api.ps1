# Use the ID Token (not Access Token) for API Gateway Cognito Authorizer
$idToken = "eyJraWQiOiJBQzkwNVBWczhuTmJ0dXJ5aExjWGxRYmtERWZ2SEpFa3Jsdmg0bUlON05ZPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI1MTIzMGQ5YS1lMDgxLTcwMDgtZmU2Mi1mYmJiMjYwNTFmNjciLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAuYXAtc291dGgtMS5hbWF6b25hd3MuY29tXC9hcC1zb3V0aC0xX2NmQTlkejE1aCIsImNvZ25pdG86dXNlcm5hbWUiOiJ0ZXN0dXNlciIsIm9yaWdpbl9qdGkiOiIyYzE1MDAyOS1iYWM5LTQ1YTItOWE4My03ZWMxN2Q5YmYwNzUiLCJhdWQiOiI0OW43YWtwOWx1Ymx2cGEwNGRidDJxam9hMiIsImV2ZW50X2lkIjoiZmE3NmFiY2MtNWQzNS00NDUwLWFjMGUtMWE3NGUwYTNkZDA3IiwidG9rZW5fdXNlIjoiaWQiLCJhdXRoX3RpbWUiOjE3Njk4ODE3MzgsImV4cCI6MTc2OTg4NTMzOCwiaWF0IjoxNzY5ODgxNzM4LCJqdGkiOiIwY2NhNTZhZC0wYjFiLTQxZDgtODExYi0xZTdkNGQ5N2RlMWUiLCJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20ifQ.WsWexp9ZkikLS02gZvLmw4XJJdAz8IXOu6xayL5MsVNNrJ5_bjfv3uOEfeFqVBZcJL0rBH255tnrrCTWbcv1rjYfsajZdo-ol8n_orCLkXiuDoqIiz64ezC4UafrlMCypE2Y_eyDChiQbzjuZi_1DiMwsBlJXJobCryo5-TtmYZEwCU5KfXFASBim3itVivOeg0ZdgSlujYAdCitL_RXFLOnimtCRTlFwz9O4bl7ILWexW3oRJ48PzwHg6twrcViC7sBSg910faqENvIBROJjh6Z146UBvxNFNIyuOwAQW8oelQtca9cvuD0hhkGBCKNc4T67FkQlFyolkbyA2vA9A"

$headers = @{
    "Authorization" = $idToken
    "Content-Type" = "application/json"
}

$body = @{
    content = "Python is a high-level programming language. It supports multiple programming paradigms including procedural, object-oriented, and functional programming. Python uses dynamic typing and automatic memory management."
    question_count = 5
} | ConvertTo-Json

Write-Host "`n=== Testing AI Learning Assistant API ===" -ForegroundColor Cyan
Write-Host "Endpoint: Quiz Generation" -ForegroundColor Yellow
Write-Host "Content: Python programming basics`n" -ForegroundColor Gray

try {
    $response = Invoke-RestMethod -Uri "https://qtyf9c08b4.execute-api.ap-south-1.amazonaws.com/dev/quiz/generate" -Method Post -Headers $headers -Body $body -TimeoutSec 30
    
    Write-Host "✅ SUCCESS! Quiz Generated`n" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Cyan
    $response | ConvertTo-Json -Depth 10
    
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Yellow
    }
}
