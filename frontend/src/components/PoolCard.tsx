
'use client'

import React from 'react'
import { useTranslations } from 'next-intl'
import clsx from 'clsx'
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
    <div className="rounded-2xl bg-zinc-900 border border-zinc-800 px-4 py-3 shadow-sm space-y-2">
      {/* Заголовок + доходность */}
      <div className="flex items-center justify-between">
        <h2 className="text-white font-semibold text-base">{pool.name}</h2>
        <span className="text-sm text-blue-400">
          {minYield.toFixed(2)}% – {maxYield.toFixed(2)}%
        </span>
      </div>

      {/* Минимальная сумма */}
      <div className="text-sm text-zinc-400">
        {t('poolCard.minDeposit')}: <span className="text-white">${pool.min_invest}</span>
      </div>

      {/* Баланс пользователя */}
      <div className="text-sm text-zinc-400">
        {t('poolCard.balance')}: <span className="text-white">${pool.user_balance}</span>
      </div>

      {/* Тумблер авто-реинвеста */}
      {onToggleReinvest && (
        <div className="flex items-center justify-between text-sm pt-1">
          <span className="text-white">{t('poolCard.autoReinvest')}</span>
          <label className="inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              className="sr-only peer"
              checked={pool.reinvest}
              onChange={(e) => onToggleReinvest(pool, e.target.checked)}
            />
            <div className="w-10 h-5 bg-gray-600 peer-checked:bg-blue-500 rounded-full transition-all relative">
              <div
                className={clsx(
                  'absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-all',
                  pool.reinvest && 'translate-x-5'
                )}
              />
            </div>
          </label>
        </div>
      )}

      {/* Кнопки */}
      <div className="flex mt-2 gap-2">
        <button
          onClick={() => onInvest(pool)}
          className={clsx(
            'relative overflow-hidden bg-blue-600 hover:bg-blue-700 text-white text-sm py-2 rounded-xl transition w-full',
          )}
        >
          <span className="relative z-10">{t('poolCard.invest')}</span>
          {/* статичный градиент */}
          <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent rounded-xl" />
          {/* движущийся бликовый штрих */}
          <span className="absolute top-0 left-0 h-full w-6 bg-white/40 blur-sm animate-glint-fast" />
        </button>

        {hasBalance && onWithdraw && (
          <button
            onClick={() => onWithdraw(pool)}
            className="relative overflow-hidden px-3 py-2 bg-zinc-700 hover:bg-zinc-600 rounded-xl text-white text-sm transition"
          >
            <span className="relative z-10">−</span>
            <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent rounded-xl" />
            <span className="absolute top-0 left-0 h-full w-6 bg-white/40 blur-sm animate-glint-fast" />
          </button>
        )}
      </div>

      <style jsx>{`
        @keyframes glint-fast {
          0% { transform: translateX(-100%) skewX(-20deg); opacity: 0; }
          50% { opacity: 1; }
          100% { transform: translateX(200%) skewX(-20deg); opacity: 0; }
        }
        .animate-glint-fast {
          animation: glint-fast 2s linear infinite;
        }
      `}</style>
    </div>
  )
}
