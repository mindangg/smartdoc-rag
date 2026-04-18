# SmartDoc RAG 🦾

**Intelligent Document Q&A System** — kết hợp Standard RAG + **CoRAG (Corrective RAG)** với Local LLM qua Ollama/Ngrok.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite + Zustand |
| Backend | FastAPI + LangChain + **LangGraph** |
| Vector DB | FAISS (local) |
| Embeddings | `paraphrase-multilingual-mpnet-base-v2` |
| OCR | EasyOCR (tự động download model) |
| LLM | Ollama (exposed via Ngrok) |
| Web Search | Tavily API (fallback: DuckDuckGo) |
| CoRAG Eval | CrossEncoder `ms-marco-MiniLM-L-6-v2` |

---

## Cấu Trúc Thư Mục

```
smartdoc-rag/
├── app.py                       # FastAPI entrypoint
├── .env                         # Cấu hình (ngrok URL, API keys)
├── requirements.txt
├── core/
│   ├── document_loader.py       # PDF + EasyOCR
│   ├── embeddings.py            # MPNet singleton
│   ├── vector_store.py          # FAISS persist/load
│   ├── retriever.py             # Similarity search
│   ├── llm.py                   # Ollama client + anti-hallucination prompt
│   └── rag_chain.py             # Standard RAG
├── features/
│   ├── citation_tracker.py
│   └── corag/
│       ├── evaluator.py         # Cross-encoder context eval
│       ├── web_search.py        # Tavily + DuckDuckGo
│       └── corag_chain.py       # LangGraph CoRAG pipeline
├── api/
│   ├── schemas.py               # Pydantic models
│   └── routes/
│       ├── upload.py            # POST /api/upload (SSE)
│       └── query.py             # POST /api/query  (SSE)
└── frontend/                    # Vite React app
    └── src/
        ├── components/
        │   ├── Sidebar.jsx
        │   ├── upload/DropZone.jsx
        │   ├── upload/ProgressStepper.jsx
        │   ├── chat/ChatPanel.jsx
        │   ├── chat/MessageBubble.jsx
        │   ├── chat/CitationCard.jsx
        │   └── query/QueryProgress.jsx
        ├── store/chatStore.js   # Zustand global state
        └── services/api.js      # SSE fetch helpers
```

---

## Cài Đặt & Chạy

### 1. Cấu hình `.env`

```env
NGROK_LLM_URL=https://xxxx.ngrok-free.app   # URL ngrok của Ollama trên Colab
OLLAMA_MODEL=llama3.2                         # Tên model trong Ollama
TAVILY_API_KEY=tvly-xxxxxxxxxxxx              # Tavily API key của bạn
```

### 2. Backend (Python)

```bash
# Tạo và kích hoạt venv (đã làm)
source venv/bin/activate

# Cài packages
pip install -r requirements.txt

# Chạy server (port 8000)
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

> ⚠️ **Lần đầu chạy**: EasyOCR (~120 MB) và MPNet embedding (~450 MB) và CrossEncoder (~80 MB) sẽ tự động tải về.

### 3. Frontend (React)

```bash
cd frontend
npm run dev
# → http://localhost:5173
```

---

## Cấu Hình Ollama Trên Colab

Trên Google Colab, chạy Ollama và expose qua Ngrok:

```python
# Cell 1 — Cài đặt
!apt-get update
!apt-get install -y zstd
!curl -fsSL https://ollama.com/install.sh | sh

import os
import threading
import subprocess
import time

def run_ollama():
    os.environ['OLLAMA_HOST'] = '0.0.0.0:11434'
    subprocess.run(['ollama', 'serve'])

threading.Thread(target=run_ollama, daemon=True).start()

time.sleep(10)
print("Ollama server đã sẵn sàng!")

# Cell 2 — Khởi động Ollama
!ollama run qwen2.5:7b "Chào bạn, bạn đang chạy trên Google Colab phải không?"

# Cell 3 — Pull model
!pip install pyngrok

from pyngrok import ngrok
conf = ngrok.set_auth_token("YOUR_NGROK_AUTH_TOKEN")  # Thay bằng auth token của bạn

public_url = ngrok.connect(11434, "http")
print(f"Địa chỉ API Ollama công khai của bạn là: {public_url}")
# Copy URL này vào .env

```

---

## CoRAG Pipeline

```
Query
  │
  ▼
[Retrieve] FAISS top-5
  │
  ▼
[Evaluate] Cross-encoder score
  │
  ├─ score ≥ 0.35 ──► [Generate] LLM → Answer
  │
  └─ score < 0.35 ──► [Web Search] Tavily
                            │
                            ▼
                       [Generate] LLM (context + web) → Answer
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/upload` | Upload file → SSE stream |
| POST | `/api/query` | Q&A query → SSE stream |
| GET | `/api/stats` | Vector count |
| GET | `/api/health` | Health check |
| GET | `/docs` | Swagger UI |

---

## SSE Event Format

### Upload events (`step` field)
`reading_file` → `ocr` → `ocr_done` → `chunking` → `chunking_done` → `embedding` → `indexing` → `done`

### Query events (`step` field)
`retrieval` → `retrieval_done` → `evaluating` → `evaluation_done` → [`web_search` → `web_search_done`] → `generating` → `answer`
