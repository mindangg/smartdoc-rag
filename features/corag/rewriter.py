import logging
from langchain_core.messages import SystemMessage, HumanMessage
from core.llm import get_llm

logger = logging.getLogger(__name__)

REWRITE_SYSTEM_PROMPT = """\
Bạn là một chuyên gia phân tích truy vấn tìm kiếm.
Nhiệm vụ của bạn là nhận một câu hỏi của người dùng, phân tích ý nghĩa và tạo ra một câu truy vấn MỚI, TỐI ƯU HƠN để dùng cho hệ thống tìm kiếm Vector Database (Tìm kiếm theo ngữ nghĩa - Semantic Search).

Quy tắc:
1. Tập trung vào các từ khóa chính, loại bỏ các từ dư thừa (từ nối, lời chào, v.v.).
2. Thêm các từ đồng nghĩa hoặc ngữ cảnh nếu nó giúp làm rõ nghĩa.
3. CHỈ TRẢ VỀ CÂU TRUY VẤN MỚI, tuyệt đối không giải thích hay thừa lời.
"""


def rewrite_query(original_query: str) -> str:
    logger.info(f"Rewriting query: {original_query}")
    try:
        messages = [
            SystemMessage(content=REWRITE_SYSTEM_PROMPT),
            HumanMessage(content=original_query)
        ]
        llm = get_llm(streaming=False)
        response = llm.invoke(messages)
        rewritten = response.content.strip()
        logger.info(f"Rewritten query: {rewritten}")
        return rewritten
    except Exception as e:
        logger.error(f"Error rewriting query: {e}")
        return original_query
