'use client'

import React, { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import { useTranslations } from 'next-intl'
import clsx from 'clsx'
import { vibrate } from '@/shared/vibration'
import { useProfile } from '@/shared/hooks/useProfile'
import { withdrawFromBalance } from '@/shared/api'
import { toast } from 'react-hot-toast'

interface WithdrawBalanceModalProps {
  balanceUsd: number
  onClose: () => void
  onContinue: (finalAmount: number, executeUntil: string) => void
}

const PAYMENT_METHODS = [
  {
    id: 'USDT_TON',
    name: 'USDT (TON)',
    icon: '💎',
    minAmount: 10,
    description: 'TON blockchain',
    processingTime: '24h'
  },
  {
    id: 'USDT_BEP20',
    name: 'USDT (BEP-20)',
    icon: '🟡',
    minAmount: 10,
    description: 'Binance Smart Chain',
    processingTime: '24h'
  },
  {
    id: 'RUB',
    name: 'RUB',
    icon: '🇷🇺',
    minAmount: 500,
    description: 'Card/SBP',
    processingTime: '24h'
  }
]

export const WithdrawBalanceModal: React.FC<WithdrawBalanceModalProps> = ({
  balanceUsd,
  onClose,
  onContinue,
}) => {
  const t = useTranslations()
  const { userId, mutate } = useProfile()
  const [amount, setAmount] = useState('')
  const [selectedMethod, setSelectedMethod] = useState<string>('')
  const [details, setDetails] = useState('')
  const [loading, setLoading] = useState(false)

  const amountNumber = parseFloat(amount)
  const selectedPaymentMethod = PAYMENT_METHODS.find(m => m.id === selectedMethod)

  const validAmount = !isNaN(amountNumber) &&
                     amountNumber > 0 &&
                     amountNumber <= balanceUsd

  const validMethod = selectedPaymentMethod &&
                     amountNumber >= selectedPaymentMethod.minAmount

  const canSubmit = validAmount && validMethod && details.trim().length > 0

  // Расчет комиссий (пример - в реальности получать с API)
  const withdrawalInfo = useMemo(() => {
    if (!validAmount || !selectedPaymentMethod) return null

    // Комиссия 0% для вывода прибыли (в отличие от депозитов)
    const commission = 0
    const finalAmount = amountNumber

    const executeDate = new Date()
    executeDate.setDate(executeDate.getDate() + 1) // +1 день

    return {
      commission,
      finalAmount,
      executeDate,
      processingTime: selectedPaymentMethod.processingTime,
      description: t('withdraw.balanceDescription')
    }
  }, [validAmount, amountNumber, selectedPaymentMethod, t])

  const handleWithdraw = async () => {
    if (!canSubmit) return

    vibrate()
    setLoading(true)
    try {
      const res = await withdrawFromBalance(
        amountNumber,
        selectedMethod,
        details,
        userId!
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

  return (
    <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="w-full max-w-md bg-zinc-900 p-6 rounded-2xl border border-zinc-700 space-y-4 max-h-[90vh] overflow-y-auto"
      >
        <div className="flex items-center justify-between">
          <h2 className="text-white text-xl font-bold">
            {t('withdraw.profitWithdraw')}
          </h2>
          <div className="text-xs bg-green-600/20 text-green-400 px-2 py-1 rounded-full">
            {t('withdraw.noFee')}
          </div>
        </div>

        {/* Сумма */}
        <div>
          <label className="block text-sm text-zinc-400 mb-1">
            {t('withdraw.amount')}
          </label>
          <input
            type="text"
            inputMode="decimal"
            pattern="[0-9]*"
            value={amount}
            onChange={e => setAmount(e.target.value.replace(/[^0-9.]/g, ''))}
            placeholder={t('withdraw.enterAmount')}
            className="w-full px-4 py-2 rounded-xl bg-zinc-800 text-white border border-zinc-600 focus:outline-none"
          />
          <p className="text-xs text-zinc-400 mt-1">
            {t('withdraw.available')}: ${balanceUsd.toFixed(2)}
          </p>
        </div>

        {/* Способы вывода */}
        {validAmount && (
          <div>
            <label className="block text-sm text-zinc-400 mb-2">
              {t('withdraw.paymentMethod')}
            </label>
            <div className="space-y-2">
              {PAYMENT_METHODS.map(method => (
                <div
                  key={method.id}
                  onClick={() => setSelectedMethod(method.id)}
                  className={clsx(
                    'p-3 rounded-xl border cursor-pointer transition-all',
                    selectedMethod === method.id
                      ? 'border-blue-500 bg-blue-500/10'
                      : 'border-zinc-600 hover:border-zinc-500'
                  )}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-xl">{method.icon}</span>
                      <div>
                        <div className="text-white font-medium">{method.name}</div>
                        <div className="text-xs text-zinc-400">{method.description}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-zinc-400">
                        {t('withdraw.processingTime')}: {method.processingTime}
                      </div>
                      <div className="text-xs text-zinc-500">
                        {t('withdraw.minAmount')}: ${method.minAmount}
                      </div>
                    </div>
                  </div>

                  {selectedMethod === method.id && amountNumber < method.minAmount && (
                    <div className="mt-2 text-xs text-red-400">
                      {t('withdraw.minimumRequired', { amount: method.minAmount })}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Реквизиты */}
        {validMethod && (
          <div>
            <label className="block text-sm text-zinc-400 mb-1">
              {t('withdraw.paymentDetails')}
            </label>
            <textarea
              value={details}
              onChange={e => setDetails(e.target.value)}
              placeholder={t('withdraw.paymentDetailsPlaceholder')}
              className="w-full px-4 py-2 rounded-xl bg-zinc-800 text-white border border-zinc-600 focus:outline-none resize-none"
              rows={3}
            />
            <p className="text-xs text-zinc-500 mt-1">
              {t('withdraw.paymentDetailsHint')}
            </p>
          </div>
        )}

        {/* Информация о выводе */}
        {withdrawalInfo && (
          <div className="bg-zinc-800/50 p-3 rounded-xl space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-zinc-400">{t('withdraw.requestedAmount')}:</span>
              <span className="text-white">${withdrawalInfo.finalAmount.toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-zinc-400">{t('withdraw.commission')}:</span>
              <span className="text-green-400">{t('withdraw.free')}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-zinc-400">{t('withdraw.toReceive')}:</span>
              <span className="text-green-400 font-medium">${withdrawalInfo.finalAmount.toFixed(2)}</span>
            </div>
            <div className="text-xs text-zinc-500 border-t border-zinc-700 pt-2">
              📋 {withdrawalInfo.description}
            </div>
          </div>
        )}

        {/* Важная информация */}
        <div className="bg-blue-600/10 border border-blue-600/20 p-3 rounded-xl">
          <div className="text-blue-400 text-sm font-medium mb-1">
            ℹ️ {t('withdraw.importantInfo')}
          </div>
          <div className="text-xs text-blue-300 space-y-1">
            <p>• {t('withdraw.processingUp24h')}</p>
            <p>• {t('withdraw.workingDaysOnly')}</p>
            <p>• {t('withdraw.supportContact')}</p>
          </div>
        </div>

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
            disabled={!canSubmit || loading}
            className={clsx(
              'flex-1 px-4 py-3 rounded-xl text-sm text-white transition font-medium',
              canSubmit && !loading
                ? 'bg-green-600 hover:bg-green-700'
                : 'bg-zinc-600 opacity-50 cursor-not-allowed'
            )}
          >
            {loading ? t('common.processing') : t('withdraw.createRequest')}
          </button>
        </div>
      </motion.div>
    </div>
  )
}