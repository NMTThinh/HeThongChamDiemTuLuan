from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from src.student.models.student_schema import Student
from src.teacher.models.teacher_schema import Teacher
from database.database import db
from pymongo.errors import DuplicateKeyError
import logging
from passlib.context import CryptContext  # Thư viện hash mật khẩu

router = APIRouter()

# Tạo đối tượng bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

@router.post("/teacher")
async def register_teacher(teacher: Teacher):
    try:
        logging.info("📌 Bắt đầu đăng ký giáo viên")
        if db.teachers.find_one({"email": teacher.email}):
            raise HTTPException(status_code=400, detail="Email giáo viên đã tồn tại!")

        teacher_data = teacher.dict()
        teacher_data["role"] = "teacher"
        teacher_data["password"] = hash_password(teacher.password)  # Băm mật khẩu

        db.teachers.insert_one(teacher_data)
        logging.info("✅ Giáo viên đăng ký thành công")
        return {"message": "Đăng ký giáo viên thành công!"}

    except DuplicateKeyError:
        logging.error("❌ Email giáo viên đã tồn tại!")
        raise HTTPException(status_code=400, detail="Email giáo viên đã tồn tại!")

    except Exception as e:
        logging.error(f"❌ Lỗi khi đăng ký giáo viên: {e}")
        return JSONResponse(status_code=500, content={"error": "Đã có lỗi xảy ra"})

@router.post("/student")
async def register_student(student: Student):
    try:
        logging.info("📌 Bắt đầu đăng ký học sinh")
        if db.students.find_one({"email": student.email}):
            raise HTTPException(status_code=400, detail="Email học sinh đã tồn tại!")

        student_data = student.dict()
        student_data["role"] = "student"
        student_data["password"] = hash_password(student.password)  # Băm mật khẩu

        db.students.insert_one(student_data)
        logging.info("✅ Học sinh đăng ký thành công")
        return {"message": "Đăng ký học sinh thành công!"}

    except DuplicateKeyError:
        logging.error("❌ Email học sinh đã tồn tại!")
        raise HTTPException(status_code=400, detail="Email học sinh đã tồn tại!")

    except Exception as e:
        logging.error(f"❌ Lỗi khi đăng ký học sinh: {e}")
        return JSONResponse(status_code=500, content={"error": "Đã có lỗi xảy ra"})
