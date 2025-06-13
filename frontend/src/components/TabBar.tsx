'use client';
import React from 'react';
import clsx from 'clsx';
import { vibrate } from '@/shared/vibration';

type TabKey = 'pools' | 'profile' | 'info';

interface TabBarProps {
  activeTab: TabKey;
  onTabChange: (tab: TabKey) => void;
}

const tabs: { key: TabKey; label: string }[] = [
  { key: 'pools', label: 'POOLS' },
  { key: 'profile', label: 'TEAM' },
  { key: 'info', label: 'INFO' },
];

export const TabBar: React.FC<TabBarProps> = ({ activeTab, onTabChange }) => {
  return (
    <div className="relative flex overflow-hidden bg-black rounded-2xl px-[1px] py-[1px]">
      {tabs.map((tab, index) => {
        const isActive = tab.key === activeTab;

        return (
          <button
            key={tab.key}
            onClick={() => {
              vibrate();
              onTabChange(tab.key);
            }}
            className={clsx(
              'flex-1 py-2 text-center font-medium text-sm transition-all duration-200',
              isActive
                ? 'bg-zinc-900 text-white z-10'
                : 'bg-zinc-950 text-zinc-500 z-0 border-b border-zinc-800',
              index === 0 && 'rounded-l-2xl',
              index === tabs.length - 1 && 'rounded-r-2xl'
            )}
            style={{
              boxShadow: isActive ? 'inset 0px -1px 0px #18181b' : undefined,
            }}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
};
