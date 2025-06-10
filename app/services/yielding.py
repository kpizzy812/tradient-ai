from datetime import datetime, timedelta, time as dtime
from sqlalchemy import select, func
from app.models.trades import Trade
from app.models.daily_yield import DailyYield
from app.core.db import SessionLocal

from app.core.logger import logger  # добавь в начало если ещё нет

def generate_and_record_daily_yield():
    now = datetime.utcnow() + timedelta(hours=3)  # Москва
    today = now.date()
    yesterday = today - timedelta(days=1)

    start = datetime.combine(yesterday, dtime(18, 0)) - timedelta(hours=3)  # UTC
    end = datetime.combine(today, dtime(18, 0)) - timedelta(hours=3)

    logger.info(f"[YIELD] 📅 Диапазон трейдов: {start} → {end}")

    db = SessionLocal()
    try:
        existing = db.execute(select(DailyYield).where(DailyYield.date == yesterday)).scalar_one_or_none()
        if existing:
            logger.warning(f"[YIELD] 🟡 Доходность за {yesterday} уже есть: {existing.base_yield}%")
            return

        result = db.query(func.sum(Trade.result_pct)).filter(
            Trade.created_at >= start,
            Trade.created_at < end
        ).scalar()

        logger.info(f"[YIELD] 📈 Найдено суммарно %: {result}")

        yield_percent = round(float(result or 0), 2)
        db.add(DailyYield(date=yesterday, base_yield=yield_percent))
        db.commit()

        logger.success(f"[YIELD] ✅ Записана доходность за {yesterday}: {yield_percent}%")
    except Exception as e:
        logger.error(f"[YIELD] ❌ Ошибка при записи доходности: {e}")
    finally:
        db.close()

