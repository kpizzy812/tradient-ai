import type { Metadata } from 'next'
import '../globals.css'
import ClientWrapperShell from './ClientWrapperShell'

export const metadata: Metadata = {
  title: 'Tradient AI Mini App',
  description: 'Your Tradient AI dashboard',
}

type Props = {
  children: React.ReactNode
  params: Promise<{ locale: string }>
}

export default async function LocaleLayout({ children, params }: Props) {
  const { locale } = await params
  const messagesModule = await import(`../../messages/${locale}.json`)
  const messages: Record<string, any> = messagesModule.default

  return (
    <ClientWrapperShell locale={locale} messages={messages}>
      {children}
    </ClientWrapperShell>
  )
}
