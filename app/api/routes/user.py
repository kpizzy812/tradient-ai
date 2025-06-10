from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.users import User
from app.schemas.language import LanguageUpdate
from app.schemas.user import ProfileResponse
from app.core.config import settings
from app.core.utils.auth import get_current_user
from sqlalchemy import func
from app.models.income_log import IncomeLog

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/language")
def set_language(payload: LanguageUpdate, db: Session = Depends(get_db)):
    if payload.lang not in ["ru", "en", "uk"]:
        raise HTTPException(status_code=400, detail="Unsupported language")

    user = db.query(User).filter(User.tg_id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.lang or user.lang not in ["ru", "en", "uk"]:
        user.lang = payload.lang
        db.commit()
    return {"success": True, "lang": user.lang}

@router.get("/language/{tg_id}")
def get_lang_by_id(tg_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.tg_id == tg_id).first()
    if not user:
        return {"lang": "ru"}
    return {"lang": user.lang}


@router.get("/profile", response_model=ProfileResponse)
def profile(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    total_income = db.query(func.sum(IncomeLog.amount_usd)).filter(
        IncomeLog.user_id == current_user.id
    ).scalar() or 0.0
    return ProfileResponse(
        user_id=current_user.tg_id,
        username=current_user.username,
        lang=current_user.lang,
        profit_usd=current_user.profit_usd,
        hold_balance=current_user.hold_balance,
        auto_reinvest_flags=current_user.auto_reinvest_flags,
        ref_code=current_user.ref_code,
        ref_link=f"https://t.me/{settings.BOT_USERNAME}?start={current_user.ref_code}",
        total_earned_usd=round(total_income, 2)
    )

