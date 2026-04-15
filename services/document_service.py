# app/services/document_service.py
import os
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from core.config import settings


def process_pdf(file_path: str):
    """Đọc file PDF và chia nhỏ thành các chunks"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Không tìm thấy file: {file_path}")

    # 1. Load document
    loader = PDFPlumberLoader(file_path)
    docs = loader.load()

    # 2. Split text
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP
    )
    chunks = text_splitter.split_documents(docs)

    return chunks