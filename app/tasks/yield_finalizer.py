# app/tasks/yield_finalizer.py - НОВЫЙ ФАЙЛ
import asyncio
from datetime import datetime, time
import pytz
from app.core.config import settings
from app.core.logger import logger
from app.services.yield_finalization import finalize_daily_yield
from app.bot.handlers.yield_report import post_daily_yield

msk = pytz.timezone("Europe/Moscow")


class YieldFinalizer:
    def __init__(self, bot):
        self.bot = bot
        self.last_processed_date = None

    async def finalization_loop(self):
        """Планировщик финализации и публикации доходности"""
        logger.info("📊 Планировщик финализации доходности запущен")

        while True:
            try:
                now_utc = datetime.utcnow()
                today_utc = now_utc.date()

                # Проверяем время финализации
                if (now_utc.hour == settings.YIELD_TIME_UTC_HOUR and
                        0 <= now_utc.minute <= 5 and  # 5-минутное окно
                        self.last_processed_date != today_utc):

                    self.last_processed_date = today_utc

                    now_msk = now_utc.replace(tzinfo=pytz.UTC).astimezone(msk)
                    logger.info(f"[{now_msk.strftime('%Y-%m-%d %H:%M')} МСК] 🚀 Финализация доходности...")

                    try:
                        # Финализируем доходность
                        yield_pct = finalize_daily_yield()

                        if yield_pct is not None:
                            # Публикуем пост
                            success = await post_daily_yield(self.bot)

                            if success:
                                logger.success(f"✅ Финализация завершена: {yield_pct}%")
                            else:
                                logger.error("❌ Ошибка публикации поста")
                        else:
                            logger.error("❌ Ошибка финализации доходности")

                    except Exception as e:
                        logger.error(f"❌ Ошибка при финализации: {e}")

                        # Уведомляем админов
                        for admin_id in settings.ADMIN_TG_IDS:
                            try:
                                await self.bot.send_message(
                                    admin_id,
                                    f"❌ Ошибка финализации доходности\n\n"
                                    f"Время: {now_msk.strftime('%Y-%m-%d %H:%M')} МСК\n"
                                    f"Ошибка: {e}"
                                )
                            except:
                                pass

                await asyncio.sleep(60)  # Проверяем каждую минуту

            except Exception as e:
                logger.error(f"❌ Ошибка в планировщике финализации: {e}")
                await asyncio.sleep(5 * 60)