from datetime import datetime
from fastapi import APIRouter, HTTPException
from auth import hash_password 
from src.student.models.student_schema import Student
from database.database import students_collection
from bson import ObjectId
from typing import List

router = APIRouter()

# API: Lấy danh sách sinh viên
@router.get("/", response_model=List[Student])
async def get_students():
    students = list(students_collection.find({}))
    for student in students:
        student["id"] = str(student.pop("_id"))  # Chuyển ObjectId thành string
    return students

# API: Thêm sinh viên mới (POST)
@router.post("/", response_model=Student)
async def create_student(student: Student):
    if students_collection.find_one({"email": student.email}):
        raise HTTPException(status_code=400, detail="Email đã tồn tại")

    student_dict = student.dict(exclude={"id"})
    student_dict["password"] = hash_password(student.password)
    student_dict["role"] = student.role if student.role else "student"  # Đảm bảo có role

    result = students_collection.insert_one(student_dict)
    student_dict["id"] = str(result.inserted_id)
    return student_dict

# API: Cập nhật thông tin sinh viên (PUT)
@router.put("/{student_id}", response_model=Student)
async def update_student(student_id: str, student: Student):
    if not ObjectId.is_valid(student_id):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")

    student_dict = student.dict(exclude_unset=True, exclude={"id"})
    if "role" not in student_dict:  # Đảm bảo role không bị mất khi cập nhật
        student_dict["role"] = "student"

    result = students_collection.update_one(
        {"_id": ObjectId(student_id)}, {"$set": student_dict}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy học sinh")

    updated_student = students_collection.find_one({"_id": ObjectId(student_id)})
    updated_student["id"] = str(updated_student.pop("_id"))

    return updated_student


# API: Xóa sinh viên theo ID
@router.delete("/{student_id}")
async def delete_student(student_id: str):
    if not ObjectId.is_valid(student_id):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")

    result = students_collection.delete_one({"_id": ObjectId(student_id)})
    if result.deleted_count == 1:
        return {"message": f"Học sinh {student_id} đã bị xóa"}

    raise HTTPException(status_code=404, detail="Không tìm thấy học sinh")


# API: Tìm kiếm sinh viên bằng ID
@router.get("/{student_id}", response_model=Student)
async def get_student_by_id(student_id: str):
    if not ObjectId.is_valid(student_id):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")

    student = students_collection.find_one({"_id": ObjectId(student_id)})

    if student is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy học sinh")

    student["id"] = str(student.pop("_id"))
    return student
