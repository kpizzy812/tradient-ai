'use client'

import { useEffect, ReactNode } from 'react'
import { loginFromTelegram } from '@/shared/auth'
import { useStore } from '@/shared/store'
import { NextIntlClientProvider } from 'next-intl'
import { SkeletonTheme } from 'react-loading-skeleton'
import { Geist, Geist_Mono } from 'next/font/google'
import { Toaster } from 'react-hot-toast'
import 'react-loading-skeleton/dist/skeleton.css'

const geistSans = Geist({ variable: '--font-geist-sans', subsets: ['latin'] })
const geistMono = Geist_Mono({ variable: '--font-geist-mono', subsets: ['latin'] })

export default function ClientWrapper({
  children,
  locale,
  messages,
}: {
  children: ReactNode
  locale: string
  messages: Record<string, any>
}) {
  useEffect(() => {
    ;(async () => {
      const mod = await import('@twa-dev/sdk')
      const WebApp = mod.default
      WebApp.ready()
      WebApp.expand()
    })()

    loginFromTelegram()
  }, [])

  return (
    <div className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
      <NextIntlClientProvider
        locale={locale}
        messages={messages}
        timeZone="Europe/Paris"
      >
        <SkeletonTheme baseColor="#1e1e1e" highlightColor="#333">
          <div id="wrap" className="mobile-wrap">
            <div id="content" className="mobile-content">
              {children}
            </div>
          </div>
        </SkeletonTheme>
        <Toaster
          position="bottom-center"
          toastOptions={{
            style: {
              background: '#27272a',
              color: '#fff',
              fontSize: '14px',
              border: '1px solid #3f3f46',
              borderRadius: '8px',
              padding: '10px 14px',
            },
            success: {
              iconTheme: {
                primary: '#22c55e',
                secondary: '#fff',
              },
            },
            error: {
              iconTheme: {
                primary: '#ef4444',
                secondary: '#fff',
              },
            },
          }}
        />
      </NextIntlClientProvider>
    </div>
  )
}
