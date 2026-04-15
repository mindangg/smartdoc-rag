# app/core/config.py
class Settings:
    PROJECT_NAME: str = "SmartDoc AI - Parallel RAG"

    # LLM Config [cite: 370, 371, 372, 373, 374]
    LLM_MODEL: str = "qwen2.5:7b"
    TEMPERATURE: float = 0.7
    TOP_P: float = 0.9
    REPEAT_PENALTY: float = 1.1

    # Embedding Config [cite: 337, 338, 339, 348, 349]
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

    # Document Processing Config [cite: 170, 171, 173, 174, 176]
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 100

    # Retriever Config [cite: 214, 215, 218, 219]
    RETRIEVER_K: int = 3
    SEARCH_TYPE: str = "similarity"


settings = Settings()