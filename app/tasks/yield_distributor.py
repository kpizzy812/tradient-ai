from aiogram import Bot
from datetime import date, datetime
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.investments import Investment
from app.models.users import User
from app.models.income_log import IncomeLog
from app.core.config import settings
from app.services.logic import t
from app.core.logger import logger
import random
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def distribute_full_yield(bot: Bot):
    today = date.today()
    db: Session = SessionLocal()

    investments = db.query(Investment).filter(
        Investment.created_at < datetime(today.year, today.month, today.day)
    ).all()

    total_distributed = 0.0
    user_profits = {}

    for inv in investments:
        coeff = settings.POOL_COEFFICIENTS.get(inv.pool_name)
        yield_range = settings.POOL_YIELD_RANGES.get(inv.pool_name)
        if coeff is None or yield_range is None:
            continue

        percent = round(random.uniform(*yield_range) * coeff, 2)

        user = db.query(User).filter(User.id == inv.user_id).first()
        if not user:
            continue

        income = round(inv.amount_usd * percent / 100, 4)

        # 🔔 Подробный учёт для уведомлений
        if user.tg_id not in user_profits:
            user_profits[user.tg_id] = {"lang": user.lang, "total": 0.0, "pools": {}}
        user_profits[user.tg_id]["total"] += income
        user_profits[user.tg_id]["pools"].setdefault(inv.pool_name, {"percent": percent, "income": 0.0})
        user_profits[user.tg_id]["pools"][inv.pool_name]["income"] += income

        # 💸 Автореинвест
        if user.auto_reinvest_flags.get(inv.pool_name):
            inv.amount_usd += income
            inv.reinvested = (inv.reinvested or 0) + income
        else:
            user.profit_usd += income

        db.add(IncomeLog(
            user_id=user.id,
            amount_usd=income,
            pool_name=inv.pool_name,
            date=today
        ))

        total_distributed += income

    db.commit()

    for tg_id, info in user_profits.items():
        lang = info["lang"]
        lines = []
        for pool_name, detail in info["pools"].items():
            percent_str = f"{detail['percent']:.2f}%"
            income_str = f"${detail['income']:.2f}"
            lines.append(f"{pool_name}: {percent_str} ({income_str})")
        pools_text = "\n".join(lines)
        text = t("yield_notify", lang).replace("{amount}", pools_text)
        try:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=t("reinvest_button", lang),
                            callback_data=f"reinvest_start"
                        )
                    ]
                ]
            )

            photo_url = "https://i.ibb.co/mrrB7XWh/Chat-GPT-Image-31-2025-15-35-19.jpg"
            await bot.send_photo(
                tg_id,
                photo=photo_url,
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"❌ Ошибка отправки уведомления {tg_id}: {e}")

    db.close()

    logger.info(f"[{today}] 👥 Пользователей: {len(user_profits)}")
    logger.info(f"[{today}] 💰 Всего начислено: {total_distributed:.2f} $")
