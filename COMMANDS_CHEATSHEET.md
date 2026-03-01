# 🚀 Commands Cheatsheet

## Quick Deploy (3 Commands)

```bash
cd frontend
npm install && npm run build
vercel --prod
```

## Development

### Start Development Server
```bash
cd frontend
npm start
```
Opens: http://localhost:3000

### Run Tests
```bash
cd frontend
npm test
```

### Build for Production
```bash
cd frontend
npm run build
```

### Check Build Size
```bash
cd frontend
npm run build
# Look for "File sizes after gzip"
```

## Deployment

### Install Vercel CLI
```bash
npm install -g vercel
```

### Login to Vercel
```bash
vercel login
```

### Deploy to Production
```bash
cd frontend
vercel --prod
```

### Deploy with Debug Info
```bash
cd frontend
vercel --prod --debug
```

### Check Deployment Status
```bash
vercel ls
```

## Troubleshooting

### Clear Cache and Reinstall
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Fix Build Issues
```bash
cd frontend
npm install
npm run build
```

### Check for Errors
```bash
cd frontend
npm run build 2>&1 | grep -i error
```

## Git Commands

### Commit Changes
```bash
git add .
git commit -m "Fixed theme and added new features"
git push origin main
```

### Check Status
```bash
git status
```

### View Changes
```bash
git diff
```

## Environment Variables

### View Current Environment
```bash
cd frontend
cat .env.production
```

### Set Environment Variable (Vercel)
```bash
vercel env add REACT_APP_API_URL production
# Enter: https://qtyf9c08b4.execute-api.ap-south-1.amazonaws.com/dev
```

## Testing

### Run All Tests
```bash
cd frontend
npm test -- --watchAll=false
```

### Run Tests with Coverage
```bash
cd frontend
npm test -- --coverage --watchAll=false
```

### Run Specific Test
```bash
cd frontend
npm test -- App.test.tsx
```

## Build Analysis

### Analyze Bundle Size
```bash
cd frontend
npm run build
# Check output for file sizes
```

### Check Dependencies
```bash
cd frontend
npm list --depth=0
```

### Update Dependencies
```bash
cd frontend
npm update
```

## Vercel Specific

### Link Project
```bash
cd frontend
vercel link
```

### View Logs
```bash
vercel logs
```

### View Deployments
```bash
vercel ls
```

### Remove Deployment
```bash
vercel rm [deployment-url]
```

### Set Environment Variable
```bash
vercel env add [variable-name] [environment]
```

## Quick Fixes

### Fix Port Already in Use
```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID [PID] /F

# Mac/Linux
lsof -ti:3000 | xargs kill -9
```

### Clear React Cache
```bash
cd frontend
rm -rf node_modules/.cache
```

### Reset Everything
```bash
cd frontend
rm -rf node_modules package-lock.json build
npm install
npm run build
```

## Performance Testing

### Test Load Time
```bash
# Use Chrome DevTools
# Network tab -> Disable cache -> Reload
```

### Lighthouse Audit
```bash
# Chrome DevTools -> Lighthouse -> Generate Report
```

## Useful Checks

### Check Node Version
```bash
node --version
# Should be 16+ for best compatibility
```

### Check npm Version
```bash
npm --version
```

### Check Vercel CLI Version
```bash
vercel --version
```

### Check React Version
```bash
cd frontend
npm list react
```

## One-Liners

### Full Deploy Pipeline
```bash
cd frontend && npm install && npm run build && vercel --prod
```

### Quick Test and Build
```bash
cd frontend && npm test -- --watchAll=false && npm run build
```

### Clean and Deploy
```bash
cd frontend && rm -rf node_modules build && npm install && npm run build && vercel --prod
```

## Emergency Commands

### If Everything Breaks
```bash
cd frontend
rm -rf node_modules package-lock.json build .cache
npm cache clean --force
npm install
npm run build
```

### If Vercel Fails
```bash
vercel --debug
# Read error messages carefully
# Check environment variables
# Verify build settings
```

### If Tests Fail
```bash
cd frontend
npm test -- --clearCache
npm test -- --watchAll=false
```

## Monitoring

### Watch Build Output
```bash
cd frontend
npm run build | tee build.log
```

### Monitor Deployment
```bash
vercel --prod --debug 2>&1 | tee deploy.log
```

## Quick Reference

| Task | Command |
|------|---------|
| Install | `npm install` |
| Dev Server | `npm start` |
| Build | `npm run build` |
| Test | `npm test` |
| Deploy | `vercel --prod` |
| Logs | `vercel logs` |
| Status | `vercel ls` |

## 🎯 Most Important Commands

### 1. Deploy Now
```bash
cd frontend && vercel --prod
```

### 2. Test Everything
```bash
cd frontend && npm test -- --watchAll=false
```

### 3. Build Check
```bash
cd frontend && npm run build
```

---

**Pro Tip**: Save this file for quick reference during deployment!

**Need Help?** Check the error messages carefully - they usually tell you exactly what's wrong.

**Good luck! 🚀**
