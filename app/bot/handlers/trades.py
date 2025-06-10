from aiogram import Bot
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from app.core.config import settings
from app.models.trades import Trade
from app.core.db import SessionLocal

async def post_last_trade(bot: Bot):
    db = SessionLocal()
    try:
        trade = db.query(Trade).order_by(Trade.id.desc()).first()
        if not trade:
            return

        exchange_icon = {
            "Binance": "🟡",
            "Bybit": "🟠",
            "OKX": "⚫️"
        }.get(trade.exchange, "💹")

        duration = trade.exit_time - trade.entry_time
        hours, minutes = divmod(duration.seconds // 60, 60)

        text = (
            f"📈 <b>Tradient AI Trade #{trade.id}</b>\n"
            f"{exchange_icon} <b>Биржа:</b> {trade.exchange}\n"
            f"🧮 <b>Пара:</b> {trade.ticker}\n"
            f"🔁 <b>Тип:</b> {trade.direction}\n"
            f"⏱ <b>Длительность:</b> {hours}ч {minutes}м\n\n"
            f"💎 <b>Вход:</b> {round(trade.entry_price, 2)}  |  🔸 <b>Выход:</b> {round(trade.exit_price, 2)}\n"
            f"💰 <b>Прибыль:</b> {'+' if trade.result_pct >= 0 else ''}{round(trade.result_pct, 2)}%"
        )

        photo = FSInputFile(trade.chart_path)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Запустить AI Бот", url="https://t.me/TradientBot?startapp")]
        ])

        await bot.send_photo(
            chat_id=settings.PROJECT_CHAT_ID,
            message_thread_id=settings.TRADE_TOPIC_ID,
            photo=photo,
            caption=text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    finally:
        db.close()
