'use client';

import React, { useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import { useStore } from '@/shared/store';
import { fetchProfile, fetchPools, updateAutoReinvest } from '@/shared/api';
import { PoolInfo } from '@/types/pools';
import { PoolCard } from '@/components/PoolCard';
import { HeaderBar } from '@/components/HeaderBar';
import { InvestModal } from '@/components/modals/InvestModal';
import { WithdrawModal } from '@/components/modals/WithdrawModal';
import WithdrawModalBal from '@/components/modals/WithdrawModalBal';
import Skeleton from 'react-loading-skeleton';
import { motion } from 'framer-motion';
import 'react-loading-skeleton/dist/skeleton.css';
import { useRouter, useParams } from 'next/navigation';
import { vibrate } from '@/shared/vibration';


import { TabBar } from '@/components/TabBar';
import TeamSection from '@/components/TeamSection';
import InfoSection from '@/components/InfoSection';

export default function HubPage() {
  const t = useTranslations();
  const router = useRouter();
  const params = useParams();
  const token = useStore((s) => s.token);

  const [pools, setPools] = useState<PoolInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [userBalanceUsd, setUserBalanceUsd] = useState<number | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const [showInvestModal, setShowInvestModal] = useState(false);
  const [selectedPool, setSelectedPool] = useState<PoolInfo | null>(null);

  const [showWithdrawModal, setShowWithdrawModal] = useState(false);
  const [withdrawPool, setWithdrawPool] = useState<PoolInfo | null>(null);

  // **Новый стейт для вкладок**
  const [activeTab, setActiveTab] = useState<'pools' | 'profile' | 'info'>('pools');

  useEffect(() => {
    if (!token) return;

    (async () => {
      setLoading(true);
      try {
        const mod = await import('@twa-dev/sdk');
        const WebApp = mod.default;
        WebApp.MainButton.hide();

        const tgUserId = WebApp.initDataUnsafe?.user?.id;
        if (!tgUserId) {
          console.warn('Telegram user ID not found');
          return;
        }

        const profileRes = await fetchProfile();
        setUserBalanceUsd(profileRes.profit_usd);

        const poolsRes = await fetchPools(tgUserId);
        setPools(poolsRes);
      } catch (e) {
        console.error('fetch failed:', e);
      } finally {
        setLoading(false);
      }
    })();
  }, [token, refreshTrigger]);

 const handleLanguageSwitch = () => {
  vibrate();
  const current = (params.locale as string) || 'ru';
  const next = current === 'ru' ? 'en' : 'ru';
  router.replace(`/${next}`);
};

  const handleWithdraw = () => {
  vibrate();
  // открываем модалку вывода с баланса
  setWithdrawPool(null);
  setShowWithdrawModal(true);
};

  const handleWithdrawFromPool = (pool: PoolInfo) => {
  vibrate();
  // открываем модалку вывода из выбранного пула
  setWithdrawPool(pool);
  setShowWithdrawModal(true);
};

  const handleWithdrawContinue = (finalAmount: number, executeUntil: string) => {
    setShowWithdrawModal(false);
    setRefreshTrigger((prev) => prev + 1);
    alert(
      `Заявка создана. С учетом комиссии вы получите $${finalAmount.toFixed(
        2
      )}. Ожидается зачисление до ${new Date(executeUntil).toLocaleDateString()}.`
    );
  };

  const handleToggleReinvest = async (pool: PoolInfo, value: boolean) => {
    vibrate();
    setPools((prev) =>
      prev.map((p) => (p.name === pool.name ? { ...p, reinvest: value } : p))
    );

    const tgUserId = (window as any).Telegram?.WebApp?.initDataUnsafe?.user?.id;
    if (!tgUserId) {
      console.warn('❌ Нет Telegram user ID');
      return;
    }

    try {
      await updateAutoReinvest(tgUserId, pool.name, value);
      console.log('✅ Обновлено в БД');
    } catch (e) {
      console.error('❌ Ошибка при обновлении reinvest в БД:', e);
    }
  };

  const handleInvestClick = (pool: PoolInfo) => {
    vibrate();
    setSelectedPool(pool);
    setShowInvestModal(true);
  };

  const handleInvestContinue = (amount: number, status: string) => {
    setShowInvestModal(false);
    if (status === 'reinvested') {
      setRefreshTrigger((prev) => prev + 1);
    } else {
      alert('Заявка создана. Ожидайте зачисления.');
    }
  };

  return (
    <div className="min-h-screen bg-zinc-900 text-white">
      <HeaderBar
        balanceUsd={userBalanceUsd ?? 0}
        onWithdraw={handleWithdraw}
        onLanguageSwitch={handleLanguageSwitch}
      />

      <div className="p-4">
        {/* новая панель вкладок */}
        <TabBar activeTab={activeTab} onTabChange={setActiveTab} />

        <div className="mt-4 space-y-4">
          {/* ПУЛЫ */}
          {activeTab === 'pools' && (
            loading ? (
              <>
                <Skeleton height={120} borderRadius={16} />
                <Skeleton height={120} borderRadius={16} />
              </>
            ) : (
              pools.map((pool) => (
                <motion.div
                  key={pool.name}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  <PoolCard
                    pool={pool}
                    onInvest={handleInvestClick}
                    onWithdraw={handleWithdrawFromPool}
                    onToggleReinvest={handleToggleReinvest}
                  />
                </motion.div>
              ))
            )
          )}

          {/* КОМАНДА */}
          {activeTab === 'profile' && <TeamSection />}

          {/* ИНФО */}
          {activeTab === 'info' && (
              <InfoSection />
            )}

        </div>
      </div>

      {showWithdrawModal && (
          withdrawPool ? (
            // вывод из пула
            <WithdrawModal
              pool={withdrawPool}
              onClose={() => setShowWithdrawModal(false)}
              onContinue={handleWithdrawContinue}
            />
          ) : (
            // вывод с общего баланса
            <WithdrawModalBal
              balanceUsd={userBalanceUsd!}
              onClose={() => setShowWithdrawModal(false)}
              onContinue={handleWithdrawContinue}
            />
          )
        )}

      {showInvestModal && selectedPool && (
        <InvestModal
          pool={selectedPool}
          balanceUsd={userBalanceUsd ?? 0}
          onClose={() => setShowInvestModal(false)}
          onContinue={handleInvestContinue}
        />
      )}
    </div>
  );
}
