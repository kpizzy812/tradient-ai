'use client';

import React, { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { motion, AnimatePresence } from 'framer-motion';
import { UserProfile } from '@/shared/api';

interface BalanceCardProps {
  profile: UserProfile | null;
  onWithdraw?: () => void;
  loading?: boolean;
}

// Простой мини-график для демонстрации роста
const MiniChart: React.FC<{ data: number[]; positive: boolean }> = ({ data, positive }) => {
  const maxValue = Math.max(...data);
  const minValue = Math.min(...data);
  const range = maxValue - minValue || 1;

  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * 100;
    const y = 100 - ((value - minValue) / range) * 100;
    return `${x},${y}`;
  }).join(' ');

  return (
    <div className="w-full h-16 relative overflow-hidden">
      <svg
        width="100%"
        height="100%"
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        className="absolute inset-0"
      >
        <defs>
          <linearGradient id={`gradient-${positive ? 'up' : 'down'}`} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor={positive ? '#10B981' : '#EF4444'} stopOpacity="0.8" />
            <stop offset="100%" stopColor={positive ? '#10B981' : '#EF4444'} stopOpacity="0.1" />
          </linearGradient>
        </defs>

        {/* Заливка области под графиком */}
        <path
          d={`M 0,100 L ${points} L 100,100 Z`}
          fill={`url(#gradient-${positive ? 'up' : 'down'})`}
        />

        {/* Линия графика */}
        <polyline
          fill="none"
          stroke={positive ? '#10B981' : '#EF4444'}
          strokeWidth="2"
          points={points}
          className="drop-shadow-sm"
        />

        {/* Точки на графике */}
        {data.map((_, index) => {
          const x = (index / (data.length - 1)) * 100;
          const y = 100 - ((data[index] - minValue) / range) * 100;
          return (
            <circle
              key={index}
              cx={x}
              cy={y}
              r="1.5"
              fill={positive ? '#10B981' : '#EF4444'}
              className="drop-shadow-sm"
            />
          );
        })}
      </svg>
    </div>
  );
};

const CountingNumber: React.FC<{ value: number; prefix?: string; suffix?: string; decimals?: number }> = ({
  value,
  prefix = '',
  suffix = '',
  decimals = 2
}) => {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    let startTime: number;
    let startValue = displayValue;
    const duration = 1000; // 1 секунда анимации

    const animate = (currentTime: number) => {
      if (!startTime) startTime = currentTime;
      const progress = Math.min((currentTime - startTime) / duration, 1);

      // Easing function
      const easeOut = 1 - Math.pow(1 - progress, 3);
      const currentValue = startValue + (value - startValue) * easeOut;

      setDisplayValue(currentValue);

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    requestAnimationFrame(animate);
  }, [value]);

  return (
    <span>
      {prefix}{displayValue.toFixed(decimals)}{suffix}
    </span>
  );
};

export const BalanceCard: React.FC<BalanceCardProps> = ({ profile, onWithdraw, loading = false }) => {
  const t = useTranslations();
  const [selectedPeriod, setSelectedPeriod] = useState<'24h' | '7d' | '30d' | 'all'>('all');

  if (loading || !profile) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glassmorphism-card rounded-2xl p-6 mb-6 animate-pulse"
      >
        <div className="space-y-4">
          <div className="h-6 bg-slate-700 rounded w-1/3"></div>
          <div className="h-12 bg-slate-700 rounded w-2/3"></div>
          <div className="grid grid-cols-3 gap-4">
            <div className="h-16 bg-slate-700 rounded"></div>
            <div className="h-16 bg-slate-700 rounded"></div>
            <div className="h-16 bg-slate-700 rounded"></div>
          </div>
        </div>
      </motion.div>
    );
  }

  // Вычисляем PNL данные
  const currentBalance = profile.profit_usd;
  const totalDeposited = profile.deposit_usd;
  const totalWithdrawn = profile.withdraw_usd;
  const totalEarned = profile.total_earned_usd;

  // Расчет нереализованной прибыли/убытка
  const unrealizedPNL = currentBalance;
  const totalPNL = totalEarned;
  const totalROI = totalDeposited > 0 ? ((totalEarned / totalDeposited) * 100) : 0;

  const isProfitable = totalPNL >= 0;

  // Генерируем фиктивные данные для графика (в реальном приложении это будут исторические данные)
  const generateMockData = () => {
    const baseValue = Math.max(totalDeposited, 100);
    return Array.from({ length: 30 }, (_, i) => {
      const progress = i / 29;
      const noise = (Math.random() - 0.5) * baseValue * 0.1;
      return baseValue + (totalEarned * progress) + noise;
    });
  };

  const chartData = generateMockData();

  const periods = [
    { key: '24h' as const, label: '24H', active: selectedPeriod === '24h' },
    { key: '7d' as const, label: '7D', active: selectedPeriod === '7d' },
    { key: '30d' as const, label: '30D', active: selectedPeriod === '30d' },
    { key: 'all' as const, label: 'ALL', active: selectedPeriod === 'all' },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glassmorphism-card rounded-2xl p-6 mb-6 interactive-card group"
    >
      {/* Заголовок с балансом */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex-1">
          <p className="text-slate-400 text-sm font-medium mb-2">
            {t('common.balance')}
          </p>
          <div className="flex items-baseline gap-2">
            <h1 className="heading-lg text-gradient-blue">
              $<CountingNumber value={currentBalance} />
            </h1>
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.3, type: "spring" }}
              className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold ${
                isProfitable
                  ? 'bg-green-500/20 text-green-400'
                  : 'bg-red-500/20 text-red-400'
              }`}
            >
              <span className={isProfitable ? '↗' : '↘'}>
                {isProfitable ? '+' : ''}{totalROI.toFixed(1)}%
              </span>
            </motion.div>
          </div>
        </div>

        <button
          onClick={onWithdraw}
          className="btn-primary ml-4 group-hover:glow-blue transition-all duration-300"
        >
          <span className="flex items-center gap-2">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
            </svg>
            {t('common.withdraw')}
          </span>
        </button>
      </div>

      {/* График с периодами */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-white font-semibold">Portfolio Performance</h3>
          <div className="flex items-center gap-1 bg-slate-800/50 rounded-lg p-1">
            {periods.map((period) => (
              <button
                key={period.key}
                onClick={() => setSelectedPeriod(period.key)}
                className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${
                  period.active
                    ? 'bg-blue-500 text-white'
                    : 'text-slate-400 hover:text-white hover:bg-slate-700'
                }`}
              >
                {period.label}
              </button>
            ))}
          </div>
        </div>

        <MiniChart data={chartData} positive={isProfitable} />
      </div>

      {/* PNL статистика */}
      <div className="grid grid-cols-3 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-slate-800/30 rounded-xl p-4 border border-slate-700/50"
        >
          <p className="text-slate-400 text-xs font-medium mb-1">Total P&L</p>
          <p className={`font-bold text-lg ${isProfitable ? 'text-gradient-success' : 'text-gradient-danger'}`}>
            <CountingNumber value={totalPNL} prefix={isProfitable ? '+$' : '-$'} />
          </p>
          <p className="text-slate-500 text-xs">
            {isProfitable ? '+' : ''}<CountingNumber value={totalROI} suffix="%" decimals={1} />
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-slate-800/30 rounded-xl p-4 border border-slate-700/50"
        >
          <p className="text-slate-400 text-xs font-medium mb-1">Invested</p>
          <p className="font-bold text-lg text-white">
            $<CountingNumber value={totalDeposited} />
          </p>
          <p className="text-slate-500 text-xs">Total Deposits</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-slate-800/30 rounded-xl p-4 border border-slate-700/50"
        >
          <p className="text-slate-400 text-xs font-medium mb-1">Withdrawn</p>
          <p className="font-bold text-lg text-blue-400">
            $<CountingNumber value={totalWithdrawn} />
          </p>
          <p className="text-slate-500 text-xs">Total Paid Out</p>
        </motion.div>
      </div>

      {/* Дополнительная статистика */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="mt-4 pt-4 border-t border-slate-700/50"
      >
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-400">Available Balance</span>
          <span className="text-white font-semibold">
            $<CountingNumber value={currentBalance} />
          </span>
        </div>
      </motion.div>
    </motion.div>
  );
};