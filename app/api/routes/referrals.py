from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.users import User
from app.schemas.referrals import ReferralStats, ReferralLevelInfo
from app.core.config import settings

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("", response_model=ReferralStats)
def get_referrals(user_id: int = Query(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.tg_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    levels_info = []
    total = 0.0
    current_ids = [user.id]

    for i, percent in enumerate(settings.REFERRAL_LEVELS, start=1):
        refs = db.query(User).filter(User.referrer_id.in_(current_ids)).all()
        current_ids = [u.id for u in refs]

        level_earned = sum(round(r.deposit_usd * percent / 100, 2) for r in refs)
        total += level_earned
        levels_info.append(ReferralLevelInfo(level=i, count=len(refs), earned=round(level_earned, 2)))

        if not current_ids:
            break

    return ReferralStats(
        ref_code=user.ref_code,
        levels=levels_info,
        total_earned=round(total, 2)
    )
