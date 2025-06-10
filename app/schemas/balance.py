from pydantic import BaseModel

class BalanceResponse(BaseModel):
    profit_usd: float
    hold_balance: float
