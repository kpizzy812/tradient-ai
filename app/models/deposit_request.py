from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from datetime import datetime
from app.core.db import Base

class DepositRequest(Base):
    __tablename__ = "deposit_requests"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount_usd = Column(Float)
    pool_name = Column(String)
    method = Column(String)  # способ оплаты: TON, USDT, QIWI
    currency = Column(String, nullable=True)  # usdt_ton / usdt_bep20 / card_ru / trx
    details = Column(String, nullable=True)   # реквизиты или комментарий
    status = Column(String, default="pending")  # pending / approved / declined / deleted
    created_at = Column(DateTime, default=datetime.utcnow)