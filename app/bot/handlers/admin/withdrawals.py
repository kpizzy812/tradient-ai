# app/bot/handlers/admin/withdrawals.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta

from app.core.db import SessionLocal
from app.models.users import User
from app.models.withdraw_request import WithdrawRequest
from app.bot.states.admin import AdminStates

router = Router()

ITEMS_PER_PAGE = 20


def get_withdraw_filter_kb(current_filter="all"):
    """Клавиатура фильтров для заявок на вывод"""
    filters = {
        "all": "Все",
        "pending": "Ожидают",
        "executed": "Выполнено",
        "auto_paid": "Авто",
        "declined": "Отклонено"
    }

    buttons = []
    row = []
    for key, text in filters.items():
        mark = "✅ " if key == current_filter else ""
        row.append(InlineKeyboardButton(
            text=f"{mark}{text}",
            callback_data=f"withdraws_filter_{key}"
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


def get_withdraw_list_kb(page=0, total_pages=0, status_filter="all", requests_on_page=[]):
    """Клавиатура для списка заявок на вывод с интерактивными кнопками"""
    buttons = []

    # Кнопки для каждой заявки (только для pending заявок)
    request_buttons = []
    for req in requests_on_page:
        if req.status == "pending":
            request_buttons.append(InlineKeyboardButton(
                text=f"#{req.id} 👁",
                callback_data=f"view_withdraw_{req.id}"
            ))

    # Располагаем кнопки заявок по 3 в ряд
    for i in range(0, len(request_buttons), 3):
        row = request_buttons[i:i + 3]
        buttons.append(row)

    # Пагинация
    if total_pages > 1:
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton(
                text="⬅️",
                callback_data=f"withdraws_page_{page - 1}_{status_filter}"
            ))

        nav_row.append(InlineKeyboardButton(
            text=f"{page + 1}/{total_pages}",
            callback_data="withdraws_noop"
        ))

        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton(
                text="➡️",
                callback_data=f"withdraws_page_{page + 1}_{status_filter}"
            ))

        buttons.append(nav_row)

    # Управление
    buttons.extend([
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data=f"withdraws_page_{page}_{status_filter}"),
            InlineKeyboardButton(text="📊 Фильтры", callback_data="admin_withdraws")
        ],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="admin_menu")]
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data == "admin_withdraws")
async def show_withdraws_filters(call: CallbackQuery, state: FSMContext):
    """Показать фильтры для заявок на вывод"""
    db = SessionLocal()

    try:
        # Статистика по статусам
        stats = {}
        for status in ["pending", "executed", "auto_paid", "declined"]:
            count = db.query(WithdrawRequest).filter(WithdrawRequest.status == status).count()
            stats[status] = count

        total = db.query(WithdrawRequest).count()

        # Сумма ожидающих
        pending_amount = db.query(func.sum(WithdrawRequest.amount_usd)).filter(
            WithdrawRequest.status == "pending"
        ).scalar() or 0

        text = (
            "📉 <b>Управление заявками на вывод</b>\n\n"
            f"📊 <b>Статистика:</b>\n"
            f"• Всего заявок: {total:,}\n"
            f"• Ожидают: {stats['pending']:,} (${pending_amount:,.2f})\n"
            f"• Выполнено: {stats['executed']:,}\n"
            f"• Автовыплата: {stats['auto_paid']:,}\n"
            f"• Отклонено: {stats['declined']:,}\n\n"
            "Выберите фильтр для просмотра:"
        )

        await call.message.edit_text(text, reply_markup=get_withdraw_filter_kb())
        await state.set_state(AdminStates.withdraws_filter)

    finally:
        db.close()


@router.callback_query(StateFilter(AdminStates.withdraws_filter), F.data.startswith("withdraws_filter_"))
async def show_withdraws_list(call: CallbackQuery, state: FSMContext):
    """Показать список заявок с выбранным фильтром"""
    status_filter = call.data.split("_")[-1]
    await show_withdraws_page(call, state, 0, status_filter)


@router.callback_query(F.data.startswith("withdraws_page_"))
async def handle_withdraws_pagination(call: CallbackQuery, state: FSMContext):
    """Обработка пагинации"""
    parts = call.data.split("_")
    page = int(parts[2])
    status_filter = parts[3] if len(parts) > 3 else "all"
    await show_withdraws_page(call, state, page, status_filter)


async def show_withdraws_page(call: CallbackQuery, state: FSMContext, page: int, status_filter: str):
    """Показать страницу заявок на вывод"""
    db = SessionLocal()

    try:
        # Создаем запрос с фильтром
        query = db.query(WithdrawRequest)

        if status_filter != "all":
            query = query.filter(WithdrawRequest.status == status_filter)

        # Общее количество
        total_count = query.count()
        total_pages = (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

        if total_pages == 0:
            await call.message.edit_text(
                f"📉 <b>Заявки на вывод ({status_filter})</b>\n\n"
                "🚫 Заявок не найдено",
                reply_markup=get_withdraw_filter_kb(status_filter)
            )
            return

        # Получаем заявки для текущей страницы
        requests = query.order_by(desc(WithdrawRequest.created_at)).offset(
            page * ITEMS_PER_PAGE
        ).limit(ITEMS_PER_PAGE).all()

        # Формируем текст
        status_names = {
            "pending": "⏳ Ожидают",
            "executed": "✅ Выполнено",
            "auto_paid": "🤖 Автовыплата",
            "declined": "❌ Отклонено",
            "all": "📉 Все заявки"
        }

        text = f"{status_names.get(status_filter, '📉 Заявки')} на вывод\n\n"

        # Добавляем заявки
        for i, req in enumerate(requests, 1):
            user = db.query(User).filter(User.id == req.user_id).first()
            username = f"@{user.username}" if user and user.username else f"ID{user.tg_id if user else 'N/A'}"

            status_emoji = {
                "pending": "⏳",
                "executed": "✅",
                "auto_paid": "🤖",
                "declined": "❌"
            }.get(req.status, "❓")

            # Источник
            source_text = "💰 Баланс" if req.source == "balance" else f"🏦 {req.pool_name or 'Пул'}"

            # Режим (если есть)
            mode_text = ""
            if req.mode:
                mode_text = f" ({req.mode})"

            # Показываем clickable индикатор для pending заявок
            clickable_indicator = " 👁" if req.status == "pending" else ""

            text += (
                f"<b>{page * ITEMS_PER_PAGE + i}.</b> {status_emoji} {username}{clickable_indicator}\n"
                f"{source_text}{mode_text}\n"
                f"💵 ${req.amount_usd:.2f} → ${req.final_amount_usd:.2f}\n"
                f"💳 {req.method}"
            )

            if req.currency:
                text += f" ({req.currency})"

            text += f"\n🕒 {req.created_at.strftime('%d.%m %H:%M')}\n"

            if req.execute_until:
                text += f"⏰ До: {req.execute_until.strftime('%d.%m %H:%M')}\n"

            if req.details and len(req.details) <= 30:
                text += f"📝 <code>{req.details}</code>\n"

            text += "\n"

        # Добавляем информацию о пагинации
        if total_pages > 1:
            text += f"📄 Страница {page + 1} из {total_pages} | Всего: {total_count}"

        # Подсказка для интерактивных заявок
        if any(req.status == "pending" for req in requests):
            text += "\n\n💡 Нажмите кнопку <b>#ID 👁</b> для управления заявкой"

        await call.message.edit_text(
            text,
            reply_markup=get_withdraw_list_kb(page, total_pages, status_filter, requests),
            parse_mode="HTML"
        )
        await state.set_state(AdminStates.withdraws_list)

    finally:
        db.close()


@router.callback_query(F.data == "withdraws_noop")
async def withdraws_noop(call: CallbackQuery):
    """Заглушка для неактивных кнопок"""
    await call.answer()