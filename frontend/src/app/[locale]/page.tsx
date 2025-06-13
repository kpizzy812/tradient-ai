'use client';

import React, { useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import { useStore } from '@/shared/store';
import { fetchProfile, fetchPools, updateAutoReinvest, UserProfile } from '@/shared/api';
import { PoolInfo } from '@/types/pools';
import { PoolCard } from '@/components/PoolCard';
import { HeaderBar } from '@/components/HeaderBar';
import { BalanceCard } from '@/components/BalanceCard';
import { InvestModal } from '@/components/modals/InvestModal';
import { WithdrawModal } from '@/components/modals/WithdrawModal';
import WithdrawModalBal from '@/components/modals/WithdrawModalBal';
import Skeleton from 'react-loading-skeleton';
import { motion, AnimatePresence } from 'framer-motion';
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
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const [showInvestModal, setShowInvestModal] = useState(false);
  const [selectedPool, setSelectedPool] = useState<PoolInfo | null>(null);

  const [showWithdrawModal, setShowWithdrawModal] = useState(false);
  const [withdrawPool, setWithdrawPool] = useState<PoolInfo | null>(null);

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
        setProfile(profileRes);

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
    setWithdrawPool(null);
    setShowWithdrawModal(true);
  };

  const handleWithdrawFromPool = (pool: PoolInfo) => {
    vibrate();
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
    <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #0F172A 0%, #1E293B 100%)' }}>
      <HeaderBar onLanguageSwitch={handleLanguageSwitch} />

      <div className="px-4 pb-8">
        {/* Карточка баланса - показываем только на вкладке pools */}
        <AnimatePresence>
          {activeTab === 'pools' && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <BalanceCard
                profile={profile}
                onWithdraw={handleWithdraw}
                loading={loading}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Панель вкладок */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <TabBar activeTab={activeTab} onTabChange={setActiveTab} />
        </motion.div>

        {/* Контент вкладок */}
        <div className="mt-6">
          <AnimatePresence mode="wait">
            {/* ПУЛЫ */}
            {activeTab === 'pools' && (
              <motion.div
                key="pools"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.3 }}
                className="space-y-4"
              >
                {loading ? (
                  <>
                    <Skeleton height={140} borderRadius={16} baseColor="#1E293B" highlightColor="#334155" />
                    <Skeleton height={140} borderRadius={16} baseColor="#1E293B" highlightColor="#334155" />
                  </>
                ) : (
                  pools.map((pool, index) => (
                    <motion.div
                      key={pool.name}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, delay: index * 0.1 }}
                    >
                      <PoolCard
                        pool={pool}
                        onInvest={handleInvestClick}
                        onWithdraw={handleWithdrawFromPool}
                        onToggleReinvest={handleToggleReinvest}
                      />
                    </motion.div>
                  ))
                )}
              </motion.div>
            )}

            {/* КОМАНДА */}
            {activeTab === 'profile' && (
              <motion.div
                key="profile"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.3 }}
              >
                <TeamSection />
              </motion.div>
            )}

            {/* ИНФО */}
            {activeTab === 'info' && (
              <motion.div
                key="info"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.3 }}
              >
                <InfoSection />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Модальные окна */}
      <AnimatePresence>
        {showWithdrawModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            {withdrawPool ? (
              <WithdrawModal
                pool={withdrawPool}
                onClose={() => setShowWithdrawModal(false)}
                onContinue={handleWithdrawContinue}
              />
            ) : (
              <WithdrawModalBal
                balanceUsd={profile?.profit_usd || 0}
                onClose={() => setShowWithdrawModal(false)}
                onContinue={handleWithdrawContinue}
              />
            )}
          </motion.div>
        )}

        {showInvestModal && selectedPool && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <InvestModal
              pool={selectedPool}
              balanceUsd={profile?.profit_usd || 0}
              onClose={() => setShowInvestModal(false)}
              onContinue={handleInvestContinue}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}