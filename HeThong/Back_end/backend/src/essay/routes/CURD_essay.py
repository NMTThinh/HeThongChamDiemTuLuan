import asyncio
from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from bson import ObjectId
from datetime import datetime
import os
import shutil
from src.essay.model.essay_schema import EssayStatus
from database.database import essays_collection, students_collection, teachers_collection, gradings_collection
from gemini import grade_essay_from_pdf
from auth import get_current_user
router = APIRouter()
UPLOAD_DIR = "uploads"  # Thư mục lưu file

@router.post("/")
async def create_essay(
    id_student: str = Form(...),
    id_teacher: str = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...),
    status: str = Form("pending")
):
    validate_student_teacher(id_student, id_teacher)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    essay_dict = {
        "id_student": ObjectId(id_student),
        "id_teacher": ObjectId(id_teacher),
        "title": title,
        "file_url": f"/{UPLOAD_DIR}/{file.filename}",
        "submission_date": datetime.now(),
        "status": status
    }
    result = essays_collection.insert_one(essay_dict)
    essay_dict["_id"] = result.inserted_id
    essay_id = str(essay_dict["_id"])

    # Chấm điểm AI
    try:
        ai_result = await grade_essay_from_pdf(file_path, title) #thêm title vào đây
        essay_dict["ai_score"] = ai_result
        # Cập nhật ai_score vào database
        essays_collection.update_one(
            {"_id": ObjectId(essay_id)},
            {"$set": {"ai_score": ai_result}}
        )
    except Exception as e:
        essay_dict["ai_score"] = f"Lỗi chấm điểm AI: {str(e)}"

    # Tạo Grading
    grading_dict = {
        "id_essay": ObjectId(essay_id),
        "id_teacher": ObjectId(id_teacher),
        "final_score": None, # Hoặc giá trị mặc định
        "feedback": None, # Hoặc giá trị mặc định
        "ai_score": essay_dict["ai_score"],
        "grading_date": datetime.now()
    }
    grading_result = gradings_collection.insert_one(grading_dict)
    grading_dict["_id"] = grading_result.inserted_id

    return convert_objectid(essay_dict)
@router.post("/grade")
async def grade_essays(files: List[UploadFile] = File(...)):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    results = []

    for file in files:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"File '{file.filename}' không phải PDF.")

        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        try:
            essay = essays_collection.find_one({"file_url": f"/{UPLOAD_DIR}/{file.filename}"})

            if essay:
                essay_title = essay["title"]  # Lấy essay_title từ database
                score = await grade_essay_from_pdf(file_path, essay_title)  # Truyền essay_title
                essays_collection.update_one(
                    {"_id": essay["_id"]},
                    {"$set": {"ai_score": score}}
                )
                results.append({"filename": file.filename, "ai_score": score})
            else:
                results.append({"filename": file.filename, "error": "Không tìm thấy bài luận tương ứng."})
        except Exception as e:
            results.append({"filename": file.filename, "error": str(e)})

    return results
def convert_objectid(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, dict):
        return {k: convert_objectid(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_objectid(v) for v in obj]
    return obj

def validate_student_teacher(id_student: str, id_teacher: str):
    if not ObjectId.is_valid(id_student):
        raise HTTPException(status_code=400, detail="Student ID không hợp lệ")
    if not ObjectId.is_valid(id_teacher):
        raise HTTPException(status_code=400, detail="Teacher ID không hợp lệ")

    student = students_collection.find_one({"_id": ObjectId(id_student)})
    if not student:
        raise HTTPException(status_code=404, detail="Student ID không tồn tại")

    teacher = teachers_collection.find_one({"_id": ObjectId(id_teacher)})
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher ID không tồn tại")

@router.get("/")
async def get_essays():
    essays = list(essays_collection.find({}))
    return [convert_objectid(essay) for essay in essays]

@router.put("/{essay_id}")
async def update_essay(essay_id: str, title: str = Form(...), status: str = Form(...)):
    if not ObjectId.is_valid(essay_id):
        raise HTTPException(status_code=400, detail="Định dạng ID không hợp lệ")
    update_data = {"title": title, "status": status}
    result = essays_collection.update_one({"_id": ObjectId(essay_id)}, {"$set": update_data})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài luận")
    return {"message": "Cập nhật thành công"}

@router.delete("/{essay_id}")
async def delete_essay(essay_id: str):
    if not ObjectId.is_valid(essay_id):
        raise HTTPException(status_code=400, detail="Định dạng ID không hợp lệ")

    # Xóa Grading liên quan
    grading_result = gradings_collection.delete_one({"id_essay": ObjectId(essay_id)})

    # Xóa Essay
    essay_result = essays_collection.delete_one({"_id": ObjectId(essay_id)})

    if essay_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài luận")

    return {"message": "Xóa thành công"}

@router.get("/{essay_id}")
async def get_essay_by_id(essay_id: str):
    if not ObjectId.is_valid(essay_id):
        raise HTTPException(status_code=400, detail="Định dạng ID không hợp lệ")
    
    essay = essays_collection.find_one({"_id": ObjectId(essay_id)})
    if not essay:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài luận")

    # Lấy thêm thông tin student và teacher nếu cần
    student = students_collection.find_one({"_id": essay["id_student"]})
    teacher = teachers_collection.find_one({"_id": essay["id_teacher"]})

    essay["student_name"] = student["name"] if student else None
    essay["teacher_name"] = teacher["name"] if teacher else None

    return convert_objectid(essay)

@router.get("/my")
async def get_my_essays(current_user: str = Depends(get_current_user)):
    # current_user chính là id_student lấy từ token
    try:
        essays = list(essays_collection.find({"id_student": ObjectId(current_user)}))
        return [convert_objectid(essay) for essay in essays]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")