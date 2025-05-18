from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class Student(BaseModel):
    id: Optional[str] = None  # Dùng string vì Mongo tự tạo ObjectId
    name: str
    email: EmailStr
    password: str
    classinfor: str
    essays: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    role: str = "student"