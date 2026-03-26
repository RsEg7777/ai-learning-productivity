/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Allow all image domains for multimodal processor previews
  images: {
    unoptimized: true,
  },
  // Environment variables exposed to the browser
  env: {
    NEXT_PUBLIC_APP_NAME: process.env.NEXT_PUBLIC_APP_NAME || 'AI Learning Assistant',
  },
}

module.exports = nextConfig
