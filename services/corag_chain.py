# app/services/corag_chain.py
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from services.llm_service import get_llm


def get_conversational_rag_chain(retriever):
    llm = get_llm()

    # ==========================================
    # PHẦN 1: TẠO RETRIEVER CÓ TRÍ NHỚ
    # ==========================================
    # Prompt này chỉ làm 1 việc: Viết lại câu hỏi
    contextualize_q_system_prompt = (
        "Dựa vào lịch sử hội thoại và câu hỏi mới nhất của người dùng "
        "(câu hỏi này có thể đang tham chiếu đến những gì đã nói trước đó), "
        "hãy viết lại thành một câu hỏi độc lập, đầy đủ ý nghĩa mà không cần đọc lại lịch sử.\n"
        "LƯU Ý QUAN TRỌNG: KHÔNG trả lời câu hỏi này. Chỉ viết lại câu hỏi nếu cần thiết, "
        "nếu câu hỏi đã rõ ràng rồi thì trả về nguyên bản."
    )

    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}")  # Biến input này LangChain sẽ tự động truyền câu hỏi vào
    ])

    # Khởi tạo retriever biết đọc lịch sử
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )

    # ==========================================
    # PHẦN 2: TẠO CHAIN TRẢ LỜI CÂU HỎI
    # ==========================================
    # Prompt này mới thực sự là prompt để AI trả lời
    qa_system_prompt = (
        "Bạn là một trợ lý thông minh. Hãy sử dụng các đoạn ngữ cảnh (context) dưới đây "
        "để trả lời câu hỏi của người dùng.\n"
        "Nếu bạn không tìm thấy câu trả lời trong ngữ cảnh, hãy trung thực nói là bạn không biết, "
        "tuyệt đối không được bịa ra thông tin.\n"
        "Trả lời ngắn gọn, súc tích (khoảng 3-4 câu) và BẮT BUỘC bằng tiếng Việt.\n\n"
        "Ngữ cảnh:\n{context}"
    )

    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", qa_system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}")
    ])

    # Khởi tạo chain kết hợp tài liệu để trả lời
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

    # ==========================================
    # PHẦN 3: GỘP CHÚNG LẠI THÀNH CORAG
    # ==========================================
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    return rag_chain