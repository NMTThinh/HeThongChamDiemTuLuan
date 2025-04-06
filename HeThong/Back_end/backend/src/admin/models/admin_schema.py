from pydantic import BaseModel
from typing import Optional

class Admin(BaseModel):
    id: Optional[str] = None
    name: str
    email: str
    password: str
    role: str = "admin"