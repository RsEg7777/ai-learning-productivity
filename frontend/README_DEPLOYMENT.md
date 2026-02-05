# 🚀 AI Learning Assistant - Deployment Guide

## Vercel Deployment (Recommended - Free & Easy)

### Quick Deploy

1. **Install Vercel CLI** (if not already installed):
```bash
npm install -g vercel
```

2. **Navigate to frontend directory**:
```bash
cd frontend
```

3. **Deploy to Vercel**:
```bash
vercel
```

Follow the prompts:
- Set up and deploy? **Y**
- Which scope? Select your account
- Link to existing project? **N**
- Project name? **ai-learning-assistant** (or your choice)
- Directory? **./frontend** or **./** (if already in frontend)
- Override settings? **N**

4. **Production Deployment**:
```bash
vercel --prod
```

Your app will be live at: `https://your-project-name.vercel.app`

### Deploy via Vercel Dashboard

1. Go to [vercel.com](https://vercel.com)
2. Click "Add New Project"
3. Import your Git repository
4. Set **Root Directory** to `frontend`
5. Framework Preset: **Create React App**
6. Click "Deploy"

### Environment Variables

Add these in Vercel Dashboard → Settings → Environment Variables:
- `REACT_APP_API_URL`: `https://qtyf9c08b4.execute-api.ap-south-1.amazonaws.com/dev`

## Alternative: Netlify Deployment

### Via Netlify CLI

1. **Install Netlify CLI**:
```bash
npm install -g netlify-cli
```

2. **Build the app**:
```bash
cd frontend
npm run build
```

3. **Deploy**:
```bash
netlify deploy --prod --dir=build
```

### Via Netlify Dashboard

1. Go to [netlify.com](https://netlify.com)
2. Drag and drop the `build` folder
3. Or connect your Git repository

## Build Locally

```bash
cd frontend
npm run build
```

The optimized production build will be in the `build/` folder.

## Configuration Files

- `vercel.json` - Vercel configuration
- `.env.production` - Production environment variables
- `package.json` - Dependencies and scripts

## Post-Deployment

1. **Test the deployment**: Visit your deployed URL
2. **Update API endpoint**: If needed, update the API URL in components
3. **Get Cognito token**: Use the PowerShell script to get your auth token
4. **Login and test**: Paste the token and test all features

## Troubleshooting

### Build Fails
- Check Node version (should be 16+)
- Clear cache: `npm cache clean --force`
- Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`

### API Not Working
- Verify CORS is enabled on API Gateway
- Check API endpoint URL is correct
- Ensure Cognito token is valid

### Blank Page
- Check browser console for errors
- Verify build completed successfully
- Check routing configuration

## Custom Domain

### Vercel
1. Go to Project Settings → Domains
2. Add your custom domain
3. Update DNS records as instructed

### Netlify
1. Go to Site Settings → Domain Management
2. Add custom domain
3. Configure DNS

## Performance Optimization

The app includes:
- ✅ Code splitting
- ✅ Lazy loading
- ✅ Minification
- ✅ Compression
- ✅ Optimized images
- ✅ Caching headers

## Security

- HTTPS enabled by default
- Security headers configured
- No sensitive data in frontend
- API authentication required

## Monitoring

- Vercel Analytics (automatic)
- Netlify Analytics (enable in dashboard)
- Custom analytics can be added

## Support

For issues:
1. Check build logs in Vercel/Netlify dashboard
2. Review browser console errors
3. Verify API connectivity
4. Check authentication token

---

**Your AI Learning Assistant is ready for the world! 🌟**
