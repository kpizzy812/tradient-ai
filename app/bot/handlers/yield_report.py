# app/bot/handlers/yield_report.py

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
    if percent >= 4.5:
        trend_emoji = "🚀🔥"
    elif percent >= 3.5:
        trend_emoji = "📈✨"
    elif percent >= 2.0:
        trend_emoji = "📊✅"
    elif percent >= 1.0:
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

    media = InputMediaPhoto(media=photo_url, caption=text, parse_mode="HTML")

    return media, keyboard


async def post_daily_yield(bot: Bot, target_date=None):
    """
    Публикует пост о суточной доходности
    """
    db = SessionLocal()
    try:
        if target_date is None:
            # По умолчанию берем вчерашний день
            now_msk = datetime.utcnow() + timedelta(hours=3)
            target_date = (now_msk - timedelta(days=1)).date()

        # Ищем запись о доходности
        record = db.execute(
            select(DailyYield).where(DailyYield.date == target_date)
        ).scalar_one_or_none()

        if not record:
            logger.error(f"[YIELD_POST] ❌ Нет данных о доходности за {target_date}")
            return False

        logger.info(f"[YIELD_POST] 📤 Публикуем доходность за {target_date}: {record.base_yield}%")

        # Форматируем пост
        media, keyboard = format_yield_post(target_date, record.base_yield)

        # Отправляем пост
        msg = await bot.send_photo(
            chat_id=settings.PROJECT_CHAT_ID,
            message_thread_id=settings.DAILY_YIELD_TOPIC_ID,
            photo=media.media,
            caption=media.caption,
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


async def post_manual_yield(bot: Bot, date_str: str, percent: float):
    """
    Ручная публикация доходности (для тестирования или исправлений)
    """
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()

        # Сохраняем в БД если нет
        db = SessionLocal()
        existing = db.execute(
            select(DailyYield).where(DailyYield.date == date)
        ).scalar_one_or_none()

        if not existing:
            record = DailyYield(date=date, base_yield=percent)
            db.add(record)
            db.commit()
            logger.info(f"[YIELD_POST] 💾 Сохранено в БД: {date} = {percent}%")

        db.close()

        # Публикуем
        return await post_daily_yield(bot, date)

    except Exception as e:
        logger.error(f"[YIELD_POST] ❌ Ошибка ручной публикации: {e}")
        return False


async def daily_yield_routine(bot: Bot):
    """
    Основная рутина: генерация доходности + публикация
    """
    from app.services.yielding import generate_and_record_daily_yield, validate_system_health

    try:
        # Проверяем здоровье системы
        if not validate_system_health():
            logger.warning("[YIELD_ROUTINE] ⚠️ Система работает нестабильно")

        # Генерируем и записываем доходность
        yield_pct = generate_and_record_daily_yield()

        if yield_pct is None:
            logger.error("[YIELD_ROUTINE] ❌ Не удалось сгенерировать доходность")
            return False

        # Публикуем пост
        success = await post_daily_yield(bot)

        if success:
            logger.success(f"[YIELD_ROUTINE] ✅ Рутина завершена успешно: {yield_pct}%")
        else:
            logger.error("[YIELD_ROUTINE] ❌ Ошибка при публикации поста")

        return success

    except Exception as e:
        logger.error(f"[YIELD_ROUTINE] ❌ Ошибка в рутине: {e}")
        return False


# Команды для админов
async def admin_check_yield_system(bot: Bot, admin_id: int):
    """Проверка системы для админов"""
    from app.services.yielding import get_recent_yields, validate_system_health

    try:
        # Проверяем здоровье
        is_healthy = validate_system_health()

        # Получаем последние результаты
        recent = get_recent_yields(5)

        status = "✅ Исправно" if is_healthy else "⚠️ Есть проблемы"

        report = f"🔍 <b>Статус системы доходности:</b> {status}\n\n"

        if recent:
            report += "📊 <b>Последние 5 дней:</b>\n"
            for date, pct in recent:
                emoji = "✅" if 2.0 <= pct <= 5.0 else "⚠️"
                report += f"{emoji} {date}: {pct}%\n"

            avg = sum(pct for _, pct in recent) / len(recent)
            report += f"\n📈 <b>Средняя:</b> {avg:.2f}%"
        else:
            report += "❌ <b>Нет данных за последние дни</b>"

        await bot.send_message(admin_id, report, parse_mode=ParseMode.HTML)

    except Exception as e:
        await bot.send_message(admin_id, f"❌ Ошибка проверки: {e}")


async def admin_force_yield_post(bot: Bot, admin_id: int, date_str: str = None, percent: float = None):
    """Принудительная публикация поста админом"""
    try:
        if date_str and percent:
            # Ручная публикация с заданными параметрами
            success = await post_manual_yield(bot, date_str, percent)
        else:
            # Публикация за вчера
            success = await post_daily_yield(bot)

        if success:
            await bot.send_message(admin_id, "✅ Пост опубликован успешно")
        else:
            await bot.send_message(admin_id, "❌ Ошибка публикации поста")

    except Exception as e:
        await bot.send_message(admin_id, f"❌ Ошибка: {e}")