from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware  # Import CORS middleware
from fastapi.staticfiles import StaticFiles
from src.student.routes.CURD_student import router as student_router
from src.teacher.routes.CURD_teacher import router as teacher_router
from src.gradingCriteria.routes.CURD_gradingCriteria import router as gradingCriteria_router
from src.essay.routes.CURD_essay import router as essay_router
from src.grading.routes.CURD_grading import router as grading_router
from src.admin.routes.CURD_admin import router as admin_router
from database.database import db
from routes.register import router as register_router  
from routes.login import router as login_router  
from routes.login_admin import router as login_admin_router
from src.dashboard.routes.dashboard import router as dashboard_router
from src.dashboard.routes.teacher_dashboard import router as teacher_dashboard_router
from auth import oauth2_scheme
from dotenv import load_dotenv

app = FastAPI()

load_dotenv()
# ✅ Thêm CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Hoặc ["http://localhost:3000"] để chỉ cho phép frontend
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép tất cả các phương thức (GET, POST, PUT, DELETE, ...)
    allow_headers=["*"],  # Cho phép tất cả các headers
)
@app.get("/")
def read_root():
    return {"message": "🚀 FastAPI server is running!"}

# Kiểm tra kết nối MongoDB
@app.get("/test_db")
async def test_db():
    try:
        collections = db.list_collection_names()
        return {"status": "Connected", "collections": collections}
    except Exception as e:
        return {"status": "Error", "message": str(e)}
    
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Thêm các router
app.include_router(student_router, prefix="/students", tags=["Students"])
app.include_router(teacher_router, prefix="/teachers", tags=["Teachers"])
app.include_router(gradingCriteria_router, prefix="/gradingCriterias", tags=["GradingCriterias"])
app.include_router(essay_router, prefix="/essays", tags=["Essays"])
app.include_router(grading_router, prefix="/gradings", tags=["Gradings"])
app.include_router(admin_router, prefix="/admins", tags=["Admins"])

app.include_router(register_router, prefix="/register")
app.include_router(login_router, prefix="/login")
app.include_router(login_admin_router, prefix="/login_admin")  
app.include_router(dashboard_router)
app.include_router(teacher_dashboard_router)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"📥 Request: {request.method} {request.url}")
    print("🔎 Headers:", dict(request.headers))
    print("🧪 oauth2_scheme:", oauth2_scheme)
    response = await call_next(request)
    print(f"📤 Response status: {response.status_code}")
    return response