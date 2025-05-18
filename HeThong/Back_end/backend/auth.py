from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from database.database import students_collection, teachers_collection, admins_collection
from datetime import datetime, timedelta
from bson import ObjectId, errors as bson_errors
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="") 

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "motkhacbimatchoadmin123")
ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=120))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_student(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        role = payload.get("role")

        if not user_id or role != "student":
            raise HTTPException(status_code=401, detail="Token không hợp lệ hoặc không phải học sinh")

        try:
            obj_id = ObjectId(user_id)
        except Exception:
            raise HTTPException(status_code=400, detail="ID không hợp lệ")

        student = students_collection.find_one({"_id": obj_id})
        if not student:
            raise HTTPException(status_code=404, detail="Không tìm thấy học sinh")

        student["id"] = str(student.pop("_id"))
        return student

    except JWTError:
        raise HTTPException(status_code=403, detail="Không thể xác thực token")
    
async def get_current_teacher(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        role = payload.get("role")

        if not user_id or role != "teacher":
            raise HTTPException(status_code=401, detail="Token không hợp lệ hoặc không phải giáo viên")

        try:
            obj_id = ObjectId(user_id)
        except Exception:
            raise HTTPException(status_code=400, detail="ID không hợp lệ")

        teacher = teachers_collection.find_one({"_id": obj_id})
        if not teacher:
            raise HTTPException(status_code=404, detail="Không tìm thấy giáo viên")

        teacher["id"] = str(teacher.pop("_id"))
        return teacher

    except JWTError:
        raise HTTPException(status_code=403, detail="Không thể xác thực token")
    
async def get_current_admin(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, ADMIN_SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        role = payload.get("role")

        if not user_id or role != "admin":
            raise HTTPException(status_code=401, detail="Token không hợp lệ hoặc không phải quản trị viên")

        try:
            obj_id = ObjectId(user_id)
        except bson_errors.InvalidId:
            raise HTTPException(status_code=400, detail="ID không hợp lệ")

        admin = admins_collection.find_one({"_id": obj_id}) 
        if not admin:
            raise HTTPException(status_code=404, detail="Không tìm thấy quản trị viên")

        admin["id"] = str(admin.pop("_id"))
        return admin

    except JWTError:
        raise HTTPException(status_code=403, detail="Không thể xác thực token")