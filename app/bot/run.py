import asyncio
from datetime import datetime, time
import pytz
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.bot import register_handlers
from app.bot.middleware.logger_middleware import MessageLoggerMiddleware
from app.core.config import settings
from app.core.db import Base, SessionLocal, engine
from app.core.logger import logger
from app.models import *  # важно, чтобы в models/__init__.py были все импорты
from app.tasks.update_rates import periodic_rate_updater
from app.tasks.withdraw_monitor import withdraw_monitor_loop
from app.tasks.yield_distributor import distribute_full_yield
from app.tasks.generate_trades import trade_loop
from app.tasks.investment_transfers import process_pending_transfers_loop

# Создаём все таблицы
Base.metadata.create_all(bind=engine)

# Инициализируем бота
bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# Диспетчер
dp = Dispatcher()

# Регистрируем все ваши хендлеры из папки handlers/
register_handlers(dp)


# Middleware
dp.message.middleware(MessageLoggerMiddleware())

# Параметры расписания
msk = pytz.timezone("Europe/Moscow")
YIELD_TIME = time(18, 0)  # 18:00 по МСК
CHECK_INTERVAL = 60  # секунд
DIAGNOSTIC_INTERVAL = 30 * 60  # каждые 30 минут

last_processed_date = None
last_diagnostic = None


async def improved_yield_scheduler():
    """Улучшенный планировщик доходности"""
    global last_processed_date
    logger.info("🎯 Планировщик доходности запущен")

    while True:
        try:
            now_msk = datetime.now(msk)
            today = now_msk.date()
            hour, minute = now_msk.hour, now_msk.minute

            # Проверяем время для публикации (18:00-18:05)
            if (
                    hour == YIELD_TIME.hour and
                    0 <= minute <= 5 and  # 5-минутное окно
                    last_processed_date != today
            ):
                last_processed_date = today
                logger.info(f"[{today}] 🚀 Запуск рутины доходности...")

                try:
                    from app.bot.handlers.yield_report import daily_yield_routine
                    success = await daily_yield_routine(bot)

                    if success:
                        logger.success(f"[{today}] ✅ Рутина доходности выполнена успешно")
                    else:
                        logger.error(f"[{today}] ❌ Ошибка в рутине доходности")

                        # Уведомляем админов об ошибке
                        for admin_id in settings.ADMIN_TG_IDS:
                            try:
                                await bot.send_message(
                                    admin_id,
                                    f"❌ Ошибка рутины доходности за {today}\nПроверьте логи и запустите /yield_routine"
                                )
                            except:
                                pass

                except Exception as e:
                    logger.error(f"[{today}] ❌ Критическая ошибка в планировщике: {e}")

                    # Критическое уведомление админам
                    for admin_id in settings.ADMIN_TG_IDS:
                        try:
                            await bot.send_message(
                                admin_id,
                                f"🚨 Критическая ошибка планировщика доходности!\n\nОшибка: {e}\n\nТребуется ручное вмешательство!"
                            )
                        except:
                            pass

            else:
                logger.debug(
                    f"⏳ Ожидание времени публикации. Сейчас: {hour:02d}:{minute:02d}, "
                    f"обработан: {last_processed_date == today}"
                )

        except Exception as e:
            logger.error(f"❌ Ошибка в планировщике: {e}")

        await asyncio.sleep(CHECK_INTERVAL)


async def diagnostic_scheduler():
    """Периодическая диагностика системы"""
    global last_diagnostic
    logger.info("🔍 Диагностический планировщик запущен")

    while True:
        try:
            now = datetime.utcnow()

            # Запускаем диагностику каждые 30 минут
            if last_diagnostic is None or (now - last_diagnostic).seconds >= DIAGNOSTIC_INTERVAL:
                last_diagnostic = now

                from app.bot.handlers.admin.yield_management import auto_diagnostic_check
                await auto_diagnostic_check(bot)

                logger.debug("🔍 Автодиагностика выполнена")

        except Exception as e:
            logger.error(f"❌ Ошибка в диагностике: {e}")

        await asyncio.sleep(DIAGNOSTIC_INTERVAL)


# Тестовый планировщик (для отладки)
async def test_yield_scheduler():
    """Тестовый планировщик - каждые 2 минуты"""
    logger.warning("🧪 ТЕСТОВЫЙ РЕЖИМ: Генерация доходности каждые 2 минуты")

    while True:
        try:
            now_msk = datetime.now(msk)
            logger.info(f"[{now_msk}] 🧪 ТЕСТ: Запуск рутины доходности...")

            from app.bot.handlers.yield_report import daily_yield_routine
            success = await daily_yield_routine(bot)

            if success:
                logger.success(f"[{now_msk}] 🧪 ТЕСТ: Рутина выполнена успешно")
            else:
                logger.error(f"[{now_msk}] 🧪 ТЕСТ: Ошибка в рутине")

        except Exception as e:
            logger.error(f"🧪 ТЕСТ: Ошибка в планировщике: {e}")

        await asyncio.sleep(120)  # каждые 2 минуты


async def startup_diagnostic():
    """Диагностика при запуске"""
    try:
        logger.info("🔍 Запуск диагностики системы...")

        from app.services.yielding import validate_system_health, get_recent_yields

        # Проверяем здоровье системы
        is_healthy = validate_system_health()

        if is_healthy:
            logger.success("✅ Система доходности работает нормально")
        else:
            logger.warning("⚠️ Обнаружены проблемы с системой доходности")

            # Показываем последние результаты
            recent = get_recent_yields(3)
            for date, pct in recent:
                status = "✅" if 2.0 <= pct <= 5.0 else "⚠️"
                logger.info(f"{status} {date}: {pct}%")

        # Уведомляем админов о запуске
        startup_msg = (
            f"🤖 <b>Бот запущен</b>\n\n"
            f"📊 Система доходности: {'✅ Исправна' if is_healthy else '⚠️ Есть проблемы'}\n"
            f"⏰ Время публикации: 18:00 МСК\n"
            f"🔧 Доступные команды:\n"
            f"• /yield_status - статус системы\n"
            f"• /yield_post - принудительная публикация\n"
            f"• /yield_manual - ручная публикация\n"
            f"• /trade_generate - создать трейд\n"
            f"• /day_stats - статистика дня"
        )

        for admin_id in settings.ADMIN_TG_IDS:
            try:
                await bot.send_message(admin_id, startup_msg, parse_mode="HTML")
            except Exception as e:
                logger.warning(f"Не удалось отправить уведомление админу {admin_id}: {e}")

    except Exception as e:
        logger.error(f"Ошибка стартовой диагностики: {e}")


async def main():
    logger.info("🤖 Запускаем бота и фоновые задачи")

    # Стартовая диагностика
    await startup_diagnostic()

    # Фоновые задачи
    asyncio.create_task(improved_yield_scheduler())  # Основной планировщик
    # asyncio.create_task(test_yield_scheduler())    # Раскомментировать для тестов
    asyncio.create_task(diagnostic_scheduler())  # Диагностика
    asyncio.create_task(withdraw_monitor_loop())  # Мониторинг выводов
    asyncio.create_task(periodic_rate_updater())  # Обновление курсов
    asyncio.create_task(trade_loop())  # Генерация трейдов
    asyncio.create_task(process_pending_transfers_loop())  # Трансферы

    # Старт polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())