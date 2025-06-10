from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from app.models.withdraw_request import WithdrawRequest
from app.models.users import User
from app.services.logic import t
from app.core.db import SessionLocal

router = Router()


@router.callback_query(F.data.startswith("withdraw_approve_"))
async def callback_withdraw_approve(call: CallbackQuery, bot: Bot):
    request_id = int(call.data.split("_")[-1])
    db = SessionLocal()
    try:
        req = db.query(WithdrawRequest).filter_by(id=request_id, status="pending").first()
        if not req:
            return await call.answer("❌ Заявка не найдена или уже обработана", show_alert=True)

        req.status = "executed"  # статус завершён, как и у автообработки

        # Зачисляем на баланс, если метод INTERNAL
        user = db.query(User).get(req.user_id)
        if user:
            if req.source == "investment":
                user.profit_usd += req.final_amount_usd
            elif req.method == "INTERNAL":
                user.profit_usd += req.final_amount_usd

        db.commit()

        user = db.query(User).get(req.user_id)
        if user:
            try:
                await bot.send_message(user.tg_id, t("withdraw_approved", user.lang))
            except:
                pass

        await call.answer("✅ Заявка одобрена")
    finally:
        db.close()


@router.callback_query(F.data.startswith("withdraw_decline_"))
async def callback_withdraw_decline(call: CallbackQuery, bot: Bot):
    request_id = int(call.data.split("_")[-1])
    db = SessionLocal()
    try:
        req = db.query(WithdrawRequest).filter_by(id=request_id, status="pending").first()
        if not req:
            return await call.answer("❌ Заявка не найдена или уже обработана", show_alert=True)

        req.status = "declined"
        user = db.query(User).get(req.user_id)
        if user:
            if req.source == "balance":
                user.profit_usd += req.amount_usd

            elif req.source == "investment":
                from app.models.investments import Investment
                inv = Investment(
                    user_id=user.id,
                    pool_name=req.pool_name,
                    amount_usd=req.amount_usd,
                    is_active=True
                )
                db.add(inv)

        db.commit()

        if user:
            try:
                await bot.send_message(user.tg_id, t("withdraw_declined", user.lang))
            except:
                pass

        await call.answer("🚫 Заявка отклонена")
    finally:
        db.close()


