'use client'

import React, { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import { useTranslations } from 'next-intl'
import clsx from 'clsx'
import { vibrate } from '@/shared/vibration'
import { PoolInfo } from '@/types/pools'
import { useProfile } from '@/shared/hooks/useProfile'
import { useWithdrawFees } from '@/shared/hooks/useWithdrawFees'
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
  const { feesData, calculateFees, loading: feesLoading } = useWithdrawFees()
  const [amount, setAmount] = useState('')
  const amountNumber = parseFloat(amount)
  const [mode, setMode] = useState<'basic' | 'express'>('basic')
  const [loading, setLoading] = useState(false)

  const validAmount = !isNaN(amountNumber) && amountNumber > 0 && amountNumber <= pool.user_balance

  const poolFeesInfo = useMemo(() => {
    return feesData?.pool_withdrawals.find(p => p.pool_name === pool.name)
  }, [feesData, pool.name])

  // Расчет комиссии и итоговой суммы на основе реальных данных
  const withdrawalInfo = useMemo(() => {
    if (!validAmount || !poolFeesInfo) return null

    const feeMode = mode === 'express' ? 'express' : 'standard'
    const calculatedFees = calculateFees(amountNumber, feeMode, pool.name)

    if (!calculatedFees) return null

    return {
      commission: calculatedFees.commissionRate * 100,
      commissionAmount: calculatedFees.commission,
      finalAmount: calculatedFees.finalAmount,
      executeDays: calculatedFees.executeDays,
      description: calculatedFees.description
    }
  }, [validAmount, amountNumber, mode, poolFeesInfo, calculateFees, pool.name])

  const handleWithdraw = async () => {
    vibrate()
    setLoading(true)
    try {
      const res = await withdrawFromPool(
        amountNumber,
        pool.name,
        mode,
        'INTERNAL',
        userId!,
        poolFeesInfo?.days_since_first_deposit || 0
      )
      await mutate()
      toast.success(
        t('withdraw.requestCreated', { amount: res.final_amount.toFixed(2) })
      )
      onContinue(res.final_amount, res.execute_until)
    } catch (err: any) {
      const msg = err.response?.data?.detail || t('withdraw.error')
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  if (feesLoading) {
    return (
      <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="w-full max-w-md bg-zinc-900 p-6 rounded-2xl border border-zinc-700 flex items-center justify-center"
        >
          <div className="text-white">{t('common.loading')}...</div>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="w-full max-w-md bg-zinc-900 p-6 rounded-2xl border border-zinc-700 space-y-4 max-h-[90vh] overflow-y-auto"
      >
        <div className="flex items-center justify-between">
          <h2 className="text-white text-xl font-bold">
            {t('withdraw.fromPool')} {pool.name}
          </h2>
          {poolFeesInfo && (
            <div className="text-xs text-zinc-400">
              {t('withdraw.investedDaysAgo', { days: poolFeesInfo.days_since_first_deposit })}
            </div>
          )}
        </div>

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
            placeholder={t('withdraw.enterAmount')}
            className="w-full px-4 py-2 rounded-xl bg-zinc-800 text-white border border-zinc-600 focus:outline-none appearance-none"
          />
          <p className="text-xs text-zinc-400 mt-1">
            {t('withdraw.available')}: ${pool.user_balance.toFixed(2)}
          </p>
        </div>

        {validAmount && poolFeesInfo && (
          <>
            <div className="space-y-3">
              <div className="text-sm text-zinc-300 font-medium">
                {t('withdraw.chooseMode')}:
              </div>

              {/* Базовый режим */}
              <div
                onClick={() => setMode('basic')}
                className={clsx(
                  'p-3 rounded-xl border cursor-pointer transition-all',
                  mode === 'basic'
                    ? 'border-blue-500 bg-blue-500/10'
                    : 'border-zinc-600 hover:border-zinc-500'
                )}
              >
                <div className="flex justify-between items-center mb-2">
                  <span className="text-white font-medium">
                    📅 {t('withdraw.standardMode')}
                  </span>
                  <span className="text-blue-400 text-sm">
                    {poolFeesInfo.standard_mode.execute_days} {t('common.days')}
                  </span>
                </div>

                {mode === 'basic' && withdrawalInfo && (
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-zinc-400">{t('withdraw.commission')}:</span>
                      <span className="text-orange-400">
                        {withdrawalInfo.commission.toFixed(1)}% ($${withdrawalInfo.commissionAmount.toFixed(2)})
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-400">{t('withdraw.toReceive')}:</span>
                      <span className="text-green-400 font-medium">
                        ${withdrawalInfo.finalAmount.toFixed(2)}
                      </span>
                    </div>
                    <div className="text-xs text-zinc-500 mt-2">
                      {withdrawalInfo.description}
                    </div>
                  </div>
                )}
              </div>

              {/* Экспресс режим */}
              <div
                onClick={() => setMode('express')}
                className={clsx(
                  'p-3 rounded-xl border cursor-pointer transition-all',
                  mode === 'express'
                    ? 'border-red-500 bg-red-500/10'
                    : 'border-zinc-600 hover:border-zinc-500'
                )}
              >
                <div className="flex justify-between items-center mb-2">
                  <span className="text-white font-medium">
                    ⚡ {t('withdraw.expressMode')}
                  </span>
                  <span className="text-red-400 text-sm">
                    {poolFeesInfo.express_mode.execute_days} {t('common.day')}
                  </span>
                </div>

                {mode === 'express' && withdrawalInfo && (
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-zinc-400">{t('withdraw.commission')}:</span>
                      <span className="text-red-400">
                        {withdrawalInfo.commission.toFixed(1)}% ($${withdrawalInfo.commissionAmount.toFixed(2)})
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-400">{t('withdraw.toReceive')}:</span>
                      <span className="text-green-400 font-medium">
                        ${withdrawalInfo.finalAmount.toFixed(2)}
                      </span>
                    </div>
                    <div className="text-xs text-zinc-500 mt-2">
                      {withdrawalInfo.description}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Таблица комиссий для справки */}
            {feesData && (
              <div className="bg-zinc-800/50 p-3 rounded-xl">
                <div className="text-xs text-zinc-400 mb-2">
                  📊 {t('withdraw.feesByPeriod')}:
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  {Object.entries(feesData.fee_tiers)
                    .sort(([a], [b]) => parseInt(a) - parseInt(b))
                    .map(([days, fee]) => (
                      <div key={days} className="flex justify-between">
                        <span className="text-zinc-500">
                          {days === '0' ? t('withdraw.immediately') :
                           `${t('withdraw.after')} ${days} ${t('common.days')}`}:
                        </span>
                        <span className={clsx(
                          fee === 0 ? 'text-green-400' :
                          fee <= 0.05 ? 'text-yellow-400' :
                          fee <= 0.10 ? 'text-orange-400' : 'text-red-400'
                        )}>
                          {(fee * 100).toFixed(0)}%
                        </span>
                      </div>
                    ))}
                </div>
              </div>
            )}
          </>
        )}

        <div className="flex justify-between gap-3 pt-2">
          <button
            onClick={() => {
              vibrate()
              onClose()
            }}
            className="flex-1 px-4 py-3 rounded-xl text-sm bg-zinc-700 text-white hover:bg-zinc-600 transition"
          >
            {t('common.cancel')}
          </button>
          <button
            onClick={handleWithdraw}
            disabled={!validAmount || loading || !withdrawalInfo}
            className={clsx(
              'flex-1 px-4 py-3 rounded-xl text-sm text-white transition font-medium',
              validAmount && !loading && withdrawalInfo
                ? mode === 'express'
                  ? 'bg-red-600 hover:bg-red-700'
                  : 'bg-blue-600 hover:bg-blue-700'
                : 'bg-zinc-600 opacity-50 cursor-not-allowed'
            )}
          >
            {loading ? t('common.processing') :
             mode === 'express' ? t('withdraw.expressSubmit') : t('withdraw.standardSubmit')}
          </button>
        </div>
      </motion.div>
    </div>
  )
}