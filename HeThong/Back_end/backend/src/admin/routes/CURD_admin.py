from pydantic import BaseModel, EmailStr
from typing import Optional
from fastapi import APIRouter, HTTPException
from src.admin.models.admin_schema import Admin
from database.database import admins_collection
from auth import hash_password #Import hàm mã hóa mật khẩu
from bson import ObjectId

router = APIRouter()

# API: Lấy danh sách quản trị viên
@router.get("/")
async def get_admins():
    admins = list(admins_collection.find({}))
    for admin in admins:
        admin["id"] = str(admin.pop("_id"))
    return admins

# API: Thêm quản trị viên mới (POST)
@router.post("/", response_model=Admin)
async def create_admin(admin: Admin):
    if admins_collection.find_one({"email": admin.email}):
        raise HTTPException(status_code=400, detail="Email đã tồn tại")

    admin_dict = admin.dict(exclude={"id"})
    admin_dict["password"] = hash_password(admin.password)
    admin_dict["role"] = admin.role if admin.role else "admin"

    result = admins_collection.insert_one(admin_dict)
    admin_dict["id"] = str(result.inserted_id)
    return admin_dict

# API: Cập nhật thông tin quản trị viên (PUT)
@router.put("/{admin_id}", response_model=Admin)
async def update_admin(admin_id: str, admin: Admin):
    if not ObjectId.is_valid(admin_id):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")

    admin_dict = admin.dict(exclude_unset=True, exclude={"id"})

    if "email" in admin_dict:
        existing_admin = admins_collection.find_one({"email": admin_dict["email"]})
        if existing_admin and str(existing_admin["_id"]) != admin_id:
            raise HTTPException(status_code=400, detail="Email đã tồn tại")

    if "role" not in admin_dict:
        admin_dict["role"] = "admin"

    result = admins_collection.update_one(
        {"_id": ObjectId(admin_id)}, {"$set": admin_dict}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy quản trị viên")

    updated_admin = admins_collection.find_one({"_id": ObjectId(admin_id)})
    updated_admin["id"] = str(updated_admin.pop("_id"))

    return updated_admin

# API: Xóa quản trị viên theo ID
@router.delete("/{admin_id}")
async def delete_admin(admin_id: str):
    if not ObjectId.is_valid(admin_id):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")

    result = admins_collection.delete_one({"_id": ObjectId(admin_id)})

    if result.deleted_count == 1:
        return {"message": f"Quản trị viên có ID {admin_id} đã được xóa"}
    else:
        raise HTTPException(status_code=404, detail="Không tìm thấy quản trị viên")

# API: Tìm kiếm quản trị viên bằng ID
@router.get("/{admin_id}", response_model=Admin)
async def get_admin_by_id(admin_id: str):
    if not ObjectId.is_valid(admin_id):
        raise HTTPException(status_code=400, detail="Định dạng ID không hợp lệ")

    admin = admins_collection.find_one({"_id": ObjectId(admin_id)})

    if admin is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy quản trị viên")

    admin["id"] = str(admin.pop("_id"))
    return admin