// middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export const config = {
  matcher: ['/'], // реагируем только на корень
}

export async function middleware(req: NextRequest) {
  // клонируем URL, чтобы не мутировать исходный
  const url = req.nextUrl.clone()

  // дефолтный язык
  let lang = 'ru'

  // Telegram-WebApp передаёт initData в query-параметре tgWebAppStartParam
  const raw = url.searchParams.get('tgWebAppStartParam')
  if (raw) {
    try {
      // декодируем и парсим
      const params = new URLSearchParams(decodeURIComponent(raw))
      const userJson = params.get('user')
      if (userJson) {
        const { id: tgId } = JSON.parse(userJson)
        // вызываем ваш эндпоинт, который отдаёт язык по tg_id
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/user/language/${tgId}`,
          { cache: 'no-store' }
        )
        if (res.ok) {
          const data = await res.json()
          lang = data.lang || lang
        }
      }
    } catch (e) {
      console.error('middleware language detect failed:', e)
    }
  }

  // редиректим на подпуть /ru, /en или /uk
  url.pathname = `/${lang}`
  return NextResponse.redirect(url)
}
