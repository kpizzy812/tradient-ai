'use client';
import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { useTranslations, useLocale } from 'next-intl';
import clsx from 'clsx';
import { vibrate } from '@/shared/vibration';
import { PoolInfo } from '@/types/pools';
import { useProfile } from '@/shared/hooks/useProfile';
import { createWithdrawRequest } from '@/shared/api';
import { toast } from 'react-hot-toast';

interface WithdrawModalProps {
  onClose: () => void;
  onContinue: (finalAmount: number, executeUntil: string) => void;
  balanceUsd: number;
  pool?: PoolInfo;
}

export const WithdrawModalBal: React.FC<WithdrawModalProps> = ({ onClose, onContinue, balanceUsd, pool }) => {
  const tWithdraw = useTranslations('withdraw');
  const tCommon   = useTranslations('common');

  const locale    = useLocale();
  const { userId, mutate } = useProfile();

  const [step, setStep] = useState(1);
  const [amount, setAmount] = useState('');
  const amountNumber = parseFloat(amount);
  const validAmount = !isNaN(amountNumber)
    && amountNumber > 0
    && (pool ? amountNumber <= (pool.user_balance || 0) : amountNumber <= balanceUsd);

  const currencyOptions = useMemo(() => {
    const base = [
      { key: 'ton',  label: 'TON' },
      { key: 'usdt', label: 'USDT (TON)' },
      { key: 'trx',  label: 'TRX' },
    ];
    if (locale === 'ru') base.unshift({ key: 'card', label: tWithdraw('card') });
    return base;
  }, [locale, tWithdraw]);

  const [currency, setCurrency] = useState(currencyOptions[0].key);
  const [address, setAddress]   = useState('');
  const validAddress = address.trim().length > 0;

  const handleNext = () => { vibrate(); setStep(s => s + 1); };
  const handleBack = () => { vibrate(); setStep(s => s - 1); };

  const handleSubmit = async () => {
    vibrate();
    try {
      const input = {
        user_id: userId!,
        amount: amountNumber,
        source: 'balance' as const,
        method: currency,
        details: address,
      };
      const res = await createWithdrawRequest(input);
      await mutate();
      onContinue(res.final_amount, res.execute_until);
      onClose();
    } catch (err: any) {
      toast.error(err.message || tWithdraw('error'));
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
      <motion.div
        initial={{ scale: .95, opacity: 0 }}
        animate={{ scale: 1,   opacity: 1 }}
        className="w-full max-w-md bg-zinc-900 p-6 rounded-2xl border border-zinc-700 space-y-4"
      >
        <h2 className="text-white text-xl font-bold">
          {tWithdraw('title')} {pool ? `— ${pool.name}` : ''}
        </h2>

        {step === 1 && (
          <>
            <div>
              <label className="block text-sm text-zinc-400 mb-1">
                {tWithdraw('amount')}
              </label>
              <input
                type="text"
                inputMode="decimal"
                pattern="[0-9]*"
                value={amount}
                onChange={e => setAmount(e.target.value.replace(/[^0-9.]/g, ''))}
                placeholder={tWithdraw('enter_amount')}
                className="w-full px-4 py-2 rounded-xl bg-zinc-800 text-white border border-zinc-600 focus:outline-none"
              />
              <p className="text-xs text-zinc-400 mt-1">
                {tWithdraw('balance')}: ${ (pool ? pool.user_balance : balanceUsd).toFixed(2) }
              </p>
            </div>
            <div className="flex justify-between gap-2">
              <button
                onClick={onClose}
                className="w-1/2 px-4 py-2 rounded-xl text-sm bg-zinc-700 text-white"
              >
                {tCommon('cancel')}
              </button>
              <button
                onClick={handleNext}
                disabled={!validAmount}
                className={clsx(
                  'w-1/2 px-4 py-2 rounded-xl text-sm text-white transition',
                  validAmount
                    ? 'bg-blue-600 hover:bg-blue-700'
                    : 'bg-blue-600 opacity-50 cursor-not-allowed'
                )}
              >
                {tCommon('next')}
              </button>
            </div>
          </>
        )}

        {step === 2 && (
          <>
            <div>
              <p className="text-sm text-zinc-400 mb-2">
                {tWithdraw('choose_currency')}
              </p>
              <div className="grid grid-cols-2 gap-2">
                {currencyOptions.map(opt => (
                  <button
                    key={opt.key}
                    onClick={() => { vibrate(); setCurrency(opt.key); }}
                    className={clsx(
                      'py-2 rounded-xl text-sm transition',
                      currency === opt.key
                        ? 'bg-blue-600 text-white'
                        : 'bg-zinc-800 text-zinc-400'
                    )}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex justify-between gap-2">
              <button
                onClick={handleBack}
                className="w-1/2 px-4 py-2 rounded-xl text-sm bg-zinc-700 text-white"
              >
                {tCommon('back')}
              </button>
              <button
                onClick={handleNext}
                className="w-1/2 px-4 py-2 rounded-xl text-sm bg-blue-600 text-white hover:bg-blue-700"
              >
                {tCommon('next')}
              </button>
            </div>
          </>
        )}

        {step === 3 && (
          <>
            <div>
              <label className="block text-sm text-zinc-400 mb-1">
                {tWithdraw('address')}
              </label>
              <input
                type="text"
                value={address}
                onChange={e => setAddress(e.target.value)}
                placeholder={tWithdraw('enter_address')}
                className="w-full px-4 py-2 rounded-xl bg-zinc-800 text-white border border-zinc-600 focus:outline-none"
              />
            </div>
            <div className="flex justify-between gap-2">
              <button
                onClick={handleBack}
                className="w-1/2 px-4 py-2 rounded-xl text-sm bg-zinc-700 text-white"
              >
                {tCommon('back')}
              </button>
              <button
                onClick={handleSubmit}
                disabled={!validAddress}
                className={clsx(
                  'w-1/2 px-4 py-2 rounded-xl text-sm text-white transition',
                  validAddress
                    ? 'bg-blue-600 hover:bg-blue-700'
                    : 'bg-blue-600 opacity-50 cursor-not-allowed'
                )}
              >
                {tCommon('continue')}
              </button>
            </div>
          </>
        )}
      </motion.div>
    </div>
  );
};

export default WithdrawModalBal;
