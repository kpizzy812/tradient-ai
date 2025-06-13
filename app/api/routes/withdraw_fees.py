# app/api/routes/withdraw_fees.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.users import User
from app.models.investments import Investment
from app.core.config import settings
from datetime import datetime
from pydantic import BaseModel
from typing import Dict, List, Any

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class WithdrawFeeInfo(BaseModel):
    days_since_deposit: int
    commission_rate: float
    commission_amount: float
    final_amount: float
    execute_days: int
    description: str


class PoolWithdrawInfo(BaseModel):
    pool_name: str
    user_balance: float
    days_since_first_deposit: int
    standard_mode: WithdrawFeeInfo
    express_mode: WithdrawFeeInfo


class WithdrawFeesResponse(BaseModel):
    pool_withdrawals: List[PoolWithdrawInfo]
    balance_withdrawal: Dict[str, Any]
    fee_tiers: Dict[int, float]
    express_fee: float


def get_withdraw_commission(days_since_deposit: int) -> float:
    """Рассчитать комиссию на основе дней с момента депозита"""
    for days, fee in sorted(settings.WITHDRAW_TIERS.items(), reverse=True):
        if days_since_deposit >= days:
            return fee
    return max(settings.WITHDRAW_TIERS.values())  # Максимальная комиссия


@router.get("/fees/{user_id}", response_model=WithdrawFeesResponse)
def get_withdraw_fees(user_id: int, db: Session = Depends(get_db)):
    """Получить информацию о комиссиях для пользователя"""
    user = db.query(User).filter(User.tg_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Получаем активные инвестиции пользователя по пулам
    investments = db.query(Investment).filter(
        Investment.user_id == user.id,
        Investment.is_active == True
    ).all()

    # Группируем по пулам
    pools_data = {}
    for inv in investments:
        if inv.pool_name not in pools_data:
            pools_data[inv.pool_name] = {
                'total_amount': 0,
                'first_deposit_date': inv.created_at,
                'investments': []
            }

        pools_data[inv.pool_name]['total_amount'] += inv.amount_usd
        pools_data[inv.pool_name]['investments'].append(inv)

        # Находим самый ранний депозит
        if inv.created_at < pools_data[inv.pool_name]['first_deposit_date']:
            pools_data[inv.pool_name]['first_deposit_date'] = inv.created_at

    # Формируем информацию по пулам
    pool_withdrawals = []
    for pool_name, data in pools_data.items():
        days_since_deposit = (datetime.utcnow() - data['first_deposit_date']).days
        user_balance = data['total_amount']

        # Рассчитываем комиссии для разных режимов
        standard_commission = get_withdraw_commission(days_since_deposit)
        express_commission = settings.WITHDRAW_EXPRESS_FEE

        # Пример расчета для $100
        example_amount = min(100.0, user_balance)

        standard_info = WithdrawFeeInfo(
            days_since_deposit=days_since_deposit,
            commission_rate=standard_commission,
            commission_amount=example_amount * standard_commission,
            final_amount=example_amount * (1 - standard_commission),
            execute_days=settings.WITHDRAW_BASE_DAYS,
            description=f"Standard withdrawal - funds arrive in {settings.WITHDRAW_BASE_DAYS} days"
        )

        express_info = WithdrawFeeInfo(
            days_since_deposit=days_since_deposit,
            commission_rate=express_commission,
            commission_amount=example_amount * express_commission,
            final_amount=example_amount * (1 - express_commission),
            execute_days=1,
            description="Express withdrawal - funds arrive within 24 hours"
        )

        pool_withdrawals.append(PoolWithdrawInfo(
            pool_name=pool_name,
            user_balance=user_balance,
            days_since_first_deposit=days_since_deposit,
            standard_mode=standard_info,
            express_mode=express_info
        ))

    # Информация о выводе с баланса (без комиссий)
    balance_withdrawal = {
        "available_balance": user.profit_usd,
        "commission_rate": 0.0,
        "processing_time": "up to 24 hours",
        "description": "Profit withdrawal - no commission",
        "min_amounts": {
            "USDT_TON": 10,
            "USDT_BEP20": 10,
            "RUB": 500
        }
    }

    return WithdrawFeesResponse(
        pool_withdrawals=pool_withdrawals,
        balance_withdrawal=balance_withdrawal,
        fee_tiers=settings.WITHDRAW_TIERS,
        express_fee=settings.WITHDRAW_EXPRESS_FEE
    )