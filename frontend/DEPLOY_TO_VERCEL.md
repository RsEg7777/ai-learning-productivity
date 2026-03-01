# 🚀 Quick Vercel Deployment Guide

## Option 1: Deploy via Vercel CLI (Recommended)

```bash
# Install Vercel CLI if you haven't
npm install -g vercel

# Navigate to frontend directory
cd frontend

# Login to Vercel
vercel login

# Deploy to production
vercel --prod
```

## Option 2: Deploy via Vercel Dashboard

1. Go to https://vercel.com/new
2. Import your GitHub repository: `https://github.com/RsEg7777/ai-learning-productivity`
3. Configure project:
   - **Framework Preset**: Create React App
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `build`

4. Add Environment Variables:
   ```
   REACT_APP_API_URL=https://qtyf9c08b4.execute-api.ap-south-1.amazonaws.com/dev
   GENERATE_SOURCEMAP=false
   CI=false
   ```

5. Click "Deploy"

## Option 3: Deploy via Git Push

```bash
# Make sure you're in the frontend directory
cd frontend

# If you haven't initialized Vercel yet
vercel

# Link to your project
vercel link

# Push to deploy
git push

# Vercel will automatically deploy on push
```

## ✅ Post-Deployment Checklist

After deployment, test these URLs:

1. **Homepage**: `https://your-app.vercel.app`
2. **Login**: Should redirect to Google OAuth
3. **All Features**: Test each of the 9 features

## 🔧 Troubleshooting

### Build Fails
- Check that all dependencies are installed: `npm install`
- Verify Node version: `node --version` (should be 16+)
- Clear cache: `rm -rf node_modules package-lock.json && npm install`

### API Not Working
- Verify `REACT_APP_API_URL` environment variable is set
- Check CORS settings on API Gateway
- Verify API is deployed and accessible

### Authentication Issues
- Update Google OAuth redirect URIs to include your Vercel domain
- Check that tokens are being stored correctly

## 📊 Expected Build Output

```
File sizes after gzip:
  113.47 kB  build/static/js/main.0e7badb0.js
  3.08 kB    build/static/css/main.d3ac7504.css
  1.71 kB    build/static/js/206.5f917b3c.chunk.js
```

## 🎉 Success!

Your app should now be live at: `https://your-app.vercel.app`

Share this link for your hackathon submission! 🏆
