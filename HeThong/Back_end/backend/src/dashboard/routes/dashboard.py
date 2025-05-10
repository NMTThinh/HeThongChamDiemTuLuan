from fastapi import APIRouter, Query
from database.database import essays_collection
from src.essay.model.essay_schema import EssayStatus

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/")
async def get_dashboard_stats():
    # Đếm tổng số bài luận
    num_total_essays = essays_collection.count_documents({})
    # Đếm số bài luận đang chờ xử lý (pending)
    num_processing_essays = essays_collection.count_documents({"status": EssayStatus.pending})
    # Đếm số bài luận đã chấm (approved hoặc rejected)
    num_graded_essays = essays_collection.count_documents(
        {"status": {"$in": [EssayStatus.approved, EssayStatus.rejected]}}
    )

    return {
        "total_essays": num_total_essays,         # Tổng số essay
        "processing_essays": num_processing_essays, # Essay đang xử lý (pending)
        "graded_essays": num_graded_essays          # Essay đã xử lý (approved/rejected)
    }

@router.get("/stats/pie")
async def get_essay_status_pie_data():
    """
    Lấy dữ liệu cho biểu đồ tròn hiển thị tỷ lệ trạng thái essay hiện tại.
    """
    total_essays = await essays_collection.count_documents({})
    processing_essays = await essays_collection.count_documents({"status": EssayStatus.pending})
    graded_essays = await essays_collection.count_documents(
        {"status": {"$in": [EssayStatus.approved, EssayStatus.rejected]}}
    )
    return [
        {"name": "Đang xử lý", "value": processing_essays},
        {"name": "Đã chấm", "value": graded_essays},
        {"name": "Chưa phân loại", "value": total_essays - processing_essays - graded_essays},
    ]

@router.get("/stats/all")
async def get_all_stats_by_period(period: str = Query("day", enum=["day", "month", "year"])):
    # ... (phần code thống kê theo thời gian của bạn vẫn giữ nguyên)
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

    total_pipeline = [group_stage, sort_stage]
    total_essays_data = list(essays_collection.aggregate(total_pipeline))
    for item in total_essays_data:
        data["total_submitted"].append({"time": item["_id"], "value": item["count"]})

    processing_pipeline = [
        {"$match": {"status": EssayStatus.pending}},
        group_stage,
        sort_stage
    ]
    processing_essays_data = list(essays_collection.aggregate(processing_pipeline))
    for item in processing_essays_data:
        data["processing"].append({"time": item["_id"], "value": item["count"]})

    graded_pipeline = [
        {"$match": {"status": {"$in": [EssayStatus.approved, EssayStatus.rejected]}}},
        group_stage,
        sort_stage
    ]
    graded_essays_data = list(essays_collection.aggregate(graded_pipeline))
    for item in graded_essays_data:
        data["graded"].append({"time": item["_id"], "value": item["count"]})

    return data