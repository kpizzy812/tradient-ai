from pydantic import BaseModel
from typing import List

class ReferralLevelInfo(BaseModel):
    level: int
    count: int
    earned: float

class ReferralStats(BaseModel):
    ref_code: str
    levels: List[ReferralLevelInfo]
    total_earned: float
