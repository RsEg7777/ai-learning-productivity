# Git Push Production Changes Script
# Commits and pushes all production-ready changes to GitHub

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Git Push Production Changes" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if git is installed
try {
    $gitVersion = git --version 2>&1
    Write-Host "✅ Git installed: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Git not found. Please install Git first." -ForegroundColor Red
    exit 1
}

# Check if we're in a git repository
if (-not (Test-Path ".git")) {
    Write-Host "❌ Not a git repository. Initializing..." -ForegroundColor Yellow
    git init
    Write-Host "✅ Git repository initialized" -ForegroundColor Green
}

# Check git status
Write-Host ""
Write-Host "Current git status:" -ForegroundColor Cyan
git status --short

# Stage all changes
Write-Host ""
Write-Host "Staging all changes..." -ForegroundColor Yellow
git add .

# Show what will be committed
Write-Host ""
Write-Host "Files to be committed:" -ForegroundColor Cyan
git status --short

# Create commit message
$commitMessage = @"
🚀 Production Ready - All Features Fixed

## Changes Summary

### Deleted (19 files)
- Removed all demo mode files
- Cleaned up unnecessary documentation
- Project is now production-focused

### Fixed Issues (7)
✅ AI Tutor - Enhanced AI responses
✅ AI Study Buddy - Fully implemented
✅ Code Playground - Fixed execution
✅ Multimodal AI - All 4 features working
✅ Quiz Generator - Fixed content handling
✅ Flashcard Generator - Fixed count limits
✅ Code Analyzer - Enhanced AI analysis

### New Files (7)
- PRODUCTION_READY.md - Complete production guide
- PRODUCTION_FIXES.md - Issues fixed
- DEPLOYMENT_GUIDE.md - Deployment instructions
- CHANGES_SUMMARY.md - Complete changelog
- test_production_features.py - Automated tests
- quick-start.ps1 - Quick start script
- verify-production.ps1 - Verification script

### Status
✅ All features tested and working
✅ No demo mode dependencies
✅ Full AI integration
✅ Production ready

See PRODUCTION_READY.md for complete details.
"@

# Commit changes
Write-Host ""
Write-Host "Committing changes..." -ForegroundColor Yellow
git commit -m $commitMessage

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Changes committed successfully" -ForegroundColor Green
} else {
    Write-Host "⚠️  No changes to commit or commit failed" -ForegroundColor Yellow
}

# Check if remote exists
Write-Host ""
Write-Host "Checking remote repository..." -ForegroundColor Yellow
$remotes = git remote -v 2>&1

if ($remotes -match "origin") {
    Write-Host "✅ Remote 'origin' found" -ForegroundColor Green
    
    # Get current branch
    $currentBranch = git branch --show-current
    Write-Host "Current branch: $currentBranch" -ForegroundColor Cyan
    
    # Ask user to confirm push
    Write-Host ""
    Write-Host "Ready to push to GitHub. Continue? (Y/N)" -ForegroundColor Yellow
    $confirm = Read-Host
    
    if ($confirm -eq "Y" -or $confirm -eq "y") {
        Write-Host ""
        Write-Host "Pushing to GitHub..." -ForegroundColor Cyan
        git push origin $currentBranch
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "================================" -ForegroundColor Green
            Write-Host "✅ SUCCESS!" -ForegroundColor Green
            Write-Host "================================" -ForegroundColor Green
            Write-Host ""
            Write-Host "All changes pushed to GitHub successfully!" -ForegroundColor Green
            Write-Host ""
            Write-Host "View your repository:" -ForegroundColor Cyan
            $repoUrl = git config --get remote.origin.url
            if ($repoUrl -match "github.com[:/](.+/.+)\.git") {
                $repoPath = $matches[1]
                Write-Host "  https://github.com/$repoPath" -ForegroundColor White
            } else {
                Write-Host "  $repoUrl" -ForegroundColor White
            }
        } else {
            Write-Host ""
            Write-Host "❌ Push failed. Please check your credentials and try again." -ForegroundColor Red
            Write-Host ""
            Write-Host "Common issues:" -ForegroundColor Yellow
            Write-Host "  1. Authentication required - run: git config credential.helper store" -ForegroundColor White
            Write-Host "  2. Branch protection - check GitHub settings" -ForegroundColor White
            Write-Host "  3. Network issues - check your connection" -ForegroundColor White
        }
    } else {
        Write-Host ""
        Write-Host "Push cancelled. You can push manually later with:" -ForegroundColor Yellow
        Write-Host "  git push origin $currentBranch" -ForegroundColor White
    }
} else {
    Write-Host "⚠️  No remote repository configured" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To add a remote repository:" -ForegroundColor Cyan
    Write-Host "  git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git" -ForegroundColor White
    Write-Host ""
    Write-Host "Then run this script again to push changes." -ForegroundColor Yellow
}

Write-Host ""
