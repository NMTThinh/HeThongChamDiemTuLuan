from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database.database import db, teachers_collection, students_collection
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
router = APIRouter()

# Cấu hình JWT

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

SECRET_KEY = os.getenv("SECRET_KEY")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class LoginRequest(BaseModel):
    email: str
    password: str

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("")
async def login_user(login_data: LoginRequest):
    # Kiểm tra trong bảng Teachers
    user = teachers_collection.find_one({"email": login_data.email})

    # Nếu không có trong Teachers, kiểm tra trong Students
    if not user:
        user = students_collection.find_one({"email": login_data.email})

    if not user:
        raise HTTPException(status_code=401, detail="❌ Không tìm thấy tài khoản!")

    hashed_password = user.get("password")
    if not hashed_password:
        raise HTTPException(status_code=500, detail="❌ User không có mật khẩu!")

    if not verify_password(login_data.password, hashed_password):
        raise HTTPException(status_code=401, detail="❌ Mật khẩu không đúng!")

    # Tạo JWT token và lấy thêm thông tin chi tiết người dùng
    access_token = create_access_token(data={"id": user.get("email"), "role": user.get("role")})

    # Kiểm tra role và lấy thông tin cụ thể
    if user.get("role") == "student":
        return {
            "message": "✅ Đăng nhập thành công!",
            "role": user.get("role"),
            "token": access_token,
            "id": str(user.get("_id")),
            "name": user.get("name"),
            "class": user.get("classinfor")  # Trả về lớp của học sinh
        }
    elif user.get("role") == "teacher":
        return {
            "message": "✅ Đăng nhập thành công!",
            "role": user.get("role"),
            "token": access_token,
            "id": str(user.get("_id")),
            "name": user.get("name"),
            "subject": user.get("subject")  # Trả về môn dạy của giáo viên
        }
    else:
        raise HTTPException(status_code=401, detail="❌ Vai trò không hợp lệ!")
