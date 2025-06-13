from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from app.models.deposit_request import DepositRequest
from app.services.logic import invest_user, t
from app.core.db import SessionLocal
from app.models.users import User

router = Router()


@router.callback_query(F.data.startswith("approve_"))
async def callback_approve(call: CallbackQuery, bot: Bot):
    request_id = int(call.data.split("_")[1])
    db = SessionLocal()
    try:
        req = db.query(DepositRequest).get(request_id)
        if not req or req.status != "pending":
            return await call.answer("⛔️ Заявка недействительна или уже обработана", show_alert=True)

        user = db.query(User).get(req.user_id)
        if not user:
            return await call.answer("❌ Пользователь не найден")

        if user.hold_balance > 0:
            total = req.amount_usd + user.hold_balance
            success = invest_user(db, user, total, req.pool_name, bot)
            user.hold_balance = 0.0
        else:
            success = invest_user(db, user, req.amount_usd, req.pool_name, bot)

        if success:
            req.status = "approved"
            db.commit()

            # Обновляем сообщение без кнопок
            updated_text = call.message.text + f"\n\n✅ <b>ОДОБРЕНО</b> администратором @{call.from_user.username or call.from_user.id}"
            await call.message.edit_text(updated_text, parse_mode="HTML")
            await call.answer("✅ Заявка одобрена")

            try:
                await bot.send_message(user.tg_id, t("deposit_approved", user.lang))
            except:
                pass
        else:
            db.rollback()
            await call.answer("❌ Ошибка при обработке")
    finally:
        db.close()


@router.callback_query(F.data.startswith("decline_"))
async def callback_decline(call: CallbackQuery, bot: Bot):
    request_id = int(call.data.split("_")[1])
    db = SessionLocal()
    try:
        req = db.query(DepositRequest).get(request_id)
        if not req or req.status != "pending":
            return await call.answer("⛔️ Уже обработано", show_alert=True)

        req.status = "declined"
        db.commit()

        user = db.query(User).get(req.user_id)
        if user and user.hold_balance > 0:
            user.profit_usd += user.hold_balance
            user.hold_balance = 0.0
            db.commit()

        # Обновляем сообщение без кнопок
        updated_text = call.message.text + f"\n\n❌ <b>ОТКЛОНЕНО</b> администратором @{call.from_user.username or call.from_user.id}"
        await call.message.edit_text(updated_text, parse_mode="HTML")
        await call.answer("🚫 Заявка отклонена")

        try:
            await bot.send_message(user.tg_id, t("deposit_declined", user.lang))
        except:
            pass

    finally:
        db.close()


@router.callback_query(F.data.startswith("delete_"))
async def callback_delete(call: CallbackQuery):
    request_id = int(call.data.split("_")[1])
    db = SessionLocal()
    try:
        req = db.query(DepositRequest).get(request_id)
        if not req:
            return await call.answer("❌ Не найдено", show_alert=True)
        req.status = "deleted"
        db.commit()

        # Обновляем сообщение без кнопок
        updated_text = call.message.text + f"\n\n🗑 <b>УДАЛЕНО</b> администратором @{call.from_user.username or call.from_user.id}"
        await call.message.edit_text(updated_text, parse_mode="HTML")
        await call.answer("🗑 Заявка удалена")
    finally:
        db.close()