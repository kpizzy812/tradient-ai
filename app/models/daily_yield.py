from sqlalchemy import Column, Integer, String, Float, Date
from app.core.db import Base
from datetime import date

class DailyYield(Base):
    __tablename__ = "daily_yields"

    id = Column(Integer, primary_key=True)
    date = Column(Date, unique=True)
    base_yield = Column(Float)  # общий процент прибыли AI за день (например, 3.2%)
