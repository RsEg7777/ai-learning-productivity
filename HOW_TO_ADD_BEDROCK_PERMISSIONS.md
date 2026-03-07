# How to Add Bedrock IAM Permissions

## Quick Guide

You need to add `bedrock:InvokeModel` permission to your AWS IAM user/role so the application can use AI features.

## Step-by-Step Instructions

### Option 1: Using AWS Console (Easiest)

#### Step 1: Open AWS IAM Console
1. Go to https://console.aws.amazon.com/iam/
2. Sign in with your AWS credentials

#### Step 2: Find Your User/Role
1. Click on "Users" in the left sidebar
2. Find and click on your username (the one you're using for AWS credentials)
   - If you're using an IAM role instead, click "Roles" and find your role

#### Step 3: Add Bedrock Policy
1. Click the "Add permissions" button
2. Select "Create inline policy"
3. Click the "JSON" tab
4. Paste this policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "*"
    }
  ]
}
```

5. Click "Review policy"
6. Name it: `BedrockInvokeAccess`
7. Click "Create policy"

#### Step 4: Verify
1. Go back to your user/role
2. You should see the new policy listed under "Permissions"

#### Step 5: Test
1. Wait 1-2 minutes for AWS to propagate the changes
2. Restart your server:
   ```bash
   # Stop the current server (Ctrl+C in the terminal)
   # Then start it again:
   python -m uvicorn app:app --port 8000
   ```
3. Run the tests:
   ```bash
   python test_api.py
   ```

---

### Option 2: Using AWS CLI (For Advanced Users)

If you have AWS CLI installed and configured:

#### Step 1: Create Policy File
Create a file named `bedrock-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "*"
    }
  ]
}
```

#### Step 2: Attach Policy to Your User
Replace `YOUR_USERNAME` with your actual IAM username:

```bash
aws iam put-user-policy \
  --user-name YOUR_USERNAME \
  --policy-name BedrockInvokeAccess \
  --policy-document file://bedrock-policy.json
```

#### Step 3: Verify
```bash
aws iam list-user-policies --user-name YOUR_USERNAME
```

You should see `BedrockInvokeAccess` in the list.

---

### Option 3: Attach AWS Managed Policy (Simplest but Broader Access)

If you want to use AWS's pre-made policy (gives more permissions than needed):

#### Using Console:
1. Go to IAM → Users → Your User
2. Click "Add permissions"
3. Select "Attach policies directly"
4. Search for: `AmazonBedrockFullAccess`
5. Check the box next to it
6. Click "Add permissions"

#### Using CLI:
```bash
aws iam attach-user-policy \
  --user-name YOUR_USERNAME \
  --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess
```

---

## Troubleshooting

### "I don't know my IAM username"
Run this command to find it:
```bash
aws sts get-caller-identity
```

Look for the "Arn" field. Your username is at the end after `user/`.

### "I'm using an IAM role, not a user"
If you see `assumed-role` in your ARN, you're using a role. You need to:
1. Find the role name in the ARN
2. Go to IAM → Roles → Your Role
3. Follow the same steps but for the role instead of user

### "Access Denied when trying to add policy"
You need administrator permissions to add IAM policies. Ask your AWS administrator to:
1. Add the Bedrock policy for you, OR
2. Give you IAM permissions to manage your own policies

### "Still getting Access Denied after adding policy"
1. Wait 2-3 minutes for AWS to propagate changes
2. Restart your application
3. Check you added the policy to the correct user/role
4. Verify the policy was created:
   ```bash
   aws iam get-user-policy --user-name YOUR_USERNAME --policy-name BedrockInvokeAccess
   ```

---

## What This Permission Does

- **bedrock:InvokeModel**: Allows calling Bedrock AI models (required for all AI features)
- **bedrock:InvokeModelWithResponseStream**: Allows streaming responses (optional, for future features)

These permissions let your application:
- Generate quiz questions
- Answer student questions
- Analyze code
- Create flashcards
- All other AI-powered features

---

## Security Note

The policy uses `"Resource": "*"` which means it can invoke any Bedrock model. If you want to restrict to specific models, you can change it to:

```json
{
  "Resource": [
    "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0"
  ]
}
```

But for development, `"*"` is fine.

---

## After Adding Permissions

Once you've added the permissions:

1. **Restart the server:**
   ```bash
   python -m uvicorn app:app --port 8000
   ```

2. **Run the tests:**
   ```bash
   python test_api.py
   ```

3. **Expected result:**
   ```
   ✓ Health Check
   ✓ AI Tutor
   ✓ Quiz Generation
   ✓ Code Analysis
   
   4/4 tests passed
   ```

---

## Need Help?

If you're stuck, tell me:
1. What error message you're seeing
2. Whether you're using an IAM user or role
3. Whether you have admin permissions in AWS

I can provide more specific guidance!
