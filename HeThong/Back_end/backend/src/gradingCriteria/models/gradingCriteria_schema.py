from pydantic import BaseModel
from typing import Optional

class GradingCriteria(BaseModel):
    id: Optional[str] = None
    name: str
    maxScore: float
    description: Optional[str] = None
