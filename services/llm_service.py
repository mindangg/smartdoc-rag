# app/services/llm_service.py
from langchain_community.llms import Ollama
from core.config import settings

def get_llm():
    """Khởi tạo và trả về mô hình Ollama"""
    return Ollama(
        model=settings.LLM_MODEL,
        temperature=settings.TEMPERATURE,
        top_p=settings.TOP_P,
        repeat_penalty=settings.REPEAT_PENALTY
    )