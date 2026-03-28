import type { Metadata } from 'next'
import './globals.css'
import ApiGuard from '@/components/ApiGuard'

export const metadata: Metadata = {
  title: 'AI Learning Assistant | AWS AI Bharat Hackathon 2026',
  description: 'AI-powered learning platform with quiz generation, code analysis, multilingual support, and adaptive tutoring — powered by Amazon Bedrock Nova Pro.',
  keywords: ['AI', 'learning', 'education', 'AWS Bedrock', 'Amazon Nova', 'India', 'hackathon'],
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&family=Sora:wght@300;400;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <ApiGuard />
        {children}
      </body>
    </html>
  )
}
