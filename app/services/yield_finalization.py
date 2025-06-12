# app/services/yield_finalization.py - НОВЫЙ ФАЙЛ
from datetime import datetime, timedelta, date
from sqlalchemy import func
from app.models.trades import Trade
from app.models.daily_yield import DailyYield
from app.core.db import SessionLocal
from app.core.logger import logger
from app.core.config import settings


def finalize_daily_yield():
    """Финализирует доходность за прошедший торговый день"""
    db = SessionLocal()
    try:
        # Определяем прошедший торговый день
        now_utc = datetime.utcnow()
        finalize_hour = settings.YIELD_TIME_UTC_HOUR

        # Прошедший торговый день (вчера 18:00 - сегодня 18:00)
        end_utc = datetime.combine(now_utc.date(), datetime.min.time().replace(hour=finalize_hour))
        start_utc = end_utc - timedelta(days=1)

        # Дата для записи (сегодняшняя)
        record_date = now_utc.date()

        logger.info(f"[FINALIZE] Финализация торгового дня {start_utc} - {end_utc}")

        # Проверяем, не записано ли уже
        existing = db.query(DailyYield).filter(DailyYield.date == record_date).first()
        if existing:
            logger.warning(f"[FINALIZE] Доходность за {record_date} уже записана: {existing.base_yield}%")
            return existing.base_yield

        # Считаем доходность за период
        total_yield = db.query(func.sum(Trade.result_pct)).filter(
            Trade.created_at >= start_utc,
            Trade.created_at < end_utc
        ).scalar() or 0.0

        # Подсчитываем трейды для статистики
        trades_count = db.query(Trade).filter(
            Trade.created_at >= start_utc,
            Trade.created_at < end_utc
        ).count()

        total_yield = round(total_yield, 2)
        target_min, target_max = settings.DAILY_YIELD_RANGE

        # Проверяем попадание в диапазон
        if target_min <= total_yield <= target_max:
            status = "✅ В ДИАПАЗОНЕ"
        elif total_yield < target_min:
            status = f"⚠️ НИЖЕ ДИАПАЗОНА ({target_min - total_yield:.2f}%)"
        else:
            status = f"⚠️ ВЫШЕ ДИАПАЗОНА (+{total_yield - target_max:.2f}%)"

        logger.info(f"[FINALIZE] {status}: {total_yield}% ({trades_count} трейдов)")

        # Записываем результат
        daily_yield = DailyYield(date=record_date, base_yield=total_yield)
        db.add(daily_yield)
        db.commit()

        logger.success(f"[FINALIZE] Доходность за {record_date} записана: {total_yield}%")
        return total_yield

    except Exception as e:
        logger.error(f"[FINALIZE] Ошибка финализации: {e}")
        db.rollback()
        return None
    finally:
        db.close()