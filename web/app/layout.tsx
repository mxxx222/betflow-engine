import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from './providers'
import { ComplianceNotice } from '@/components/ComplianceNotice'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'BetFlow Engine - Analytics Dashboard',
  description: 'Analytics-only sports data insights platform. Educational analytics only.',
  keywords: ['analytics', 'sports', 'data', 'insights', 'educational'],
  authors: [{ name: 'BetFlow Engine' }],
  robots: 'noindex, nofollow',
  viewport: 'width=device-width, initial-scale=1',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="h-full">
      <body className={`${inter.className} h-full bg-gray-50`}>
        <Providers>
          <div className="min-h-full">
            {children}
            <ComplianceNotice />
          </div>
        </Providers>
      </body>
    </html>
  )
}
