# Добавить в app/bot/handlers/admin/yield_management.py

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from app.core.config import settings
from app.core.logger import logger
from datetime import datetime

router = Router()


@router.message(Command("yield_status"))
async def cmd_yield_status(msg: Message):
    """Проверка статуса системы доходности"""
    if msg.from_user.id not in settings.ADMIN_TG_IDS:
        return

    from app.bot.handlers.yield_report import admin_check_yield_system
    await admin_check_yield_system(msg.bot, msg.from_user.id)


@router.message(Command("yield_post"))
async def cmd_yield_post(msg: Message):
    """Принудительная публикация поста о доходности"""
    if msg.from_user.id not in settings.ADMIN_TG_IDS:
        return

    from app.bot.handlers.yield_report import admin_force_yield_post
    await admin_force_yield_post(msg.bot, msg.from_user.id)


@router.message(Command("yield_manual"))
async def cmd_yield_manual(msg: Message):
    """Ручная публикация с заданными параметрами
    Формат: /yield_manual 2025-06-10 3.5
    """
    if msg.from_user.id not in settings.ADMIN_TG_IDS:
        return

    try:
        parts = msg.text.split()
        if len(parts) != 3:
            await msg.answer("❌ Формат: /yield_manual YYYY-MM-DD процент\nПример: /yield_manual 2025-06-10 3.5")
            return

        date_str = parts[1]
        percent = float(parts[2])

        if not (0 <= percent <= 15):
            await msg.answer("❌ Процент должен быть от 0 до 15")
            return

        from app.bot.handlers.yield_report import admin_force_yield_post
        await admin_force_yield_post(msg.bot, msg.from_user.id, date_str, percent)

    except ValueError:
        await msg.answer("❌ Неверный формат. Пример: /yield_manual 2025-06-10 3.5")
    except Exception as e:
        await msg.answer(f"❌ Ошибка: {e}")


@router.message(Command("trade_generate"))
async def cmd_trade_generate(msg: Message):
    """Принудительная генерация трейда"""
    if msg.from_user.id not in settings.ADMIN_TG_IDS:
        return

    try:
        from app.services.trade_generator import generate_fake_trade
        from app.bot.handlers.trades import post_last_trade

        await msg.answer("🔄 Генерирую трейд...")

        trade_id = generate_fake_trade()

        if trade_id:
            await post_last_trade(msg.bot)
            await msg.answer(f"✅ Трейд #{trade_id} создан и опубликован")
        else:
            await msg.answer("❌ Не удалось создать трейд")

    except Exception as e:
        logger.error(f"Ошибка генерации трейда: {e}")
        await msg.answer(f"❌ Ошибка: {e}")


@router.message(Command("yield_routine"))
async def cmd_yield_routine(msg: Message):
    """Запуск полной рутины доходности (генерация + пост)"""
    if msg.from_user.id not in settings.ADMIN_TG_IDS:
        return

    try:
        from app.bot.handlers.yield_report import daily_yield_routine

        await msg.answer("🔄 Запускаю рутину доходности...")

        success = await daily_yield_routine(msg.bot)

        if success:
            await msg.answer("✅ Рутина выполнена успешно")
        else:
            await msg.answer("❌ Ошибка в рутине")

    except Exception as e:
        logger.error(f"Ошибка рутины: {e}")
        await msg.answer(f"❌ Ошибка: {e}")


@router.message(Command("day_stats"))
async def cmd_day_stats(msg: Message):
    """Статистика по текущему торговому дню"""
    if msg.from_user.id not in settings.ADMIN_TG_IDS:
        return

    try:
        from app.services.trade_generator import calculate_daily_stats
        from app.core.db import SessionLocal

        db = SessionLocal()
        stats = calculate_daily_stats(db)
        db.close()

        hours_left = stats['time_left_seconds'] / 3600

        report = (
            f"📊 <b>Статистика торгового дня:</b>\n\n"
            f"💰 <b>Доходность:</b> {stats['total_pct']:.2f}%\n"
            f"📈 <b>Сделок:</b> {stats['total_trades']}\n"
            f"✅ <b>Винрейт:</b> {stats['winrate']:.1%}\n"
            f"⏰ <b>До конца:</b> {hours_left:.1f}ч\n"
            f"🎯 <b>Цель:</b> 2.0-5.0%"
        )

        await msg.answer(report, parse_mode="HTML")

    except Exception as e:
        await msg.answer(f"❌ Ошибка: {e}")


# Автоматическая диагностика
async def auto_diagnostic_check(bot):
    """Автоматическая проверка системы (можно запускать по расписанию)"""
    try:
        from app.services.yielding import validate_system_health, get_recent_yields
        from app.services.trade_generator import calculate_daily_stats
        from app.core.db import SessionLocal

        # Проверяем здоровье системы
        is_healthy = validate_system_health()

        if not is_healthy:
            # Уведомляем админов о проблемах
            recent = get_recent_yields(3)
            problems = []

            for date, pct in recent:
                if pct < 1.5:
                    problems.append(f"{date}: {pct}% (низко)")
                elif pct > 7.0:
                    problems.append(f"{date}: {pct}% (высоко)")

            alert = f"⚠️ <b>Проблемы с системой доходности:</b>\n\n"
            alert += "\n".join(problems)
            alert += f"\n\n💡 Возможно нужно скорректировать генерацию трейдов"

            for admin_id in settings.ADMIN_TG_IDS:
                try:
                    await bot.send_message(admin_id, alert, parse_mode="HTML")
                except:
                    pass

        # Проверяем текущий день
        db = SessionLocal()
        stats = calculate_daily_stats(db)
        db.close()

        current_pct = stats['total_pct']
        hours_left = stats['time_left_seconds'] / 3600

        # Предупреждаем если день идет плохо
        if hours_left < 4 and (current_pct < 1.0 or current_pct > 6.0):
            warning = (
                f"⚠️ <b>Внимание: проблемы с текущим днем</b>\n\n"
                f"💰 Доходность: {current_pct:.2f}%\n"
                f"⏰ Осталось: {hours_left:.1f}ч\n"
                f"🎯 Цель: 2.0-5.0%"
            )

            for admin_id in settings.ADMIN_TG_IDS:
                try:
                    await bot.send_message(admin_id, warning, parse_mode="HTML")
                except:
                    pass

    except Exception as e:
        logger.error(f"Ошибка автодиагностики: {e}")