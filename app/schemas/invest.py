from pydantic import BaseModel

class InvestRequest(BaseModel):
    user_id: int
    pool_name: str
    amount: float
    use_balance: bool
    currency: str | None = None       # "usdt_ton", "usdt_bep20", "card_ru", "trx"
    details: str | None = None

class ConfirmInvestRequest(BaseModel):
    user_id: int
    pool_name: str
    amount_usd: float
    currency: str
    details: str