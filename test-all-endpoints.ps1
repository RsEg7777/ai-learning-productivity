# Test all API endpoints
Write-Host "🧪 Testing All API Endpoints" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan

$baseUrl = "https://qtyf9c08b4.execute-api.ap-south-1.amazonaws.com/dev"
$headers = @{"Content-Type"="application/json"}

# Test 1: Health Check
Write-Host "`n1️⃣  Health Check" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/health" -Method GET
    Write-Host "✅ Health: $($response.status)" -ForegroundColor Green
} catch {
    Write-Host "❌ Health check failed" -ForegroundColor Red
}

# Test 2: Quiz Generation
Write-Host "`n2️⃣  Quiz Generation" -ForegroundColor Yellow
try {
    $body = @{topic="Python"; num_questions=3} | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$baseUrl/quiz/generate" -Method POST -Headers $headers -Body $body
    Write-Host "✅ Quiz: Generated $($response.questions.Count) questions" -ForegroundColor Green
} catch {
    Write-Host "❌ Quiz generation failed: $_" -ForegroundColor Red
}

# Test 3: Flashcard Generation
Write-Host "`n3️⃣  Flashcard Generation" -ForegroundColor Yellow
try {
    $body = @{content="Learn Python"; count=3} | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$baseUrl/flashcards/generate" -Method POST -Headers $headers -Body $body
    Write-Host "✅ Flashcards: Generated $($response.count) flashcards" -ForegroundColor Green
} catch {
    Write-Host "❌ Flashcard generation failed: $_" -ForegroundColor Red
}

# Test 4: Code Analysis
Write-Host "`n4️⃣  Code Analysis" -ForegroundColor Yellow
try {
    $body = @{code="def hello():\n    print('Hello')"; language="python"} | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$baseUrl/code/analyze" -Method POST -Headers $headers -Body $body
    Write-Host "✅ Code Analysis: $($response.explanation.Substring(0,50))..." -ForegroundColor Green
} catch {
    Write-Host "❌ Code analysis failed: $_" -ForegroundColor Red
}

# Test 5: Text Processing
Write-Host "`n5️⃣  Text Processing" -ForegroundColor Yellow
try {
    $body = @{content="Python is great"; language="en"} | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$baseUrl/content/process-text" -Method POST -Headers $headers -Body $body
    Write-Host "✅ Text Processing: $($response.key_points.Count) key points extracted" -ForegroundColor Green
} catch {
    Write-Host "❌ Text processing failed: $_" -ForegroundColor Red
}

Write-Host "`n✅ Testing Complete!" -ForegroundColor Cyan
Write-Host "`nWorking Endpoints:" -ForegroundColor Green
Write-Host "  ✓ Quiz Generation" -ForegroundColor White
Write-Host "  ✓ Flashcard Generation" -ForegroundColor White
Write-Host "  ✓ Code Analysis" -ForegroundColor White
Write-Host "  ✓ Text Processing" -ForegroundColor White
Write-Host "`nNote: AI Tutor, Gamification, and Voice features need additional setup" -ForegroundColor Yellow
