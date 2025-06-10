from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.db import SessionLocal
from app.models.users import User
from app.models.deposit_request import DepositRequest
from app.services.logic import invest_user
from app.schemas.invest import InvestRequest
from datetime import datetime
from app.core.config import settings
from app.services.notify import notify_admins_new_request
from aiogram import Bot
from app.schemas.invest import ConfirmInvestRequest
from app.state import get_token_rate
from traceback import print_exc
from app.core.logger import logger

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/payment_details")
def get_payment_details():
    return settings.PAYMENT_ADDRESSES

# @router.post("")
# async def handle_invest(payload: InvestRequest, db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.tg_id == payload.user_id).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#
#     bot = Bot(token=settings.BOT_TOKEN)
#
#     # ✅ Проверка лимитов по пулу
#     limits = settings.POOL_LIMITS.get(payload.pool_name)
#     if not limits:
#         await bot.session.close()
#         raise HTTPException(status_code=400, detail="Invalid pool")
#
#     # сколько уже инвестировал этот юзер в этот пул
#     user_total = db.query(func.sum(DepositRequest.amount_usd)).filter(
#         DepositRequest.user_id == user.id,
#         DepositRequest.pool_name == payload.pool_name,
#         DepositRequest.status.in_(["pending", "approved"])
#     ).scalar() or 0
#
#     if user_total == 0 and payload.amount < limits["min"]:
#         await bot.session.close()
#         raise HTTPException(status_code=400, detail=f"Минимальный вход в пул {payload.pool_name}: ${limits['min']}")
#
#     if payload.amount > limits["max"]:
#         await bot.session.close()
#         raise HTTPException(status_code=400, detail=f"Максимум за одну заявку: ${limits['max']}")
#
#     if user_total + payload.amount > limits["max_per_user"]:
#         await bot.session.close()
#         raise HTTPException(status_code=400, detail=f"Превышен лимит по вкладу в пул: ${limits['max_per_user']}")
#
#     # ✅ Далее обычная логика
#     if payload.use_balance:
#         available = round(user.profit_usd, 2)
#
#         if available >= payload.amount:
#             # прямой реинвест
#             user.profit_usd -= payload.amount
#             success = invest_user(db, user, payload.amount, payload.pool_name, bot=None)
#             if success:
#                 await bot.session.close()
#                 return {"status": "reinvested"}
#             await bot.session.close()
#             raise HTTPException(status_code=500, detail="Invest failed")
#
#         elif available > 0:
#             hold = round(available, 2)
#             remainder = round(payload.amount - hold, 2)
#
#             user.profit_usd -= hold
#             user.hold_balance += hold
#
#             req = DepositRequest(
#                 user_id=user.id,
#                 amount_usd=remainder,
#                 pool_name=payload.pool_name,
#                 method="internal_balance",
#                 currency=payload.currency,
#                 details=payload.details,
#                 status="pending",
#                 created_at=datetime.utcnow()
#             )
#             db.add(req)
#             db.commit()
#
#             try:
#                 await notify_admins_new_request(bot, req, user)
#             except Exception as e:
#                 print(f"⚠️ Ошибка при уведомлении админов: {e}")
#
#             await bot.session.close()
#             return {"status": "partial_hold", "held": hold, "request_id": req.id}
#
#         else:
#             req = DepositRequest(
#                 user_id=user.id,
#                 amount_usd=payload.amount,
#                 pool_name=payload.pool_name,
#                 method="manual",
#                 status="pending",
#                 created_at=datetime.utcnow()
#             )
#             db.add(req)
#             db.commit()
#
#             try:
#                 await notify_admins_new_request(bot, req, user)
#             except Exception as e:
#                 print(f"⚠️ Ошибка при уведомлении админов: {e}")
#
#             await bot.session.close()
#             return {"status": "request_only", "request_id": req.id}
#
#     else:
#         req = DepositRequest(
#             user_id=user.id,
#             amount_usd=payload.amount,
#             pool_name=payload.pool_name,
#             method="manual",
#             status="pending",
#             created_at=datetime.utcnow()
#         )
#         db.add(req)
#         db.commit()
#
#         try:
#             await notify_admins_new_request(bot, req, user)
#         except Exception as e:
#             print(f"⚠️ Ошибка при уведомлении админов: {e}")
#
#         await bot.session.close()
#         return {"status": "request_created", "request_id": req.id}


@router.post("/confirm")
async def confirm_investment(payload: ConfirmInvestRequest, db: Session = Depends(get_db)):
    print("📩 confirm_investment called")
    print(f"payload = {payload}")
    try:
        user = db.query(User).filter(User.tg_id == payload.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Map currency keys to token symbols
        symbol_map = {
            "usdt_ton": "USDT",
            "usdt_bep20": "USDT",
            "trx": "TRX",
            "card_ru": "RUB"
        }

        symbol = symbol_map.get(payload.currency.lower())
        print(f"symbol = {symbol}")
        if not symbol:
            raise HTTPException(status_code=400, detail="Unsupported currency")

        if symbol == "USD" or symbol == "USDT":
            rate = 1.0  # USDT по сути равен USD
        else:
            rate = await get_token_rate(f"{symbol.upper()}_USD")
            if not rate:
                from app.tasks.update_rates import update_all_token_rates
                await update_all_token_rates()
                rate = await get_token_rate(f"{symbol.upper()}_USD")

        print(f"rate = {rate}")
        if not rate:
            raise HTTPException(status_code=500, detail="Rate not available for this currency")

        amount_token = round(payload.amount_usd / rate, 6)

        request = DepositRequest(
            user_id=user.id,
            amount_usd=payload.amount_usd,
            pool_name=payload.pool_name,
            method="manual",
            currency=payload.currency,
            details=payload.details,
            status="pending",
            created_at=datetime.utcnow()
        )
        db.add(request)
        db.commit()

        bot = Bot(token=settings.BOT_TOKEN)
        try:
            await notify_admins_new_request(bot, request, user)
        except Exception as e:
            print(f"[ADMINS] notify error: {e}")
        await bot.session.close()

        return {
            "status": "request_created",
            "request_id": request.id,
            "amount_token": amount_token,
            "currency": payload.currency
        }

    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        print_exc()
        raise HTTPException(status_code=500, detail="Internal error")



@router.post("")
async def handle_invest(payload: InvestRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.tg_id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    bot = Bot(token=settings.BOT_TOKEN)
    limits = settings.POOL_LIMITS.get(payload.pool_name)
    if not limits:
        await bot.session.close()
        raise HTTPException(status_code=400, detail="Invalid pool")

    user_total = db.query(func.sum(DepositRequest.amount_usd)).filter(
        DepositRequest.user_id == user.id,
        DepositRequest.pool_name == payload.pool_name,
        DepositRequest.status.in_(["pending", "approved"])
    ).scalar() or 0

    if user_total == 0 and payload.amount < limits["min"]:
        await bot.session.close()
        raise HTTPException(status_code=400, detail=f"Минимальный вход в пул {payload.pool_name}: ${limits['min']}")

    if payload.amount > limits["max"]:
        await bot.session.close()
        raise HTTPException(status_code=400, detail=f"Максимум за одну заявку: ${limits['max']}")

    if user_total + payload.amount > limits["max_per_user"]:
        await bot.session.close()
        raise HTTPException(status_code=400, detail=f"Превышен лимит по вкладу в пул: ${limits['max_per_user']}")

    if payload.use_balance:
        available = round(user.profit_usd, 2)

        if available >= payload.amount:
            user.profit_usd -= payload.amount
            success = invest_user(db, user, payload.amount, payload.pool_name, bot=None)
            if success:
                await bot.session.close()
                return {"status": "reinvested"}
            await bot.session.close()
            raise HTTPException(status_code=500, detail="Invest failed")

        elif available > 0:
            hold = round(available, 2)
            remainder = round(payload.amount - hold, 2)
            user.profit_usd -= hold
            user.hold_balance += hold
            db.commit()
            await bot.session.close()
            return {
                "status": "partial_hold",
                "held": hold,
                "remainder": remainder
            }

        else:
            await bot.session.close()
            return {
                "status": "request_required",
                "remainder": payload.amount
            }

    else:
        await bot.session.close()
        return {
            "status": "request_required",
            "remainder": payload.amount
        }

@router.get("/rates")
async def get_token_rates():
    keys = [
        "TRX_USD", "TRX_RUB",
        "TON_USD", "TON_RUB",
        "USDT_USD", "USDT_RUB",
        "RUB_USD", "USD_RUB",
    ]
    from app.state import get_token_rate
    result = {}
    for k in keys:
        rate = await get_token_rate(k)
        if rate:
            result[k] = rate

    logger.info(f"[API:RATES] Отправлены курсы: {result}")
    return result