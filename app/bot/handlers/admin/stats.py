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


@router.callback_query(StateFilter(AdminStates.stats_menu), F.data == "stats_finance")
async def show_finance_stats(call: CallbackQuery, state: FSMContext):
    """Финансовая статистика"""
    db = SessionLocal()

    try:
        # Общие финансовые показатели
        total_deposits = db.query(func.sum(User.deposit_usd)).scalar() or 0
        total_profits = db.query(func.sum(User.profit_usd)).scalar() or 0
        total_ref_balance = db.query(func.sum(User.ref_balance)).scalar() or 0

        # Активные инвестиции
        active_investments = db.query(func.sum(Investment.amount_usd)).filter(
            Investment.is_active == True
        ).scalar() or 0

        # Заявки на вывод
        pending_withdrawals = db.query(func.sum(WithdrawRequest.amount_usd)).filter(
            WithdrawRequest.status == "pending"
        ).scalar() or 0

        completed_withdrawals = db.query(func.sum(WithdrawRequest.final_amount_usd)).filter(
            WithdrawRequest.status.in_(["executed", "auto_paid"])
        ).scalar() or 0

        # Капитализация (общий баланс системы)
        total_system_balance = total_deposits - completed_withdrawals

        # Соотношения
        deposit_to_withdrawal_ratio = (completed_withdrawals / max(total_deposits, 1)) * 100
        profit_to_deposit_ratio = (total_profits / max(total_deposits, 1)) * 100

        text = (
            "💰 <b>Финансовая статистика</b>\n\n"

            f"📈 <b>Поступления:</b>\n"
            f"• Общий депозит: ${total_deposits:,.2f}\n"
            f"• Активные инвестиции: ${active_investments:,.2f}\n\n"

            f"📉 <b>Выплаты:</b>\n"
            f"• Выплачено: ${completed_withdrawals:,.2f}\n"
            f"• Ожидают: ${pending_withdrawals:,.2f}\n"
            f"• Прибыль пользователей: ${total_profits:,.2f}\n"
            f"• Реферальные: ${total_ref_balance:,.2f}\n\n"

            f"📊 <b>Показатели:</b>\n"
            f"• Капитализация: ${total_system_balance:,.2f}\n"
            f"• Коэф. выплат: {deposit_to_withdrawal_ratio:.1f}%\n"
            f"• Доходность: {profit_to_deposit_ratio:.1f}%\n"
        )

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Обновить", callback_data="stats_finance")],
                [InlineKeyboardButton(text="🔙 К статистике", callback_data="admin_stats")]
            ]
        )

    finally:
        db.close()

    await call.message.edit_text(text, reply_markup=kb)
    await state.set_state(AdminStates.stats_finance)


@router.callback_query(StateFilter(AdminStates.stats_menu), F.data == "stats_users")
async def show_users_stats(call: CallbackQuery, state: FSMContext):
    """Статистика пользователей"""
    db = SessionLocal()

    try:
        # Основные показатели
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.deposit_usd > 0).count()

        # По периодам
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        new_today = db.query(User).filter(User.created_at >= today).count()
        new_week = db.query(User).filter(User.created_at >= week_ago).count()
        new_month = db.query(User).filter(User.created_at >= month_ago).count()

        # По сумме депозита
        users_100_plus = db.query(User).filter(User.deposit_usd >= 100).count()
        users_500_plus = db.query(User).filter(User.deposit_usd >= 500).count()
        users_1000_plus = db.query(User).filter(User.deposit_usd >= 1000).count()

        # Средние показатели
        avg_deposit = db.query(func.avg(User.deposit_usd)).filter(User.deposit_usd > 0).scalar() or 0
        avg_profit = db.query(func.avg(User.profit_usd)).filter(User.profit_usd > 0).scalar() or 0

        # Топ-10 пользователей по депозиту
        top_depositors = db.query(User).filter(User.deposit_usd > 0).order_by(
            User.deposit_usd.desc()
        ).limit(5).all()

        top_lines = []
        for i, user in enumerate(top_depositors, 1):
            username = f"@{user.username}" if user.username else f"ID{user.tg_id}"
            top_lines.append(f"{i}. {username} - ${user.deposit_usd:,.2f}")

        text = (
                "👥 <b>Статистика пользователей</b>\n\n"

                f"📊 <b>Общие показатели:</b>\n"
                f"• Всего: {total_users:,}\n"
                f"• Активных: {active_users:,} ({(active_users / max(total_users, 1) * 100):.1f}%)\n\n"

                f"📅 <b>Регистрации:</b>\n"
                f"• Сегодня: {new_today:,}\n"
                f"• За неделю: {new_week:,}\n"
                f"• За месяц: {new_month:,}\n\n"

                f"💰 <b>По депозитам:</b>\n"
                f"• От $100: {users_100_plus:,}\n"
                f"• От $500: {users_500_plus:,}\n"
                f"• От $1000: {users_1000_plus:,}\n\n"

                f"📈 <b>Средние значения:</b>\n"
                f"• Депозит: ${avg_deposit:.2f}\n"
                f"• Прибыль: ${avg_profit:.2f}\n\n"

                f"🏆 <b>Топ-5 по депозиту:</b>\n" + "\n".join(top_lines or ["Нет данных"])
        )

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Обновить", callback_data="stats_users")],
                [InlineKeyboardButton(text="🔙 К статистике", callback_data="admin_stats")]
            ]
        )

    finally:
        db.close()

    await call.message.edit_text(text, reply_markup=kb)
    await state.set_state(AdminStates.stats_users)


@router.callback_query(StateFilter(AdminStates.stats_menu), F.data == "stats_pools")
async def show_pools_stats(call: CallbackQuery, state: FSMContext):
    """Статистика по пулам"""
    db = SessionLocal()

    try:
        from app.core.config import settings

        pool_stats = {}

        for pool_name in settings.POOL_LIMITS.keys():
            # Активные инвестиции в пуле
            active_amount = db.query(func.sum(Investment.amount_usd)).filter(
                and_(Investment.pool_name == pool_name, Investment.is_active == True)
            ).scalar() or 0

            # Количество инвесторов
            investors_count = db.query(Investment.user_id).filter(
                and_(Investment.pool_name == pool_name, Investment.is_active == True)
            ).distinct().count()

            # Всего инвестиций в пул (включая завершенные)
            total_invested = db.query(func.sum(Investment.amount_usd)).filter(
                Investment.pool_name == pool_name
            ).scalar() or 0

            # Заявки на пополнение этого пула
            pending_deposits = db.query(func.sum(DepositRequest.amount_usd)).filter(
                and_(
                    DepositRequest.pool_name == pool_name,
                    DepositRequest.status == "pending"
                )
            ).scalar() or 0

            pool_stats[pool_name] = {
                "active_amount": active_amount,
                "investors": investors_count,
                "total_invested": total_invested,
                "pending": pending_deposits
            }

        text = "🏦 <b>Статистика по пулам</b>\n\n"

        for pool_name, stats in pool_stats.items():
            limits = settings.POOL_LIMITS.get(pool_name, {})
            yield_range = settings.POOL_YIELD_RANGES.get(pool_name, (0, 0))
            coeff = settings.POOL_COEFFICIENTS.get(pool_name, 1.0)

            # Процент заполненности
            max_capacity = limits.get("max", 1) * stats["investors"] if stats["investors"] > 0 else limits.get("max", 1)
            fill_percent = (stats["active_amount"] / max_capacity * 100) if max_capacity > 0 else 0

            text += (
                f"<b>{pool_name}:</b>\n"
                f"• Активно: ${stats['active_amount']:,.2f}\n"
                f"• Инвесторов: {stats['investors']:,}\n"
                f"• Всего вложено: ${stats['total_invested']:,.2f}\n"
                f"• Ожидают: ${stats['pending']:,.2f}\n"
                f"• Доходность: {yield_range[0]:.1f}%-{yield_range[1]:.1f}% (x{coeff})\n"
                f"• Заполненность: {fill_percent:.1f}%\n\n"
            )

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Обновить", callback_data="stats_pools")],
                [InlineKeyboardButton(text="🔙 К статистике", callback_data="admin_stats")]
            ]
        )

    finally:
        db.close()

    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await state.set_state(AdminStates.stats_pools)


@router.callback_query(StateFilter(AdminStates.stats_menu), F.data == "stats_period")
async def show_period_selection(call: CallbackQuery, state: FSMContext):
    """Показать выбор периода для статистики"""
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Сегодня", callback_data="period_today"),
                InlineKeyboardButton(text="📅 Вчера", callback_data="period_yesterday")
            ],
            [
                InlineKeyboardButton(text="📅 7 дней", callback_data="period_week"),
                InlineKeyboardButton(text="📅 30 дней", callback_data="period_month")
            ],
            [
                InlineKeyboardButton(text="📅 90 дней", callback_data="period_quarter"),
                InlineKeyboardButton(text="📅 Год", callback_data="period_year")
            ],
            [
                InlineKeyboardButton(text="🔙 К статистике", callback_data="admin_stats")
            ]
        ]
    )

    await call.message.edit_text(
        "📅 <b>Статистика за период</b>\n\n"
        "Выберите период для анализа:",
        reply_markup=kb
    )
    await state.set_state(AdminStates.stats_period)


@router.callback_query(StateFilter(AdminStates.stats_period), F.data.startswith("period_"))
async def show_period_stats(call: CallbackQuery, state: FSMContext):
    """Показать статистику за выбранный период"""
    period = call.data.split("_")[1]

    db = SessionLocal()

    try:
        # Определяем временные рамки
        now = datetime.utcnow()

        if period == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            period_name = "сегодня"
        elif period == "yesterday":
            start_date = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            period_name = "вчера"
        elif period == "week":
            start_date = now - timedelta(days=7)
            period_name = "за 7 дней"
        elif period == "month":
            start_date = now - timedelta(days=30)
            period_name = "за 30 дней"
        elif period == "quarter":
            start_date = now - timedelta(days=90)
            period_name = "за 90 дней"
        elif period == "year":
            start_date = now - timedelta(days=365)
            period_name = "за год"
        else:
            start_date = now - timedelta(days=7)
            period_name = "за 7 дней"

        # Для периодов кроме "вчера" конечная дата = сейчас
        if period != "yesterday":
            end_date = now

        # Регистрации пользователей
        new_users = db.query(User).filter(
            User.created_at >= start_date,
            User.created_at <= end_date
        ).count()

        # Пополнения
        deposits_filter = and_(
            DepositRequest.created_at >= start_date,
            DepositRequest.created_at <= end_date,
            DepositRequest.status == "approved"
        )
        deposits_count = db.query(DepositRequest).filter(deposits_filter).count()
        deposits_amount = db.query(func.sum(DepositRequest.amount_usd)).filter(deposits_filter).scalar() or 0

        # Выводы
        withdraws_filter = and_(
            WithdrawRequest.created_at >= start_date,
            WithdrawRequest.created_at <= end_date,
            WithdrawRequest.status.in_(["executed", "auto_paid"])
        )
        withdraws_count = db.query(WithdrawRequest).filter(withdraws_filter).count()
        withdraws_amount = db.query(func.sum(WithdrawRequest.final_amount_usd)).filter(withdraws_filter).scalar() or 0

        # Активность пользователей (кто делал депозиты)
        active_users = db.query(DepositRequest.user_id).filter(deposits_filter).distinct().count()

        # Соотношения
        net_flow = deposits_amount - withdraws_amount
        avg_deposit = deposits_amount / max(deposits_count, 1)
        avg_withdraw = withdraws_amount / max(withdraws_count, 1)

        text = (
            f"📊 <b>Статистика {period_name}</b>\n\n"
            f"📅 <b>Период:</b> {start_date.strftime('%d.%m.%Y')}"
        )

        if period == "yesterday":
            text += f" - {end_date.strftime('%d.%m.%Y')}"
        elif period == "today":
            text += f" - сейчас"
        else:
            text += f" - {end_date.strftime('%d.%m.%Y')}"

        text += (
            f"\n\n👥 <b>Пользователи:</b>\n"
            f"• Новых регистраций: {new_users:,}\n"
            f"• Активных (с депозитами): {active_users:,}\n\n"

            f"📈 <b>Пополнения:</b>\n"
            f"• Количество: {deposits_count:,}\n"
            f"• Сумма: ${deposits_amount:,.2f}\n"
            f"• Средний чек: ${avg_deposit:.2f}\n\n"

            f"📉 <b>Выводы:</b>\n"
            f"• Количество: {withdraws_count:,}\n"
            f"• Сумма: ${withdraws_amount:,.2f}\n"
            f"• Средний чек: ${avg_withdraw:.2f}\n\n"

            f"💰 <b>Итоги:</b>\n"
            f"• Чистый приток: ${net_flow:,.2f}\n"
            f"• Коэффициент оборота: {(withdraws_amount / max(deposits_amount, 1)):.2f}\n"
        )

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔄 Обновить", callback_data=f"period_{period}"),
                    InlineKeyboardButton(text="📅 Другой период", callback_data="stats_period")
                ],
                [InlineKeyboardButton(text="🔙 К статистике", callback_data="admin_stats")]
            ]
        )

    finally:
        db.close()

    await call.message.edit_text(text, reply_markup=kb)


# Добавляем новое состояние для финансов
@router.callback_query(F.data == "stats_finance")
async def show_finance_stats_redirect(call: CallbackQuery, state: FSMContext):
    """Редирект для финансовой статистики из любого состояния"""
    await state.set_state(AdminStates.stats_menu)
    await show_finance_stats(call, state)