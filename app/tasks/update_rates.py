# app/tasks/update_rates.py

from app.core.utils.crypto_rates import fetch_token_price
from loguru import logger
import asyncio
from app.state import set_token_rate, get_token_rate

async def update_all_token_rates():
    await fetch_token_price("TON", "usd")
    await fetch_token_price("TON", "rub")
    await fetch_token_price("TRX", "usd")
    await fetch_token_price("TRX", "rub")
    await fetch_token_price("USDT", "usd")
    await fetch_token_price("USDT", "rub")
    await fetch_token_price("RUB", "usd")
    rub_usd = await get_token_rate("RUB_USD")
    if rub_usd:
        await set_token_rate("USD_RUB", round(1 / rub_usd, 6))

    await set_token_rate("USDT_USD", 1.0)

    logger.info("[RATES] ✅ Курс всех токенов обновлён")

async def periodic_rate_updater():
    while True:
        try:
            await update_all_token_rates()
        except Exception as e:
            logger.warning(f"[RATES] ❌ Ошибка в periodic_rate_updater: {e}")
        await asyncio.sleep(180)  # обновляем раз в 3 минуты
