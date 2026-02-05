#!/bin/bash

echo "🚀 Deploying AI Learning Assistant to Vercel..."
echo ""

# Build the app
echo "📦 Building production bundle..."
npm run build

# Deploy to Vercel
echo "🌐 Deploying to Vercel..."
vercel --prod

echo ""
echo "✅ Deployment complete!"
echo "🎉 Your AI Learning Assistant is now live!"
