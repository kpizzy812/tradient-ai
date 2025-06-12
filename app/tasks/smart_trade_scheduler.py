# app/tasks/smart_trade_scheduler.py - НОВЫЙ ФАЙЛ
import asyncio
from datetime import datetime
from app.services.smart_trade_generator import generate_smart_trade, get_current_day_stats, calculate_next_trade_delay
from app.bot.handlers.trades import post_last_trade
from app.core.logger import logger


class SmartTradeScheduler:
    def __init__(self, bot):
        self.bot = bot
        self.last_trade_time = None

    async def trade_generator_loop(self):
        """Основной цикл генерации трейдов"""
        logger.info("🤖 Умный генератор трейдов запущен")

        while True:
            try:
                # Получаем статистику
                stats = get_current_day_stats()

                if not stats['is_active']:
                    logger.debug("[TRADE_SCHEDULER] Торговый день неактивен, ждем...")
                    await asyncio.sleep(10 * 60)  # 10 минут
                    continue

                # Генерируем трейд
                trade_id = generate_smart_trade()

                if trade_id:
                    # Публикуем трейд
                    try:
                        await post_last_trade(self.bot)
                        logger.info(f"[TRADE_SCHEDULER] Трейд #{trade_id} опубликован")
                        self.last_trade_time = datetime.utcnow()
                    except Exception as e:
                        logger.error(f"[TRADE_SCHEDULER] Ошибка публикации: {e}")

                # Рассчитываем задержку до следующего трейда
                delay = calculate_next_trade_delay(stats)

                if delay is None:
                    logger.info("[TRADE_SCHEDULER] Торговый день завершен")
                    await asyncio.sleep(30 * 60)  # 30 минут
                    continue

                logger.info(f"[TRADE_SCHEDULER] Следующий трейд через {delay // 60} минут")
                await asyncio.sleep(delay)

            except Exception as e:
                logger.error(f"[TRADE_SCHEDULER] Ошибка в цикле: {e}")
                await asyncio.sleep(5 * 60)  # 5 минут при ошибке