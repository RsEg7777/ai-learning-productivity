# Setup Google Authentication for AWS Cognito
# Run this script to configure Google as an identity provider

$UserPoolId = "ap-south-1_cfA9dz15h"
$ClientId = "49n7akp9lublvpa04dbt2qjoa2"
$GoogleClientId = "18697676680-5pm58nr37uasdjkr826p2v8v63f8m02o.apps.googleusercontent.com"
$GoogleClientSecret = "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"
$Region = "ap-south-1"

Write-Host "Setting up Google Authentication for Cognito..." -ForegroundColor Cyan

# Step 1: Create Cognito Domain (if not exists)
Write-Host "`n1. Creating Cognito Domain..." -ForegroundColor Yellow
$DomainPrefix = "ai-learning-assistant-2026"

try {
    aws cognito-idp create-user-pool-domain `
        --domain $DomainPrefix `
        --user-pool-id $UserPoolId `
        --region $Region
    Write-Host "✓ Cognito domain created: https://$DomainPrefix.auth.$Region.amazoncognito.com" -ForegroundColor Green
} catch {
    Write-Host "Domain might already exist or error occurred. Continuing..." -ForegroundColor Yellow
}

# Step 2: Add Google as Identity Provider
Write-Host "`n2. Adding Google as Identity Provider..." -ForegroundColor Yellow

$ProviderDetails = @{
    client_id = $GoogleClientId
    client_secret = $GoogleClientSecret
    authorize_scopes = "profile email openid"
}

$ProviderDetailsJson = $ProviderDetails | ConvertTo-Json -Compress

try {
    aws cognito-idp create-identity-provider `
        --user-pool-id $UserPoolId `
        --provider-name Google `
        --provider-type Google `
        --provider-details $ProviderDetailsJson `
        --attribute-mapping email=email,username=sub,name=name `
        --region $Region
    Write-Host "✓ Google identity provider added successfully" -ForegroundColor Green
} catch {
    Write-Host "Google provider might already exist. Trying to update..." -ForegroundColor Yellow
    
    try {
        aws cognito-idp update-identity-provider `
            --user-pool-id $UserPoolId `
            --provider-name Google `
            --provider-details $ProviderDetailsJson `
            --attribute-mapping email=email,username=sub,name=name `
            --region $Region
        Write-Host "✓ Google identity provider updated successfully" -ForegroundColor Green
    } catch {
        Write-Host "Error updating Google provider: $_" -ForegroundColor Red
    }
}

# Step 3: Update App Client to support Google login
Write-Host "`n3. Updating App Client settings..." -ForegroundColor Yellow

$CallbackURLs = @(
    "https://ai-learning-productivity.vercel.app",
    "http://localhost:3000"
)

$LogoutURLs = @(
    "https://ai-learning-productivity.vercel.app",
    "http://localhost:3000"
)

try {
    aws cognito-idp update-user-pool-client `
        --user-pool-id $UserPoolId `
        --client-id $ClientId `
        --callback-urls $CallbackURLs `
        --logout-urls $LogoutURLs `
        --allowed-o-auth-flows "implicit" "code" `
        --allowed-o-auth-scopes "email" "openid" "profile" `
        --allowed-o-auth-flows-user-pool-client `
        --supported-identity-providers "Google" "COGNITO" `
        --region $Region
    Write-Host "✓ App client updated successfully" -ForegroundColor Green
} catch {
    Write-Host "Error updating app client: $_" -ForegroundColor Red
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nYour Cognito Hosted UI URL:" -ForegroundColor Yellow
Write-Host "https://$DomainPrefix.auth.$Region.amazoncognito.com/login?client_id=$ClientId&response_type=token&scope=email+openid+profile&redirect_uri=https://ai-learning-productivity.vercel.app" -ForegroundColor White

Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "1. Update Google Cloud Console with the redirect URI:" -ForegroundColor White
Write-Host "   https://$DomainPrefix.auth.$Region.amazoncognito.com/oauth2/idpresponse" -ForegroundColor Cyan
Write-Host "2. Test the Google login on your app!" -ForegroundColor White
