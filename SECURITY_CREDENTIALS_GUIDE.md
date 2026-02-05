# 🔒 Security & Credentials Management Guide

## ⚠️ CRITICAL: Exposed Credentials Detected

GitGuardian detected exposed Google OAuth2 credentials in your repository. This has been **FIXED** but you need to take additional actions.

---

## 🚨 IMMEDIATE ACTIONS REQUIRED

### 1. Revoke Exposed Google OAuth Credentials

**The following credentials were exposed and MUST be revoked:**

- **Google Client ID**: `18697676680-5pm58nr37uasdjkr826p2v8v63f8m02o.apps.googleusercontent.com`
- **Google Client Secret**: `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`

**Steps to Revoke:**

1. Go to [Google Cloud Console Credentials](https://console.cloud.google.com/apis/credentials)
2. Find the OAuth 2.0 Client ID: `18697676680-5pm58nr37uasdjkr826p2v8v63f8m02o`
3. Click **DELETE** to remove it completely
4. Create a **NEW** OAuth 2.0 Client ID
5. Update your application with the new credentials

### 2. Rotate AWS Cognito Credentials (Optional but Recommended)

The following Cognito IDs were also exposed:
- **User Pool ID**: `ap-south-1_cfA9dz15h`
- **Client ID**: `49n7akp9lublvpa04dbt2qjoa2`

While these are less sensitive, consider:
1. Creating a new Cognito User Pool Client
2. Updating your application configuration
3. Deprecating the old client

---

## ✅ What Has Been Fixed

### Files Updated (Credentials Removed):
1. ✅ `setup-google-auth.ps1` - Now uses placeholders
2. ✅ `GOOGLE_AUTH_SETUP.md` - Now uses placeholders
3. ✅ `DEPLOYMENT_SUCCESS.md` - Credentials removed
4. ✅ `API_DEMO.md` - Credentials removed
5. ✅ `.gitignore` - Added credential patterns

### Changes Made:
- All hardcoded credentials replaced with `YOUR_*` placeholders
- Added security warnings to documentation
- Updated .gitignore to prevent future leaks

---

## 🔐 Secure Credential Management

### Option 1: Environment Variables (Recommended)

Create a `.env` file (already in .gitignore):

```bash
# .env (NEVER commit this file!)
GOOGLE_CLIENT_ID=your_new_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_new_client_secret
AWS_USER_POOL_ID=your_user_pool_id
AWS_CLIENT_ID=your_client_id
AWS_REGION=ap-south-1
```

Update your scripts to read from environment:

```powershell
# setup-google-auth.ps1
$GoogleClientId = $env:GOOGLE_CLIENT_ID
$GoogleClientSecret = $env:GOOGLE_CLIENT_SECRET
```

### Option 2: AWS Secrets Manager (Production)

Store credentials in AWS Secrets Manager:

```bash
# Store secret
aws secretsmanager create-secret \
    --name google-oauth-credentials \
    --secret-string '{"client_id":"YOUR_ID","client_secret":"YOUR_SECRET"}' \
    --region ap-south-1

# Retrieve in code
aws secretsmanager get-secret-value \
    --secret-id google-oauth-credentials \
    --region ap-south-1
```

### Option 3: AWS Systems Manager Parameter Store

```bash
# Store parameters
aws ssm put-parameter \
    --name /app/google/client-id \
    --value "YOUR_CLIENT_ID" \
    --type SecureString \
    --region ap-south-1

aws ssm put-parameter \
    --name /app/google/client-secret \
    --value "YOUR_CLIENT_SECRET" \
    --type SecureString \
    --region ap-south-1

# Retrieve in code
aws ssm get-parameter \
    --name /app/google/client-id \
    --with-decryption \
    --region ap-south-1
```

---

## 📝 Best Practices

### ✅ DO:
- Use environment variables for local development
- Use AWS Secrets Manager for production
- Add all credential files to .gitignore
- Use placeholders in documentation
- Rotate credentials regularly
- Use IAM roles when possible
- Enable MFA on AWS accounts

### ❌ DON'T:
- Commit credentials to git (EVER!)
- Share credentials in chat/email
- Hardcode credentials in code
- Use the same credentials across environments
- Leave default credentials unchanged
- Store credentials in plain text files

---

## 🔍 How to Check for Exposed Secrets

### Before Committing:

```bash
# Check what you're about to commit
git diff --cached

# Search for potential secrets
git grep -i "client_id"
git grep -i "client_secret"
git grep -i "password"
git grep -i "api_key"
```

### Install git-secrets (Recommended):

```bash
# Install git-secrets
git clone https://github.com/awslabs/git-secrets.git
cd git-secrets
make install

# Set up in your repo
cd /path/to/your/repo
git secrets --install
git secrets --register-aws
```

### Use GitGuardian CLI:

```bash
# Install
pip install ggshield

# Scan repository
ggshield secret scan repo .
```

---

## 🚀 Next Steps

### 1. Revoke Old Credentials (URGENT)
- [ ] Delete exposed Google OAuth client
- [ ] Create new Google OAuth client
- [ ] Update application with new credentials

### 2. Update Configuration
- [ ] Create `.env` file with new credentials
- [ ] Test application with new credentials
- [ ] Update production secrets in AWS Secrets Manager

### 3. Commit Security Fixes
```bash
git add .
git commit -m "🔒 Security: Remove exposed credentials and add security guidelines"
git push origin main
```

### 4. Verify Repository is Clean
- [ ] Check GitHub repository for any remaining credentials
- [ ] Review all markdown files
- [ ] Review all script files
- [ ] Confirm .gitignore is working

### 5. Set Up Monitoring
- [ ] Enable GitGuardian monitoring
- [ ] Set up AWS CloudTrail
- [ ] Enable AWS Config
- [ ] Review IAM policies

---

## 📚 Additional Resources

- [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)
- [GitGuardian Documentation](https://docs.gitguardian.com/)
- [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security/getting-started/best-practices-for-preventing-data-leaks-in-your-organization)

---

## 🆘 If Credentials Are Already Compromised

### Immediate Actions:
1. **Revoke credentials immediately**
2. **Check AWS CloudTrail for unauthorized access**
3. **Review Google Cloud audit logs**
4. **Change all related passwords**
5. **Enable MFA if not already enabled**
6. **Monitor for suspicious activity**

### AWS Security Check:
```bash
# Check recent API calls
aws cloudtrail lookup-events \
    --lookup-attributes AttributeKey=Username,AttributeValue=YOUR_USER \
    --max-results 50 \
    --region ap-south-1

# Check for unauthorized resources
aws ec2 describe-instances --region ap-south-1
aws s3 ls
aws lambda list-functions --region ap-south-1
```

---

## ✅ Verification Checklist

After fixing:
- [ ] All credentials removed from git repository
- [ ] New credentials generated
- [ ] Application tested with new credentials
- [ ] .gitignore updated
- [ ] Security guide created
- [ ] Team notified about security practices
- [ ] Monitoring enabled
- [ ] Old credentials revoked

---

## 🎯 Summary

**What Happened:**
- Google OAuth credentials were accidentally committed to GitHub
- GitGuardian detected the exposure
- Credentials have been removed from repository

**What You Need to Do:**
1. ✅ Revoke old Google OAuth credentials (URGENT)
2. ✅ Create new credentials
3. ✅ Store securely using environment variables or AWS Secrets Manager
4. ✅ Commit the security fixes
5. ✅ Monitor for any unauthorized access

**Prevention:**
- Never commit credentials to git
- Use .env files (in .gitignore)
- Use AWS Secrets Manager for production
- Enable GitGuardian monitoring
- Review code before committing

---

## 📞 Need Help?

If you suspect unauthorized access:
1. Contact AWS Support immediately
2. Review AWS CloudTrail logs
3. Change all credentials
4. Enable MFA on all accounts

**Stay secure! 🔒**
