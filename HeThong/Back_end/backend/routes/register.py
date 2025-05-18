from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator, EmailStr 
from pymongo.errors import DuplicateKeyError
import logging
from passlib.context import CryptContext  
from database.database import db
router = APIRouter()

# Tạo đối tượng bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Định nghĩa BaseModel cho việc đăng ký, bao gồm cả trường confirm_password
class BaseRegistration(BaseModel):
    name: str
    email: EmailStr # Sử dụng EmailStr để validate email
    password: str
    confirm_password: str

    @validator('confirm_password')
    def password_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class TeacherRegistration(BaseRegistration):
    subject: str

class StudentRegistration(BaseRegistration):
    classinfor: str

@router.post("/teacher")
async def register_teacher(teacher: TeacherRegistration):
    try:
        logging.info("📌 Bắt đầu đăng ký giáo viên")
        if db.teachers.find_one({"email": teacher.email}):
            raise HTTPException(status_code=400, detail="Email giáo viên đã tồn tại!")

        teacher_data = teacher.dict()
        # Loại bỏ confirm_password trước khi lưu
        teacher_data.pop("confirm_password")
        teacher_data["role"] = "teacher"
        teacher_data["password"] = hash_password(teacher_data["password"])  # Băm mật khẩu

        db.teachers.insert_one(teacher_data)
        logging.info("✅ Giáo viên đăng ký thành công")
        return {"message": "Đăng ký giáo viên thành công!"}

    except DuplicateKeyError:
        logging.error("❌ Email giáo viên đã tồn tại!")
        raise HTTPException(status_code=400, detail="Email giáo viên đã tồn tại!")

    except ValueError as e:
        logging.error(f"❌ Lỗi xác nhận mật khẩu: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logging.error(f"❌ Lỗi khi đăng ký giáo viên: {e}")
        return JSONResponse(status_code=500, content={"error": "Đã có lỗi xảy ra"})

@router.post("/student")
async def register_student(student: StudentRegistration):
    try:
        logging.info("📌 Bắt đầu đăng ký học sinh")
        if db.students.find_one({"email": student.email}):
            raise HTTPException(status_code=400, detail="Email học sinh đã tồn tại!")

        student_data = student.dict()
        # Loại bỏ confirm_password trước khi lưu
        student_data.pop("confirm_password")
        student_data["role"] = "student"
        student_data["password"] = hash_password(student_data["password"])  # Băm mật khẩu

        db.students.insert_one(student_data)
        logging.info("✅ Học sinh đăng ký thành công")
        return {"message": "Đăng ký học sinh thành công!"}

    except DuplicateKeyError:
        logging.error("❌ Email học sinh đã tồn tại!")
        raise HTTPException(status_code=400, detail="Email học sinh đã tồn tại!")

    except ValueError as e:
        logging.error(f"❌ Lỗi xác nhận mật khẩu: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logging.error(f"❌ Lỗi khi đăng ký học sinh: {e}")
        return JSONResponse(status_code=500, content={"error": "Đã có lỗi xảy ra"})
