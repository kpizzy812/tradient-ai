# app/bot/handlers/admin/stats.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta

from app.core.db import SessionLocal
from app.models.users import User
from app.models.investments import Investment
from app.models.deposit_request import DepositRequest
from app.models.withdraw_request import WithdrawRequest
from app.models.income_log import IncomeLog
from app.bot.states.admin import AdminStates
from app.bot.keyboards.admin import get_back_to_stats_kb, get_back_to_menu_kb
from app.services.logic import t

router = Router()


@router.callback_query(StateFilter(AdminStates.stats_menu), F.data == "stats_general")
async def show_general_stats(call: CallbackQuery, state: FSMContext):
    """Общая статистика платформы"""
    db = SessionLocal()

    try:
        # Основные метрики
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.deposit_usd > 0).count()

        total_deposits = db.query(func.sum(User.deposit_usd)).scalar() or 0
        total_profits = db.query(func.sum(User.profit_usd)).scalar() or 0
        total_ref_balance = db.query(func.sum(User.ref_balance)).scalar() or 0

        # Активные инвестиции
        active_investments = db.query(func.sum(Investment.amount_usd)).filter(
            Investment.is_active == True
        ).scalar() or 0

        # Статистика за последние 30 дней
        month_ago = datetime.utcnow() - timedelta(days=30)
        new_users_month = db.query(User).filter(User.created_at >= month_ago).count()

        # Среднее по пользователю
        avg_deposit = total_deposits / max(active_users, 1)
        avg_profit = total_profits / max(active_users, 1)

        text = (
            "📊 <b>Общая статистика платформы</b>\n\n"
            f"👤 <b>Пользователи:</b>\n"
            f"• Всего: {total_users:,}\n"
            f"• Активных: {active_users:,} ({active_users / max(total_users, 1) * 100:.1f}%)\n"
            f"• Новых за месяц: {new_users_month:,}\n\n"

            f"💰 <b>Финансы:</b>\n"
            f"• Общий депозит: ${total_deposits:,.2f}\n"
            f"• Активные инвестиции: ${active_investments:,.2f}\n"
            f"• Прибыль пользователей: ${total_profits:,.2f}\n"
            f"• Реферальные: ${total_ref_balance:,.2f}\n\n"

            f"📈 <b>Средние показатели:</b>\n"
            f"• Депозит на активного: ${avg_deposit:.2f}\n"
            f"• Прибыль на активного: ${avg_profit:.2f}\n"
        )

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Обновить", callback_data="stats_general")],
                [InlineKeyboardButton(text="🔙 К статистике", callback_data="admin_stats")]
            ]
        )

    finally:
        db.close()

    await call.message.edit_text(text, reply_markup=kb)
    await state.set_state(AdminStates.stats_general)


@router.callback_query(StateFilter(AdminStates.stats_menu), F.data == "stats_deposits")
async def show_deposits_stats(call: CallbackQuery, state: FSMContext):
    """Статистика пополнений"""
    db = SessionLocal()

    try:
        # Общая статистика заявок
        total_requests = db.query(DepositRequest).count()
        pending_requests = db.query(DepositRequest).filter(
            DepositRequest.status == "pending"
        ).count()
        approved_requests = db.query(DepositRequest).filter(
            DepositRequest.status == "approved"
        ).count()
        declined_requests = db.query(DepositRequest).filter(
            DepositRequest.status == "declined"
        ).count()

        # Суммы по статусам
        pending_amount = db.query(func.sum(DepositRequest.amount_usd)).filter(
            DepositRequest.status == "pending"
        ).scalar() or 0

        approved_amount = db.query(func.sum(DepositRequest.amount_usd)).filter(
            DepositRequest.status == "approved"
        ).scalar() or 0

        # Статистика по пулам
        pool_stats = db.query(
            DepositRequest.pool_name,
            func.count(DepositRequest.id).label('count'),
            func.sum(DepositRequest.amount_usd).label('total')
        ).filter(
            DepositRequest.status == "approved"
        ).group_by(DepositRequest.pool_name).all()

        # За последние 7 дней
        week_ago = datetime.utcnow() - timedelta(days=7)
        week_deposits = db.query(func.sum(DepositRequest.amount_usd)).filter(
            and_(
                DepositRequest.status == "approved",
                DepositRequest.created_at >= week_ago
            )
        ).scalar() or 0

        # За сегодня
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_deposits = db.query(func.sum(DepositRequest.amount_usd)).filter(
            and_(
                DepositRequest.status == "approved",
                DepositRequest.created_at >= today
            )
        ).scalar() or 0

        pool_lines = "\n".join([
            f"• {pool}: {count} заявок, ${total:,.2f}"
            for pool, count, total in pool_stats
        ])

        text = (
            "📈 <b>Статистика пополнений</b>\n\n"
            f"📋 <b>Заявки:</b>\n"
            f"• Всего: {total_requests:,}\n"
            f"• Ожидают: {pending_requests:,} (${pending_amount:,.2f})\n"
            f"• Одобрено: {approved_requests:,} (${approved_amount:,.2f})\n"
            f"• Отклонено: {declined_requests:,}\n\n"

            f"📊 <b>По периодам:</b>\n"
            f"• Сегодня: ${today_deposits:,.2f}\n"
            f"• За неделю: ${week_deposits:,.2f}\n\n"

            f"🏦 <b>По пулам:</b>\n{pool_lines or '• Нет данных'}\n"
        )

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="⏳ Ожидающие", callback_data="pending_deposits"),
                    InlineKeyboardButton(text="🔄 Обновить", callback_data="stats_deposits")
                ],
                [InlineKeyboardButton(text="🔙 К статистике", callback_data="admin_stats")]
            ]
        )

    finally:
        db.close()

    await call.message.edit_text(text, reply_markup=kb)
    await state.set_state(AdminStates.stats_deposits)


@router.callback_query(StateFilter(AdminStates.stats_menu), F.data == "stats_withdrawals")
async def show_withdrawals_stats(call: CallbackQuery, state: FSMContext):
    """Статистика выводов"""
    db = SessionLocal()

    try:
        # Общая статистика заявок на вывод
        total_requests = db.query(WithdrawRequest).count()
        pending_requests = db.query(WithdrawRequest).filter(
            WithdrawRequest.status == "pending"
        ).count()
        approved_requests = db.query(WithdrawRequest).filter(
            WithdrawRequest.status == "approved"
        ).count()

        # Суммы по статусам
        pending_amount = db.query(func.sum(WithdrawRequest.amount_usd)).filter(
            WithdrawRequest.status == "pending"
        ).scalar() or 0

        approved_amount = db.query(func.sum(WithdrawRequest.final_amount_usd)).filter(
            WithdrawRequest.status == "approved"
        ).scalar() or 0

        # По источникам
        balance_withdrawals = db.query(func.sum(WithdrawRequest.amount_usd)).filter(
            and_(
                WithdrawRequest.source == "balance",
                WithdrawRequest.status == "approved"
            )
        ).scalar() or 0

        investment_withdrawals = db.query(func.sum(WithdrawRequest.amount_usd)).filter(
            and_(
                WithdrawRequest.source == "investment",
                WithdrawRequest.status == "approved"
            )
        ).scalar() or 0

        # По методам вывода
        method_stats = db.query(
            WithdrawRequest.method,
            func.count(WithdrawRequest.id).label('count'),
            func.sum(WithdrawRequest.final_amount_usd).label('total')
        ).filter(
            WithdrawRequest.status == "approved"
        ).group_by(WithdrawRequest.method).all()

        method_lines = "\n".join([
            f"• {method}: {count} шт, ${total:,.2f}"
            for method, count, total in method_stats
        ])

        text = (
            "📉 <b>Статистика выводов</b>\n\n"
            f"📋 <b>Заявки:</b>\n"
            f"• Всего: {total_requests:,}\n"
            f"• Ожидают: {pending_requests:,} (${pending_amount:,.2f})\n"
            f"• Выплачено: {approved_requests:,} (${approved_amount:,.2f})\n\n"

            f"📊 <b>По источникам:</b>\n"
            f"• С баланса: ${balance_withdrawals:,.2f}\n"
            f"• Из инвестиций: ${investment_withdrawals:,.2f}\n\n"

            f"💳 <b>По методам:</b>\n{method_lines or '• Нет данных'}\n"
        )

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="⏳ Ожидающие", callback_data="pending_withdrawals"),
                    InlineKeyboardButton(text="🔄 Обновить", callback_data="stats_withdrawals")
                ],
                [InlineKeyboardButton(text="🔙 К статистике", callback_data="admin_stats")]
            ]
        )

    finally:
        db.close()

    await call.message.edit_text(text, reply_markup=kb)
    await state.set_state(AdminStates.stats_withdrawals)


@router.callback_query(F.data == "pending_deposits")
async def show_pending_deposits(call: CallbackQuery, state: FSMContext):
    """Показать ожидающие пополнения"""
    db = SessionLocal()

    try:
        pending_requests = db.query(DepositRequest).filter(
            DepositRequest.status == "pending"
        ).order_by(DepositRequest.created_at.desc()).limit(10).all()

        if not pending_requests:
            text = "✅ Нет ожидающих заявок на пополнение"
        else:
            lines = []
            for req in pending_requests:
                user = db.query(User).filter(User.id == req.user_id).first()
                username = f"@{user.username}" if user.username else f"ID{user.tg_id}"

                lines.append(
                    f"• {username} | {req.pool_name} | ${req.amount_usd:.2f}\n"
                    f"  {req.created_at.strftime('%d.%m %H:%M')}"
                )

            text = "⏳ <b>Ожидающие пополнения (последние 10):</b>\n\n" + "\n\n".join(lines)

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Обновить", callback_data="pending_deposits")],
                [InlineKeyboardButton(text="🔙 К пополнениям", callback_data="stats_deposits")]
            ]
        )

    finally:
        db.close()

    await call.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data == "pending_withdrawals")
async def show_pending_withdrawals(call: CallbackQuery, state: FSMContext):
    """Показать ожидающие выводы"""
    db = SessionLocal()

    try:
        pending_requests = db.query(WithdrawRequest).filter(
            WithdrawRequest.status == "pending"
        ).order_by(WithdrawRequest.created_at.desc()).limit(10).all()

        if not pending_requests:
            text = "✅ Нет ожидающих заявок на вывод"
        else:
            lines = []
            for req in pending_requests:
                user = db.query(User).filter(User.id == req.user_id).first()
                username = f"@{user.username}" if user.username else f"ID{user.tg_id}"

                source_text = "Баланс" if req.source == "balance" else f"Пул {req.pool_name}"
                mode_text = f" ({req.mode})" if req.mode else ""

                lines.append(
                    f"• {username} | {source_text}{mode_text}\n"
                    f"  ${req.amount_usd:.2f} → ${req.final_amount_usd:.2f} | {req.method}\n"
                    f"  {req.created_at.strftime('%d.%m %H:%M')}"
                )

            text = "⏳ <b>Ожидающие выводы (последние 10):</b>\n\n" + "\n\n".join(lines)

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Обновить", callback_data="pending_withdrawals")],
                [InlineKeyboardButton(text="🔙 К выводам", callback_data="stats_withdrawals")]
            ]
        )

    finally:
        db.close()

    await call.message.edit_text(text, reply_markup=kb)