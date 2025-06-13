'use client';
import React from 'react';
import { motion } from 'framer-motion';
import { vibrate } from '@/shared/vibration';

type TabKey = 'pools' | 'profile' | 'info';

interface TabBarProps {
  activeTab: TabKey;
  onTabChange: (tab: TabKey) => void;
}

const tabs: { key: TabKey; label: string; icon: string }[] = [
  { key: 'pools', label: 'POOLS', icon: '💎' },
  { key: 'profile', label: 'TEAM', icon: '👥' },
  { key: 'info', label: 'INFO', icon: '📊' },
];

export const TabBar: React.FC<TabBarProps> = ({ activeTab, onTabChange }) => {
  return (
    <div className="glassmorphism-card rounded-2xl p-1 relative overflow-hidden">
      {/* Фоновая анимация */}
      <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 via-cyan-500/10 to-blue-500/10 animate-shimmer"></div>

      <div className="relative flex">
        {tabs.map((tab, index) => {
          const isActive = tab.key === activeTab;

          return (
            <div key={tab.key} className="flex-1 relative">
              {/* Активный индикатор */}
              {isActive && (
                <motion.div
                  layoutId="activeTab"
                  className="absolute inset-0 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-xl shadow-lg glow-blue"
                  transition={{ type: "spring", bounce: 0.15, duration: 0.5 }}
                />
              )}

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => {
                  vibrate();
                  onTabChange(tab.key);
                }}
                className={`
                  relative w-full py-3 px-4 text-center font-semibold text-sm
                  transition-all duration-300 rounded-xl
                  flex items-center justify-center gap-2
                  ${isActive
                    ? 'text-white z-10'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/30'
                  }
                `}
              >
                <span className="text-base">{tab.icon}</span>
                <span className="tracking-wider">{tab.label}</span>

                {/* Hover эффект для неактивных вкладок */}
                {!isActive && (
                  <motion.div
                    className="absolute inset-0 bg-slate-700/20 rounded-xl opacity-0 hover:opacity-100 transition-opacity"
                    whileHover={{ opacity: 1 }}
                  />
                )}
              </motion.button>
            </div>
          );
        })}
      </div>

      {/* Декоративные элементы */}
      <div className="absolute -top-1 -left-1 w-8 h-8 bg-gradient-to-br from-blue-500/20 to-transparent rounded-full blur-sm"></div>
      <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-gradient-to-tl from-cyan-500/20 to-transparent rounded-full blur-sm"></div>
    </div>
  );
};