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
from app.models.deposit_request import DepositRequest
from app.models.investments import Investment
from app.models.users import User
from app.models.withdraw_request import WithdrawRequest
from app.models.daily_yield import DailyYield  # если есть такая модель
from app.tasks.generate_trades import trade_loop
from app.services.yielding import generate_and_record_daily_yield
from app.bot.handlers.yield_report import post_daily_yield
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
CHECK_INTERVAL = 30  # секунд

last_processed_date = None

async def yield_scheduler():
    global last_processed_date
    logger.info("🎯 yield_scheduler запущен")

    while True:
        now_msk = datetime.now(msk)
        today = now_msk.date()
        hour, minute = now_msk.hour, now_msk.minute

        if (
            hour == YIELD_TIME.hour and
            minute == YIELD_TIME.minute and
            last_processed_date != today
        ):
            last_processed_date = today

            try:
                logger.info(f"[{today}] ⛏️ Начисляем доход пользователям...")
                await distribute_full_yield(bot)

                logger.info(f"[{today}] 🧮 Сохраняем доходность за сегодня...")
                generate_and_record_daily_yield()

                logger.info(f"[{today}] 📣 Публикуем доходность в Telegram...")
                await post_daily_yield(bot)

                logger.success(f"[{today}] ✅ Пост доходности отправлен")
            except Exception as e:
                logger.error(f"[{today}] ❌ Ошибка в yield_scheduler: {e}")
        else:
            logger.debug(
                f"⏳ Пока не время. Сейчас {hour}:{minute}, уже было: {last_processed_date == today}"
            )

        await asyncio.sleep(CHECK_INTERVAL)


# async def yield_scheduler():
#     while True:
#         try:
#             now_msk = datetime.now(msk)
#             logger.info(f"[{now_msk}] ⏱ ТЕСТОВОЕ начисление дохода...")
#
#             await distribute_full_yield(bot)
#
#             logger.info(f"[{now_msk}] ⏱ Сохраняем доходность за вчера...")
#             generate_and_record_daily_yield()
#
#             logger.info(f"[{now_msk}] ⏱ Публикуем доходность в Telegram...")
#             await post_daily_yield(bot)
#
#             logger.success(f"[{now_msk}] ✅ Пост доходности отправлен")
#         except Exception as e:
#             logger.error(f"[{now_msk}] ❌ Ошибка в тестовом yield_scheduler: {e}")
#
#         await asyncio.sleep(120)  # каждые 2 минуты


async def main():
    logger.info("🤖 Запускаем бота и фоновые задачи")
    # Фоновые задачи
    asyncio.create_task(yield_scheduler())
    asyncio.create_task(withdraw_monitor_loop())
    asyncio.create_task(periodic_rate_updater())
    asyncio.create_task(trade_loop())
    asyncio.create_task(process_pending_transfers_loop())
    # Старт polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
