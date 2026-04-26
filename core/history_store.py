"""
SQLite-based Q&A history store for SmartDoc RAG.
Stores question + RAG/CoRAG answers per session.
"""
import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("HISTORY_DB_PATH", "./data/history.db")


def init_db() -> None:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  TEXT    NOT NULL,
                question    TEXT    NOT NULL,
                rag_answer  TEXT,
                corag_answer TEXT,
                created_at  TEXT    NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON chat_history(session_id)")
        conn.commit()
    logger.info(f"History DB ready at {DB_PATH}")


@contextmanager
def _connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def save_qa(
    session_id: str,
    question: str,
    rag_answer: Optional[str] = None,
    corag_answer: Optional[str] = None,
) -> int:
    ts = datetime.now().isoformat(timespec="seconds")
    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO chat_history (session_id, question, rag_answer, corag_answer, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, question, rag_answer, corag_answer, ts),
        )
        conn.commit()
        return cursor.lastrowid


def get_history(session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, question, rag_answer, corag_answer, created_at
            FROM chat_history
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (session_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def clear_history(session_id: str) -> int:
    with _connect() as conn:
        cursor = conn.execute(
            "DELETE FROM chat_history WHERE session_id = ?",
            (session_id,),
        )
        conn.commit()
        return cursor.rowcount
