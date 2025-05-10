from bson import ObjectId
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class EssayStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class Essay(BaseModel):
    id: Optional[str] = None  # Chuyển từ Optional[ObjectId] sang Optional[str]
    id_student: Optional[str]
    id_teacher: Optional[str]
    title: str
    file: str
    ai_score: Optional[float] = None
    submission_date: datetime = Field(default_factory=datetime.now)
    status: EssayStatus = EssayStatus.pending

    class Config:
        json_encoders = {ObjectId: str}  # Tự động chuyển ObjectId thành string
