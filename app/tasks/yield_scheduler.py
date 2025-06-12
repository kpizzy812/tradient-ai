import asyncio
from datetime import datetime, time
import pytz
from app.core.config import settings
from app.core.logger import logger
from app.tasks.yield_distributor import distribute_full_yield

msk = pytz.timezone("Europe/Moscow")


class YieldScheduler:
    def __init__(self, bot):
        self.bot = bot
        self.last_processed_date = None

    async def yield_scheduler_loop(self):
        """Планировщик начисления доходности пользователям"""
        logger.info("💰 Планировщик начисления доходности запущен")

        while True:
            try:
                # Получаем текущее время в UTC
                now_utc = datetime.utcnow()
                today_utc = now_utc.date()

                # Проверяем время для начисления (по UTC)
                if (now_utc.hour == settings.YIELD_TIME_UTC_HOUR and
                        0 <= now_utc.minute <= 5 and  # 5-минутное окно
                        self.last_processed_date != today_utc):

                    self.last_processed_date = today_utc

                    # Конвертируем в МСК для логов
                    now_msk = now_utc.replace(tzinfo=pytz.UTC).astimezone(msk)
                    logger.info(f"[{now_msk.strftime('%Y-%m-%d %H:%M')} МСК] 🚀 Запуск начисления доходности...")

                    try:
                        # Запускаем начисление
                        await distribute_full_yield(self.bot)
                        logger.success(f"✅ Начисление доходности завершено успешно")

                    except Exception as e:
                        logger.error(f"❌ Ошибка при начислении доходности: {e}")

                        # Уведомляем админов об ошибке
                        for admin_id in settings.ADMIN_TG_IDS:
                            try:
                                await self.bot.send_message(
                                    admin_id,
                                    f"❌ Ошибка начисления доходности\n\n"
                                    f"Время: {now_msk.strftime('%Y-%m-%d %H:%M')} МСК\n"
                                    f"Ошибка: {e}\n\n"
                                    f"Используйте /yield_users для ручного запуска"
                                )
                            except:
                                pass

                else:
                    # Логируем каждые 30 минут для контроля
                    if now_utc.minute in [0, 30]:
                        now_msk = now_utc.replace(tzinfo=pytz.UTC).astimezone(msk)
                        logger.debug(f"⏳ Ожидание времени начисления. Сейчас: {now_msk.strftime('%H:%M')} МСК")

                await asyncio.sleep(60)  # Проверяем каждую минуту

            except Exception as e:
                logger.error(f"❌ Ошибка в планировщике начисления: {e}")
                await asyncio.sleep(5 * 60)  # 5 минут при ошибке