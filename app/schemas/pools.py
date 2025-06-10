from pydantic import BaseModel
from typing import Tuple, Optional

class PoolInfo(BaseModel):
    name: str
    coefficient: float
    yield_range: Tuple[float, float]
    description: str
    min_invest: Optional[int] = None        # ← добавили
    user_balance: Optional[float] = 0       # ← добавили
    reinvest: Optional[bool] = False        # ← добавили

class PoolsResponse(BaseModel):
    pools: list[PoolInfo]
