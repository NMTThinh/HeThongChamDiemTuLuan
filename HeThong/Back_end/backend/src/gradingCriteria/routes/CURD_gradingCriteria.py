from pydantic import BaseModel, Field
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from src.gradingCriteria.models.gradingCriteria_schema import GradingCriteria
from database.database import gradingCriterias_collection
from bson import ObjectId

router = APIRouter()

# API: Lấy danh sách tiêu chí chấm điểm
@router.get("/", response_model=List[GradingCriteria])
async def get_gradingCriterias():
    gradingCriterias = list(gradingCriterias_collection.find({}))
    for gradingCriteria in gradingCriterias:
        gradingCriteria["id"] = str(gradingCriteria.pop("_id"))
    return gradingCriterias

# API: Thêm tiêu chí chấm điểm mới (POST)
@router.post("/", response_model=GradingCriteria)
async def create_gradingCriteria(gradingCriteria: GradingCriteria):
    if gradingCriterias_collection.find_one({"name": gradingCriteria.name}):
        raise HTTPException(status_code=400, detail="Tên tiêu chí đã tồn tại")

    gradingCriteria_dict = gradingCriteria.dict(exclude={"id"})
    result = gradingCriterias_collection.insert_one(gradingCriteria_dict)
    gradingCriteria_dict["id"] = str(result.inserted_id)
    return gradingCriteria_dict

# API: Cập nhật thông tin tiêu chí chấm điểm (PUT)
@router.put("/{gradingCriteria_id}", response_model=GradingCriteria)
async def update_gradingCriteria(gradingCriteria_id: str, gradingCriteria: GradingCriteria):
    if not ObjectId.is_valid(gradingCriteria_id):
        raise HTTPException(status_code=400, detail="Định dạng ID không hợp lệ")

    if gradingCriterias_collection.find_one({"name": gradingCriteria.name, "_id": {"$ne": ObjectId(gradingCriteria_id)}}):
        raise HTTPException(status_code=400, detail="Tên tiêu chí đã tồn tại")

    gradingCriteria_dict = gradingCriteria.dict(exclude_unset=True, exclude={"id"})
    result = gradingCriterias_collection.update_one(
        {"_id": ObjectId(gradingCriteria_id)}, {"$set": gradingCriteria_dict}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy tiêu chí chấm điểm")

    updated_gradingCriteria = gradingCriterias_collection.find_one({"_id": ObjectId(gradingCriteria_id)})
    updated_gradingCriteria["id"] = str(updated_gradingCriteria.pop("_id"))
    return updated_gradingCriteria

# API: Xóa tiêu chí chấm điểm theo ID
@router.delete("/{gradingCriteria_id}")
async def delete_gradingCriteria(gradingCriteria_id: str):
    if not ObjectId.is_valid(gradingCriteria_id):
        raise HTTPException(status_code=400, detail="Định dạng ID không hợp lệ")

    result = gradingCriterias_collection.delete_one({"_id": ObjectId(gradingCriteria_id)})

    if result.deleted_count == 1:
        return {"message": f"Tiêu chí chấm điểm có ID {gradingCriteria_id} đã được xóa"}
    else:
        raise HTTPException(status_code=404, detail="Không tìm thấy tiêu chí chấm điểm")

# API: Tìm kiếm tiêu chí chấm điểm bằng ID
@router.get("/{gradingCriteria_id}", response_model=GradingCriteria)
async def get_gradingCriteria_by_id(gradingCriteria_id: str):
    if not ObjectId.is_valid(gradingCriteria_id):
        raise HTTPException(status_code=400, detail="Định dạng ID không hợp lệ")

    gradingCriteria = gradingCriterias_collection.find_one({"_id": ObjectId(gradingCriteria_id)})

    if gradingCriteria is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy tiêu chí chấm điểm")

    gradingCriteria["id"] = str(gradingCriteria.pop("_id"))
    return gradingCriteria