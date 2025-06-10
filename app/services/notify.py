from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.core.config import settings
from app.core.db import SessionLocal
from app.models.users import User as UserModel
from app.models.withdraw_request import WithdrawRequest

async def notify_admins_new_request(bot: Bot, request, user: UserModel):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"approve_{request.id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"decline_{request.id}"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_{request.id}")
        ]
    ])

    user_line = f"👤 <b>Пользователь:</b> "
    user_line += f"@{user.username} ({user.tg_id})" if user.username else f"ID {user.tg_id}"

    ref_line = "🔗 <b>Пригласитель:</b> —"
    if user.referrer_id:
        db = SessionLocal()
        ref = db.query(UserModel).filter(UserModel.id == user.referrer_id).first()
        db.close()
        if ref:
            ref_line = f"🔗 <b>Пригласитель:</b> "
            ref_line += f"@{ref.username} ({ref.tg_id})" if ref.username else f"ID {ref.tg_id}"

    currency_line = f"💱 <b>Валюта:</b> {request.currency}\n" if hasattr(request, "currency") and request.currency else ""
    details_line = f"📋 <b>Детали:</b> <code>{request.details}</code>\n" if hasattr(request, "details") and request.details else ""

    for admin_id in settings.ADMIN_TG_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=(
                    f"💰 <b>Новая заявка на пополнение</b>\n\n"
                    f"{user_line}\n"
                    f"{ref_line}\n"
                    f"💵 <b>Сумма:</b> {request.amount_usd} $\n"
                    f"📦 <b>Пул:</b> {request.pool_name}\n"
                    f"💳 <b>Метод:</b> {request.method}\n"
                    f"{currency_line}"
                    f"{details_line}"
                    f"🕒 <i>{request.created_at.strftime('%Y-%m-%d %H:%M')}</i>"
                ),
                reply_markup=kb,
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"⚠️ Не удалось отправить сообщение админу {admin_id}: {e}")

async def notify_admins_withdraw_request(bot: Bot, request: WithdrawRequest, user: UserModel):

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"withdraw_approve_{request.id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"withdraw_decline_{request.id}"),
        ]
    ])

    user_line = f"👤 <b>Пользователь:</b> "
    user_line += f"@{user.username} ({user.tg_id})" if user.username else f"ID {user.tg_id}"

    ref_line = "🔗 <b>Пригласитель:</b> —"
    if user.referrer_id:
        db = SessionLocal()
        ref = db.query(UserModel).filter(UserModel.id == user.referrer_id).first()
        db.close()
        if ref:
            ref_line = f"🔗 <b>Пригласитель:</b> "
            ref_line += f"@{ref.username} ({ref.tg_id})" if ref.username else f"ID {ref.tg_id}"

    mode_line = ""
    if request.source == "investment":
        mode_line = f"🏷️ <b>Режим:</b> {'Экспресс' if request.mode == 'express' else 'Базовый'}\n"

    method_line = f"💳 <b>Метод:</b> {request.method}\n"
    currency_line = f"💱 <b>Валюта:</b> {request.currency}\n" if request.currency else ""
    deadline_line = f"⏳ <b>Выполнить до:</b> {request.execute_until.strftime('%Y-%m-%d %H:%M')}\n"

    for admin_id in settings.ADMIN_TG_IDS:
        await bot.send_message(
            chat_id=admin_id,
            text=(
                f"💸 <b>Заявка на вывод</b>\n\n"
                f"{user_line}\n"
                f"{ref_line}\n\n"
                f"📤 <b>Источник:</b> {'Пул' if request.source == 'investment' else 'Баланс'}\n"
                f"{mode_line}"
                f"💰 <b>Запрошено:</b> {request.amount_usd} $\n"
                f"💵 <b>К выплате:</b> {request.final_amount_usd} $\n"
                f"{method_line}"
                f"{currency_line}"
                f"📥 <b>Реквизиты:</b> <code>{request.details}</code>\n"
                f"{deadline_line}"
                f"🕒 <i>Создана: {request.created_at.strftime('%Y-%m-%d %H:%M')}</i>"
            ),
            reply_markup=kb,
            parse_mode="HTML"
        )
