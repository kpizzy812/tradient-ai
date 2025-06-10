from fastapi import APIRouter, Depends
from app.core.config import settings
from app.schemas.pools import PoolsResponse, PoolInfo
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.db import SessionLocal
from app.models.users import User
from app.models.investments import Investment

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/info", response_model=PoolsResponse)
def get_pools_info(user_id: int, db: Session = Depends(get_db)):
    result = []

    user = db.query(User).filter_by(tg_id=user_id).first()
    user_flags = user.auto_reinvest_flags if user else {}

    for name, yield_range in settings.POOL_YIELD_RANGES.items():
        coeff = settings.POOL_COEFFICIENTS.get(name, 1.0)
        limits = settings.POOL_LIMITS.get(name, {})
        reinvest_flag = user_flags.get(name, False)

        # Считаем сколько вложено пользователем в пул
        balance = 0
        if user:
            balance = db.query(func.sum(Investment.amount_usd)).filter(
                Investment.user_id == user.id,
                Investment.pool_name == name,
                Investment.is_active == True  # ← только активные
            ).scalar() or 0

        result.append(PoolInfo(
            name=name,
            coefficient=coeff,
            yield_range=yield_range,
            description=f"Доходность пула {name} с коэффициентом {coeff}",
            min_invest=limits.get("min", 0),
            user_balance=round(balance, 2),
            reinvest=reinvest_flag
        ))

    return PoolsResponse(pools=result)

