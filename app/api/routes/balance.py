from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.users import User
from app.schemas.balance import BalanceResponse

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/balance", response_model=BalanceResponse)
def get_balance(user_id: int = Query(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.tg_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return BalanceResponse(
        profit_usd=round(user.profit_usd, 2),
        hold_balance=round(user.hold_balance, 2)
    )
