import os
import threading
from typing import Optional, Sequence, Any

import psycopg2
from psycopg2.pool import SimpleConnectionPool
from dotenv import load_dotenv


_pool_lock = threading.Lock()
_pool: Optional[SimpleConnectionPool] = None

load_dotenv()


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        # 默认连接到 chaoX/docker-compose 内的 pg 服务（5432）
        url = "postgresql://appuser:123456@pg:5432/appdb"
    return url


def get_pool() -> SimpleConnectionPool:
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                _pool = SimpleConnectionPool(minconn=1, maxconn=10, dsn=get_database_url())
    return _pool


def get_conn():
    return get_pool().getconn()


def release_conn(conn) -> None:
    get_pool().putconn(conn)


def _execute(conn, sql: str, params: Optional[Sequence[Any]] = None):
    with conn.cursor() as cur:
        cur.execute(sql, params or [])


def _query(conn, sql: str, params: Optional[Sequence[Any]] = None):
    with conn.cursor() as cur:
        cur.execute(sql, params or [])
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        return [dict(zip(cols, r)) for r in rows]


def _query_one(conn, sql: str, params: Optional[Sequence[Any]] = None):
    with conn.cursor() as cur:
        cur.execute(sql, params or [])
        row = cur.fetchone()
        if row is None:
            return None
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))


def ensure_extensions_and_schema(conn) -> None:
    conn.autocommit = True
    # pg_trgm 扩展
    try:
        _execute(conn, "CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    except Exception:
        # 非超级用户或没有权限时，尽量忽略，不影响基础功能
        pass

    # 表结构
    _execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS public.doc (
          doc_id           BIGSERIAL PRIMARY KEY,
          title            TEXT NOT NULL,
          chapter          INT,
          section_number   INT,
          source_filename  TEXT NOT NULL,
          source           TEXT DEFAULT 'kb',
          sha256           TEXT UNIQUE,
          created_at       TIMESTAMP DEFAULT now()
        );
        """,
    )
    # 兼容旧表：补全 source 列
    _execute(conn, "ALTER TABLE public.doc ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'kb';")

    _execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS public.chunk (
          chunk_id       BIGSERIAL PRIMARY KEY,
          doc_id         BIGINT REFERENCES public.doc(doc_id) ON DELETE CASCADE,
          kind           TEXT NOT NULL,
          heading_h1     TEXT,
          heading_h2     TEXT,
          anchor         TEXT,
          content_md     TEXT NOT NULL,
          content_plain  TEXT NOT NULL,
          canonical      TEXT,
          tokens         INT,
          created_at     TIMESTAMP DEFAULT now()
        );
        """,
    )

    # 索引
    _execute(
        conn,
        """
        CREATE INDEX IF NOT EXISTS idx_chunk_plain_trgm ON public.chunk USING gin (content_plain gin_trgm_ops);
        """,
    )
    _execute(conn, "CREATE INDEX IF NOT EXISTS idx_chunk_kind ON public.chunk (kind);")
    _execute(conn, "CREATE INDEX IF NOT EXISTS idx_chunk_doc ON public.chunk (doc_id);")
    _execute(conn, "CREATE INDEX IF NOT EXISTS idx_doc_source ON public.doc (source);")

    # 题库表：每题作为一条记录
    _execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS public.question (
          qid            BIGSERIAL PRIMARY KEY,
          qtype          TEXT,
          stem_md        TEXT NOT NULL,
          options_json   JSONB,
          answer_text    TEXT,
          explanation_md TEXT,
          tags           TEXT[],
          difficulty     INT,
          source_file    TEXT,
          sha256         TEXT UNIQUE,
          created_at     TIMESTAMP DEFAULT now()
        );
        """,
    )

    # 题库索引（若有 pg_trgm 则创建全文相似度索引）
    try:
        has_trgm = _query_one(conn, "SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm';") is not None
        if has_trgm:
            _execute(conn, "CREATE INDEX IF NOT EXISTS idx_q_stem_trgm ON public.question USING gin (stem_md gin_trgm_ops);")
            _execute(conn, "CREATE INDEX IF NOT EXISTS idx_q_expl_trgm ON public.question USING gin (explanation_md gin_trgm_ops);")
    except Exception:
        pass

    # 可选：vector 扩展与列
    try:
        has_vector = _query_one(conn, "SELECT 1 FROM pg_extension WHERE extname = 'vector';") is not None
        if has_vector:
            _execute(conn, "ALTER TABLE public.chunk ADD COLUMN IF NOT EXISTS embedding vector(768);")
            # ivfflat 需要预先构建
            _execute(
                conn,
                "CREATE INDEX IF NOT EXISTS idx_chunk_embedding ON public.chunk USING ivfflat (embedding vector_cosine_ops);",
            )
    except Exception:
        pass


def init_db() -> None:
    conn = get_conn()
    try:
        ensure_extensions_and_schema(conn)
    finally:
        release_conn(conn)


