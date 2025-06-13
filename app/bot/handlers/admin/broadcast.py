# app/bot/handlers/admin/broadcast.py
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.types.input_media import InputMediaPhoto, InputMediaVideo
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List
import asyncio
from datetime import datetime, timedelta

from app.core.db import SessionLocal
from app.models.users import User
from app.models.investments import Investment
from app.bot.states.admin import AdminStates

router = Router()


def get_broadcast_menu_kb():
    """Меню рассылки"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👥 Всем пользователям", callback_data="broadcast_all"),
                InlineKeyboardButton(text="⚡ Только активным", callback_data="broadcast_active")
            ],
            [
                InlineKeyboardButton(text="🏦 По пулам", callback_data="broadcast_pools"),
                InlineKeyboardButton(text="💰 По сумме депозита", callback_data="broadcast_amount")
            ],
            [
                InlineKeyboardButton(text="📅 По дате регистрации", callback_data="broadcast_date"),
                InlineKeyboardButton(text="🎯 Кастомная группа", callback_data="broadcast_custom")
            ],
            [
                InlineKeyboardButton(text="🔙 В главное меню", callback_data="admin_menu")
            ]
        ]
    )


def get_pool_selection_kb():
    """Клавиатура выбора пула"""
    from app.core.config import settings

    buttons = []
    row = []

    for pool_name in settings.POOL_LIMITS.keys():
        row.append(InlineKeyboardButton(
            text=pool_name,
            callback_data=f"broadcast_pool_{pool_name}"
        ))
        if len(row) == 2:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton(text="🔙 К рассылке", callback_data="admin_broadcast")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_confirm_broadcast_kb(target_group: str, target_value: str = ""):
    """Клавиатура подтверждения рассылки"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Отправить рассылку",
                    callback_data=f"confirm_broadcast_{target_group}_{target_value}"
                )
            ],
            [
                InlineKeyboardButton(text="❌ Отменить", callback_data="admin_broadcast")
            ]
        ]
    )


@router.callback_query(F.data == "admin_broadcast")
async def show_broadcast_menu(call: CallbackQuery, state: FSMContext):
    """Показать меню рассылки"""
    db = SessionLocal()

    try:
        # Статистика пользователей
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.deposit_usd > 0).count()

        text = (
            "📢 <b>Рассылка сообщений</b>\n\n"
            f"👥 Всего пользователей: {total_users:,}\n"
            f"⚡ Активных пользователей: {active_users:,}\n\n"
            "Выберите целевую аудиторию:"
        )

        await call.message.edit_text(text, reply_markup=get_broadcast_menu_kb())
        await state.set_state(AdminStates.broadcast_menu)

    finally:
        db.close()


@router.callback_query(StateFilter(AdminStates.broadcast_menu), F.data.startswith("broadcast_"))
async def select_broadcast_target(call: CallbackQuery, state: FSMContext):
    """Выбор целевой группы для рассылки"""
    target = call.data.split("_", 1)[1]

    if target == "all":
        await prepare_broadcast(call, state, "all", "")
    elif target == "active":
        await prepare_broadcast(call, state, "active", "")
    elif target == "pools":
        await call.message.edit_text(
            "🏦 <b>Выберите пул:</b>",
            reply_markup=get_pool_selection_kb()
        )
        await state.set_state(AdminStates.broadcast_pool_selection)
    elif target == "amount":
        await call.message.edit_text(
            "💰 <b>Рассылка по сумме депозита</b>\n\n"
            "Введите минимальную сумму депозита в долларах:\n"
            "Пример: <code>100</code> (для пользователей с депозитом от $100)",
            parse_mode="HTML"
        )
        await state.set_state(AdminStates.broadcast_amount_input)
    elif target == "date":
        await call.message.edit_text(
            "📅 <b>Рассылка по дате регистрации</b>\n\n"
            "Введите количество дней назад:\n"
            "Пример: <code>7</code> (пользователи за последние 7 дней)\n"
            "Или: <code>30</code> (пользователи за последние 30 дней)",
            parse_mode="HTML"
        )
        await state.set_state(AdminStates.broadcast_date_input)
    elif target == "custom":
        await call.message.edit_text(
            "🎯 <b>Кастомная рассылка</b>\n\n"
            "Введите TG ID пользователей через запятую:\n"
            "Пример: <code>123456789, 987654321, 456789123</code>",
            parse_mode="HTML"
        )
        await state.set_state(AdminStates.broadcast_custom_input)


@router.callback_query(StateFilter(AdminStates.broadcast_pool_selection), F.data.startswith("broadcast_pool_"))
async def select_pool_for_broadcast(call: CallbackQuery, state: FSMContext):
    """Выбор пула для рассылки"""
    pool_name = call.data.split("_", 2)[2]
    await prepare_broadcast(call, state, "pool", pool_name)


@router.message(StateFilter(AdminStates.broadcast_amount_input))
async def process_amount_input(msg: Message, state: FSMContext):
    """Обработка ввода суммы для рассылки"""
    try:
        min_amount = float(msg.text.strip())
        if min_amount < 0:
            await msg.answer("❌ Сумма не может быть отрицательной")
            return

        await prepare_broadcast(msg, state, "amount", str(min_amount))

    except ValueError:
        await msg.answer("❌ Введите корректную сумму в долларах")


@router.message(StateFilter(AdminStates.broadcast_date_input))
async def process_date_input(msg: Message, state: FSMContext):
    """Обработка ввода даты для рассылки"""
    try:
        days = int(msg.text.strip())
        if days < 1:
            await msg.answer("❌ Количество дней должно быть больше 0")
            return

        await prepare_broadcast(msg, state, "date", str(days))

    except ValueError:
        await msg.answer("❌ Введите корректное количество дней")


@router.message(StateFilter(AdminStates.broadcast_custom_input))
async def process_custom_input(msg: Message, state: FSMContext):
    """Обработка кастомного списка пользователей"""
    try:
        user_ids = [int(uid.strip()) for uid in msg.text.split(",")]
        if not user_ids:
            await msg.answer("❌ Введите хотя бы один TG ID")
            return

        # Проверяем существование пользователей
        db = SessionLocal()
        existing_users = db.query(User).filter(User.tg_id.in_(user_ids)).all()
        db.close()

        if not existing_users:
            await msg.answer("❌ Ни один из указанных пользователей не найден")
            return

        existing_ids = [str(user.tg_id) for user in existing_users]
        await prepare_broadcast(msg, state, "custom", ",".join(existing_ids))

    except ValueError:
        await msg.answer("❌ Все ID должны быть числами")


async def prepare_broadcast(message, state: FSMContext, target_group: str, target_value: str):
    """Подготовка к рассылке - запрос сообщения"""
    db = SessionLocal()

    try:
        # Подсчитываем целевую аудиторию
        user_count = await get_target_users_count(db, target_group, target_value)

        if user_count == 0:
            await message.answer("❌ Не найдено пользователей для рассылки")
            return

        # Сохраняем параметры рассылки
        await state.update_data(
            broadcast_target=target_group,
            broadcast_value=target_value,
            broadcast_count=user_count
        )

        # Описание целевой группы
        group_descriptions = {
            "all": "всем пользователям",
            "active": "активным пользователям",
            "pool": f"пользователям пула {target_value}",
            "amount": f"пользователям с депозитом от ${target_value}",
            "date": f"пользователям за последние {target_value} дней",
            "custom": "выбранным пользователям"
        }

        group_desc = group_descriptions.get(target_group, "пользователям")

        text = (
            f"📢 <b>Рассылка {group_desc}</b>\n\n"
            f"👥 Получателей: {user_count:,}\n\n"
            "Теперь отправьте сообщение для рассылки.\n\n"
            "<b>Поддерживается:</b>\n"
            "• Текстовые сообщения с форматированием\n"
            "• Фото с подписью\n"
            "• Видео с подписью\n"
            "• Кнопки (будут сохранены)\n\n"
            "❗ Сообщение будет отправлено в том же виде, что и вы пришлете"
        )

        await message.answer(text, parse_mode="HTML")
        await state.set_state(AdminStates.broadcast_message_input)

    finally:
        db.close()


@router.message(StateFilter(AdminStates.broadcast_message_input))
async def process_broadcast_message(msg: Message, state: FSMContext):
    """Обработка сообщения для рассылки"""
    data = await state.get_data()
    target_group = data.get("broadcast_target")
    target_value = data.get("broadcast_value", "")
    user_count = data.get("broadcast_count", 0)

    # Сохраняем сообщение для рассылки
    broadcast_data = {
        "message_type": None,
        "text": None,
        "photo": None,
        "video": None,
        "reply_markup": None,
        "entities": None
    }

    if msg.photo:
        broadcast_data["message_type"] = "photo"
        broadcast_data["photo"] = msg.photo[-1].file_id
        broadcast_data["text"] = msg.caption
        broadcast_data["entities"] = msg.caption_entities
        broadcast_data["reply_markup"] = msg.reply_markup
    elif msg.video:
        broadcast_data["message_type"] = "video"
        broadcast_data["video"] = msg.video.file_id
        broadcast_data["text"] = msg.caption
        broadcast_data["entities"] = msg.caption_entities
        broadcast_data["reply_markup"] = msg.reply_markup
    elif msg.text:
        broadcast_data["message_type"] = "text"
        broadcast_data["text"] = msg.text
        broadcast_data["entities"] = msg.entities
        broadcast_data["reply_markup"] = msg.reply_markup
    else:
        await msg.answer("❌ Поддерживаются только текстовые сообщения, фото и видео")
        return

    # Сохраняем данные сообщения
    await state.update_data(broadcast_message=broadcast_data)

    # Показываем превью
    group_descriptions = {
        "all": "всем пользователям",
        "active": "активным пользователям",
        "pool": f"пользователям пула {target_value}",
        "amount": f"пользователям с депозитом от ${target_value}",
        "date": f"пользователям за последние {target_value} дней",
        "custom": "выбранным пользователям"
    }

    group_desc = group_descriptions.get(target_group, "пользователям")

    preview_text = (
        f"📢 <b>Подтверждение рассылки</b>\n\n"
        f"👥 Получателей: {user_count:,}\n"
        f"🎯 Группа: {group_desc}\n\n"
        "📝 <b>Сообщение готово к отправке</b>\n"
        "Подтвердите рассылку:"
    )

    await msg.answer(
        preview_text,
        reply_markup=get_confirm_broadcast_kb(target_group, target_value),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("confirm_broadcast_"))
async def confirm_and_send_broadcast(call: CallbackQuery, bot: Bot, state: FSMContext):
    """Подтверждение и отправка рассылки"""
    data = await state.get_data()
    broadcast_data = data.get("broadcast_message")
    target_group = data.get("broadcast_target")
    target_value = data.get("broadcast_value", "")

    if not broadcast_data:
        await call.answer("❌ Данные рассылки потеряны")
        return

    await call.message.edit_text(
        "🚀 <b>Рассылка запущена...</b>\n\n"
        "Это может занять некоторое время",
        parse_mode="HTML"
    )

    # Запускаем рассылку в фоне
    asyncio.create_task(
        execute_broadcast(bot, call.from_user.id, broadcast_data, target_group, target_value)
    )

    await state.clear()


async def execute_broadcast(bot: Bot, admin_id: int, broadcast_data: dict, target_group: str, target_value: str):
    """Выполнение рассылки"""
    db = SessionLocal()

    try:
        # Получаем список пользователей
        users = await get_target_users(db, target_group, target_value)

        if not users:
            await bot.send_message(admin_id, "❌ Не найдено пользователей для рассылки")
            return

        # Статистика отправки
        sent_count = 0
        failed_count = 0
        blocked_count = 0

        # Отправляем сообщения
        for user in users:
            try:
                await asyncio.sleep(0.05)  # Задержка между отправками

                if broadcast_data["message_type"] == "text":
                    await bot.send_message(
                        chat_id=user.tg_id,
                        text=broadcast_data["text"],
                        entities=broadcast_data["entities"],
                        reply_markup=broadcast_data["reply_markup"]
                    )
                elif broadcast_data["message_type"] == "photo":
                    await bot.send_photo(
                        chat_id=user.tg_id,
                        photo=broadcast_data["photo"],
                        caption=broadcast_data["text"],
                        caption_entities=broadcast_data["entities"],
                        reply_markup=broadcast_data["reply_markup"]
                    )
                elif broadcast_data["message_type"] == "video":
                    await bot.send_video(
                        chat_id=user.tg_id,
                        video=broadcast_data["video"],
                        caption=broadcast_data["text"],
                        caption_entities=broadcast_data["entities"],
                        reply_markup=broadcast_data["reply_markup"]
                    )

                sent_count += 1

            except Exception as e:
                error_str = str(e).lower()
                if "blocked" in error_str or "chat not found" in error_str:
                    blocked_count += 1
                else:
                    failed_count += 1

        # Отправляем отчет админу
        report = (
            f"📊 <b>Отчет о рассылке</b>\n\n"
            f"✅ Доставлено: {sent_count:,}\n"
            f"🚫 Заблокированы: {blocked_count:,}\n"
            f"❌ Ошибки: {failed_count:,}\n"
            f"📋 Всего: {len(users):,}\n\n"
            f"📈 Успешность: {(sent_count / len(users) * 100):.1f}%"
        )

        await bot.send_message(admin_id, report, parse_mode="HTML")

    finally:
        db.close()


async def get_target_users_count(db: Session, target_group: str, target_value: str) -> int:
    """Подсчет количества пользователей для рассылки"""
    query = db.query(User)

    if target_group == "all":
        return query.count()
    elif target_group == "active":
        return query.filter(User.deposit_usd > 0).count()
    elif target_group == "pool":
        # Пользователи с активными инвестициями в определенном пуле
        user_ids = db.query(Investment.user_id).filter(
            and_(Investment.pool_name == target_value, Investment.is_active == True)
        ).distinct().subquery()
        return query.filter(User.id.in_(user_ids)).count()
    elif target_group == "amount":
        min_amount = float(target_value)
        return query.filter(User.deposit_usd >= min_amount).count()
    elif target_group == "date":
        days_ago = int(target_value)
        date_threshold = datetime.utcnow() - timedelta(days=days_ago)
        return query.filter(User.created_at >= date_threshold).count()
    elif target_group == "custom":
        user_ids = [int(uid) for uid in target_value.split(",")]
        return query.filter(User.tg_id.in_(user_ids)).count()

    return 0


async def get_target_users(db: Session, target_group: str, target_value: str) -> List[User]:
    """Получение списка пользователей для рассылки"""
    query = db.query(User)

    if target_group == "all":
        return query.all()
    elif target_group == "active":
        return query.filter(User.deposit_usd > 0).all()
    elif target_group == "pool":
        # Пользователи с активными инвестициями в определенном пуле
        user_ids = db.query(Investment.user_id).filter(
            and_(Investment.pool_name == target_value, Investment.is_active == True)
        ).distinct().subquery()
        return query.filter(User.id.in_(user_ids)).all()
    elif target_group == "amount":
        min_amount = float(target_value)
        return query.filter(User.deposit_usd >= min_amount).all()
    elif target_group == "date":
        days_ago = int(target_value)
        date_threshold = datetime.utcnow() - timedelta(days=days_ago)
        return query.filter(User.created_at >= date_threshold).all()
    elif target_group == "custom":
        user_ids = [int(uid) for uid in target_value.split(",")]
        return query.filter(User.tg_id.in_(user_ids)).all()

    return []