from pydantic import BaseModel
from typing import Dict

class ReinvestSettings(BaseModel):
    flags: Dict[str, bool]

class ReinvestUpdate(BaseModel):
    user_id: int
    pool_name: str
    enabled: bool