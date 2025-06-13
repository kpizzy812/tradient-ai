# app/bot/handlers/admin/requests.py
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.db import SessionLocal
from app.models.users import User
from app.models.deposit_request import DepositRequest
from app.models.withdraw_request import WithdrawRequest
from app.bot.states.admin import AdminStates
from app.services.logic import invest_user, t

router = Router()


def get_request_card_kb(request_id: int, request_type: str, status: str):
    """Клавиатура для карточки заявки"""
    buttons = []

    if status == "pending":
        if request_type == "deposit":
            buttons.extend([
                [
                    InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{request_id}"),
                    InlineKeyboardButton(text="❌ Отклонить", callback_data=f"decline_{request_id}")
                ],
                [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_{request_id}")]
            ])
        elif request_type == "withdraw":
            buttons.extend([
                [
                    InlineKeyboardButton(text="✅ Одобрить", callback_data=f"withdraw_approve_{request_id}"),
                    InlineKeyboardButton(text="❌ Отклонить", callback_data=f"withdraw_decline_{request_id}")
                ]
            ])

    # Кнопка возврата
    buttons.append([
        InlineKeyboardButton(text="🔙 К списку", callback_data=f"admin_{request_type}s")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data.startswith("view_deposit_"))
async def view_deposit_request(call: CallbackQuery, state: FSMContext):
    """Показать детальную карточку заявки на пополнение"""
    request_id = int(call.data.split("_")[-1])
    db = SessionLocal()

    try:
        req = db.query(DepositRequest).filter(DepositRequest.id == request_id).first()
        if not req:
            await call.answer("❌ Заявка не найдена", show_alert=True)
            return

        user = db.query(User).filter(User.id == req.user_id).first()
        if not user:
            await call.answer("❌ Пользователь не найден", show_alert=True)
            return

        # Получаем пригласителя
        ref_line = "🔗 <b>Пригласитель:</b> —"
        if user.referrer_id:
            ref = db.query(User).filter(User.id == user.referrer_id).first()
            if ref:
                ref_line = f"🔗 <b>Пригласитель:</b> "
                ref_line += f"@{ref.username} ({ref.tg_id})" if ref.username else f"ID {ref.tg_id}"

        # Эмодзи статуса
        status_emoji = {
            "pending": "⏳",
            "approved": "✅",
            "declined": "❌",
            "deleted": "🗑"
        }.get(req.status, "❓")

        status_text = {
            "pending": "Ожидает",
            "approved": "Одобрено",
            "declined": "Отклонено",
            "deleted": "Удалено"
        }.get(req.status, "Неизвестно")

        user_line = f"👤 <b>Пользователь:</b> "
        user_line += f"@{user.username} ({user.tg_id})" if user.username else f"ID {user.tg_id}"

        text = (
            f"💰 <b>Заявка на пополнение #{req.id}</b>\n\n"
            f"{user_line}\n"
            f"💰 <b>Баланс пользователя:</b> ${user.profit_usd:.2f}\n"
            f"💳 <b>Всего депозитов:</b> ${user.deposit_usd:.2f}\n"
            f"{ref_line}\n\n"
            f"💵 <b>Сумма:</b> <code>${req.amount_usd:.2f}</code>\n"
            f"🏦 <b>Пул:</b> <code>{req.pool_name}</code>\n"
            f"💳 <b>Метод:</b> <code>{req.method}</code>\n"
        )

        if req.currency:
            text += f"💱 <b>Валюта:</b> <code>{req.currency}</code>\n"

        if req.details:
            text += f"📋 <b>Детали:</b> <code>{req.details}</code>\n"

        text += (
            f"\n📊 <b>Статус:</b> {status_emoji} {status_text}\n"
            f"🕒 <b>Создана:</b> {req.created_at.strftime('%d.%m.%Y %H:%M')}"
        )

        kb = get_request_card_kb(req.id, "deposit", req.status)

        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        await state.set_state(AdminStates.request_detail)

    finally:
        db.close()


@router.callback_query(F.data.startswith("view_withdraw_"))
async def view_withdraw_request(call: CallbackQuery, state: FSMContext):
    """Показать детальную карточку заявки на вывод"""
    request_id = int(call.data.split("_")[-1])
    db = SessionLocal()

    try:
        req = db.query(WithdrawRequest).filter(WithdrawRequest.id == request_id).first()
        if not req:
            await call.answer("❌ Заявка не найдена", show_alert=True)
            return

        user = db.query(User).filter(User.id == req.user_id).first()
        if not user:
            await call.answer("❌ Пользователь не найден", show_alert=True)
            return

        # Получаем пригласителя
        ref_line = "🔗 <b>Пригласитель:</b> —"
        if user.referrer_id:
            ref = db.query(User).filter(User.id == user.referrer_id).first()
            if ref:
                ref_line = f"🔗 <b>Пригласитель:</b> "
                ref_line += f"@{ref.username} ({ref.tg_id})" if ref.username else f"ID {ref.tg_id}"

        # Эмодзи статуса
        status_emoji = {
            "pending": "⏳",
            "executed": "✅",
            "auto_paid": "🤖",
            "declined": "❌"
        }.get(req.status, "❓")

        status_text = {
            "pending": "Ожидает",
            "executed": "Выполнено",
            "auto_paid": "Авто-выплата",
            "declined": "Отклонено"
        }.get(req.status, "Неизвестно")

        user_line = f"👤 <b>Пользователь:</b> "
        user_line += f"@{user.username} ({user.tg_id})" if user.username else f"ID {user.tg_id}"

        # Источник и режим
        source_text = "💰 Баланс" if req.source == "balance" else f"🏦 Пул {req.pool_name}"
        mode_text = ""
        if req.mode:
            mode_text = f" (<b>{req.mode}</b>)"

        # Комиссия
        commission_amount = req.amount_usd - req.final_amount_usd
        commission_percent = (commission_amount / req.amount_usd * 100) if req.amount_usd > 0 else 0

        text = (
            f"💸 <b>Заявка на вывод #{req.id}</b>\n\n"
            f"{user_line}\n"
            f"💰 <b>Баланс пользователя:</b> ${user.profit_usd:.2f}\n"
            f"{ref_line}\n\n"
            f"📤 <b>Источник:</b> {source_text}{mode_text}\n"
            f"💰 <b>Запрошено:</b> <code>${req.amount_usd:.2f}</code>\n"
            f"💵 <b>К выплате:</b> <code>${req.final_amount_usd:.2f}</code>\n"
            f"📊 <b>Комиссия:</b> <code>${commission_amount:.2f}</code> ({commission_percent:.1f}%)\n"
            f"💳 <b>Метод:</b> <code>{req.method}</code>\n"
        )

        if req.currency:
            text += f"💱 <b>Валюта:</b> <code>{req.currency}</code>\n"

        if req.details:
            text += f"📥 <b>Реквизиты:</b>\n<code>{req.details}</code>\n"

        text += f"\n📊 <b>Статус:</b> {status_emoji} {status_text}\n"

        if req.execute_until:
            text += f"⏰ <b>Выполнить до:</b> {req.execute_until.strftime('%d.%m.%Y %H:%M')}\n"

        text += f"🕒 <b>Создана:</b> {req.created_at.strftime('%d.%m.%Y %H:%M')}"

        kb = get_request_card_kb(req.id, "withdraw", req.status)

        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        await state.set_state(AdminStates.request_detail)

    finally:
        db.close()