import io
import logging
from pathlib import Path
from typing import List, Callable, Optional

import fitz
import easyocr
import numpy as np
from PIL import Image
from easyocr import Reader
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

_ocr_reader: Optional[easyocr.Reader] = None

SUPPORTED_LANGUAGES = ["vi", "en"]
MIN_NATIVE_TEXT_LEN = 50 
ZOOM_FACTOR = 2.0 


def get_ocr_reader() -> Reader | None:
    global _ocr_reader
    if _ocr_reader is None:
        logger.info("Initializing EasyOCR reader (first run downloads models)…")
        _ocr_reader = easyocr.Reader(SUPPORTED_LANGUAGES, gpu=False)
        logger.info("EasyOCR ready.")
    return _ocr_reader


ProgressCallback = Callable[[str, int, str], None]


def load_document(
    file_path: str,
    source_name: Optional[str] = None,
    progress_callback: Optional[ProgressCallback] = None,
) -> List[Document]:
    path = Path(file_path)
    suffix = path.suffix.lower()
    source = source_name or path.name

    _emit(progress_callback, "reading_file", 5, f"Đang mở file {source}…")

    if suffix == ".pdf":
        return _load_pdf(file_path, source, progress_callback)
    elif suffix in {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"}:
        return _load_image(file_path, source, progress_callback)
    else:
        raise ValueError(f"Unsupported file type: {suffix!r}")


# ── PDF Loading ───────────────────────────────────────────────────────────────

def _load_pdf(
    file_path: str,
    source: str,
    callback: Optional[ProgressCallback],
) -> List[Document]:
    documents: List[Document] = []
    pdf = fitz.open(file_path)
    total_pages = len(pdf)

    for page_num in range(total_pages):
        pct = int((page_num / max(total_pages, 1)) * 55) + 10
        _emit(
            callback, "ocr", pct,
            f"Đang xử lý trang {page_num + 1}/{total_pages}…",
        )

        page = pdf[page_num]
        text = page.get_text("text").strip()

        if len(text) < MIN_NATIVE_TEXT_LEN:
            # Scanned page → render to image and run EasyOCR
            mat = fitz.Matrix(ZOOM_FACTOR, ZOOM_FACTOR)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_bytes = pix.tobytes("png")
            img_array = np.array(Image.open(io.BytesIO(img_bytes)))

            reader = get_ocr_reader()
            results = reader.readtext(img_array, detail=0, paragraph=True)
            text = " ".join(results)

        if text.strip():
            documents.append(
                Document(
                    page_content=text.strip(),
                    metadata={
                        "source": source,
                        "page": page_num + 1,
                        "total_pages": total_pages,
                        "file_type": "pdf",
                    },
                )
            )

    pdf.close()
    _emit(callback, "ocr_done", 65, f"Đã xử lý {len(documents)} trang từ PDF.")
    return documents

def _load_image(
    file_path: str,
    source: str,
    callback: Optional[ProgressCallback],
) -> List[Document]:
    _emit(callback, "ocr", 30, "Đang chạy OCR trên hình ảnh…")

    img = Image.open(file_path).convert("RGB")
    img_array = np.array(img)

    reader = get_ocr_reader()
    results = reader.readtext(img_array, detail=0, paragraph=True)
    text = " ".join(results)

    _emit(callback, "ocr_done", 65, "Hoàn thành OCR hình ảnh.")

    if text.strip():
        return [
            Document(
                page_content=text.strip(),
                metadata={
                    "source": source,
                    "page": 1,
                    "total_pages": 1,
                    "file_type": "image",
                },
            )
        ]
    return []


# ── Helper ────────────────────────────────────────────────────────────────────

def _emit(
    callback: Optional[ProgressCallback],
    step: str,
    pct: int,
    msg: str,
) -> None:
    if callback:
        try:
            callback(step, pct, msg)
        except Exception:
            pass
