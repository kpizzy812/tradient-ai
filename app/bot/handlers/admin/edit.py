from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from datetime import datetime

from app.core.db import SessionLocal
from app.models.users import User
from app.models.investments import Investment
from app.bot.states.admin import AdminStates
from app.bot.handlers.admin.user import show_user_card

router = Router()

@router.callback_query(F.data.startswith("user_edit_menu:"))
async def show_user_edit_menu(call: CallbackQuery, state: FSMContext):
    tg_id = int(call.data.split(":")[1])
    await state.update_data(editing_user_tg=tg_id)

    user = SessionLocal().query(User).filter(User.tg_id == tg_id).first()

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Изм. пригласителя", callback_data=f"user_edit_ref:{tg_id}")],
            [InlineKeyboardButton(text="💰 Изм. баланс", callback_data=f"user_edit_balance:{tg_id}")],
            [InlineKeyboardButton(text="🏦 Изм. пул", callback_data=f"user_edit_pool:{tg_id}")],
            [
                InlineKeyboardButton(
                    text="🔓 Анбан" if getattr(user, "is_banned", False) else "⛔ Бан",
                    callback_data=f"user_{'unban' if getattr(user, 'is_banned', False) else 'ban'}:{tg_id}"
                )
            ],
            [InlineKeyboardButton(text="⛔ Бан всех партнёров", callback_data=f"user_ban_all:{tg_id}")],
            [InlineKeyboardButton(text="✅ Разбанить всех партнёров", callback_data=f"user_unban_all:{tg_id}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"user_back:{tg_id}")]

        ]
    )

    await call.message.edit_text("🔧 Что изменить?", reply_markup=kb)


@router.callback_query(F.data.startswith("user_edit_ref:"))
async def edit_referrer_prompt(call: CallbackQuery, state: FSMContext):
    tg_id = int(call.data.split(":")[1])
    await state.update_data(editing_user_tg=tg_id)
    await call.message.edit_text("Введите новый TG ID пригласителя:")
    await state.set_state(AdminStates.editing_referrer)

@router.message(StateFilter(AdminStates.editing_referrer))
async def edit_referrer_save(msg: Message, state: FSMContext):
    db = SessionLocal()
    data = await state.get_data()
    target_tg_id = data.get("editing_user_tg")

    new_ref_tg = msg.text.strip()
    if not new_ref_tg.isdigit():
        await msg.answer("❌ Введите TG ID числом.")
        return

    target_user = db.query(User).filter(User.tg_id == target_tg_id).first()
    new_ref = db.query(User).filter(User.tg_id == int(new_ref_tg)).first()

    if not target_user or not new_ref:
        db.close()
        await msg.answer("❌ Пользователь или пригласитель не найден.")
        await state.clear()
        return

    current = new_ref
    while current:
        if current.id == target_user.id:
            db.close()
            await msg.answer("❌ Нельзя указать рефералом самого себя или ниже по структуре.")
            await state.clear()
            return
        current = db.query(User).filter(User.id == current.referrer_id).first()

    target_user.referrer_id = new_ref.id
    db.commit()
    db.close()

    await show_user_card(msg, target_tg_id)
    await state.set_state(AdminStates.user_detail)


@router.callback_query(F.data.startswith("user_edit_balance:"))
async def edit_balance_prompt(call: CallbackQuery, state: FSMContext):
    tg_id = int(call.data.split(":")[1])
    await state.update_data(editing_user_tg=tg_id)
    await call.message.edit_text("Введите новый баланс в USD:")
    await state.set_state(AdminStates.editing_balance)

@router.message(StateFilter(AdminStates.editing_balance))
async def edit_balance_save(msg: Message, state: FSMContext):
    db = SessionLocal()
    data = await state.get_data()
    target_tg_id = data.get("editing_user_tg")

    try:
        new_balance = float(msg.text.strip())
    except ValueError:
        await msg.answer("❌ Введите сумму числом.")
        return

    user = db.query(User).filter(User.tg_id == target_tg_id).first()
    if not user:
        db.close()
        await msg.answer("❌ Пользователь не найден.")
        await state.clear()
        return

    user.profit_usd = round(new_balance, 2)
    db.commit()
    db.close()

    await show_user_card(msg, target_tg_id)
    await state.set_state(AdminStates.user_detail)


@router.callback_query(F.data.startswith("user_edit_pool:"))
async def edit_pool_prompt(call: CallbackQuery, state: FSMContext):
    tg_id = int(call.data.split(":")[1])
    await state.update_data(editing_user_tg=tg_id)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Basic", callback_data="set_pool:Basic")],
            [InlineKeyboardButton(text="Smart", callback_data="set_pool:Smart")],
            [InlineKeyboardButton(text="Pro", callback_data="set_pool:Pro")],
            [InlineKeyboardButton(text="Назад", callback_data=f"user_back:{tg_id}")]
        ]
    )

    await call.message.edit_text("🏦 Выберите пул для редактирования:", reply_markup=kb)
    await state.set_state(AdminStates.editing_pool)


@router.callback_query(StateFilter(AdminStates.editing_pool), F.data.startswith("set_pool:"))
async def prompt_invest_amount(call: CallbackQuery, state: FSMContext):
    pool_name = call.data.split(":")[1]
    await state.update_data(selected_pool=pool_name)
    await call.message.edit_text(f"💵 Введите сумму инвестиции в пул <b>{pool_name}</b> в USD:")
    await state.set_state(AdminStates.editing_pool_amount)


@router.message(StateFilter(AdminStates.editing_pool_amount))
async def save_pool_amount(msg: Message, state: FSMContext):
    data = await state.get_data()
    pool = data.get("selected_pool")
    target_tg_id = data.get("editing_user_tg")

    try:
        amount = float(msg.text.strip())
        if amount < 0:
            raise ValueError()
    except ValueError:
        await msg.answer("❌ Введите корректную сумму (например, 250.00).")
        return

    db = SessionLocal()
    user = db.query(User).filter(User.tg_id == target_tg_id).first()
    if not user:
        db.close()
        await msg.answer("❌ Пользователь не найден.")
        await state.clear()
        return

    investment = db.query(Investment).filter_by(user_id=user.id, pool_name=pool, is_active=True).first()

    if investment:
        investment.amount_usd = round(amount, 2)
        msg_text = f"♻️ Обновлена сумма в пуле <b>{pool}</b>: {amount:.2f} USD"
    else:
        new_inv = Investment(
            user_id=user.id,
            pool_name=pool,
            amount_usd=round(amount, 2),
            is_active=True,
            included_today=False,
            created_at=datetime.utcnow()
        )
        db.add(new_inv)
        msg_text = f"✅ Добавлена инвестиция в пул <b>{pool}</b>: {amount:.2f} USD"

    db.commit()
    db.close()

    await msg.answer(msg_text)
    await show_user_card(msg, target_tg_id)
    await state.set_state(AdminStates.user_detail)
