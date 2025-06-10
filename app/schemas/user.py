from pydantic import BaseModel
from typing import Optional
from typing import Dict
class ProfileResponse(BaseModel):
    user_id: int
    username: Optional[str]
    lang: str
    profit_usd: float
    hold_balance: float
    auto_reinvest_flags: Dict[str, bool]
    ref_code: str
    ref_link: str
    total_earned_usd: float