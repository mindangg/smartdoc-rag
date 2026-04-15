# app/api/routes.py
import os
import shutil
import asyncio
from fastapi import APIRouter, UploadFile, File, HTTPException
from langchain_core.messages import HumanMessage, AIMessage

from .schemas import ChatRequest, ChatResponse
from services.document_service import process_pdf
from services.vector_service import create_vector_store, get_retriever
from services.rag_chain import get_standard_rag_chain
from services.corag_chain import get_conversational_rag_chain

router = APIRouter()

# Biến toàn cục (tạm thời) để lưu vector store sau khi upload file
# Trong thực tế sản xuất, bạn sẽ lưu xuống ổ đĩa và load lên
global_vector_store = None


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    global global_vector_store

    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ định dạng PDF")

    try:
        # 1. Lưu file tạm thời
        os.makedirs("data/uploads", exist_ok=True)
        file_path = f"data/uploads/{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 2. Xử lý PDF thành chunks
        chunks = process_pdf(file_path)

        # 3. Tạo Vector Store
        global_vector_store = create_vector_store(chunks)

        return {"message": "Upload và xử lý tài liệu thành công!", "chunks_count": len(chunks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatResponse)
async def chat_parallel(request: ChatRequest):
    if not global_vector_store:
        raise HTTPException(status_code=400, detail="Vui lòng upload tài liệu trước khi chat!")

    try:
        # 1. Khởi tạo Retriever từ Vector Store hiện tại
        retriever = get_retriever(global_vector_store)

        # 2. Khởi tạo 2 chuỗi RAG và coRAG
        rag_chain = get_standard_rag_chain(retriever)
        corag_chain = get_conversational_rag_chain(retriever)

        # 3. Chuyển đổi định dạng lịch sử chat cho Langchain hiểu
        formatted_history = []
        for msg in request.chat_history:
            if msg.role == "user":
                formatted_history.append(HumanMessage(content=msg.content))
            else:
                formatted_history.append(AIMessage(content=msg.content))

        # 4. CHẠY SONG SONG CẢ 2 CHAIN (Điểm cốt lõi của dự án)
        task_rag = rag_chain.ainvoke(request.question)
        task_corag = corag_chain.ainvoke({
            "input": request.question,
            "chat_history": formatted_history
        })

        # Đợi cả 2 mô hình trả lời xong
        result_rag, result_corag = await asyncio.gather(task_rag, task_corag)

        # 5. Trả về kết quả
        return ChatResponse(
            rag_response=result_rag,
            # corag_chain trả về 1 dictionary, kết quả nằm trong key "answer"
            corag_response=result_corag["answer"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))