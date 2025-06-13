export async function vibrate(type: 'light' | 'medium' | 'heavy' = 'light') {
  try {
    const mod = await import('@twa-dev/sdk');
    const WebApp = mod.default;

    WebApp.HapticFeedback.impactOccurred(type);
  } catch (e) {
    console.warn('vibration failed:', e);
  }
}
