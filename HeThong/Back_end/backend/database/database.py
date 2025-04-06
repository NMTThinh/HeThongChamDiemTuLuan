import pymongo

# Kết nối đến MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["hethong_database"] 

# Collection cho sinh viên
students_collection = db["students"]
# Collection cho giáo viên
teachers_collection = db["teachers"]
# Collection cho tiêu chí chấm điểm
gradingCriterias_collection = db["gradingCriterias"]
# Collection cho bài luận
essays_collection = db["essays"]
# Collection cho bảng điểm
gradings_collection = db["gradings"]
# Collection cho quản trị viên
admins_collection = db["admins"]