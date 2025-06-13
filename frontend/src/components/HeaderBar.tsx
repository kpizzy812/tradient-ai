'use client';

import React from 'react';
import { useTranslations } from 'next-intl';
import Image from 'next/image';
import { motion } from 'framer-motion';

type HeaderBarProps = {
  onLanguageSwitch?: () => void;
};

export const HeaderBar: React.FC<HeaderBarProps> = ({
  onLanguageSwitch,
}) => {
  const t = useTranslations();

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glassmorphism flex items-center justify-between px-6 py-4 backdrop-blur-xl"
    >
      {/* Логотип */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.98 }}
        onClick={onLanguageSwitch}
        className="flex items-center gap-3 hover:opacity-80 transition-all duration-300"
        aria-label={t('common.switchLanguage')}
      >
        <div className="relative">
          <Image
            src="/images/logo.png"
            alt="logo"
            width={40}
            height={40}
            className="rounded-xl shadow-lg"
          />
          <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-blue-500/20 to-cyan-500/20 animate-pulse-glow"></div>
        </div>
        <div className="hidden sm:block">
          <h1 className="text-white font-bold text-lg text-gradient-blue">
            Tradient AI
          </h1>
          <p className="text-slate-400 text-xs">
            AI Trading Platform
          </p>
        </div>
      </motion.button>

      {/* Дополнительные элементы */}
      <div className="flex items-center gap-3">
        {/* Индикатор статуса */}
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2 }}
          className="flex items-center gap-2 px-3 py-1.5 bg-green-500/20 rounded-lg border border-green-500/30"
        >
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
          <span className="text-green-400 text-xs font-medium">
            Online
          </span>
        </motion.div>

        {/* Меню/настройки */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="p-2 rounded-lg bg-slate-800/50 hover:bg-slate-700/50 transition-all duration-300 border border-slate-600/30"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-slate-300">
            <circle cx="12" cy="12" r="3"/>
            <path d="M12 1v6m0 6v6"/>
            <path d="M1 12h6m6 0h6"/>
          </svg>
        </motion.button>
      </div>
    </motion.div>
  );
};