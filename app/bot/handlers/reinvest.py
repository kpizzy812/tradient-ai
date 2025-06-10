from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from app.core.config import settings
from app.models import User, Investment
from app.core.db import SessionLocal
from app.services.logic import t

router = Router()

@router.callback_query(F.data == "reinvest_start")
async def handle_reinvest_start(callback: CallbackQuery, bot: Bot):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.tg_id == callback.from_user.id).first()
        if not user or user.profit_usd < 0.01:
            await callback.answer("Недостаточно средств", show_alert=True)
            return

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=pool, callback_data=f"reinvest_{pool}")]
            for pool in settings.POOL_COEFFICIENTS.keys()
        ])
        await callback.message.answer(
            t("reinvest_select_pool", user.lang),
            reply_markup=keyboard
        )
        await callback.answer()
    finally:
        db.close()

@router.callback_query(F.data.startswith("reinvest_"))
async def handle_reinvest_pool(callback: CallbackQuery, bot: Bot):
    db = SessionLocal()
    try:
        pool = callback.data.split("_", 1)[1]
        user = db.query(User).filter(User.tg_id == callback.from_user.id).first()
        if not user or user.profit_usd < 0.01:
            await callback.answer("Недостаточно средств", show_alert=True)
            return

        investment = db.query(Investment).filter_by(user_id=user.id, pool_name=pool).first()
        if investment:
            investment.amount_usd += user.profit_usd
        else:
            investment = Investment(
                user_id=user.id,
                amount_usd=user.profit_usd,
                pool_name=pool
            )
            db.add(investment)

        reinvested = round(user.profit_usd, 2)
        user.deposit_usd += user.profit_usd
        user.profit_usd = 0.0
        db.commit()

        await callback.message.delete()  # 🧹 удаляем сообщение с кнопками

        await callback.message.answer(
            t("reinvest_success", user.lang).replace("{amount}", f"{reinvested:.2f}").replace("{pool_name}", pool)
        )
        await callback.answer()
    finally:
        db.close()
