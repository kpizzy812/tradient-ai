# app/bot/run.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.bot import register_handlers
from app.bot.middleware.logger_middleware import MessageLoggerMiddleware
from app.core.config import settings
from app.core.db import Base, SessionLocal, engine
from app.core.logger import logger
from app.models import *

# Импорты для задач
from app.tasks.yield_scheduler import YieldScheduler
from app.tasks.smart_trade_scheduler import SmartTradeScheduler
from app.tasks.yield_finalizer import YieldFinalizer
from app.tasks.update_rates import periodic_rate_updater
from app.tasks.withdraw_monitor import withdraw_monitor_loop
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

# Регистрируем хендлеры
register_handlers(dp)

# Middleware
dp.message.middleware(MessageLoggerMiddleware())


async def main():
    logger.info("🤖 Запускаем бота и фоновые задачи")

    # Создаем планировщики
    yield_scheduler = YieldScheduler(bot)  # Начисление пользователям
    trade_scheduler = SmartTradeScheduler(bot)  # Генерация трейдов
    yield_finalizer = YieldFinalizer(bot)  # Финализация и публикация

    # Фоновые задачи
    asyncio.create_task(yield_scheduler.yield_scheduler_loop())  # Начисление в 18:00
    asyncio.create_task(trade_scheduler.trade_generator_loop())  # Умная генерация трейдов
    asyncio.create_task(yield_finalizer.finalization_loop())  # Финализация в 18:00
    asyncio.create_task(withdraw_monitor_loop())  # Мониторинг выводов
    asyncio.create_task(periodic_rate_updater())  # Обновление курсов
    asyncio.create_task(process_pending_transfers_loop())  # Трансферы

    logger.success("🚀 Все системы запущены")

    # Старт polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())