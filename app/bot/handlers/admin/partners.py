from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from app.bot.states.admin import AdminStates
from app.core.db import SessionLocal
from app.models.users import User

router = Router()

@router.callback_query(F.data.startswith("user_partners:"))
async def choose_ref_level(call: CallbackQuery, state: FSMContext):
    tg_id = int(call.data.split(":")[1])
    await state.update_data(editing_user_tg=tg_id)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1 уровень", callback_data="ref_level:1"),
                InlineKeyboardButton(text="2", callback_data="ref_level:2"),
                InlineKeyboardButton(text="3", callback_data="ref_level:3"),
            ],
            [
                InlineKeyboardButton(text="4", callback_data="ref_level:4"),
                InlineKeyboardButton(text="5", callback_data="ref_level:5"),
                InlineKeyboardButton(text="Назад", callback_data="admin_back"),
            ],
        ]
    )

    await call.message.edit_text("Выберите уровень партнёров:", reply_markup=kb)
    await state.set_state(AdminStates.choosing_ref_level)

@router.callback_query(StateFilter(AdminStates.choosing_ref_level), F.data.startswith("ref_level:"))
async def show_partners_by_level(call: CallbackQuery, state: FSMContext):
    db = SessionLocal()
    data = await state.get_data()
    target_user = db.query(User).filter(User.tg_id == data.get("editing_user_tg")).first()
    level = int(call.data.split(":")[1])

    users = []
    current_level = [target_user]
    for _ in range(level):
        next_level = []
        for u in current_level:
            children = db.query(User).filter(User.referrer_id == u.id).all()
            next_level.extend(children)
        current_level = next_level
    users = current_level

    active_users = [u for u in users if u.deposit_usd > 0]
    inactive_users = [u for u in users if u.deposit_usd == 0]

    def format_user(u):
        return f"@{u.username or '—'} (`{u.tg_id}`) {'✅' if u.deposit_usd > 0 else '❌'}"

    text = f"<b>Партнёры {level} уровня:</b>\n\n"
    for u in active_users + inactive_users:
        text += format_user(u) + "\n"

    if not users:
        text = f"❌ Партнёров {level} уровня не найдено."

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data=f"user_partners:{target_user.tg_id}")],
            [InlineKeyboardButton(text="В меню", callback_data="admin_back")]
        ]
    )

    db.close()
    await call.message.edit_text(text, reply_markup=kb)

