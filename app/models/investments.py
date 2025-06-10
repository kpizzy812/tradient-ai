from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Boolean
from datetime import datetime
from app.core.db import Base

class Investment(Base):
    __tablename__ = "investments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount_usd = Column(Float)
    reinvested = Column(Float, default=0.0)  # новая колонка
    pool_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    included_today = Column(Boolean, default=False)
