# app/api/schemas.py
from pydantic import BaseModel
from typing import List, Optional

# Cấu trúc 1 tin nhắn trong lịch sử chat
class ChatMessage(BaseModel):
    role: str # "user" hoặc "assistant"
    content: str

# Cấu trúc dữ liệu khi Frontend gửi câu hỏi lên
class ChatRequest(BaseModel):
    question: str
    chat_history: Optional[List[ChatMessage]] = []

# Cấu trúc dữ liệu API trả về cho Frontend
class ChatResponse(BaseModel):
    rag_response: str
    corag_response: str
