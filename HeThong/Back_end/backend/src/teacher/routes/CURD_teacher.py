from fastapi import APIRouter, HTTPException
from src.teacher.models.teacher_schema import Teacher
from database.database import teachers_collection
from auth import hash_password  # Import hàm mã hóa mật khẩu
from bson import ObjectId
from typing import List

router = APIRouter()

# API: Lấy danh sách tất cả giáo viên
@router.get("/", response_model=List[Teacher])
async def get_teachers():
    teachers = list(teachers_collection.find({}))
    for teacher in teachers:
        teacher["id"] = str(teacher.pop("_id"))
    return teachers

# API: Tạo giáo viên mới
@router.post("/", response_model=Teacher)
async def create_teacher(teacher: Teacher):
    if teachers_collection.find_one({"email": teacher.email}):  
        raise HTTPException(status_code=400, detail="Email đã tồn tại")

    teacher_dict = teacher.dict(exclude={"id"})
    teacher_dict["password"] = hash_password(teacher.password)
    teacher_dict["role"] = teacher.role if teacher.role else "teacher"  # Đảm bảo có role

    result = teachers_collection.insert_one(teacher_dict)
    teacher_dict["id"] = str(result.inserted_id)
    return teacher_dict

# API: Cập nhật thông tin giáo viên (PUT)
@router.put("/{teacher_id}", response_model=Teacher)
async def update_teacher(teacher_id: str, teacher: Teacher):
    if not ObjectId.is_valid(teacher_id):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")

    teacher_dict = teacher.dict(exclude_unset=True, exclude={"id"})

    # Kiểm tra tính duy nhất của email (nếu cần)
    if "email" in teacher_dict:
        existing_teacher = teachers_collection.find_one({"email": teacher_dict["email"]})
        if existing_teacher and str(existing_teacher["_id"]) != teacher_id:
            raise HTTPException(status_code=400, detail="Email đã tồn tại")

    if "role" not in teacher_dict:  # Đảm bảo role không bị mất khi cập nhật
        teacher_dict["role"] = "teacher"

    result = teachers_collection.update_one(
        {"_id": ObjectId(teacher_id)}, {"$set": teacher_dict}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy giáo viên")

    updated_teacher = teachers_collection.find_one({"_id": ObjectId(teacher_id)})
    updated_teacher["id"] = str(updated_teacher.pop("_id"))

    return updated_teacher

# API: Xóa giáo viên theo ID
@router.delete("/{teacher_id}")
async def delete_teacher(teacher_id: str):
    if not ObjectId.is_valid(teacher_id):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")

    result = teachers_collection.delete_one({"_id": ObjectId(teacher_id)})
    if result.deleted_count == 1:
        return {"message": f"Giáo viên {teacher_id} đã bị xóa"}

    raise HTTPException(status_code=404, detail="Không tìm thấy giáo viên")

# API: Tìm kiếm giáo viên theo ID
@router.get("/{teacher_id}", response_model=Teacher)
async def get_teacher_by_id(teacher_id: str):
    if not ObjectId.is_valid(teacher_id):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")

    teacher = teachers_collection.find_one({"_id": ObjectId(teacher_id)})
    if not teacher:
        raise HTTPException(status_code=404, detail="Không tìm thấy giáo viên")

    teacher["id"] = str(teacher.pop("_id"))
    return teacher
