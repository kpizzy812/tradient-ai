'use client'

import { ReactNode } from 'react'
import ClientWrapper from '@/components/ClientWrapper'

export default function ClientWrapperShell({
  children,
  locale,
  messages,
}: {
  children: ReactNode
  locale: string
  messages: Record<string, any>
}) {
  return (
    <ClientWrapper locale={locale} messages={messages}>
      {children}
    </ClientWrapper>
  )
}
