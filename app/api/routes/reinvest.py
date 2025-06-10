from fastapi import APIRouter, Depends
from app.core.db import SessionLocal
from sqlalchemy.orm import Session
from app.models.users import User
from fastapi import Query
from app.schemas.reinvest import ReinvestSettings
from fastapi import HTTPException
from app.schemas.reinvest import ReinvestUpdate

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/settings", response_model=ReinvestSettings)
def get_reinvest_settings(user_id: int = Query(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.tg_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return ReinvestSettings(flags=user.auto_reinvest_flags or {})


@router.post("/settings")
def update_reinvest_settings(payload: ReinvestUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.tg_id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    flags = user.auto_reinvest_flags or {}
    flags[payload.pool_name] = payload.enabled
    user.auto_reinvest_flags = flags

    db.commit()
    return {"success": True, "flags": flags}