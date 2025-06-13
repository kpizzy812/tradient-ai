'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { useTranslations } from 'next-intl'
import clsx from 'clsx'
import { vibrate } from '@/shared/vibration'
import { PoolInfo } from '@/types/pools'
import { useProfile } from '@/shared/hooks/useProfile'
import { withdrawFromPool } from '@/shared/api'
import { toast } from 'react-hot-toast'

interface WithdrawModalProps {
  pool: PoolInfo
  onClose: () => void
  onContinue: (finalAmount: number, executeUntil: string) => void
}

export const WithdrawModal: React.FC<WithdrawModalProps> = ({
  pool,
  onClose,
  onContinue,
}) => {
  const t = useTranslations()
  const { userId, mutate } = useProfile()
  const [amount, setAmount] = useState('')
  const amountNumber = parseFloat(amount)
  const [mode, setMode] = useState<'basic' | 'express'>('basic')
  const [loading, setLoading] = useState(false)

  const validAmount =
    !isNaN(amountNumber) &&
    amountNumber > 0 &&
    amountNumber <= pool.user_balance

  const handleWithdraw = async () => {
    vibrate()
    setLoading(true)
    try {
      const res = await withdrawFromPool(
        amountNumber,
        pool.name,
        mode,
        'INTERNAL',      // или любой другой выбранный метод
        userId!,
        0
      )
      await mutate()
        toast.success(
          `${t('withdraw.successScheduled')} ${new Date(res.execute_until).toLocaleString()}`
        )
        onContinue(res.final_amount, res.execute_until)

    } catch (err: any) {
      const msg = err.response?.data?.detail || t('withdraw.error')
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="w-full max-w-md bg-zinc-900 p-6 rounded-2xl border border-zinc-700 space-y-4"
      >
        <h2 className="text-white text-xl font-bold">
          {t('withdraw.title')} — {pool.name}
        </h2>

        <div>
          <label className="block text-sm text-zinc-400 mb-1">
            {t('withdraw.amount')}
          </label>
          <input
            type="text"
            inputMode="decimal"
            pattern="[0-9]*"
            value={amount}
            onChange={e =>
              setAmount(e.target.value.replace(/[^0-9.]/g, ''))
            }
            placeholder={t('withdraw.enter_amount')}
            className="w-full px-4 py-2 rounded-xl bg-zinc-800 text-white border border-zinc-600 focus:outline-none appearance-none"
          />
          <p className="text-xs text-zinc-400 mt-1">
            {t('withdraw.max')}: ${pool.user_balance.toFixed(2)}
          </p>
        </div>

        {validAmount && (
          <div className="space-y-2">
            <div className="text-sm text-zinc-300">
              {t('withdraw.choose_mode')}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setMode('basic')}
                className={clsx(
                  'flex-1 px-4 py-2 rounded-xl text-sm border',
                  mode === 'basic'
                    ? 'border-blue-500 text-white'
                    : 'border-zinc-600 text-zinc-400'
                )}
              >
                {t('withdraw.basic')}
              </button>
              <button
                onClick={() => setMode('express')}
                className={clsx(
                  'flex-1 px-4 py-2 rounded-xl text-sm border',
                  mode === 'express'
                    ? 'border-blue-500 text-white'
                    : 'border-zinc-600 text-zinc-400'
                )}
              >
                {t('withdraw.express')}
              </button>
            </div>
            <p className="text-xs text-zinc-500">
              {mode === 'basic'
                ? t('withdraw.basicDesc')
                : t('withdraw.expressDesc')}
            </p>
          </div>
        )}

        <div className="flex justify-between gap-2">
          <button
            onClick={() => {
              vibrate()
              onClose()
            }}
            className="w-1/2 px-4 py-2 rounded-xl text-sm bg-zinc-700 text-white"
          >
            {t('common.cancel')}
          </button>
          <button
            onClick={handleWithdraw}
            disabled={!validAmount || loading}
            className={clsx(
              'w-1/2 px-4 py-2 rounded-xl text-sm text-white transition',
              validAmount && !loading
                ? 'bg-blue-600 hover:bg-blue-700'
                : 'bg-blue-600 opacity-50 cursor-not-allowed'
            )}
          >
            {t('common.continue')}
          </button>
        </div>
      </motion.div>
    </div>
  )
}
