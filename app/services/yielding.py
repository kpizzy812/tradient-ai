from datetime import datetime, timedelta, time as dtime
from sqlalchemy import select, func
from app.models.trades import Trade
from app.models.daily_yield import DailyYield
from app.core.db import SessionLocal
from app.core.logger import logger


def get_trading_day_range(target_date=None):
    """
    Возвращает диапазон торгового дня (18:00 МСК предыдущего дня - 18:00 МСК текущего дня)
    """
    if target_date is None:
        # Для текущего момента
        now_msk = datetime.utcnow() + timedelta(hours=3)

        if now_msk.hour >= 18:
            # После 18:00 - берем сегодняшний торговый день
            target_date = now_msk.date()
        else:
            # До 18:00 - берем вчерашний торговый день
            target_date = (now_msk - timedelta(days=1)).date()

    # Торговый день: с 18:00 предыдущего дня до 18:00 текущего дня (UTC)
    start_utc = datetime.combine(target_date - timedelta(days=1), dtime(15, 0))  # 18:00 МСК = 15:00 UTC
    end_utc = datetime.combine(target_date, dtime(15, 0))

    return start_utc, end_utc, target_date


def calculate_daily_yield_with_validation():
    """
    Рассчитывает и валидирует суточную доходность
    """
    db = SessionLocal()
    try:
        start_utc, end_utc, date = get_trading_day_range()

        logger.info(f"[YIELD] 📅 Расчет доходности за {date}")
        logger.info(f"[YIELD] ⏰ Диапазон: {start_utc} → {end_utc} (UTC)")

        # Проверяем, есть ли уже запись
        existing = db.execute(
            select(DailyYield).where(DailyYield.date == date)
        ).scalar_one_or_none()

        if existing:
            logger.warning(f"[YIELD] ⚠️ Доходность за {date} уже записана: {existing.base_yield}%")
            return existing.base_yield

        # Считаем сумму всех трейдов за период
        trades_result = db.query(func.sum(Trade.result_pct)).filter(
            Trade.created_at >= start_utc,
            Trade.created_at < end_utc
        ).scalar()

        # Получаем детали для логирования
        trades_count = db.query(Trade).filter(
            Trade.created_at >= start_utc,
            Trade.created_at < end_utc
        ).count()

        profitable_count = db.query(Trade).filter(
            Trade.created_at >= start_utc,
            Trade.created_at < end_utc,
            Trade.is_profitable == True
        ).count()

        yield_percent = round(float(trades_result or 0), 2)
        winrate = (profitable_count / trades_count * 100) if trades_count > 0 else 0

        logger.info(f"[YIELD] 📊 Найдено сделок: {trades_count}")
        logger.info(f"[YIELD] 💹 Прибыльных: {profitable_count} ({winrate:.1f}%)")
        logger.info(f"[YIELD] 💰 Суммарная доходность: {yield_percent}%")

        # Валидация результата
        if trades_count == 0:
            logger.warning(f"[YIELD] ⚠️ Нет сделок за {date}, устанавливаем 0%")
        elif yield_percent < 1.0:
            logger.warning(f"[YIELD] ⚠️ Низкая доходность: {yield_percent}% (ожидается 2-5%)")
        elif yield_percent > 8.0:
            logger.warning(f"[YIELD] ⚠️ Высокая доходность: {yield_percent}% (ожидается 2-5%)")
        else:
            logger.success(f"[YIELD] ✅ Доходность в норме: {yield_percent}%")

        # Записываем результат
        daily_yield = DailyYield(date=date, base_yield=yield_percent)
        db.add(daily_yield)
        db.commit()

        logger.success(f"[YIELD] ✅ Доходность за {date} записана: {yield_percent}%")
        return yield_percent

    except Exception as e:
        logger.error(f"[YIELD] ❌ Ошибка при расчете доходности: {e}")
        db.rollback()
        return None
    finally:
        db.close()


def generate_and_record_daily_yield():
    """
    Основная функция для генерации и записи суточной доходности
    """
    return calculate_daily_yield_with_validation()


def get_recent_yields(days=7):
    """
    Получает доходность за последние N дней для анализа
    """
    db = SessionLocal()
    try:
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)

        yields = db.query(DailyYield).filter(
            DailyYield.date >= start_date,
            DailyYield.date <= end_date
        ).order_by(DailyYield.date.desc()).all()

        return [(y.date, y.base_yield) for y in yields]

    finally:
        db.close()


def validate_system_health():
    """
    Проверяет здоровье системы генерации доходности
    """
    recent_yields = get_recent_yields(7)

    if not recent_yields:
        logger.error("[YIELD] ❌ Нет данных о доходности за последние 7 дней!")
        return False

    # Проверяем последние 3 дня
    recent_3days = recent_yields[:3]
    problems = []

    for date, yield_pct in recent_3days:
        if yield_pct < 1.5:
            problems.append(f"{date}: {yield_pct}% (слишком низко)")
        elif yield_pct > 7.0:
            problems.append(f"{date}: {yield_pct}% (слишком высоко)")

    if problems:
        logger.warning(f"[YIELD] ⚠️ Проблемы с доходностью: {problems}")
        return False

    avg_yield = sum(y[1] for y in recent_3days) / len(recent_3days)
    logger.info(f"[YIELD] ✅ Система работает нормально. Средняя доходность за 3 дня: {avg_yield:.2f}%")
    return True