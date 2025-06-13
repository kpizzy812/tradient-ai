'use client'

import React, { useState, useEffect } from 'react'
import useSWR from 'swr'
import { useTranslations } from 'next-intl'
import { motion } from 'framer-motion'
import { toast } from 'react-hot-toast'
import { vibrate } from '@/shared/vibration'
import { useProfile } from '@/shared/hooks/useProfile'
import { CopyButton } from '@/components/CopyButton'

interface InvestConfirmProps {
  amount: number
  poolName: string
  remainder: number
  held: number
  onClose: () => void
  onContinue: (amount: number, status: string) => void
}

export const InvestConfirm: React.FC<InvestConfirmProps> = ({
  amount,
  poolName,
  remainder,
  held,
  onClose,
  onContinue,
}) => {
  const t = useTranslations()
  const { userId, mutate } = useProfile()
  const [method, setMethod] = useState<string | null>(null)
  const [network, setNetwork] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [tokenAmount, setTokenAmount] = useState<number | null>(null)
  const [rates, setRates] = useState<Record<string, number>>({})

  const fetcher = (url: string) => fetch(url).then(res => res.json())
  const { data: paymentDetails } = useSWR<Record<string, string>>(
    '/api/invest/payment_details',
    fetcher
  )
  const { data: fetchedRates } = useSWR<Record<string, number>>(
    '/api/invest/rates',
    fetcher
  )

  const detailKey = method === 'ton'
  ? 'usdt_ton'
  : method === 'usdt'
    ? network!
    : method

  useEffect(() => {
    if (fetchedRates) {
      setRates(fetchedRates)
    }
  }, [fetchedRates])

  useEffect(() => {
    if (!method || !rates) return

    if (method === 'card_ru') {
      const usdtRub = rates['USDT_RUB'] ?? 0
      setTokenAmount(remainder * usdtRub)
      return
    }

    if (method === 'usdt' && network) {
      const rate = rates[`${network.toUpperCase()}_USD`]
      const usdtRub = rates['USDT_RUB'] ?? 0
      if (rate && network.endsWith('rub')) {
        // network = usdt_bep20 или usdt_ton подчас в рублях (если backend отдает usdt_rub)
        setTokenAmount(remainder * usdtRub)
      } else if (rate) {
        setTokenAmount(remainder / rate)
      } else {
        setTokenAmount(null)
      }
      return
    }

    if (method === 'trx' || method === 'ton') {
      const rateUsd = rates[`${method.toUpperCase()}_USD`]
      if (rateUsd) {
        setTokenAmount(remainder / rateUsd)
      } else {
        setTokenAmount(null)
      }
      return
    }
  }, [method, network, rates, remainder])

  const handleSubmit = async () => {
    if (!method || (method === 'usdt' && !network) || !userId) return
    vibrate()
    setLoading(true)
    const currencyKey =
      method === 'usdt'
        ? network!
        : method === 'ton'
        ? 'usdt_ton'  // используем тот же адрес, что USDT (TON)
        : method
    try {
      const res = await fetch('/api/invest/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          pool_name: poolName,
          amount_usd: remainder,
          currency: currencyKey,
          details: paymentDetails?.[currencyKey],
        }),
      })
      const data = await res.json()
      if (data.status === 'request_created') {
        toast.success(t('invest.request_sent'))
        setTokenAmount(data.amount_token)
        await mutate()
        onContinue(amount, data.status)
      } else {
        toast.error('Не удалось создать заявку')
      }
    } catch (e) {
      console.error(e)
      toast.error('Ошибка. Попробуйте позже')
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
          {t('invest.confirm_title')} — {poolName}
        </h2>

        <p className="text-zinc-300 text-sm">
          {t('invest.to_pay')}: <span className="text-white">${remainder.toFixed(2)}</span>
        </p>

        {/* Основные методы оплаты */}
        <div className="space-y-2">
          {/* Карта РФ */}
          {paymentDetails?.card_ru && (
            <button
              onClick={() => { setMethod('card_ru'); setNetwork(null) }}
              className={`w-full px-4 py-2 rounded-2xl text-sm font-medium text-white border shadow-sm transition ${
                method === 'card_ru'
                  ? 'bg-blue-600 border-blue-500'
                  : 'bg-zinc-900 border-zinc-700 hover:bg-zinc-800'
              }`}
            >
              {t('invest.currency.card_ru')}
            </button>
          )}

          {/* TON (берём тот же адрес, что usdt_ton) */}
          {paymentDetails?.usdt_ton && (
            <button
              onClick={() => { setMethod('ton'); setNetwork(null) }}
              className={`w-full px-4 py-2 rounded-2xl text-sm font-medium text-white border shadow-sm transition ${
                method === 'ton'
                  ? 'bg-blue-600 border-blue-500'
                  : 'bg-zinc-900 border-zinc-700 hover:bg-zinc-800'
              }`}
            >
              TON
            </button>
          )}

          {/* USDT (с выбором сети дальше) */}
          <button
            onClick={() => { setMethod('usdt'); setNetwork(null) }}
            className={`w-full px-4 py-2 rounded-2xl text-sm font-medium text-white border shadow-sm transition ${
              method === 'usdt'
                ? 'bg-blue-600 border-blue-500'
                : 'bg-zinc-900 border-zinc-700 hover:bg-zinc-800'
            }`}
          >
            USDT
          </button>

          {/* TRX */}
          {paymentDetails?.trx && (
            <button
              onClick={() => { setMethod('trx'); setNetwork(null) }}
              className={`w-full px-4 py-2 rounded-2xl text-sm font-medium text-white border shadow-sm transition ${
                method === 'trx'
                  ? 'bg-blue-600 border-blue-500'
                  : 'bg-zinc-900 border-zinc-700 hover:bg-zinc-800'
              }`}
            >
              TRX
            </button>
          )}
        </div>


        {/* Подвыбор сети для USDT */}
        {method === 'usdt' && (
          <div className="space-y-2 mt-2">
            <p className="text-zinc-300 text-sm">{t('invest.choose_network')}</p>
            {['usdt_ton', 'usdt_bep20'].map(net => (
              <button
                key={net}
                onClick={() => setNetwork(net)}
                className={`w-full px-4 py-2 rounded-2xl text-sm font-medium text-white border shadow-sm transition ${
                  network === net
                    ? 'bg-blue-600 border-blue-500'
                    : 'bg-zinc-900 border-zinc-700 hover:bg-zinc-800'
                }`}
              >
                {t(`invest.currency.${net}`)}
              </button>
            ))}
          </div>
        )}

        {/* Инструкция по оплате */}
            {detailKey && (
              <div className="bg-zinc-900 p-4 rounded-2xl text-sm text-white space-y-3 border border-zinc-700">
                <div className="flex items-center justify-between">
                  <span>
                    {t('invest.send_exact')}:&nbsp;
                    <b>
                  {tokenAmount !== null
                    ? `${tokenAmount.toFixed(2)} ${
                        method === 'ton'
                          ? t('invest.currency.ton')
                          : t(`invest.currency.${detailKey}`)
                      }`
                    : `${remainder.toFixed(2)} ${
                        method === 'ton'
                          ? t('invest.currency.ton')
                          : t(`invest.currency.${detailKey}`)
                      }`
                  }
                </b>

                  </span>
                  <CopyButton
                    value={tokenAmount !== null ? tokenAmount.toFixed(2) : remainder.toFixed(2)}
                    className="ml-2 p-1"
                    iconSize={16}
                  />
                </div>
                <div className="break-all text-zinc-400 text-xs">
                  {t('invest.send_to')}:
                  <div className="mt-1 flex items-center">
                    <span className="font-mono text-sm text-white mr-2">
                      {paymentDetails?.[detailKey] ?? ''}
                    </span>
                    <CopyButton
                      value={paymentDetails?.[detailKey] ?? ''}
                      className="p-1"
                      iconSize={16}
                    />

                  </div>
                </div>
              </div>
            )}


        <div className="flex justify-between gap-2">
          <button
            onClick={onClose}
            className="w-1/2 px-4 py-2 rounded-xl text-sm bg-zinc-700 text-white"
          >
            {t('common.cancel')}
          </button>
          <button
            onClick={handleSubmit}
            disabled={
              !method || (method === 'usdt' && !network) || loading
            }
            className={`w-1/2 px-4 py-2 rounded-xl text-sm text-white transition ${
              method && (method !== 'usdt' ? true : network) && !loading
                ? 'bg-blue-600 hover:bg-blue-700'
                : 'bg-blue-600 opacity-50 cursor-not-allowed'
            }`}
          >
            {t('common.done')}
          </button>
        </div>
      </motion.div>
    </div>
  )
}
