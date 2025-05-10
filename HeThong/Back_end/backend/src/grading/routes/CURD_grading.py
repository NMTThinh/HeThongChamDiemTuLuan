from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from datetime import datetime
from src.grading.models.grading_schema import Grading
from database.database import gradings_collection, essays_collection, teachers_collection
from auth import get_current_teacher
router = APIRouter()

def convert_objectid(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, dict):
        return {k: convert_objectid(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_objectid(v) for v in obj]
    return obj

def validate_essay_teacher(id_essay: str, id_teacher: str):
    if not ObjectId.is_valid(id_essay):
        raise HTTPException(status_code=400, detail="Essay ID không hợp lệ")
    if not ObjectId.is_valid(id_teacher):
        raise HTTPException(status_code=400, detail="Teacher ID không hợp lệ")

    essay = essays_collection.find_one({"_id": ObjectId(id_essay)})
    if not essay:
        raise HTTPException(status_code=404, detail="Essay ID không tồn tại")

    teacher = teachers_collection.find_one({"_id": ObjectId(id_teacher)})
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher ID không tồn tại")

@router.get("/")
async def get_gradings():
    gradings = list(gradings_collection.find({}))
    for grading in gradings:
        grading["id"] = str(grading["_id"])
        grading["id_essay"] = str(grading["id_essay"])
        grading["id_teacher"] = str(grading["id_teacher"])
        grading.pop("_id", None)
    return gradings

@router.get("/me")
async def get_my_gradings(current_teacher: dict = Depends(get_current_teacher)):
    """
    Lấy danh sách các bài chấm điểm của giáo viên đang đăng nhập.
    """
    teacher_id = current_teacher["id"]
    gradings = list(gradings_collection.find({"id_teacher": ObjectId(teacher_id)}))
    for grading in gradings:
        grading["id"] = str(grading["_id"])
        grading["id_essay"] = str(grading["id_essay"])
        grading["id_teacher"] = str(grading["id_teacher"])
        grading.pop("_id", None)
    return gradings

@router.get("/essay/{essay_id}")
async def get_gradings_by_essay_id(essay_id: str):
    """
    Lấy danh sách các bài chấm điểm theo ID của bài luận.
    """
    if not ObjectId.is_valid(essay_id):
        raise HTTPException(status_code=400, detail="Essay ID không hợp lệ")

    gradings = list(gradings_collection.find({"id_essay": ObjectId(essay_id)}))
    if not gradings:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy chấm điểm nào cho Essay ID: {essay_id}")

    for grading in gradings:
        grading["id"] = str(grading["_id"])
        grading["id_essay"] = str(grading["id_essay"])
        grading["id_teacher"] = str(grading["id_teacher"])
        grading.pop("_id", None)
    return gradings

@router.post("/")
async def create_grading(grading: Grading):
    validate_essay_teacher(grading.id_essay, grading.id_teacher)
    
    # Tìm bài essay để lấy ai_score
    essay = essays_collection.find_one({"_id": ObjectId(grading.id_essay)})
    if not essay:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài essay")
    
    ai_score = essay.get("ai_score")  # Lấy điểm AI từ bài essay
    
    grading_dict = grading.dict(exclude={"id"})
    grading_dict["id_essay"] = ObjectId(grading.id_essay)
    grading_dict["id_teacher"] = ObjectId(grading.id_teacher)
    grading_dict["grading_date"] = datetime.now()
    
    # Gán ai_score từ essay vào grading
    grading_dict["ai_score"] = ai_score  

    result = gradings_collection.insert_one(grading_dict)
    grading_dict["id"] = str(result.inserted_id)
    grading_dict["id_essay"] = str(grading_dict["id_essay"])
    grading_dict["id_teacher"] = str(grading_dict["id_teacher"])
    
    return convert_objectid(grading_dict)


@router.put("/{grading_id}")
async def update_grading(grading_id: str, grading: Grading):
    if not ObjectId.is_valid(grading_id):
        raise HTTPException(status_code=400, detail="Định dạng ID không hợp lệ")
    
    validate_essay_teacher(grading.id_essay, grading.id_teacher)
    
    grading_dict = grading.dict(exclude_unset=True, exclude={"id"})
    if "id_essay" in grading_dict:
        grading_dict["id_essay"] = ObjectId(grading_dict["id_essay"])
    if "id_teacher" in grading_dict:
        grading_dict["id_teacher"] = ObjectId(grading_dict["id_teacher"])
    
    result = gradings_collection.update_one({"_id": ObjectId(grading_id)}, {"$set": grading_dict})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy chấm điểm")
    
    return {"message": "Cập nhật thành công"}

@router.delete("/{grading_id}")
async def delete_grading(grading_id: str):
    if not ObjectId.is_valid(grading_id):
        raise HTTPException(status_code=400, detail="Định dạng ID không hợp lệ")
    
    result = gradings_collection.delete_one({"_id": ObjectId(grading_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy chấm điểm")
    
    return {"message": "Xóa thành công"}

@router.get("/{grading_id}")
async def get_grading_by_id(grading_id: str):
    if not ObjectId.is_valid(grading_id):
        raise HTTPException(status_code=400, detail="Định dạng ID không hợp lệ")
    
    grading = gradings_collection.find_one({"_id": ObjectId(grading_id)})
    if not grading:
        raise HTTPException(status_code=404, detail="Không tìm thấy chấm điểm")
    
    grading["id"] = str(grading["_id"])
    grading["id_essay"] = str(grading["id_essay"])
    grading["id_teacher"] = str(grading["id_teacher"])
    grading.pop("_id", None)
    return grading
