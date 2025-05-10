from pydantic import BaseModel, EmailStr
from typing import List, Optional

class Teacher(BaseModel):
    id: Optional[str] = None
    name: str
    email: EmailStr #Đảm bảo email hợp lệ.
    password: str
    subject: str
    graded_essays: List[str] = []
    role: str = "teacher"