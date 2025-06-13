# app/bot/handlers/admin/entry.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from app.core.config import settings
from app.bot.states.admin import AdminStates
from app.bot.keyboards.admin import get_admin_menu_kb, get_stats_menu_kb
from app.services.logic import t

router = Router()

@router.message(F.text == "/admin")
async def cmd_admin(msg: Message, state: FSMContext):
    if msg.from_user.id not in settings.ADMIN_TG_IDS:
        await msg.answer(t("not_admin", msg.from_user.language_code))
        return

    await msg.answer(
        t("admin_panel", msg.from_user.language_code),
        reply_markup=get_admin_menu_kb()
    )
    await state.set_state(AdminStates.menu)

# Главное меню
@router.callback_query(F.data == "admin_menu")
async def show_admin_menu(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        t("admin_panel", call.from_user.language_code),
        reply_markup=get_admin_menu_kb()
    )
    await state.set_state(AdminStates.menu)

# Пользователи
@router.callback_query(StateFilter(AdminStates.menu), F.data == "admin_users")
async def callback_admin_users(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Введите TG ID пользователя для просмотра:")
    await state.set_state(AdminStates.user_input_id)

# Статистика - главное меню
@router.callback_query(F.data == "admin_stats")
async def show_stats_menu(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "📊 <b>Статистика и аналитика</b>\n\n"
        "Выберите раздел для просмотра:",
        reply_markup=get_stats_menu_kb()
    )
    await state.set_state(AdminStates.stats_menu)

# Обратная совместимость с существующими хендлерами
@router.callback_query(StateFilter(AdminStates.user_detail), F.data == "admin_back")
async def callback_admin_back_from_user(call: CallbackQuery, state: FSMContext):
    await show_admin_menu(call, state)

@router.callback_query(F.data == "admin_back")
async def callback_admin_back_general(call: CallbackQuery, state: FSMContext):
    await show_admin_menu(call, state)