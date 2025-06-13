# app/bot/handlers/admin/deposits.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta

from app.core.db import SessionLocal
from app.models.users import User
from app.models.deposit_request import DepositRequest
from app.bot.states.admin import AdminStates

router = Router()

# Константы для пагинации
ITEMS_PER_PAGE = 20


def get_deposit_filter_kb(current_filter="all"):
    """Клавиатура фильтров для заявок"""
    filters = {
        "all": "Все",
        "pending": "Ожидают",
        "approved": "Одобрено",
        "declined": "Отклонено",
        "deleted": "Удалено"
    }

    buttons = []
    row = []
    for key, text in filters.items():
        mark = "✅ " if key == current_filter else ""
        row.append(InlineKeyboardButton(
            text=f"{mark}{text}",
            callback_data=f"deposits_filter_{key}"
        ))
        if len(row) == 2:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton(text="🔙 В главное меню", callback_data="admin_menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_deposit_list_kb(page=0, total_pages=0, status_filter="all"):
    """Клавиатура для списка заявок с пагинацией"""
    buttons = []

    # Пагинация
    if total_pages > 1:
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton(
                text="⬅️",
                callback_data=f"deposits_page_{page - 1}_{status_filter}"
            ))

        nav_row.append(InlineKeyboardButton(
            text=f"{page + 1}/{total_pages}",
            callback_data="deposits_noop"
        ))

        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton(
                text="➡️",
                callback_data=f"deposits_page_{page + 1}_{status_filter}"
            ))

        buttons.append(nav_row)

    # Управление
    buttons.extend([
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data=f"deposits_page_{page}_{status_filter}"),
            InlineKeyboardButton(text="📊 Фильтры", callback_data="admin_deposits")
        ],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="admin_menu")]
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data == "admin_deposits")
async def show_deposits_filters(call: CallbackQuery, state: FSMContext):
    """Показать фильтры для заявок на пополнение"""
    db = SessionLocal()

    try:
        # Статистика по статусам
        stats = {}
        for status in ["pending", "approved", "declined", "deleted"]:
            count = db.query(DepositRequest).filter(DepositRequest.status == status).count()
            stats[status] = count

        total = db.query(DepositRequest).count()

        text = (
            "📈 <b>Управление заявками на пополнение</b>\n\n"
            f"📊 <b>Статистика:</b>\n"
            f"• Всего заявок: {total:,}\n"
            f"• Ожидают: {stats['pending']:,}\n"
            f"• Одобрено: {stats['approved']:,}\n"
            f"• Отклонено: {stats['declined']:,}\n"
            f"• Удалено: {stats['deleted']:,}\n\n"
            "Выберите фильтр для просмотра:"
        )

        await call.message.edit_text(text, reply_markup=get_deposit_filter_kb())
        await state.set_state(AdminStates.deposits_filter)

    finally:
        db.close()


@router.callback_query(StateFilter(AdminStates.deposits_filter), F.data.startswith("deposits_filter_"))
async def show_deposits_list(call: CallbackQuery, state: FSMContext):
    """Показать список заявок с выбранным фильтром"""
    status_filter = call.data.split("_")[-1]
    await show_deposits_page(call, state, 0, status_filter)


@router.callback_query(F.data.startswith("deposits_page_"))
async def handle_deposits_pagination(call: CallbackQuery, state: FSMContext):
    """Обработка пагинации"""
    parts = call.data.split("_")
    page = int(parts[2])
    status_filter = parts[3] if len(parts) > 3 else "all"
    await show_deposits_page(call, state, page, status_filter)


async def show_deposits_page(call: CallbackQuery, state: FSMContext, page: int, status_filter: str):
    """Показать страницу заявок"""
    db = SessionLocal()

    try:
        # Создаем запрос с фильтром
        query = db.query(DepositRequest)

        if status_filter != "all":
            query = query.filter(DepositRequest.status == status_filter)

        # Общее количество
        total_count = query.count()
        total_pages = (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

        if total_pages == 0:
            await call.message.edit_text(
                f"📈 <b>Заявки на пополнение ({status_filter})</b>\n\n"
                "🚫 Заявок не найдено",
                reply_markup=get_deposit_filter_kb(status_filter)
            )
            return

        # Получаем заявки для текущей страницы
        requests = query.order_by(desc(DepositRequest.created_at)).offset(
            page * ITEMS_PER_PAGE
        ).limit(ITEMS_PER_PAGE).all()

        # Формируем текст
        status_names = {
            "pending": "⏳ Ожидают",
            "approved": "✅ Одобрено",
            "declined": "❌ Отклонено",
            "deleted": "🗑 Удалено",
            "all": "📈 Все заявки"
        }

        text = f"{status_names.get(status_filter, '📈 Заявки')} на пополнение\n\n"

        # Добавляем заявки
        for i, req in enumerate(requests, 1):
            user = db.query(User).filter(User.id == req.user_id).first()
            username = f"@{user.username}" if user and user.username else f"ID{user.tg_id if user else 'N/A'}"

            status_emoji = {
                "pending": "⏳",
                "approved": "✅",
                "declined": "❌",
                "deleted": "🗑"
            }.get(req.status, "❓")

            text += (
                f"<b>{page * ITEMS_PER_PAGE + i}.</b> {status_emoji} {username}\n"
                f"💰 ${req.amount_usd:.2f} → {req.pool_name}\n"
                f"💳 {req.method}"
            )

            if req.currency:
                text += f" ({req.currency})"

            text += f"\n🕒 {req.created_at.strftime('%d.%m.%Y %H:%M')}\n"

            if req.details:
                details = req.details[:50] + "..." if len(req.details) > 50 else req.details
                text += f"📝 <code>{details}</code>\n"

            text += "\n"

        # Добавляем информацию о пагинации
        if total_pages > 1:
            text += f"📄 Страница {page + 1} из {total_pages} | Всего: {total_count}"

        await call.message.edit_text(
            text,
            reply_markup=get_deposit_list_kb(page, total_pages, status_filter),
            parse_mode="HTML"
        )
        await state.set_state(AdminStates.deposits_list)

    finally:
        db.close()


@router.callback_query(F.data == "deposits_noop")
async def deposits_noop(call: CallbackQuery):
    """Заглушка для неактивных кнопок"""
    await call.answer()