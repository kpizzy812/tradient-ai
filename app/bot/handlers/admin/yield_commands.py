# app/bot/handlers/admin/yield_commands.py - НОВЫЙ ФАЙЛ
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from app.core.config import settings
from app.core.logger import logger
from app.tasks.yield_distributor import distribute_full_yield
from datetime import date, datetime
import pytz

router = Router()

msk = pytz.timezone("Europe/Moscow")


@router.message(Command("yield_users"))
async def cmd_yield_users(msg: Message):
    """Ручное начисление доходности пользователям"""
    if msg.from_user.id not in settings.ADMIN_TG_IDS:
        return

    await msg.answer("🔄 Запускаю начисление доходности...")

    try:
        await distribute_full_yield(msg.bot)
        await msg.answer("✅ Начисление доходности завершено успешно")
    except Exception as e:
        logger.error(f"Ошибка ручного начисления: {e}")
        await msg.answer(f"❌ Ошибка при начислении: {e}")


@router.message(Command("yield_info"))
async def cmd_yield_info(msg: Message):
    """Информация о системе начисления"""
    if msg.from_user.id not in settings.ADMIN_TG_IDS:
        return

    now_msk = datetime.now(msk)
    today = date.today()

    # Проверяем последнее начисление
    from app.core.db import SessionLocal
    from app.models.income_log import IncomeLog
    from sqlalchemy import func

    db = SessionLocal()
    try:
        # Последнее начисление
        last_income = db.query(IncomeLog).order_by(IncomeLog.date.desc()).first()

        # Начисления за сегодня
        today_total = db.query(func.sum(IncomeLog.amount_usd)).filter(
            IncomeLog.date == today
        ).scalar() or 0.0

        today_users = db.query(func.count(func.distinct(IncomeLog.user_id))).filter(
            IncomeLog.date == today
        ).scalar() or 0

        info = (
            f"💰 <b>Система начисления доходности</b>\n\n"
            f"🕐 <b>Время начисления:</b> {settings.YIELD_TIME_UTC_HOUR + 3}:00 МСК\n"
            f"📅 <b>Сейчас:</b> {now_msk.strftime('%H:%M')} МСК\n\n"
            f"<b>Последнее начисление:</b>\n"
            f"📅 Дата: {last_income.date if last_income else 'Нет данных'}\n\n"
            f"<b>За сегодня ({today.strftime('%d.%m.%Y')}):</b>\n"
            f"👥 Пользователей: {today_users}\n"
            f"💵 Сумма: ${today_total:.2f}\n\n"
            f"<b>Пулы и диапазоны:</b>\n"
        )

        for pool_name, yield_range in settings.POOL_YIELD_RANGES.items():
            coeff = settings.POOL_COEFFICIENTS.get(pool_name, 1.0)
            final_min = yield_range[0] * coeff
            final_max = yield_range[1] * coeff
            info += f"• {pool_name}: {final_min:.1f}-{final_max:.1f}%\n"

        await msg.answer(info, parse_mode="HTML")

    finally:
        db.close()