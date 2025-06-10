from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from app.core.db import SessionLocal
from app.models.users import User
from app.bot.states.admin import AdminStates
from app.services.logic import t
from aiogram import Bot
from app.bot.handlers.admin.user import show_user_card
from app.core.config import settings

router = Router()


@router.callback_query(F.data.startswith("user_ban:"))
async def handle_ban_user(call: CallbackQuery, state: FSMContext, bot: Bot):
    tg_id = int(call.data.split(":")[1])

    db = SessionLocal()
    user = db.query(User).filter(User.tg_id == tg_id).first()
    if not user:
        db.close()
        await call.message.answer("❌ Пользователь не найден.")
        return

    user.is_banned = True
    db.commit()

    # Кикаем из чата
    try:
        await bot.ban_chat_member(settings.PROJECT_CHAT_ID, user.tg_id)
        await bot.unban_chat_member(settings.PROJECT_CHAT_ID, user.tg_id)
    except Exception as e:
        await call.message.answer(f"⚠️ Не удалось исключить из чата: {e}")

    db.close()

    await show_user_card(call, tg_id)
    await state.set_state(AdminStates.user_detail)


@router.callback_query(F.data.startswith("user_unban:"))
async def handle_unban_user(call: CallbackQuery, state: FSMContext):
    tg_id = int(call.data.split(":")[1])

    db = SessionLocal()
    user = db.query(User).filter(User.tg_id == tg_id).first()
    if not user:
        db.close()
        await call.message.answer("❌ Пользователь не найден.")
        return

    user.is_banned = False
    db.commit()
    db.close()

    await show_user_card(call, tg_id)
    await state.set_state(AdminStates.user_detail)


@router.callback_query(F.data.startswith("user_ban_all:"))
async def handle_ban_all(call: CallbackQuery, state: FSMContext, bot: Bot):
    tg_id = int(call.data.split(":")[1])

    db = SessionLocal()
    root_user = db.query(User).filter(User.tg_id == tg_id).first()
    if not root_user:
        db.close()
        await call.message.answer("❌ Пользователь не найден.")
        return

    to_ban = []

    def collect_descendants(user):
        children = db.query(User).filter(User.referrer_id == user.id).all()
        for child in children:
            to_ban.append(child)
            collect_descendants(child)

    collect_descendants(root_user)
    to_ban.append(root_user)

    banned = []
    for u in to_ban:
        u.is_banned = True
        banned.append(u.tg_id)
        try:
            await bot.ban_chat_member(settings.PROJECT_CHAT_ID, u.tg_id)
            await bot.unban_chat_member(settings.PROJECT_CHAT_ID, u.tg_id)
        except:
            pass

    db.commit()
    db.close()

    lines = [f"@{u.username or '—'} (`{u.tg_id}`)" for u in to_ban]
    user_list = "\n".join(lines)

    await call.message.edit_text(
        f"⛔ Забанено {len(banned)} пользователей:\n\n{user_list[:4000]}"
    )
    await show_user_card(call, tg_id)
    await state.set_state(AdminStates.user_detail)


@router.callback_query(F.data.startswith("user_unban_all:"))
async def handle_unban_all(call: CallbackQuery, state: FSMContext):
    tg_id = int(call.data.split(":")[1])

    db = SessionLocal()
    root_user = db.query(User).filter(User.tg_id == tg_id).first()
    if not root_user:
        db.close()
        await call.message.answer("❌ Пользователь не найден.")
        return

    to_unban = []

    def collect_descendants(user):
        children = db.query(User).filter(User.referrer_id == user.id).all()
        for child in children:
            to_unban.append(child)
            collect_descendants(child)

    collect_descendants(root_user)
    to_unban.append(root_user)

    for u in to_unban:
        u.is_banned = False

    db.commit()
    db.close()

    lines = [f"@{u.username or '—'} (`{u.tg_id}`)" for u in to_unban]
    user_list = "\n".join(lines)

    await call.message.edit_text(
        f"✅ Разблокировано {len(to_unban)} пользователей:\n\n{user_list[:4000]}"
    )
    await show_user_card(call, tg_id)
    await state.set_state(AdminStates.user_detail)
