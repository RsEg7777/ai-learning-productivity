# Google Authentication Setup Guide

## ⚠️ IMPORTANT: Security Notice
**DO NOT commit your actual Google OAuth credentials to git!**

Store your credentials securely:
- Use environment variables
- Use AWS Secrets Manager
- Use a local `.env` file (add to .gitignore)

## Your Google OAuth Credentials (Template)
- **Client ID**: `YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com`
- **Client Secret**: `YOUR_GOOGLE_CLIENT_SECRET`
- **User Pool ID**: `YOUR_USER_POOL_ID`
- **Cognito Client ID**: `YOUR_COGNITO_CLIENT_ID`

## Step 1: Update Google Cloud Console

1. Go to [Google Cloud Console Credentials](https://console.cloud.google.com/apis/credentials)
2. Find your OAuth 2.0 Client ID
3. Click **Edit**
4. Add these **Authorized redirect URIs**:
   ```
   https://ai-learning-assistant-2026.auth.ap-south-1.amazoncognito.com/oauth2/idpresponse
   ```
5. Click **Save**

## Step 2: Configure AWS Cognito (Manual Steps)

### A. Create Cognito Domain
1. Go to [AWS Cognito Console](https://ap-south-1.console.aws.amazon.com/cognito/v2/idp/user-pools?region=ap-south-1)
2. Click on your User Pool
3. Go to **App integration** tab
4. Scroll down to **Domain** section
5. Click **Actions** → **Create Cognito domain**
6. Enter domain prefix: `ai-learning-assistant-2026`
7. Click **Create Cognito domain**

### B. Add Google Identity Provider
1. In the same User Pool, go to **Sign-in experience** tab
2. Scroll to **Federated identity provider sign-in**
3. Click **Add identity provider**
4. Select **Google**
5. Enter your Google OAuth credentials:
   - **Google app ID**: `YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com`
   - **Google app secret**: `YOUR_GOOGLE_CLIENT_SECRET`
   - **Authorized scopes**: `profile email openid`
6. Under **Attribute mapping**, set:
   - `email` → `email`
   - `name` → `name`
   - `sub` → `username`
7. Click **Add identity provider**

### C. Update App Client
1. Go to **App integration** tab
2. Scroll to **App clients and analytics**
3. Click on your app client: `49n7akp9lublvpa04dbt2qjoa2`
4. Click **Edit** under **Hosted UI**
5. Configure:
   - **Allowed callback URLs**: 
     ```
     https://ai-learning-productivity.vercel.app
     http://localhost:3000
     ```
   - **Allowed sign-out URLs**:
     ```
     https://ai-learning-productivity.vercel.app
     http://localhost:3000
     ```
   - **Identity providers**: Check ✓ **Google** and ✓ **Cognito User Pool**
   - **OAuth 2.0 grant types**: 
     - ✓ Implicit grant
     - ✓ Authorization code grant
   - **OpenID Connect scopes**: 
     - ✓ email
     - ✓ openid
     - ✓ profile
6. Click **Save changes**

## Step 3: Test

Once configured, your Google login will work at:
https://ai-learning-productivity.vercel.app

The "Continue with Google" button will redirect to:
```
https://ai-learning-assistant-2026.auth.ap-south-1.amazoncognito.com/oauth2/authorize?identity_provider=Google&redirect_uri=https://ai-learning-productivity.vercel.app&response_type=token&client_id=49n7akp9lublvpa04dbt2qjoa2&scope=email+openid+profile
```

## Troubleshooting

If you get errors:
1. Make sure the Cognito domain is created
2. Verify Google redirect URI matches exactly
3. Check that Google provider is enabled in app client settings
4. Ensure callback URLs are added to both Google and Cognito
