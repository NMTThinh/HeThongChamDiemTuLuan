import jwt
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database.database import admins_collection
from passlib.context import CryptContext
import os

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AdminLoginRequest(BaseModel):
    email: str
    password: str

@router.post("")
async def admin_login(login_data: AdminLoginRequest):
    admin = admins_collection.find_one({"email": login_data.email})

    if not admin:
        raise HTTPException(status_code=401, detail="❌ Không tìm thấy tài khoản admin!")

    if not pwd_context.verify(login_data.password, admin["password"]):
        raise HTTPException(status_code=401, detail="❌ Mật khẩu không đúng!")

    # Tạo token
    token_data = {
        "sub": admin["email"],
        "role": "admin",
        "name": admin["name"],  # Thêm tên admin
        "exp": datetime.utcnow() + timedelta(hours=3),  # Token hết hạn sau 3 giờ
    }
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "message": "✅ Đăng nhập thành công!",
        "token": token,
        "role": "admin",
        "name": admin["name"]  # Trả về tên admin
    }
