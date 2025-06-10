# app/bot/handlers/yield_report.py

from aiogram import Bot
from aiogram.enums import ParseMode
from app.core.config import settings
from app.models.daily_yield import DailyYield
from sqlalchemy import select
from app.core.db import SessionLocal
from datetime import datetime, timedelta
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

photo_url = "https://i.ibb.co/mrrB7XWh/Chat-GPT-Image-31-2025-15-35-19.jpg"

def format_yield_post(date: datetime, percent: float):
    d = date.strftime("%d.%m.%Y")

    text = (
        f"📊 <b>Доходность Tradient AI за {d}</b>\n"
        f"📈 Всего: <b>{percent}%</b>\n\n"
        f"📊 <b>Tradient AI Yield for {d}</b>\n"
        f"📈 Total: <b>{percent}%</b>\n\n"
        f"🚀 <b>Launch your AI trading now 👇</b>"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="EARN WITH AI", url="https://t.me/TradientBot?startapp")]
    ])

    media = InputMediaPhoto(media=photo_url, caption=text, parse_mode="HTML")

    return media, keyboard


async def post_daily_yield(bot: Bot) -> object:
    db = SessionLocal()
    try:
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        record = db.execute(select(DailyYield).where(DailyYield.date == yesterday)).scalar_one_or_none()
        if not record:
            return

        media, keyboard = format_yield_post(record.date, record.base_yield)
        msg = await bot.send_photo(
            chat_id=settings.PROJECT_CHAT_ID,
            message_thread_id=settings.DAILY_YIELD_TOPIC_ID,
            photo=media.media,
            caption=media.caption,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
        await bot.pin_chat_message(
            chat_id=settings.PROJECT_CHAT_ID,
            message_id=msg.message_id,
            disable_notification=True
        )
    finally:
        db.close()


from app.services.yielding import generate_and_record_daily_yield

async def daily_yield_routine(bot: Bot):
    generate_and_record_daily_yield()
    await post_daily_yield(bot)
