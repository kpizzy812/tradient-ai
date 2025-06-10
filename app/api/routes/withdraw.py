from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.users import User
from app.schemas.withdraw import WithdrawRequestInput, WithdrawRequestResponse
from app.services.logic import create_withdraw_request
from app.bot.instance import bot as telegram_bot
from app.services.logic import withdraw_from_investment_to_balance
from datetime import datetime



router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=WithdrawRequestResponse)
async def handle_withdraw(payload: WithdrawRequestInput, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.tg_id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    # проверить баланс при source = balance
    if payload.source == "balance":
        if user.profit_usd < payload.amount:
            raise HTTPException(status_code=400, detail="Недостаточно средств")

        user.profit_usd -= payload.amount

        # создаём заявку как обычно
        request = await create_withdraw_request(
            db=db,
            user=user,
            amount_usd=payload.amount,
            source=payload.source,
            method=payload.method,
            details=payload.details,
            bot=telegram_bot
        )
        db.commit()
        return WithdrawRequestResponse(
            final_amount=request.final_amount_usd,
            execute_until=request.execute_until,
            status="pending",
            request_id=request.id
        )

    if payload.source == "investment" and payload.method == "INTERNAL":
        final = await withdraw_from_investment_to_balance(
            db=db,
            user=user,
            amount_usd=payload.amount,
            pool_name=payload.pool_name,
            mode=payload.mode,
            days_since_deposit=payload.days_since_deposit or 0
        )
        db.commit()
        return WithdrawRequestResponse(
            final_amount=final,
            execute_until=datetime.utcnow(),
            status="executed",
            request_id=0
        )

    request = await create_withdraw_request(
        db=db,
        user=user,
        amount_usd=payload.amount,
        source=payload.source,
        method=payload.method,
        details=payload.details,
        pool_name=payload.pool_name,
        mode=payload.mode,
        days_since_deposit=payload.days_since_deposit or 0,
        bot=telegram_bot
    )

    return WithdrawRequestResponse(
        final_amount=request.final_amount_usd,
        execute_until=request.execute_until,
        status="pending",
        request_id=request.id
    )
