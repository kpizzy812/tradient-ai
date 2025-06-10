# app/models/investment_transfer.py

from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from app.core.db import Base
from datetime import datetime

class InvestmentTransfer(Base):
    __tablename__ = "investment_transfers"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    pool_name = Column(String)
    amount_usd = Column(Float)
    final_amount_usd = Column(Float)
    mode = Column(String)  # basic / express
    status = Column(String, default="pending")  # pending / completed
    created_at = Column(DateTime, default=datetime.utcnow)
    execute_until = Column(DateTime)
