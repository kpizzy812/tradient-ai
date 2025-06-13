'use client';

import React, { useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import { toast } from 'react-hot-toast';
import { CopyButton } from '@/components/CopyButton';
import { vibrate } from '@/shared/vibration';
import { useProfile } from '@/shared/hooks/useProfile';
import clsx from 'clsx';

interface ReferralLevel {
  level: number;
  count: number;
  earned: number;
}

interface ReferralStats {
  ref_code: string;
  levels: ReferralLevel[];
  total_earned: number;
}

export default function TeamSection() {
  const t = useTranslations();
  const { userId } = useProfile();

  const [refStats, setRefStats] = useState<ReferralStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!userId) return;
    (async () => {
      try {
        const res = await fetch(`/api/referrals?user_id=${userId}`);
        const data = await res.json();
        setRefStats(data);
      } catch (e) {
        console.error('Failed to load referrals:', e);
      } finally {
        setLoading(false);
      }
    })();
  }, [userId]);

  if (loading || !refStats) return null;

  const botUsername = process.env.NEXT_PUBLIC_BOT_USERNAME || 'TradientBot';
  const referralLink = `https://t.me/${botUsername}?start=${refStats.ref_code}`;

  const handleShare = () => {
    vibrate();
    const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(referralLink)}&text=${encodeURIComponent(t('team.shareText'))}`;
    window.open(shareUrl, '_blank');
  };

  return (
    <div className="space-y-4">
      {/* Ссылка */}
      <div className="rounded-2xl bg-zinc-900 border border-zinc-800 px-4 py-3 shadow-sm space-y-3">
        <div className="text-sm text-zinc-400">{t('team.refLinkLabel')}</div>
        <div className="flex items-center justify-between">
          <div className="text-md break-all text-white mr-2 flex-1">{referralLink}</div>
          <CopyButton
              value={referralLink}
            />

        </div>
        <button
          onClick={handleShare}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white rounded-xl px-4 py-2 text-sm font-medium"
        >
          {t('team.send')}
        </button>
      </div>

      {/* Программа */}
      <div className="rounded-2xl bg-zinc-900 border border-zinc-800 px-4 py-3 shadow-sm space-y-1">
        <h2 className="text-white font-semibold text-base">
          {t('team.title')}
        </h2>
        <p className="text-sm text-zinc-400 leading-snug">
          {t('team.description')}
        </p>

        {refStats.levels && refStats.levels.length > 0 ? (
          refStats.levels.map((lvl) => (
            <div
              key={lvl.level}
              className="flex justify-between text-sm text-white border-t border-zinc-800 pt-2"
            >
              <span className="font-medium">{t('team.levelLine', { level: lvl.level, count: lvl.count })}</span>
              <span className="text-green-400 font-semibold">+${lvl.earned.toFixed(2)}</span>
            </div>
          ))
        ) : (
          <div className="text-sm text-zinc-400 pt-2">{t('team.noRefs')}</div>
        )}

        <div className="border-t border-zinc-800 mt-2 pt-2 flex justify-between text-white font-semibold">
          <span>{t('team.totalEarned')}:</span>
          <span className="text-green-400 font-semibold">${refStats.total_earned.toFixed(2)}</span>
        </div>
      </div>
    </div>
  );
}
