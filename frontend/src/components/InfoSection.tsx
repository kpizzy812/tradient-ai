/* eslint-disable @next/next/no-img-element, jsx-a11y/alt-text */
'use client';

import React, { useEffect, useState, useRef } from 'react';
import { createPortal } from 'react-dom';
import { useTranslations } from 'next-intl';
import { useProfile } from '@/shared/hooks/useProfile';
import { motion } from 'framer-motion';
import { useRouter, usePathname } from 'next/navigation';

export default function InfoSection() {
  const t = useTranslations();
  const { profile, mutate } = useProfile();
  const router = useRouter();
  const pathname = usePathname();
  const [langMenuOpen, setLangMenuOpen] = useState(false);
  const [tgUser, setTgUser] = useState<any>(null);
  const buttonRef = useRef<HTMLDivElement>(null);
  const [menuStyle, setMenuStyle] = useState({ top: 0, left: 0, width: 0 });

  useEffect(() => {
    const user = (window as any)?.Telegram?.WebApp?.initDataUnsafe?.user;
    setTgUser(user);
  }, []);

  useEffect(() => {
    if (langMenuOpen && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      setMenuStyle({ top: rect.bottom + window.scrollY, left: rect.left + window.scrollX, width: rect.width });
    }
  }, [langMenuOpen]);

  const handleLanguageChange = async (newLang: string) => {
    setLangMenuOpen(false);
    const userId = tgUser?.id ?? profile?.user_id;
    try {
      const res = await fetch('/api/user/language', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, lang: newLang }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || 'Error');
      await mutate();
      const segments = pathname.split('/');
      segments[1] = newLang;
      await router.replace(segments.join('/'));
    } catch (err) {
      console.error('[LangChange] failed:', err);
    }
  };

  if (!profile || !tgUser) return null;

  const avatarUrl = tgUser.photo_url || '';
  const username = tgUser.username;
  const tgId = tgUser.id;

  return (
    <>
      <div className="space-y-6 pb-[calc(7rem+env(safe-area-inset-bottom))]">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="rounded-2xl bg-zinc-900/80 backdrop-blur-sm border border-zinc-800 px-5 py-5 shadow-sm"
        >
          <div className="flex items-center gap-4">
            {avatarUrl ? (
              <img
                src={avatarUrl}
                onError={e => { e.currentTarget.style.display = 'none'; }}
                className="w-14 h-14 rounded-full border border-zinc-700"
              />
            ) : (
              <div className="w-14 h-14 rounded-full bg-zinc-700" />
            )}
            <div>
              <div className="text-white font-semibold text-lg">@{username}</div>
              <div className="text-sm text-zinc-400">ID: {tgId}</div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 mt-4">
            <div ref={buttonRef} className="relative"> {/* ссылка для портала */}
              <button
                onClick={() => setLangMenuOpen(open => !open)}
                className="flex w-full items-center justify-center gap-2 bg-zinc-800 hover:bg-zinc-700 transition text-sm text-white py-2 rounded-xl"
              >
                <img src="/icons/lang.svg" className="w-5 h-5" alt="lang" />
                {t('common.switchLanguage')}
              </button>
            </div>

            <button className="flex items-center justify-center gap-2 bg-zinc-800 hover:bg-zinc-700 transition text-sm text-white py-2 rounded-xl">
              <img src="/icons/history.svg" className="w-5 h-5" alt="history" />
              История
            </button>
          </div>
        </motion.div>

        {/* Статистика */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.3 }}
          className="rounded-2xl bg-zinc-900/80 backdrop-blur-sm border border-zinc-800 px-5 py-5 shadow-sm space-y-2"
        >
          <div className="text-white font-semibold text-base">{t('info.title')}</div>
          <div className="flex justify-between text-base text-zinc-400">
            <span>{t('info.deposit')}</span>
            <span className="text-white font-medium">${(profile.deposit_usd||0).toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-base text-zinc-400">
            <span>{t('info.withdraw')}</span>
            <span className="text-white font-medium">${(profile.withdraw_usd||0).toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-base text-zinc-400">
            <span>{t('info.profitTotal')}</span>
            <span className="text-white font-medium">${(profile.total_earned_usd||0).toFixed(2)}</span>
          </div>
        </motion.div>

        {/* О платформе */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.3 }}
          className="rounded-2xl bg-zinc-900/80 backdrop-blur-sm border border-zinc-800 px-5 py-5 shadow-sm space-y-4"
        >
          <h2 className="text-white font-semibold text-lg text-center">{t('info.title')}</h2>
          <img src="/images/legend.png" alt="legend" className="w-full max-w-[280px] mx-auto rounded-xl" />
          <p className="text-sm text-zinc-300 leading-relaxed whitespace-pre-line">{t('info.legend')}</p>
        </motion.div>

        {/* Ссылки */}
        <div className="fixed bottom-0 left-0 w-full bg-zinc-900 border-t border-zinc-800 px-4 py-3 flex justify-center gap-8">
          <a href="https://t.me/TradientChat" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-white hover:underline">
            <img src="/icons/telegram.webp" alt="tg" className="w-5 h-5" />
            <span>{t('info.chat')}</span>
          </a>
          <a href="https://t.me/SergioTradientAI" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-white hover:underline">
            <img src="/icons/telegram.webp" alt="tg" className="w-5 h-5" />
            <span>{t('info.support')}</span>
          </a>
        </div>
      </div>

      {/* Портал для меню языков */}
      {langMenuOpen &&
        createPortal(
          <div
            style={{
              position: 'absolute',
              top: menuStyle.top,
              left: menuStyle.left,
              width: menuStyle.width
            }}
            className="z-50 bg-zinc-900 border border-zinc-700 rounded-xl shadow-lg overflow-hidden"
          >
            {['ru', 'en', 'uk'].map(code => {
              const label = code === 'ru' ? '🇷🇺 Русский' : code === 'en' ? '🇺🇸 English' : '🇺🇦 Українська';
              const isActive = profile.lang === code;
              return (
                <button
                  key={code}
                  onClick={() => handleLanguageChange(code)}
                  className={`block w-full text-left px-4 py-2 text-sm hover:bg-zinc-800 transition ${
                    isActive ? 'text-white font-semibold' : 'text-zinc-400'
                  }`}
                >
                  {label}
                </button>
              );
            })}
          </div>,
          document.body
        )}
    </>
  );
}
