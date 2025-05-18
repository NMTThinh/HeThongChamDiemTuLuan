from bson import ObjectId
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class Grading(BaseModel):
    id: Optional[str] = None
    id_teacher: str  # Không cần Optional vì đã kiểm tra trước khi lưu
    id_essay: str
    ai_score: Optional[float] = None
    final_score: float
    feedback: Optional[str] = None  # Để nhận xét có thể không bắt buộc
    grading_date: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {ObjectId: str}
