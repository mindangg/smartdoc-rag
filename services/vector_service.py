# app/services/vector_service.py
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from core.config import settings


def create_vector_store(chunks):
    """Tạo Vector Store từ các chunks tài liệu"""
    # Khởi tạo embedding model
    embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)

    # Tạo FAISS vector store
    vector_store = FAISS.from_documents(chunks, embeddings)

    return vector_store


def get_retriever(vector_store):
    """Lấy retriever từ vector store"""
    return vector_store.as_retriever(
        search_type=settings.SEARCH_TYPE,
        search_kwargs={"k": settings.RETRIEVER_K}
    )
