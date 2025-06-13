'use client'

import React, { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import { useTranslations } from 'next-intl'
import clsx from 'clsx'
import { vibrate } from '@/shared/vibration'
import { PoolInfo } from '@/types/pools'
import { InvestConfirm } from './InvestConfirm'

import { investInPool } from '@/shared/api'
import { useProfile } from '@/shared/hooks/useProfile'
import { toast } from 'react-hot-toast'

interface InvestModalProps {
  onClose: () => void
  onContinue: (amount: number, status: string) => void
  balanceUsd: number
  pool: PoolInfo
}

export const InvestModal: React.FC<InvestModalProps> = ({
  onClose,
  onContinue,
  balanceUsd,
  pool,
}) => {
  const t = useTranslations()
  const [amount, setAmount] = useState('')
  const amountNumber = parseFloat(amount)
  const { userId, mutate } = useProfile()
  const [loading, setLoading] = useState(false)
  const validAmount = !isNaN(amountNumber) && amountNumber >= pool.min_invest
  const [showConfirm, setShowConfirm] = useState(false)
  const [remainder, setRemainder] = useState(0)
  const [held, setHeld] = useState(0)

  const heldAmount = useMemo(() => {
    if (!validAmount) return 0
    return amountNumber > balanceUsd ? balanceUsd : amountNumber
  }, [amountNumber, balanceUsd, validAmount])

  const calcProfit = (days: number) => {
    if (!validAmount) return { min: '0.00', max: '0.00' }
    const [minYield, maxYield] = pool.yield_range
    return {
      min: ((amountNumber * minYield * days) / 100).toFixed(2),
      max: ((amountNumber * maxYield * days) / 100).toFixed(2),
    }
  }

  const handleInvest = async () => {
    vibrate()
    setLoading(true)
    try {
      const res = await investInPool(amountNumber, pool.name, true, userId!)
      // res.status может быть 'reinvested', 'partial_hold' или 'request_required'
      if (res.status === 'reinvested') {
        await mutate()
        onContinue(amountNumber, res.status)
      } else if (res.status === 'partial_hold') {
        setHeld(res.held)
        setRemainder(res.remainder)
        setShowConfirm(true)
      } else if (res.status === 'request_required') {
        setHeld(0)
        setRemainder(res.remainder)
        setShowConfirm(true)
      } else {
        toast.error(t('invest.error'))
      }
    } catch (err: any) {
      // если пришла ошибка 400 с detail
      const message = err.response?.data?.detail || t('invest.error')
      toast.error(message)
    } finally {
      setLoading(false)
    }
  }

  if (showConfirm) {
    return (
      <InvestConfirm
        amount={amountNumber}
        poolName={pool.name}
        remainder={remainder}
        held={held}
        onClose={onClose}
        onContinue={onContinue}
      />
    )
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="w-full max-w-md bg-zinc-900 p-6 rounded-2xl border border-zinc-700 space-y-4"
      >
        <h2 className="text-white text-xl font-bold">
          {t('invest.title')} — {pool.name}
        </h2>

        <div>
          <label className="block text-sm text-zinc-400 mb-1">
            {t('invest.amount')}
          </label>
          <input
            type="text"
            inputMode="decimal"
            pattern="[0-9]*"
            value={amount}
            onChange={e => setAmount(e.target.value.replace(/[^0-9.]/g, ''))}
            placeholder={t('invest.enter_amount')}
            className="w-full px-4 py-2 rounded-xl bg-zinc-800 text-white border border-zinc-600 focus:outline-none appearance-none"
          />
          <p className="text-xs text-zinc-400 mt-1">
            {t('invest.minDeposit')}: ${pool.min_invest}
          </p>
        </div>

        {validAmount && (
          <div className="text-sm text-zinc-300 space-y-1">
            <div>
              {t('invest.your_balance')}: <span className="text-white">${balanceUsd.toFixed(2)}</span>
            </div>
            <div>
              {t('invest.from_balance')}: <span className="text-green-400">${heldAmount.toFixed(2)}</span>
            </div>
            {amountNumber > balanceUsd && (
              <div>
                {t('invest.to_pay')}: <span className="text-red-400">${(amountNumber - balanceUsd).toFixed(2)}</span>
              </div>
            )}
          </div>
        )}

        {validAmount && (
          <div className="bg-zinc-800 p-4 rounded-xl text-sm text-white space-y-1">
            <div>
              {t('invest.profit_day')}: {calcProfit(1).min} – {calcProfit(1).max} USD
            </div>
            <div>
              {t('invest.profit_week')}: {calcProfit(7).min} – {calcProfit(7).max} USD
            </div>
            <div>
              {t('invest.profit_month')}: {calcProfit(30).min} – {calcProfit(30).max} USD
            </div>
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
            onClick={handleInvest}
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
