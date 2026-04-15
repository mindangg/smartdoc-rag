# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router as api_router # Thêm dòng này

app = FastAPI(
    title="SmartDoc AI API",
    description="Backend API for Parallel RAG & coRAG comparison",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thêm dòng này để đăng ký các API vào hệ thống
app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Welcome to SmartDoc AI API! The server is running."}