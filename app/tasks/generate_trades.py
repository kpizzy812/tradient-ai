# app/tasks/improved_trade_scheduler.py

import asyncio
import random
from datetime import datetime, timedelta
import pytz
from app.services.trade_generator import generate_smart_trade, get_daily_progress_report
from app.services.yielding import (
    get_current_day_progress,
    emergency_yield_correction,
    generate_daily_yield_report
)
from app.bot.handlers.trades import post_last_trade
from app.core.logger import logger
from app.core.config import settings

msk = pytz.timezone("Europe/Moscow")


class SmartTradeScheduler:
    def __init__(self, bot):
        self.bot = bot
        self.last_trade_time = None
        self.correction_attempts = 0
        self.daily_stats = {}

    async def calculate_next_trade_delay(self):
        """
        Умный расчет задержки до следующей сделки
        """
        progress = get_current_day_progress()

        if not progress or progress['status'] != 'active':
            return 30 * 60  # 30 минут если день не активен

        hours_left = progress['hours_left']
        current_yield = progress['yield']
        trades_count = progress['trades']

        # Базовая частота: 20-35 сделок в день = примерно 1 сделка в 40-70 минут
        base_delay_minutes = random.randint(25, 65)

        # Корректировки по ситуации
        if hours_left <= 3:
            # В последние 3 часа учащаем сделки
            if current_yield < 2.0:
                # Критически мало - делаем часто
                base_delay_minutes = random.randint(15, 30)
            elif current_yield > 5.0:
                # Критически много - реже
                base_delay_minutes = random.randint(45, 90)
            else:
                # В норме - умеренно
                base_delay_minutes = random.randint(20, 40)

        elif hours_left <= 6:
            # В предпоследние часы подготавливаемся
            if current_yield < 1.5 or current_yield > 6.0:
                base_delay_minutes = random.randint(20, 45)

        # Если слишком много сделок за короткое время - увеличиваем паузы
        if trades_count > 25 and hours_left > 8:
            base_delay_minutes += 20

        delay_seconds = base_delay_minutes * 60

        logger.info(
            f"[SCHEDULER] ⏰ Следующая сделка через {base_delay_minutes} мин "
            f"(доходность: {current_yield:.2f}%, осталось: {hours_left:.1f}ч)"
        )

        return delay_seconds

    async def smart_trade_loop(self):
        """
        Основной цикл генерации сделок с умной логикой
        """
        logger.info("🤖 Умный планировщик сделок запущен")

        while True:
            try:
                # Проверяем нужно ли генерировать сделку
                progress = get_current_day_progress()

                if not progress or progress['status'] != 'active':
                    logger.debug("[SCHEDULER] 📅 Торговый день неактивен")
                    await asyncio.sleep(10 * 60)  # 10 минут
                    continue

                # Генерируем сделку
                trade_id = generate_smart_trade()

                if trade_id:
                    # Публикуем сделку
                    try:
                        await post_last_trade(self.bot)
                        logger.success(f"[SCHEDULER] ✅ Сделка #{trade_id} опубликована")
                        self.last_trade_time = datetime.utcnow()
                    except Exception as e:
                        logger.error(f"[SCHEDULER] ❌ Ошибка публикации сделки: {e}")

                else:
                    logger.warning("[SCHEDULER] ⚠️ Сделка не была создана")

                # Рассчитываем задержку до следующей сделки
                delay = await self.calculate_next_trade_delay()
                await asyncio.sleep(delay)

            except Exception as e:
                logger.error(f"[SCHEDULER] ❌ Ошибка в цикле сделок: {e}")
                await asyncio.sleep(5 * 60)  # 5 минут при ошибке

    async def correction_monitor(self):
        """
        Мониторинг и коррекция доходности
        """
        logger.info("🎯 Монитор коррекции доходности запущен")

        while True:
            try:
                progress = get_current_day_progress()

                if not progress or progress['status'] != 'active':
                    await asyncio.sleep(15 * 60)  # 15 минут
                    continue

                hours_left = progress['hours_left']
                current_yield = progress['yield']

                # Проверяем нужна ли коррекция
                needs_correction = False
                correction_type = None

                if hours_left <= 2:  # За 2 часа до конца
                    if current_yield < 1.8:
                        needs_correction = True
                        correction_type = "URGENT_PROFIT"
                    elif current_yield > 5.5:
                        needs_correction = True
                        correction_type = "URGENT_LOSS"
                elif hours_left <= 4:  # За 4 часа до конца
                    if current_yield < 1.5:
                        needs_correction = True
                        correction_type = "EARLY_PROFIT"
                    elif current_yield > 6.0:
                        needs_correction = True
                        correction_type = "EARLY_LOSS"

                if needs_correction and self.correction_attempts < 3:
                    logger.warning(
                        f"[CORRECTION] 🚨 Нужна коррекция {correction_type}: "
                        f"{current_yield:.2f}% при {hours_left:.1f}ч до конца"
                    )

                    success, message = emergency_yield_correction()
                    self.correction_attempts += 1

                    if success:
                        logger.success(f"[CORRECTION] ✅ {message}")

                        # Уведомляем админов
                        for admin_id in settings.ADMIN_TG_IDS:
                            try:
                                await self.bot.send_message(
                                    admin_id,
                                    f"⚡ Автокоррекция доходности\n\n"
                                    f"Было: {current_yield:.2f}%\n"
                                    f"Время до конца: {hours_left:.1f}ч\n"
                                    f"Действие: {message}"
                                )
                            except:
                                pass
                    else:
                        logger.error(f"[CORRECTION] ❌ {message}")

                await asyncio.sleep(20 * 60)  # Проверяем каждые 20 минут

            except Exception as e:
                logger.error(f"[CORRECTION] ❌ Ошибка монитора коррекции: {e}")
                await asyncio.sleep(10 * 60)

    async def daily_report_sender(self):
        """
        Отправка ежедневных отчетов админам
        """
        logger.info("📊 Отправщик отчетов запущен")

        last_report_date = None

        while True:
            try:
                now_msk = datetime.now(msk)
                today = now_msk.date()

                # Отправляем отчет в 17:30 МСК (за 30 минут до начисления)
                if (now_msk.hour == 17 and 30 <= now_msk.minute <= 35 and
                        last_report_date != today):

                    last_report_date = today

                    report = generate_daily_yield_report()

                    for admin_id in settings.ADMIN_TG_IDS:
                        try:
                            await self.bot.send_message(
                                admin_id,
                                f"📊 **ЕЖЕДНЕВНЫЙ ОТЧЕТ**\n\n{report}",
                                parse_mode="Markdown"
                            )
                        except Exception as e:
                            logger.error(f"Ошибка отправки отчета админу {admin_id}: {e}")

                await asyncio.sleep(60)  # Проверяем каждую минуту

            except Exception as e:
                logger.error(f"[REPORTS] ❌ Ошибка отправки отчетов: {e}")
                await asyncio.sleep(5 * 60)


# Новые админ-команды для улучшенного контроля
async def admin_force_trade_now(bot, admin_id, target_pct=None):
    """Создать сделку сейчас с опциональным целевым процентом"""
    try:
        if target_pct is not None:
            from app.services.trade_generator import force_correction_trade
            trade_id = force_correction_trade(float(target_pct))
        else:
            trade_id = generate_smart_trade()

        if trade_id:
            await post_last_trade(bot)
            await bot.send_message(admin_id, f"✅ Сделка #{trade_id} создана и опубликована")
        else:
            await bot.send_message(admin_id, "❌ Не удалось создать сделку")

    except Exception as e:
        await bot.send_message(admin_id, f"❌ Ошибка: {e}")


async def admin_day_status(bot, admin_id):
    """Подробный статус текущего дня"""
    try:
        report, stats = get_daily_progress_report()

        await bot.send_message(
            admin_id,
            report,
            parse_mode="Markdown"
        )

    except Exception as e:
        await bot.send_message(admin_id, f"❌ Ошибка получения статуса: {e}")


async def admin_force_correction(bot, admin_id):
    """Принудительная коррекция доходности"""
    try:
        success, message = emergency_yield_correction()

        if success:
            await bot.send_message(admin_id, f"✅ Коррекция выполнена: {message}")
        else:
            await bot.send_message(admin_id, f"❌ Коррекция не удалась: {message}")

    except Exception as e:
        await bot.send_message(admin_id, f"❌ Ошибка коррекции: {e}")


async def admin_system_health(bot, admin_id):
    """Проверка здоровья всей системы"""
    try:
        from app.services.yielding import validate_yield_system, get_recent_yields

        is_healthy, health_status = validate_yield_system()
        recent = get_recent_yields(5)

        status_icon = "✅" if is_healthy else "⚠️"

        report = (
            f"🏥 **ЗДОРОВЬЕ СИСТЕМЫ** {status_icon}\n\n"
            f"📊 Проверено дней: {health_status.get('days_checked', 0)}\n"
            f"✅ Дней в норме: {health_status.get('good_days', 0)}\n"
            f"📈 Средняя доходность: {health_status.get('avg_yield', 0):.2f}%\n"
            f"🎯 Индекс здоровья: {health_status.get('health_score', 0):.1%}\n\n"
            f"**Последние 5 дней:**\n"
        )

        for date, pct in recent:
            emoji = "✅" if 2.0 <= pct <= 5.0 else "⚠️"
            report += f"{emoji} {date}: {pct}%\n"

        if health_status.get('problems'):
            report += f"\n**Проблемы:**\n"
            for problem in health_status['problems'][:3]:
                report += f"• {problem}\n"

        await bot.send_message(admin_id, report, parse_mode="Markdown")

    except Exception as e:
        await bot.send_message(admin_id, f"❌ Ошибка проверки здоровья: {e}")


# Интеграция с основным планировщиком
async def start_improved_trading_system(bot):
    """
    Запуск улучшенной системы торговли
    """
    scheduler = SmartTradeScheduler(bot)

    # Запускаем все компоненты системы
    tasks = [
        scheduler.smart_trade_loop(),
        scheduler.correction_monitor(),
        scheduler.daily_report_sender()
    ]

    logger.success("🚀 Улучшенная система торговли запущена")

    await asyncio.gather(*tasks)