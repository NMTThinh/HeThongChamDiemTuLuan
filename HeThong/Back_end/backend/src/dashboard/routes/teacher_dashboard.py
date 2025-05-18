from bson import ObjectId
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from database.database import students_collection, essays_collection
from typing import Dict

router = APIRouter(prefix="/teacher_dashboard", tags=["Teacher-Dashboard"])

class StatsRequest(BaseModel):
    class_name: str
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD

@router.post("/stats")
async def get_submission_stats(stats_data: StatsRequest):
    try:
        start_date = datetime.strptime(stats_data.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(stats_data.end_date, "%Y-%m-%d")

        # Lấy danh sách học sinh theo lớp
        student_ids = list(students_collection.find({"classinfor": stats_data.class_name}, {"_id": 1, "name": 1}))
        if not student_ids:
            return {"message": "❌ Không có học sinh nào trong lớp này!"}

        student_map = {str(s["_id"]): s["name"] for s in student_ids}

        # Sử dụng aggregation để đếm số bài đã nộp và chưa nộp
        pipeline = [
            {
                "$match": {
                    "id_student": {"$in": list(student_map.keys())},
                    "submission_date": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": "$id_student",
                    "total_submitted": {"$sum": {"$cond": [{"$eq": ["$status", "approved"]}, 1, 0]}},
                    "total_not_submitted": {"$sum": {"$cond": [{"$ne": ["$status", "approved"]}, 1, 0]}}
                }
            }
        ]

        results = list(essays_collection.aggregate(pipeline))

        # Ghép dữ liệu thống kê với tên học sinh
        stats = {}
        for r in results:
            student_id = r["_id"]
            stats[student_map[student_id]] = {
                "student_name": student_map[student_id],
                "total_submitted": r["total_submitted"],
                "total_not_submitted": r["total_not_submitted"]
            }

        # Nếu có học sinh chưa có bài nộp nào thì thêm vào với số lượng = 0
        for student_name in student_map.values():
            if student_name not in stats:
                stats[student_name] = {
                    "student_name": student_name,
                    "total_submitted": 0,
                    "total_not_submitted": 0
                }

        return {"stats": stats}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ Lỗi: {str(e)}")
