from aiogram import Bot
from datetime import date, datetime
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.investments import Investment
from app.models.users import User
from app.models.income_log import IncomeLog
from app.core.config import settings
from app.services.logic import t
from app.core.logger import logger
import random
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import pytz

msk = pytz.timezone("Europe/Moscow")


async def distribute_full_yield(bot: Bot):
    """Начисление доходности всем пользователям"""
    today = date.today()
    now_msk = datetime.now(msk)

    logger.info(f"[{today}] 💰 Начинаем начисление доходности...")

    db: Session = SessionLocal()

    try:
        # Получаем все активные инвестиции (созданные до сегодняшнего дня)
        investments = db.query(Investment).filter(
            Investment.is_active == True,
            Investment.created_at < datetime(today.year, today.month, today.day)
        ).all()

        if not investments:
            logger.warning(f"[{today}] ⚠️ Нет активных инвестиций для начисления")
            return

        logger.info(f"[{today}] 📊 Найдено активных инвестиций: {len(investments)}")

        total_distributed = 0.0
        user_profits = {}  # {tg_id: {"lang": "ru", "total": 0.0, "pools": {...}}}

        # Обрабатываем каждую инвестицию
        for inv in investments:
            # Получаем параметры пула
            coeff = settings.POOL_COEFFICIENTS.get(inv.pool_name, 1.0)
            yield_range = settings.POOL_YIELD_RANGES.get(inv.pool_name)

            if yield_range is None:
                logger.warning(f"[{today}] ⚠️ Неизвестный пул: {inv.pool_name}")
                continue

            # Генерируем случайный процент в диапазоне пула
            base_percent = random.uniform(*yield_range)
            final_percent = round(base_percent * coeff, 2)

            # Получаем пользователя
            user = db.query(User).filter(User.id == inv.user_id).first()
            if not user:
                logger.warning(f"[{today}] ⚠️ Пользователь не найден: user_id={inv.user_id}")
                continue

            # Рассчитываем доход
            income = round(inv.amount_usd * final_percent / 100, 4)

            # Готовим данные для уведомления
            if user.tg_id not in user_profits:
                user_profits[user.tg_id] = {
                    "lang": user.lang,
                    "total": 0.0,
                    "pools": {}
                }

            user_profits[user.tg_id]["total"] += income

            if inv.pool_name not in user_profits[user.tg_id]["pools"]:
                user_profits[user.tg_id]["pools"][inv.pool_name] = {
                    "percent": final_percent,
                    "income": 0.0
                }
            user_profits[user.tg_id]["pools"][inv.pool_name]["income"] += income

            # Начисляем доход (автореинвест или на баланс)
            if user.auto_reinvest_flags and user.auto_reinvest_flags.get(inv.pool_name):
                # Автореинвест
                inv.amount_usd += income
                inv.reinvested = (inv.reinvested or 0) + income
                logger.debug(f"[{today}] ♻️ Автореинвест: user_id={user.id}, pool={inv.pool_name}, +{income}")
            else:
                # На баланс
                user.profit_usd += income
                logger.debug(f"[{today}] 💰 На баланс: user_id={user.id}, +{income}")

            # Записываем в лог доходов
            income_log = IncomeLog(
                user_id=user.id,
                amount_usd=income,
                pool_name=inv.pool_name,
                date=today
            )
            db.add(income_log)

            total_distributed += income

        # Сохраняем все изменения
        db.commit()

        logger.success(
            f"[{today}] ✅ Начисление завершено. Пользователей: {len(user_profits)}, сумма: ${total_distributed:.2f}")

        # Отправляем уведомления пользователям
        notifications_sent = 0
        for tg_id, info in user_profits.items():
            try:
                await send_yield_notification(bot, tg_id, info, today)
                notifications_sent += 1
            except Exception as e:
                logger.warning(f"[{today}] ⚠️ Ошибка отправки уведомления {tg_id}: {e}")

        logger.info(f"[{today}] 📱 Уведомлений отправлено: {notifications_sent}/{len(user_profits)}")

        # Уведомляем админов
        await send_admin_summary(bot, today, len(user_profits), total_distributed, notifications_sent)

    except Exception as e:
        logger.error(f"[{today}] ❌ Критическая ошибка при начислении: {e}")
        db.rollback()
        raise
    finally:
        db.close()


async def send_yield_notification(bot: Bot, tg_id: int, info: dict, today: date):
    """Отправляет уведомление о начислении пользователю"""
    lang = info["lang"]

    # Формируем текст по пулам
    pools_lines = []
    for pool_name, details in info["pools"].items():
        percent_str = f"{details['percent']:.2f}%"
        income_str = f"${details['income']:.2f}"
        pools_lines.append(f"{pool_name}: {percent_str} ({income_str})")

    pools_text = "\n".join(pools_lines)

    # Заменяем плейсхолдер в тексте
    text = t("yield_notify", lang).replace("{amount}", pools_text)

    # Кнопка реинвестирования
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("reinvest_button", lang),
                    callback_data="reinvest_start"
                )
            ]
        ]
    )

    # Отправляем с картинкой
    photo_url = "https://i.ibb.co/mrrB7XWh/Chat-GPT-Image-31-2025-15-35-19.jpg"
    await bot.send_photo(
        chat_id=tg_id,
        photo=photo_url,
        caption=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


async def send_admin_summary(bot: Bot, today: date, users_count: int, total_amount: float, notifications_sent: int):
    """Отправляет сводку админам"""
    now_msk = datetime.now(msk)
    
    summary = (
        f"💰 <b>Начисление доходности завершено</b>\n\n"
        f"📅 <b>Дата:</b> {today.strftime('%d.%m.%Y')}\n"
        f"🕐 <b>Время:</b> {now_msk.strftime('%H:%M')} МСК\n"
        f"👥 <b>Пользователей:</b> {users_count}\n"
        f"💵 <b>Всего начислено:</b> ${total_amount:.2f}\n"
        f"📱 <b>Уведомлений:</b> {notifications_sent}/{users_count}\n"
        f"📊 <b>Средняя сумма:</b> ${total_amount / users_count:.2f}" if users_count > 0 else ""
    )

    for admin_id in settings.ADMIN_TG_IDS:
        try:
            await bot.send_message(admin_id, summary, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Ошибка отправки сводки админу {admin_id}: {e}")