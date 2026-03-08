# PowerShell script to test all API endpoints
# Run this to verify your backend is working correctly

$API_URL = "https://qtyf9c08b4.execute-api.ap-south-1.amazonaws.com/dev"
$TOKEN = "test-token"

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Testing AI Learning Platform APIs" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Health Check
Write-Host "1. Testing Health Endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$API_URL/health" -Method Get
    Write-Host "✅ Health Check: " -ForegroundColor Green -NoNewline
    Write-Host $response.status
} catch {
    Write-Host "❌ Health Check Failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 2: Quiz Generation
Write-Host "2. Testing Quiz Generation..." -ForegroundColor Yellow
try {
    $body = @{
        topic = "Python Basics"
        num_questions = 3
        difficulty = "medium"
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$API_URL/quiz/generate" `
        -Method Post `
        -Headers @{"Authorization"="Bearer $TOKEN"; "Content-Type"="application/json"} `
        -Body $body
    
    Write-Host "✅ Quiz Generated: $($response.questions.Count) questions" -ForegroundColor Green
} catch {
    Write-Host "❌ Quiz Generation Failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 3: Code Analysis
Write-Host "3. Testing Code Analysis..." -ForegroundColor Yellow
try {
    $body = @{
        code = "def hello():`n    print('Hello World')"
        language = "python"
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$API_URL/code/analyze" `
        -Method Post `
        -Headers @{"Authorization"="Bearer $TOKEN"; "Content-Type"="application/json"} `
        -Body $body
    
    Write-Host "✅ Code Analyzed Successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Code Analysis Failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 4: Flashcard Generation
Write-Host "4. Testing Flashcard Generation..." -ForegroundColor Yellow
try {
    $body = @{
        content = "Python is a high-level, interpreted programming language known for its simplicity and readability."
        count = 3
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$API_URL/flashcards/generate" `
        -Method Post `
        -Headers @{"Authorization"="Bearer $TOKEN"; "Content-Type"="application/json"} `
        -Body $body
    
    Write-Host "✅ Flashcards Generated: $($response.flashcards.Count) cards" -ForegroundColor Green
} catch {
    Write-Host "❌ Flashcard Generation Failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 5: AI Tutor Session
Write-Host "5. Testing AI Tutor..." -ForegroundColor Yellow
try {
    $body = @{
        user_id = "test-user"
        subject = "Python"
        teaching_style = "socratic"
        difficulty_level = "adaptive"
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$API_URL/tutor/start-session" `
        -Method Post `
        -Headers @{"Authorization"="Bearer $TOKEN"; "Content-Type"="application/json"} `
        -Body $body
    
    Write-Host "✅ Tutor Session Started: $($response.session_id)" -ForegroundColor Green
} catch {
    Write-Host "❌ Tutor Session Failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 6: Code Playground
Write-Host "6. Testing Code Playground..." -ForegroundColor Yellow
try {
    $body = @{
        code = "print('Hello, World!')"
        language = "python"
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$API_URL/playground/execute" `
        -Method Post `
        -Headers @{"Authorization"="Bearer $TOKEN"; "Content-Type"="application/json"} `
        -Body $body
    
    Write-Host "✅ Code Executed Successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Code Execution Failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 7: Gamification Stats
Write-Host "7. Testing Gamification..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$API_URL/gamification/stats/test-user" `
        -Method Get `
        -Headers @{"Authorization"="Bearer $TOKEN"}
    
    Write-Host "✅ Gamification Stats Retrieved" -ForegroundColor Green
} catch {
    Write-Host "❌ Gamification Failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 8: Collaborative Rooms
Write-Host "8. Testing Collaborative Learning..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$API_URL/collaborative/rooms" `
        -Method Get `
        -Headers @{"Authorization"="Bearer $TOKEN"}
    
    Write-Host "✅ Rooms Retrieved: $($response.rooms.Count) rooms" -ForegroundColor Green
} catch {
    Write-Host "❌ Collaborative Learning Failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 9: Study Buddy
Write-Host "9. Testing AI Study Buddy..." -ForegroundColor Yellow
try {
    $body = @{
        title = "Learn Python"
        description = "Master Python programming"
        targetDate = "2026-06-01"
        learningStyle = "visual"
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$API_URL/study-buddy/create-goal" `
        -Method Post `
        -Headers @{"Authorization"="Bearer $TOKEN"; "Content-Type"="application/json"} `
        -Body $body
    
    Write-Host "✅ Study Goal Created" -ForegroundColor Green
} catch {
    Write-Host "❌ Study Buddy Failed: $_" -ForegroundColor Red
}
Write-Host ""

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Testing Complete!" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "If any tests failed, check:" -ForegroundColor Yellow
Write-Host "1. Backend is deployed and running" -ForegroundColor White
Write-Host "2. AWS Bedrock is enabled with model access" -ForegroundColor White
Write-Host "3. Environment variables are set correctly" -ForegroundColor White
Write-Host "4. Check CloudWatch logs for detailed errors" -ForegroundColor White
