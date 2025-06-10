import asyncio
import random
from app.services.trade_generator import generate_fake_trade
from app.bot.handlers.trades import post_last_trade
from app.bot.instance import bot
from loguru import logger


async def trade_loop():
    while True:
        trade_id = generate_fake_trade()
        if trade_id:
            await post_last_trade(bot)
            logger.info(f"[TRADE] ✅ Сделка #{trade_id} опубликована в Telegram")
        else:
            logger.warning("[TRADE] ❌ Сделка не создана (не подошли условия)")

        # случайная пауза от 20 до 50 минут
        delay_minutes = random.randint(20, 50)
        logger.info(f"[TRADE] ⏳ Следующая попытка через {delay_minutes} мин")
        await asyncio.sleep(delay_minutes * 60)

if __name__ == "__main__":
    asyncio.run(trade_loop())
