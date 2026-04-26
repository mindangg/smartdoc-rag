import asyncio
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.document_loader import load_document
from core.vector_store import add_documents, get_document_count

logger = logging.getLogger(__name__)

router = APIRouter()

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
MAX_FILE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
MAX_FILE_BYTES = MAX_FILE_MB * 1024 * 1024

SUPPORTED_EXTENSIONS = {
    ".pdf", ".png", ".jpg", ".jpeg",
    ".tiff", ".tif", ".bmp", ".webp",
    ".docx",
}

TMP_DIR = Path("./data/uploads")
TMP_DIR.mkdir(parents=True, exist_ok=True)

def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

async def _process_upload(file_path: str, filename: str) -> AsyncGenerator[str, None]:
    try:
        yield _sse({"step": "reading_file", "message": f"Đang đọc file {filename}", "progress": 5})

        yield _sse({"step": "ocr", "message": "Đang phân tích & OCR tài liệu", "progress": 15})

        documents = await asyncio.to_thread(load_document, file_path, filename, None)

        if not documents:
            yield _sse({"step": "error", "message": "Không trích xuất được nội dung.", "progress": 0})
            return

        yield _sse({"step": "ocr_done", "message": f"OCR xong {len(documents)} trang.", "progress": 45})

        yield _sse({"step": "chunking", "message": "Đang chia nhỏ văn bản", "progress": 55})

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
        )
        
        chunks = await asyncio.to_thread(splitter.split_documents, documents)

        yield _sse({"step": "chunking_done", "message": f"Tạo được {len(chunks)} chunks.", "progress": 65})

        yield _sse({"step": "indexing", "message": "Đang lưu vào Vector Store", "progress": 85})

        await asyncio.to_thread(add_documents, chunks)

        total_vectors = get_document_count()
        yield _sse({
            "step": "done",
            "progress": 100,
            "chunk_count": len(chunks),
            "total_vectors": total_vectors,
            "filename": filename,
        })

    except Exception as exc:
        logger.exception(f"Upload error: {exc}")
        yield _sse({"step": "error", "message": str(exc), "progress": 0})
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"File type '{suffix}' không được hỗ trợ. "
                f"Chấp nhận: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            ),
        )

    content = await file.read()
    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File vượt quá giới hạn {MAX_FILE_MB} MB.",
        )

    tmp = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
        dir=str(TMP_DIR),
        prefix="upload_",
    )
    tmp.write(content)
    tmp.flush()
    tmp.close()

    return StreamingResponse(
        _process_upload(tmp.name, file.filename or "document"),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
