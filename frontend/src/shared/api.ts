import axios from 'axios';
import { PoolInfo } from '@/types/pools';

export const instance = axios.create({
  baseURL: '/api',
  withCredentials: false,
});

// токен устанавливается отдельно
export function setAuthToken(token: string | null) {
  if (token) {
    instance.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete instance.defaults.headers.common['Authorization'];
  }
}

export const fetchPools = async (userId: number): Promise<PoolInfo[]> => {
  const res = await instance.get('/pools/info', {
    params: { user_id: userId },
  });
  return res.data.pools;
};

export interface UserProfile {
  user_id: number;
  username: string;
  lang: string;
  deposit_usd:   number;
  withdraw_usd:  number;
  profit_usd:    number;
  hold_balance:  number;
  auto_reinvest_flags: Record<string, boolean>;
  ref_code:      string;
  ref_link:      string;
  total_earned_usd: number;
}


export const fetchProfile = async (): Promise<UserProfile> => {
  const res = await instance.get('/user/profile');
  return res.data;
};


export const updateAutoReinvest = async (userId: number, poolName: string, value: boolean) => {
  return instance.post('/reinvest/settings', {
    user_id: userId,
    pool_name: poolName,
    enabled: value,
  });
};

export const investInPool = async (
  amount: number,
  poolName: string,
  useBalance: boolean,
  userId: number
) => {
  const res = await axios.post('/api/invest', {
    amount,
    pool_name: poolName,
    use_balance: useBalance,
    user_id: userId,
  })
  return res.data
}
export const withdrawFromPool = async (
  amount: number,
  poolName: string,
  mode: 'basic' | 'express',
  method: string,
  userId: number,
  daysSinceDeposit: number
) => {
  // Здесь инициализируем запрос и ждём ответ
  const res = await instance.post('/withdraw', {
    user_id: userId,
    source: 'investment',
    amount,
    method,
    mode,
    pool_name: poolName,
    details: poolName,
    days_since_deposit: daysSinceDeposit,
  });

  // Возвращаем именно тело ответа
  return res.data;
};


export interface WithdrawRequestInput {
  user_id: number;
  amount: number;
  source: 'balance' | 'investment';
  pool_name?: string;
  method: string;
  details: string;
  mode?: 'base' | 'express';
  days_since_deposit?: number;
}

export interface WithdrawRequestResponse {
  final_amount: number;
  execute_until: string;
  status: string;
  request_id: number;
}

export async function createWithdrawRequest(
  payload: WithdrawRequestInput
): Promise<WithdrawRequestResponse> {
  const res = await fetch('/api/withdraw', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error((await res.json()).detail || 'Withdraw error');
  return res.json();
}

export default instance;


