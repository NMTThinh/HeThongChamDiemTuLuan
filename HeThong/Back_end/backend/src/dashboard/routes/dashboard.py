from fastapi import APIRouter, Query
from database.database import students_collection, teachers_collection, essays_collection
from datetime import datetime
from bson import ObjectId
from collections import defaultdict

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/")
async def get_dashboard_stats():
    num_students = students_collection.count_documents({})
    num_teachers = teachers_collection.count_documents({})
    num_essays = essays_collection.count_documents({})
    
    return {
        "students": num_students,
        "teachers": num_teachers,
        "essays": num_essays
    }

@router.get("/stats")
async def get_stats(period: str = Query("month", enum=["month", "quarter", "year"])):
    pipeline = [
        {
            "$group": {
                "_id": {
                    "year": { "$year": "$created_at" },
                    "month": { "$month": "$created_at" }
                },
                "total": { "$sum": 1 }
            }
        },
        {
            "$sort": {
                "_id.year": 1,
                "_id.month": 1
            }
        }
    ]

    result = list(essays_collection.aggregate(pipeline))

    data = []

    if period == "month":
        for item in result:
            label = f"Tháng {item['_id']['month']}/{item['_id']['year']}"
            data.append({
                "time": label,
                "essays": item["total"]
            })

    elif period == "quarter":
        quarter_map = defaultdict(int)
        for item in result:
            year = item['_id']['year']
            month = item['_id']['month']
            quarter = (month - 1) // 3 + 1
            key = f"Q{quarter}/{year}"
            quarter_map[key] += item["total"]

        for key, total in quarter_map.items():
            data.append({
                "time": key,
                "essays": total
            })

    elif period == "year":
        year_map = defaultdict(int)
        for item in result:
            year = item['_id']['year']
            year_map[year] += item["total"]

        for year, total in year_map.items():
            data.append({
                "time": str(year),
                "essays": total
            })

    return data
