import asyncio
from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Query
from bson import ObjectId
from datetime import datetime
import os
import shutil
from src.essay.model.essay_schema import EssayStatus
from database.database import essays_collection, students_collection, teachers_collection, gradings_collection, gradingCriterias_collection
from gemini import grade_essay_from_pdf
from auth import get_current_student, get_current_teacher
from bson.errors import InvalidId
router = APIRouter()
UPLOAD_DIR = "uploads"  # Thư mục lưu file

async def get_all_grading_criteria_ids():
    cursor = gradingCriterias_collection.find({}, {"_id": 1})
    criteria = cursor.to_list(None)
    return [str(c["_id"]) for c in criteria]

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

    # Lấy tất cả ID của tiêu chí chấm điểm
    criteria_ids = await get_all_grading_criteria_ids()

    # Chấm điểm AI
    try:
        ai_result = await grade_essay_from_pdf(file_path, title, selected_criteria_ids=criteria_ids)
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

    # Lấy tất cả ID của tiêu chí chấm điểm (chấm lại cũng dùng tất cả)
    criteria_ids = await get_all_grading_criteria_ids()

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
                score = await grade_essay_from_pdf(file_path, essay_title, selected_criteria_ids=criteria_ids)  # Truyền ID tiêu chí
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
async def get_all_essays():
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


@router.get("/my-essays")
async def get_my_essays(current_student: dict = Depends(get_current_student)):
    student_id = ObjectId(current_student["id"])
    essays = list(essays_collection.find({"id_student": student_id}))
    return [convert_objectid(essay) for essay in essays]

@router.get("/teacher/essays")
async def get_essays_for_current_teacher(current_teacher: dict = Depends(get_current_teacher)):
    teacher_id = current_teacher["id"]
    essays = list(essays_collection.find({"id_teacher": ObjectId(teacher_id)}))
    return [convert_objectid(essay) for essay in essays]
@router.get("/teacher/dashboard/stats")
async def get_teacher_dashboard_stats(current_teacher: dict = Depends(get_current_teacher)):
    """
    Lấy thống kê số lượng bài luận được giao cho giáo viên đang đăng nhập.
    """
    try:
        teacher_id = ObjectId(current_teacher["id"])
    except InvalidId:
        raise HTTPException(status_code=400, detail="ID giáo viên không hợp lệ từ token")

    # Đếm tổng số bài được giao
    total_assigned = essays_collection.count_documents({"id_teacher": teacher_id})

    # Đếm số bài đã chấm (approved hoặc rejected)
    graded_count = essays_collection.count_documents({
        "id_teacher": teacher_id,
        "status": {"$in": [EssayStatus.approved, EssayStatus.rejected]}
    })

    # Đếm số bài chưa chấm (pending)
    pending_count = essays_collection.count_documents({
        "id_teacher": teacher_id,
        "status": EssayStatus.pending
    })

    return {
        "total_assigned": total_assigned,
        "graded": graded_count,
        "pending": pending_count
    }

@router.get("/teacher/dashboard/stats/all")
async def get_teacher_stats_by_period(
    period: str = Query("day", enum=["day", "month", "year"]),
    current_teacher: dict = Depends(get_current_teacher)
):
    """
    Lấy thống kê số lượng bài luận được giao cho giáo viên hiện tại theo khoảng thời gian.
    """
    teacher_id = ObjectId(current_teacher["id"])
    data = {"total_assigned": [], "graded": [], "pending": []}
    group_stage = {}

    if period == "day":
        group_stage = {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$submission_date"}},
                "count": {"$sum": 1}
            }
        }
    elif period == "month":
        group_stage = {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m", "date": "$submission_date"}},
                "count": {"$sum": 1}
            }
        }
    elif period == "year":
        group_stage = {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y", "date": "$submission_date"}},
                "count": {"$sum": 1}
            }
        }

    sort_stage = {"$sort": {"_id": 1}}
    match_stage = {"$match": {"id_teacher": teacher_id}}

    # Thống kê tổng số bài được giao
    total_pipeline = [match_stage, group_stage, sort_stage]
    total_assigned_data = list(essays_collection.aggregate(total_pipeline))
    for item in total_assigned_data:
        data["total_assigned"].append({"time": item["_id"], "value": item["count"]})

    # Thống kê số bài đã chấm
    graded_pipeline = [
        match_stage,
        {"$match": {"status": {"$in": [EssayStatus.approved, EssayStatus.rejected]}}},
        group_stage,
        sort_stage
    ]
    graded_essays_data = list(essays_collection.aggregate(graded_pipeline))
    for item in graded_essays_data:
        data["graded"].append({"time": item["_id"], "value": item["count"]})

    # Thống kê số bài chưa chấm
    pending_pipeline = [
        match_stage,
        {"$match": {"status": EssayStatus.pending}},
        group_stage,
        sort_stage
    ]
    pending_essays_data = list(essays_collection.aggregate(pending_pipeline))
    for item in pending_essays_data:
        data["pending"].append({"time": item["_id"], "value": item["count"]})

    return data
@router.get("/my-stats")
async def get_my_essay_stats(current_student: dict = Depends(get_current_student)):
    """
    Lấy thống kê số lượng bài luận cho học sinh đang đăng nhập.
    """
    try:
        student_id = ObjectId(current_student["id"])
    except InvalidId:
         raise HTTPException(status_code=400, detail="ID học sinh không hợp lệ từ token")

    # Đếm tổng số bài đã nộp
    total_submitted = essays_collection.count_documents({"id_student": student_id})

    # Đếm số bài đang xử lý (pending)
    pending_count = essays_collection.count_documents({
        "id_student": student_id,
        "status": EssayStatus.pending # Hoặc "pending"
    })

    # Đếm số bài đã xử lý (approved hoặc rejected)
    processed_count = essays_collection.count_documents({
        "id_student": student_id,
        "status": {"$in": [EssayStatus.approved, EssayStatus.rejected]} # Hoặc ["approved", "rejected"]
    })

    return {
        "total_submitted": total_submitted,
        "pending": pending_count,
        "processed": processed_count
    }
@router.get("/my-stats/all")
async def get_my_stats_by_period(
    period: str = Query("day", enum=["day", "month", "year"]),
    current_student: dict = Depends(get_current_student)
):
    """
    Lấy thống kê số lượng bài luận của sinh viên hiện tại theo khoảng thời gian.
    """
    student_id = ObjectId(current_student["id"])
    data = {"total_submitted": [], "processing": [], "graded": []}
    group_stage = {}

    if period == "day":
        group_stage = {
            "$group": {
                "_id": { "$dateToString": { "format": "%Y-%m-%d", "date": "$submission_date" } },
                "count": { "$sum": 1 }
            }
        }
    elif period == "month":
        group_stage = {
            "$group": {
                "_id": { "$dateToString": { "format": "%Y-%m", "date": "$submission_date" } },
                "count": { "$sum": 1 }
            }
        }
    elif period == "year":
        group_stage = {
            "$group": {
                "_id": { "$dateToString": { "format": "%Y", "date": "$submission_date" } },
                "count": { "$sum": 1 }
            }
        }

    sort_stage = {"$sort": {"_id": 1}}
    match_stage = {"$match": {"id_student": student_id}}

    # Thống kê tổng số bài đã nộp
    total_pipeline = [match_stage, group_stage, sort_stage]
    total_essays_data = list(essays_collection.aggregate(total_pipeline))
    for item in total_essays_data:
        data["total_submitted"].append({"time": item["_id"], "value": item["count"]})

    # Thống kê số bài đang xử lý
    processing_pipeline = [
        match_stage,
        {"$match": {"status": EssayStatus.pending}},
        group_stage,
        sort_stage
    ]
    processing_essays_data = list(essays_collection.aggregate(processing_pipeline))
    for item in processing_essays_data:
        data["processing"].append({"time": item["_id"], "value": item["count"]})

    # Thống kê số bài đã chấm
    graded_pipeline = [
        match_stage,
        {"$match": {"status": {"$in": [EssayStatus.approved, EssayStatus.rejected]}}},
        group_stage,
        sort_stage
    ]
    graded_essays_data = list(essays_collection.aggregate(graded_pipeline))
    for item in graded_essays_data:
        data["graded"].append({"time": item["_id"], "value": item["count"]})

    return data
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