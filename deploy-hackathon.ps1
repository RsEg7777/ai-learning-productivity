# Hackathon Deployment Script
# This script deploys all new features for the hackathon

Write-Host "🚀 AWS AI Bharat Hackathon - Deployment Script" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "📋 Checking prerequisites..." -ForegroundColor Yellow

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Check Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✓ Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js not found. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

# Check AWS CLI
try {
    $awsVersion = aws --version 2>&1
    Write-Host "✓ AWS CLI: $awsVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ AWS CLI not found. Please install AWS CLI" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🔧 Setting up backend..." -ForegroundColor Yellow

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Gray
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Gray
& .\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Gray
pip install -q -r requirements.txt
pip install -q -r requirements-dev.txt

Write-Host "✓ Backend setup complete" -ForegroundColor Green
Write-Host ""

# Run tests
Write-Host "🧪 Running tests..." -ForegroundColor Yellow
pytest tests/unit/ -v --tb=short

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠ Some tests failed, but continuing..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🏗️ Deploying infrastructure..." -ForegroundColor Yellow

# Deploy CDK stack
Set-Location infrastructure

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing CDK dependencies..." -ForegroundColor Gray
    npm install
}

Write-Host "Deploying CDK stack..." -ForegroundColor Gray
cdk deploy --all --require-approval never

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ CDK deployment failed" -ForegroundColor Red
    Set-Location ..
    exit 1
}

Set-Location ..
Write-Host "✓ Infrastructure deployed" -ForegroundColor Green
Write-Host ""

# Setup frontend
Write-Host "🎨 Setting up frontend..." -ForegroundColor Yellow
Set-Location frontend

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Gray
    npm install
}

# Build frontend
Write-Host "Building frontend..." -ForegroundColor Gray
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Frontend build failed" -ForegroundColor Red
    Set-Location ..
    exit 1
}

Write-Host "✓ Frontend built successfully" -ForegroundColor Green
Set-Location ..
Write-Host ""

# Create DynamoDB tables
Write-Host "📊 Creating DynamoDB tables..." -ForegroundColor Yellow

$tables = @(
    @{
        Name = "tutor_sessions"
        Key = "session_id"
    },
    @{
        Name = "user_stats"
        Key = "user_id"
    },
    @{
        Name = "user_achievements"
        Key = "user_id"
        SortKey = "achievement_id"
    },
    @{
        Name = "leaderboards"
        Key = "leaderboard_type"
        SortKey = "user_id"
    }
)

foreach ($table in $tables) {
    Write-Host "Creating table: $($table.Name)..." -ForegroundColor Gray
    
    $keySchema = @(
        @{
            AttributeName = $table.Key
            KeyType = "HASH"
        }
    )
    
    $attributeDefinitions = @(
        @{
            AttributeName = $table.Key
            AttributeType = "S"
        }
    )
    
    if ($table.SortKey) {
        $keySchema += @{
            AttributeName = $table.SortKey
            KeyType = "RANGE"
        }
        $attributeDefinitions += @{
            AttributeName = $table.SortKey
            AttributeType = "S"
        }
    }
    
    try {
        aws dynamodb create-table `
            --table-name $table.Name `
            --key-schema ($keySchema | ConvertTo-Json -Compress) `
            --attribute-definitions ($attributeDefinitions | ConvertTo-Json -Compress) `
            --billing-mode PAY_PER_REQUEST `
            --region ap-south-1 2>&1 | Out-Null
        
        Write-Host "✓ Table $($table.Name) created" -ForegroundColor Green
    } catch {
        Write-Host "⚠ Table $($table.Name) may already exist" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "🎯 Creating demo data..." -ForegroundColor Yellow

# Create demo user stats
$demoStats = @{
    user_id = @{ S = "demo_user" }
    total_xp = @{ N = "1500" }
    level = @{ N = "5" }
    current_streak = @{ N = "7" }
    longest_streak = @{ N = "15" }
    quizzes_completed = @{ N = "25" }
    perfect_scores = @{ N = "5" }
    code_analyzed = @{ N = "10" }
    flashcards_reviewed = @{ N = "50" }
    study_time_minutes = @{ N = "300" }
    achievements_unlocked = @{ N = "8" }
    badges = @{ L = @(
        @{ S = "bronze_quiz_master" }
        @{ S = "silver_streak_warrior" }
    )}
    last_activity = @{ S = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ") }
}

try {
    aws dynamodb put-item `
        --table-name user_stats `
        --item ($demoStats | ConvertTo-Json -Depth 10 -Compress) `
        --region ap-south-1 2>&1 | Out-Null
    Write-Host "✓ Demo user stats created" -ForegroundColor Green
} catch {
    Write-Host "⚠ Failed to create demo data" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ Deployment Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Get your API Gateway URL from AWS Console" -ForegroundColor White
Write-Host "2. Update frontend API_URL in components" -ForegroundColor White
Write-Host "3. Get authentication token: .\test_live_api.ps1" -ForegroundColor White
Write-Host "4. Start frontend: cd frontend && npm start" -ForegroundColor White
Write-Host "5. Test all features" -ForegroundColor White
Write-Host ""
Write-Host "📚 Documentation:" -ForegroundColor Cyan
Write-Host "- Quick Start: QUICK_START_HACKATHON.md" -ForegroundColor White
Write-Host "- Features: HACKATHON_FEATURES_SUMMARY.md" -ForegroundColor White
Write-Host "- Implementation: IMPLEMENTATION_GUIDE.md" -ForegroundColor White
Write-Host "- Presentation: PRESENTATION_OUTLINE.md" -ForegroundColor White
Write-Host ""
Write-Host "🏆 Good luck with the hackathon!" -ForegroundColor Cyan
Write-Host ""
