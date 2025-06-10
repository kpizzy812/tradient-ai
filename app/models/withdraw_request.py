from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from datetime import datetime
from app.core.db import Base

class WithdrawRequest(Base):
    __tablename__ = "withdraw_requests"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    source = Column(String)  # 'balance' или 'investment'
    mode = Column(String, nullable=True)  # 'basic' или 'express' — только если investment

    amount_usd = Column(Float)       # запрошенная сумма
    final_amount_usd = Column(Float) # с учётом комиссии

    method = Column(String)     # RUB, USDT_TON, USDT_BEP20
    details = Column(String)    # реквизиты
    pool_name = Column(String, nullable=True)
    currency = Column(String, nullable=True)

    status = Column(String, default="pending")  # pending / approved / declined
    created_at = Column(DateTime, default=datetime.utcnow)
    execute_until = Column(DateTime, nullable=True)  # дедлайн на выплату
