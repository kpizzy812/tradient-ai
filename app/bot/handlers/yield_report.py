# app/bot/handlers/yield_report.py - ОБНОВЛЕННАЯ ВЕРСИЯ
from aiogram import Bot
from aiogram.enums import ParseMode
from app.core.config import settings
from app.models.daily_yield import DailyYield
from sqlalchemy import select
from app.core.db import SessionLocal
from datetime import datetime, timedelta
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from app.core.logger import logger

photo_url = "https://i.ibb.co/mrrB7XWh/Chat-GPT-Image-31-2025-15-35-19.jpg"


def format_yield_post(date: datetime, percent: float):
    """Форматирует пост о доходности"""
    d = date.strftime("%d.%m.%Y")

    # Добавляем эмодзи в зависимости от результата
    target_min, target_max = settings.DAILY_YIELD_RANGE

    if percent >= target_max:
        trend_emoji = "🚀🔥"
    elif percent >= (target_min + target_max) / 2:
        trend_emoji = "📈✨"
    elif percent >= target_min:
        trend_emoji = "📊✅"
    elif percent >= target_min * 0.7:
        trend_emoji = "📉⚡"
    else:
        trend_emoji = "⚠️📊"

    text = (
        f"{trend_emoji} <b>Доходность Tradient AI за {d}</b>\n"
        f"📈 Всего: <b>{percent}%</b>\n\n"
        f"{trend_emoji} <b>Tradient AI Yield for {d}</b>\n"
        f"📈 Total: <b>{percent}%</b>\n\n"
        f"🚀 <b>Launch your AI trading now 👇</b>"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="EARN WITH AI", url="https://t.me/TradientBot?startapp")]
    ])

    return text, keyboard


async def post_daily_yield(bot: Bot, target_date=None):
    """Публикует пост о суточной доходности"""
    db = SessionLocal()
    try:
        if target_date is None:
            # По умолчанию берем сегодняшнюю запись
            target_date = datetime.utcnow().date()

        # Ищем запись о доходности
        record = db.execute(
            select(DailyYield).where(DailyYield.date == target_date)
        ).scalar_one_or_none()

        if not record:
            logger.error(f"[YIELD_POST] ❌ Нет данных о доходности за {target_date}")
            return False

        logger.info(f"[YIELD_POST] 📤 Публикуем доходность за {target_date}: {record.base_yield}%")

        # Форматируем пост
        text, keyboard = format_yield_post(target_date, record.base_yield)

        # Отправляем пост
        msg = await bot.send_photo(
            chat_id=settings.PROJECT_CHAT_ID,
            message_thread_id=settings.DAILY_YIELD_TOPIC_ID,
            photo=photo_url,
            caption=text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )

        # Закрепляем сообщение
        try:
            await bot.pin_chat_message(
                chat_id=settings.PROJECT_CHAT_ID,
                message_id=msg.message_id,
                disable_notification=True
            )
            logger.success(f"[YIELD_POST] 📌 Пост закреплен: {msg.message_id}")
        except Exception as e:
            logger.warning(f"[YIELD_POST] ⚠️ Не удалось закрепить пост: {e}")

        logger.success(f"[YIELD_POST] ✅ Пост опубликован: {record.base_yield}%")
        return True

    except Exception as e:
        logger.error(f"[YIELD_POST] ❌ Ошибка публикации: {e}")
        return False
    finally:
        db.close()


# ====================================

# КРАТКОЕ ОПИСАНИЕ СИСТЕМЫ

"""
УМНАЯ СИСТЕМА ФЕЙК-ТРЕЙДОВ

🎯 ЦЕЛЬ: Гарантированно попадать в диапазон 2-5% к 18:00 МСК

📅 ТОРГОВЫЕ СУТКИ: 18:00 - 18:00 МСК (15:00 - 15:00 UTC)

🤖 КОМПОНЕНТЫ:
1. SmartTradeScheduler - генерирует трейды каждые 30-90 минут
2. YieldFinalizer - в 18:00 финализирует день и публикует пост  
3. YieldScheduler - в 18:00 начисляет прибыль пользователям

🧠 УМНАЯ ЛОГИКА:
- Отслеживает текущую доходность за торговый день
- Рассчитывает сколько нужно добавить/убрать до цели
- Генерирует трейды с нужной доходностью
- Учащает/замедляет генерацию в зависимости от ситуации

⚙️ НАСТРОЙКИ В CONFIG:
- DAILY_YIELD_RANGE: (2.0, 5.0) - целевой диапазон
- TRADE_FREQUENCY_MINUTES: (30, 90) - интервал между трейдами
- CORRECTION_THRESHOLD_HOURS: 2 - за сколько часов начинать коррекцию
- YIELD_TIME_UTC_HOUR: 15 - время финализации (18:00 МСК)

🎮 АДМИН-КОМАНДЫ:
- /trade_now - сгенерировать трейд сейчас
- /trade_stats - статистика торгового дня  
- /yield_finalize - принудительная финализация
- /yield_users - ручное начисление пользователям
- /yield_info - информация о системе начисления

✅ РЕЗУЛЬТАТ: 
Система автоматически попадает в диапазон 2-5% к 18:00,
публикует красивый пост с графиком, начисляет прибыль пользователям.
"""