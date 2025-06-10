from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class WithdrawRequestInput(BaseModel):
    user_id: int
    source: str  # "balance" / "investment"
    amount: float
    method: str  # "RUB", "USDT_TON", "USDT_BEP20"
    details: str
    pool_name: Optional[str] = None
    mode: Optional[str] = None  # "basic" / "express", только для "investment"
    days_since_deposit: Optional[int] = 0

class WithdrawRequestResponse(BaseModel):
    final_amount: float
    execute_until: datetime
    status: str = "pending"
    request_id: int
