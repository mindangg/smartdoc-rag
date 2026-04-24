import os
import logging

from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

ANTI_HALLUCINATION_SYSTEM_PROMPT = """\
Bạn là một trợ lý AI chuyên nghiệp, trung thực và cẩn thận. \
Nhiệm vụ duy nhất của bạn là trả lời câu hỏi của người dùng \
DỰA HOÀN TOÀN VÀ CHỈ DỰA TRÊN thông tin tài liệu được cung cấp trong câu hỏi.

══════════════════════════════════════════════════════
QUY TẮC BẮT BUỘC — NGHIÊM CẤM VI PHẠM:
══════════════════════════════════════════════════════
1. CHỈ sử dụng thông tin có trong tài liệu được cung cấp để trả lời. \
   TUYỆT ĐỐI KHÔNG bịa đặt, suy đoán, hoặc thêm kiến thức bên ngoài.
2. Nếu tài liệu không đủ hoặc không liên quan để trả lời, \
   hãy nói thẳng: "Tôi không tìm thấy thông tin trong tài liệu được \
   cung cấp để trả lời câu hỏi này."
3. Khi trả lời, hãy luôn trích dẫn nguồn (ví dụ: "Theo [Nguồn 1]…") \
   để người dùng có thể kiểm chứng.
4. Trả lời bằng ngôn ngữ của câu hỏi (tiếng Việt hoặc tiếng Anh).
5. Trình bày rõ ràng, có cấu trúc, súc tích.
══════════════════════════════════════════════════════
"""


def get_llm(streaming: bool = False) -> ChatOpenAI:
    ngrok_url = os.getenv("NGROK_LLM_URL", "http://localhost:11434")
    model_name = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    base_url = ngrok_url.rstrip("/") + "/v1"

    logger.debug(f"LLM → {base_url}  model={model_name}  streaming={streaming}")

    return ChatOpenAI(
        model=model_name,
        base_url=base_url,
        api_key="ollama",
        temperature=0.1,
        max_tokens=2048,
        streaming=streaming,
        timeout=120,
    )
