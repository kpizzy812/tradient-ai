from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, String, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.db import Base
from sqlalchemy.ext.mutable import MutableDict

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    tg_id = Column(Integer, unique=True, index=True)
    username = Column(String, nullable=True)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    deposit_usd = Column(Float, default=0.0)
    profit_usd = Column(Float, default=0.0)
    ref_balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    lang = Column(String, default="ru")  # ru / en / uk
    ref_code = Column(String, unique=True)  # личный код
    hold_balance = Column(Float, default=0.0)  # удержанные средства (реинвест, заявка)
    auto_reinvest_flags = Column(MutableDict.as_mutable(JSON), default=dict)

    referrals = relationship("User", backref="referrer", remote_side=[id])
