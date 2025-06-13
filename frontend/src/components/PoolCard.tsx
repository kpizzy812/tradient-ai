'use client'

import React from 'react'
import { useTranslations } from 'next-intl'
import { motion } from 'framer-motion'
import { PoolInfo } from '@/types/pools'

interface PoolCardProps {
  pool: PoolInfo
  onInvest: (pool: PoolInfo) => void
  onWithdraw?: (pool: PoolInfo) => void
  onToggleReinvest?: (pool: PoolInfo, value: boolean) => void
}

export const PoolCard: React.FC<PoolCardProps> = ({
  pool,
  onInvest,
  onWithdraw,
  onToggleReinvest,
}) => {
  const t = useTranslations()
  const [minYield, maxYield] = pool.yield_range
  const hasBalance = pool.user_balance > 0

  return (
    <motion.div 
      whileHover={{ y: -4 }}
      className="glassmorphism-card rounded-2xl p-6 shadow-xl interactive-card group relative overflow-hidden"
    >
      {/* Декоративные элементы */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-blue-500/10 to-transparent rounded-full blur-2xl"></div>
      <div className="absolute bottom-0 left-0 w-24 h-24 bg-gradient-to-tr from-cyan-500/10 to-transparent rounded-full blur-xl"></div>
      
      {/* Основной контент */}
      <div className="relative z-10 space-y-4">
        {/* Заголовок + доходность */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center">
              <span className="text-white font-bold text-sm">AI</span>
            </div>
            <div>
              <h2 className="text-white font-bold text-lg">{pool.name}</h2>
              <p className="text-slate-400 text-sm">AI Trading Pool</p>
            </div>
          </div>
          
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="text-right"
          >
            <div className="text-gradient-success font-bold text-lg">
              {minYield.toFixed(1)}% – {maxYield.toFixed(1)}%
            </div>
            <p className="text-slate-400 text-xs">Expected APY</p>
          </motion.div>
        </div>

        {/* Статистика */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-slate-800/30 rounded-xl p-3 border border-slate-700/50">
            <p className="text-slate-400 text-xs font-medium mb-1">Min Deposit</p>
            <p className="text-white font-bold text-lg">${pool.min_invest}</p>
          </div>
          
          <div className="bg-slate-800/30 rounded-xl p-3 border border-slate-700/50">
            <p className="text-slate-400 text-xs font-medium mb-1">Your Balance</p>
            <p className={`font-bold text-lg ${hasBalance ? 'text-gradient-blue' : 'text-white'}`}>
              ${pool.user_balance.toFixed(2)}
            </p>
          </div>
        </div>

        {/* Тумблер авто-реинвеста */}
        {onToggleReinvest && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex items-center justify-between p-3 bg-slate-800/20 rounded-xl border border-slate-700/30"
          >
            <div>
              <span className="text-white font-medium text-sm">{t('poolCard.autoReinvest')}</span>
              <p className="text-slate-400 text-xs">Automatically compound earnings</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                className="sr-only peer"
                checked={pool.reinvest}
                onChange={(e) => onToggleReinvest(pool, e.target.checked)}
              />
              <div className="w-12 h-6 bg-slate-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-6 peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-gradient-to-r peer-checked:from-blue-500 peer-checked:to-cyan-500 peer-checked:shadow-lg peer-checked:glow-blue">
              </div>
            </label>
          </motion.div>
        )}

        {/* Кнопки */}
        <div className="flex gap-3 pt-2">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => onInvest(pool)}
            className="btn-primary flex-1 relative overflow-hidden group"
          >
            <span className="relative z-10 flex items-center justify-center gap-2">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
              </svg>
              {t('poolCard.invest')}
            </span>
            
            {/* Анимированный блик */}
            <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/20 to-transparent"></div>
          </motion.button>

          {hasBalance && onWithdraw && (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => onWithdraw(pool)}
              className="btn-secondary p-3 aspect-square flex items-center justify-center"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 5v14M5 12l7 7 7-7"/>
              </svg>
            </motion.button>
          )}
        </div>

        {/* Индикатор активности */}
        {hasBalance && (
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: '100%' }}
            transition={{ duration: 1, delay: 0.5 }}
            className="h-1 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full"
          />
        )}
      </div>
    </motion.div>
  )
}