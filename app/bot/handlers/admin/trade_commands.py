# app/bot/handlers/admin/trade_commands.py - НОВЫЙ ФАЙЛ
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from app.core.config import settings
from app.services.smart_trade_generator import generate_smart_trade, get_current_day_stats
from app.services.yield_finalization import finalize_daily_yield
from app.bot.handlers.trades import post_last_trade
from app.bot.handlers.yield_report import post_daily_yield

router = Router()


@router.message(Command("trade_now"))
async def cmd_trade_now(msg: Message):
    """Сгенерировать трейд сейчас"""
    if msg.from_user.id not in settings.ADMIN_TG_IDS:
        return

    await msg.answer("🔄 Генерирую трейд...")

    try:
        trade_id = generate_smart_trade()

        if trade_id:
            await post_last_trade(msg.bot)
            await msg.answer(f"✅ Трейд #{trade_id} создан и опубликован")
        else:
            await msg.answer("❌ Не удалось создать трейд")

    except Exception as e:
        await msg.answer(f"❌ Ошибка: {e}")


@router.message(Command("trade_stats"))
async def cmd_trade_stats(msg: Message):
    """Статистика текущего торгового дня"""
    if msg.from_user.id not in settings.ADMIN_TG_IDS:
        return

    try:
        stats = get_current_day_stats()
        target_min, target_max = settings.DAILY_YIELD_RANGE

        if stats['is_active']:
            status = "🟢 АКТИВЕН"
            if target_min <= stats['current_yield'] <= target_max:
                yield_status = "✅ В ДИАПАЗОНЕ"
            elif stats['current_yield'] < target_min:
                yield_status = f"⚠️ НИЖЕ ({target_min - stats['current_yield']:.2f}%)"
            else:
                yield_status = f"⚠️ ВЫШЕ (+{stats['current_yield'] - target_max:.2f}%)"
        else:
            status = "🔴 НЕАКТИВЕН"
            yield_status = "—"

        report = (
            f"📊 <b>Статистика торгового дня</b>\n\n"
            f"🔄 <b>Статус:</b> {status}\n"
            f"💰 <b>Доходность:</b> {stats['current_yield']:.2f}%\n"
            f"🎯 <b>Целевой диапазон:</b> {target_min}-{target_max}%\n"
            f"📈 <b>Статус:</b> {yield_status}\n"
            f"📊 <b>Трейдов:</b> {stats['trades_count']}\n"
            f"⏰ <b>Времени до финализации:</b> {stats['hours_left']:.1f}ч"
        )

        await msg.answer(report, parse_mode="HTML")

    except Exception as e:
        await msg.answer(f"❌ Ошибка: {e}")


@router.message(Command("yield_finalize"))
async def cmd_yield_finalize(msg: Message):
    """Принудительная финализация доходности"""
    if msg.from_user.id not in settings.ADMIN_TG_IDS:
        return

    await msg.answer("🔄 Финализирую доходность...")

    try:
        yield_pct = finalize_daily_yield()

        if yield_pct is not None:
            success = await post_daily_yield(msg.bot)

            if success:
                await msg.answer(f"✅ Финализация завершена: {yield_pct}%")
            else:
                await msg.answer(f"⚠️ Доходность записана ({yield_pct}%), но ошибка публикации поста")
        else:
            await msg.answer("❌ Ошибка финализации")

    except Exception as e:
        await msg.answer(f"❌ Ошибка: {e}")