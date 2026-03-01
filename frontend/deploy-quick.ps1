# Quick Deployment Script for Vercel
# Run this from the frontend directory

Write-Host "🚀 AI Learning Assistant - Quick Deploy to Vercel" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the frontend directory
if (-not (Test-Path "package.json")) {
    Write-Host "❌ Error: Please run this script from the frontend directory" -ForegroundColor Red
    exit 1
}

# Step 1: Install dependencies
Write-Host "📦 Step 1: Installing dependencies..." -ForegroundColor Yellow
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Dependencies installed" -ForegroundColor Green
Write-Host ""

# Step 2: Build the project
Write-Host "🔨 Step 2: Building production bundle..." -ForegroundColor Yellow
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Build successful" -ForegroundColor Green
Write-Host ""

# Step 3: Check if Vercel CLI is installed
Write-Host "🔍 Step 3: Checking Vercel CLI..." -ForegroundColor Yellow
$vercelInstalled = Get-Command vercel -ErrorAction SilentlyContinue
if (-not $vercelInstalled) {
    Write-Host "⚠️  Vercel CLI not found. Installing..." -ForegroundColor Yellow
    npm install -g vercel
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install Vercel CLI" -ForegroundColor Red
        Write-Host "💡 Try manually: npm install -g vercel" -ForegroundColor Cyan
        exit 1
    }
}
Write-Host "✅ Vercel CLI ready" -ForegroundColor Green
Write-Host ""

# Step 4: Deploy
Write-Host "🚀 Step 4: Deploying to Vercel..." -ForegroundColor Yellow
Write-Host "💡 You may need to login to Vercel if this is your first time" -ForegroundColor Cyan
Write-Host ""

vercel --prod

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "🎉 Deployment successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "✅ Your app is now live!" -ForegroundColor Green
    Write-Host "📝 Next steps:" -ForegroundColor Cyan
    Write-Host "   1. Test all features on the deployed URL" -ForegroundColor White
    Write-Host "   2. Update Google OAuth redirect URIs with your Vercel domain" -ForegroundColor White
    Write-Host "   3. Share the link for your hackathon submission" -ForegroundColor White
    Write-Host ""
    Write-Host "🏆 Good luck with your hackathon!" -ForegroundColor Magenta
} else {
    Write-Host ""
    Write-Host "❌ Deployment failed" -ForegroundColor Red
    Write-Host "💡 Try deploying manually:" -ForegroundColor Cyan
    Write-Host "   1. Run: vercel login" -ForegroundColor White
    Write-Host "   2. Run: vercel --prod" -ForegroundColor White
    Write-Host "   3. Or use Vercel Dashboard: https://vercel.com/new" -ForegroundColor White
}

Write-Host ""
Write-Host "=================================================" -ForegroundColor Cyan
