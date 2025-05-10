from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database.database import db, teachers_collection, students_collection
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
from bson import ObjectId

router = APIRouter()

# Cấu hình JWT

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
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
    user = teachers_collection.find_one({"email": login_data.email})
    if not user:
        user = students_collection.find_one({"email": login_data.email})

    if not user:
        raise HTTPException(status_code=401, detail="❌ Không tìm thấy tài khoản!")

    hashed_password = user.get("password")
    if not hashed_password:
        raise HTTPException(status_code=500, detail="❌ User không có mật khẩu!")

    if not verify_password(login_data.password, hashed_password):
        raise HTTPException(status_code=401, detail="❌ Mật khẩu không đúng!")

    # Tạo JWT token với _id của người dùng
    user_id = str(user.get("_id"))
    print(f"User ID from database: {user_id}")
    print(f"Type of user ID: {type(user.get('_id'))}")
    access_token = create_access_token(data={"id": user_id, "role": user.get("role")})

    if user.get("role") == "student":
        return {
            "message": "✅ Đăng nhập thành công!",
            "role": user.get("role"),
            "token": access_token,
            "id": user_id,
            "name": user.get("name"),
            "class": user.get("classinfor")
        }
    elif user.get("role") == "teacher":
        return {
            "message": "✅ Đăng nhập thành công!",
            "role": user.get("role"),
            "token": access_token,
            "id": user_id,
            "name": user.get("name"),
            "subject": user.get("subject")
        }
    else:
        raise HTTPException(status_code=401, detail="❌ Vai trò không hợp lệ!")