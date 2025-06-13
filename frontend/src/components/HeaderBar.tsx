'use client';

import React from 'react';
import { useTranslations } from 'next-intl';
import Image from 'next/image';

type HeaderBarProps = {
  balanceUsd?: number;
  onWithdraw?: () => void;
  onLanguageSwitch?: () => void;
};

export const HeaderBar: React.FC<HeaderBarProps> = ({
  balanceUsd = 0,
  onWithdraw,
  onLanguageSwitch,
}) => {
  const t = useTranslations();

  return (
    <div className="relative flex items-center justify-between px-4 py-3 bg-zinc-900 border-b border-zinc-800">
      {/* Логотип */}
      <button
        onClick={onLanguageSwitch}
        className="hover:opacity-80 transition"
        aria-label={t('common.switchLanguage')}
      >
        <Image
          src="/images/logo.png"
          alt="logo"
          width={36}
          height={36}
          className="rounded-md"
        />
      </button>

      {/* Баланс */}
      <div className="absolute left-1/2 -translate-x-1/2 text-white text-sm font-medium">
        {t('common.balance')}: {' '}
        <span className="text-green-400 font-semibold">
          ${balanceUsd.toFixed(2)}
        </span>
      </div>

      {/* Кнопка "Вывести" с улучшенной анимацией блика */}
      <button
        className="relative overflow-hidden bg-blue-600 hover:bg-blue-700 text-white text-sm px-4 py-1.5 rounded-xl transition"
        onClick={onWithdraw}
      >
        <span className="relative z-10">{t('common.withdraw')}</span>
        {/* основной слой блика */}
        <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent rounded-xl" />
        {/* движущийся узкий бликовый штрих */}
        <span className="absolute top-0 left-0 h-full w-8 bg-white/40 blur-sm animate-glint" />
      </button>

      <style jsx>{`
        @keyframes glint {
          0% { transform: translateX(-100%) skewX(-20deg); opacity: 0; }
          50% { opacity: 1; }
          100% { transform: translateX(200%) skewX(-20deg); opacity: 0; }
        }
        .animate-glint {
          animation: glint 3s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
};
