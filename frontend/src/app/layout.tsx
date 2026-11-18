import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'EstateIQ — Real Estate Intelligence Assistant',
  description:
    'AI-powered real estate assistant grounded in DarGlobal and Wasalt data. Ask about luxury projects, Saudi property listings, prices, and locations.',
  icons: { icon: '/favicon.ico' },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-navy-950 text-slate-200 antialiased h-screen overflow-hidden">
        {children}
      </body>
    </html>
  )
}
