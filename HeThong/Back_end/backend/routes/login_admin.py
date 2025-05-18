from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database.database import admins_collection
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os

router = APIRouter()

# Cấu hình JWT cho Admin
ADMIN_ALGORITHM = "HS256"
ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES = 120
ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "motkhacbimatchoadmin123") # Sử dụng key riêng cho admin
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AdminLoginRequest(BaseModel):
    email: str
    password: str

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, ADMIN_SECRET_KEY, algorithm=ADMIN_ALGORITHM) # Sử dụng ADMIN_SECRET_KEY và ADMIN_ALGORITHM
    return encoded_jwt

@router.post("")
async def login_admin(login_data: AdminLoginRequest):
    admin = admins_collection.find_one({"email": login_data.email})

    if not admin:
        raise HTTPException(status_code=401, detail="❌ Không tìm thấy tài khoản admin!")

    hashed_password = admin.get("password")
    if not hashed_password:
        raise HTTPException(status_code=500, detail="❌ Admin không có mật khẩu!")

    if not verify_password(login_data.password, hashed_password):
        raise HTTPException(status_code=401, detail="❌ Mật khẩu không đúng!")

    admin_id = str(admin.get("_id"))
    access_token = create_access_token(data={"id": admin_id, "role": "admin"})

    return {
        "message": "✅ Đăng nhập thành công!",
        "token": access_token,
        "role": "admin",
        "id": admin_id,
        "name": admin.get("name")
    }