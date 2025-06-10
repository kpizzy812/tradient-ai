# app/bot/handlers/admin/user.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from app.core.db import SessionLocal
from app.models.users import User
from app.models.investments import Investment
from app.bot.states.admin import AdminStates
from app.services.user_stats import (
    get_root_referrer, get_referral_counts,
    get_active_referrals_count, get_total_deposits, get_total_withdrawals
)
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

@router.message(StateFilter(AdminStates.user_input_id))
async def process_user_id(msg: Message, state: FSMContext):
    try:
        user_tg_id = int(msg.text.strip())
    except ValueError:
        await msg.answer("❌ Неверный TG ID. Введите только цифры.")
        return

    db = SessionLocal()
    user = db.query(User).filter(User.tg_id == user_tg_id).first()
    db.close()

    if not user:
        await msg.answer("❌ Пользователь не найден.")
        await state.clear()
        return

    await show_user_card(msg, user_tg_id)
    await state.set_state(AdminStates.user_detail)


@router.callback_query(F.data.startswith("user_back:"))
async def return_to_user_card(call: CallbackQuery, state: FSMContext):
    user_tg_id = int(call.data.split(":")[1])
    await show_user_card(call, user_tg_id)
    await state.set_state(AdminStates.user_detail)


async def show_user_card(message: Message | CallbackQuery, user_tg_id: int):
    db = SessionLocal()
    user = db.query(User).filter(User.tg_id == user_tg_id).first()
    if not user:
        db.close()
        await message.answer("❌ Пользователь не найден.")
        return

    investments = db.query(Investment).filter(Investment.user_id == user.id, Investment.is_active == True).all()
    pools = {}
    for inv in investments:
        pools.setdefault(inv.pool_name, 0.0)
        pools[inv.pool_name] += inv.amount_usd

    total_deposit = get_total_deposits(db, user.id)
    total_withdraw = get_total_withdrawals(db, user.id)
    ref_counts = get_referral_counts(db, user)
    active_refs = get_active_referrals_count(db, user)
    referrer = db.query(User).filter(User.id == user.referrer_id).first()
    root_ref = get_root_referrer(db, user)
    db.close()

    pool_lines = "\n".join(f"💼 {name}: {amount:.2f} USD" for name, amount in pools.items() if amount > 0)
    ref_line = " ".join([f"{i}:{count}" for i, count in ref_counts.items()])

    text = (
        f"👤 @{user.username or '—'} (`{user.tg_id}`)\n\n"
        f"💰 <b>Баланс:</b> {user.profit_usd:.2f} USD\n"
        + (f"{pool_lines}\n" if pool_lines else "") +
        f"🔼 <b>Пополнено:</b> {total_deposit:.2f} USD\n"
        f"🔽 <b>Выведено:</b> {total_withdraw:.2f} USD\n\n"
        f"👥 <b>Партнёры:</b> {ref_line}\n"
        f"✅ <b>Активных:</b> {active_refs}\n\n"
        + (
            f"📥 <b>Пригласитель:</b> @{referrer.username or '—'} (`{referrer.tg_id}`)\n"
            if referrer else ""
        )
        + f"🌳 <b>Главный в структуре:</b> @{root_ref.username or '—'} (`{root_ref.tg_id}`)\n"
        f"🌐 <b>Язык:</b> {user.lang.upper()}"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔧 Изменить", callback_data=f"user_edit_menu:{user.tg_id}")],
            [
                InlineKeyboardButton(text="👥 Партнеры", callback_data=f"user_partners:{user.tg_id}"),
                InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")
            ]
        ]
    )

    if isinstance(message, CallbackQuery):
        await message.message.edit_text(text, reply_markup=kb)
    else:
        await message.answer(text, reply_markup=kb)

