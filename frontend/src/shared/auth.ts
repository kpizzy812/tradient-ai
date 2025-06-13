import api, { fetchProfile, setAuthToken } from './api';
import { useStore } from './store';

export async function loginFromTelegram() {
  try {
    const mod = await import('@twa-dev/sdk');
    const WebApp = mod.default;
    const initData = WebApp.initData ?? WebApp.initDataUnsafe;

    if (!initData) {
      console.warn('Telegram initData missing');
      return;
    }

    const res = await api.post(
      '/auth/login',
      null,
      { headers: { Authorization: `tma ${initData}` } }
    );

    const { access_token } = res.data;
    const store = useStore.getState();

    // ⬇️ ОТЛАДКА: выводим токен и заголовок
    console.log('✅ access_token:', access_token);
    store.setToken(access_token);
    setAuthToken(access_token);
    console.log('✅ axios headers after auth:', api.defaults.headers.common['Authorization']);

    // ⬇️ делаем запрос к профилю
    const profile = await fetchProfile();
    console.log('📦 profile response:', profile);
    store.setProfitUsd(profile.profit_usd);

  } catch (err: any) {
    console.warn(
      'Telegram login failed:',
      err.response?.status,
      err.response?.data || err.message
    );
  }
}
