from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean
from datetime import datetime
from app.core.db import Base

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True)
    ticker = Column(String)                   # Пример: BTC/USDT
    exchange = Column(String, default="Binance")
    direction = Column(String)               # LONG / SHORT
    entry_price = Column(Float)
    exit_price = Column(Float)
    result_pct = Column(Float)
    result_usd = Column(Float)
    entry_time = Column(DateTime)
    exit_time = Column(DateTime)
    is_profitable = Column(Boolean)
    chart_path = Column(String)              # путь до PNG (например, static/trades/123.png)
    created_at = Column(DateTime, default=datetime.utcnow)