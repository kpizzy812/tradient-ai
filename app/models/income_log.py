from sqlalchemy import Column, Integer, Float, ForeignKey, Date
from app.core.db import Base

class IncomeLog(Base):
    __tablename__ = "income_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount_usd = Column(Float)
    pool_name = Column(ForeignKey("investments.pool_name"))
    date = Column(Date)
