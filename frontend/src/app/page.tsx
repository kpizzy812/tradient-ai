// src/app/page.tsx
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'

export default async function RootPage() {
  // default
  let lang = 'ru'

  // try to pull Telegram’s initData out of the session cookie
  // (this is the one your WebApp runtime automatically set for you)
  const cookieStore = await cookies()
  const initCookie = cookieStore.get('__telegram__initParams')?.value

  if (initCookie) {
    try {
      // it’s a JSON blob like:
      // { tgWebAppData: "query_id=…&user=%7B…%7D&…", … }
      const init = JSON.parse(initCookie)
      const rawQs = init.tgWebAppData
      if (typeof rawQs === 'string') {
        const params = new URLSearchParams(rawQs)
        const userJson = params.get('user')
        if (userJson) {
          const { id: tgId } = JSON.parse(userJson)
          // now ask your API what that user’s lang is
          const res = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/user/language/${tgId}`,
            { cache: 'no-store' }
          )
          if (res.ok) {
            const body = await res.json()
            if (['ru','en','uk'].includes(body.lang)) {
              lang = body.lang
            }
          }
        }
      }
    } catch (e) {
      console.error('Failed parsing initParams:', e)
    }
  }

  // finally redirect straight into /ru, /en or /uk
  redirect(`/${lang}`)
}
