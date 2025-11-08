import io
import os
import shutil
import subprocess
import hashlib
import tempfile
from typing import Optional, Any, Dict

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from db import init_db, get_conn, release_conn, _query, _query_one
from ingest import process_upload
from search import perform_search, fetch_chunk_detail, fetch_sections_with_counts
from ingest_qbank import parse_docx_questions, insert_questions

# 导入管理系统路由
from admin.router import admin_router
from admin.db_init import init_admin_schema


MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_MIME = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx only
}


app = FastAPI(
    title="ChaoX Knowledge Base System",
    version="0.2.0",
    description="知识库管理系统 - 支持文档上传、检索和管理后台"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 提供静态资源（题库导出的图片 /static/qimg/**）
if not os.path.exists("static"):
    os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
def on_startup() -> None:
    """应用启动时初始化数据库"""
    init_db()
    # 初始化管理系统数据库
    try:
        init_admin_schema()
    except Exception as e:
        print(f"管理系统初始化警告: {e}")


@app.get("/health")
def health() -> Dict[str, bool]:
    return {"ok": True}


@app.post("/ingest")
def ingest(
    file: UploadFile = File(...),
    chapter: int = Form(...),
    section_number: int = Form(...),
) -> Dict[str, Any]:
    # 类型与大小校验
    filename_lower = (file.filename or "").lower()
    if not filename_lower.endswith(".docx"):
        raise HTTPException(status_code=400, detail="仅支持 .docx 文件")

    if file.content_type and file.content_type not in ALLOWED_MIME:
        # 某些浏览器可能不给出 content_type，这里宽松处理
        pass

    file_bytes = file.file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小超过 10MB 限制")

    try:
        result = process_upload(
            file_bytes=file_bytes,
            filename=file.filename,
            chapter=chapter,
            section_number=section_number,
        )
        return {"ok": True, **result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析或入库失败: {e}")


@app.get("/search")
def search(
    q: Optional[str] = Query(None),
    kind: Optional[str] = Query(None),
    section: Optional[int] = Query(None),
    limit: int = Query(8, ge=1, le=20),
    offset: int = Query(0, ge=0),
    neighbor: int = Query(1, ge=0, le=1),
    source: Optional[str] = Query(None),
) -> Dict[str, Any]:
    try:
        results, total = perform_search(q=q, kind=kind, section=section, limit=limit, offset=offset, neighbor=neighbor, source=source)
        return {"ok": True, "count": len(results), "total": int(total or 0), "results": results}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {e}")


@app.get("/chunks/{chunk_id}")
def get_chunk(chunk_id: int) -> Dict[str, Any]:
    try:
        detail = fetch_chunk_detail(chunk_id)
        if not detail:
            raise HTTPException(status_code=404, detail="未找到该分片")
        return {"ok": True, **detail}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {e}")


@app.get("/meta/sections")
def meta_sections(source: Optional[str] = Query(None)) -> Dict[str, Any]:
    try:
        data = fetch_sections_with_counts(source=source)
        return {"ok": True, "sections": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取元数据失败: {e}")



@app.get("/search_kb")
def search_kb(
    q: Optional[str] = Query(None),
    kind: Optional[str] = Query(None),
    section: Optional[int] = Query(None),
    limit: int = Query(8, ge=1, le=20),
    offset: int = Query(0, ge=0),
    neighbor: int = Query(1, ge=0, le=1),
) -> Dict[str, Any]:
    results, total = perform_search(q=q, kind=kind, section=section, limit=limit, offset=offset, neighbor=neighbor, source="kb")
    return {"ok": True, "count": len(results), "total": int(total or 0), "results": results}


@app.get("/search_qb")
def search_qb(
    q: Optional[str] = Query(None),
    kind: Optional[str] = Query(None),
    section: Optional[int] = Query(None),
    limit: int = Query(8, ge=1, le=20),
    offset: int = Query(0, ge=0),
    neighbor: int = Query(1, ge=0, le=1),
) -> Dict[str, Any]:
    results, total = perform_search(q=q, kind=kind, section=section, limit=limit, offset=offset, neighbor=neighbor, source="qb")
    return {"ok": True, "count": len(results), "total": int(total or 0), "results": results}

@app.get("/api/knowledge")
@app.get("/knowledge")
def knowledge(
    mode: str = Query("search"),
    q: Optional[str] = Query(None),
    kind: Optional[str] = Query(None),
    section: Optional[int] = Query(None),
    limit: int = Query(8, ge=1, le=20),
    offset: int = Query(0, ge=0),
    neighbor: int = Query(1, ge=0, le=1),
    chunk_id: Optional[int] = Query(None),
    source: Optional[str] = Query(None),
    # 预留：未来可能加入更多模式或参数
) -> Dict[str, Any]:
    try:
        m = (mode or "").strip().lower()
        if m == "search":
            results, total = perform_search(
                q=q, kind=kind, section=section, limit=limit, offset=offset, neighbor=neighbor, source=source
            )
            return {"ok": True, "count": len(results), "total": int(total or 0), "results": results}
        elif m == "detail":
            if chunk_id is None:
                raise HTTPException(status_code=400, detail="detail 模式需要提供 chunk_id")
            detail = fetch_chunk_detail(chunk_id)
            if not detail:
                raise HTTPException(status_code=404, detail="未找到该分片")
            return {"ok": True, **detail}
        elif m == "stats":
            data = fetch_sections_with_counts(source=source)
            return {"ok": True, "sections": data}
        else:
            raise HTTPException(status_code=400, detail="mode 仅支持 search/detail/stats")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"知识库统一接口失败: {e}")



api_q = APIRouter(prefix="/api/qbank", tags=["qbank"])


@api_q.post("/ingest")
def ingest_qbank(
    file: UploadFile = File(...),
    tags: Optional[str] = Form(None),
    default_difficulty: int = Form(2),
) -> Dict[str, Any]:
    filename_lower = (file.filename or "").lower()
    if not filename_lower.endswith(".docx"):
        raise HTTPException(status_code=400, detail="仅支持 .docx 文件")

    file_bytes = file.file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小超过 10MB")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    try:
        rows = parse_docx_questions(tmp_path)
        if tags:
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
            for r in rows:
                r["tags"] = (r.get("tags") or []) + tag_list
        for r in rows:
            r["difficulty"] = r.get("difficulty") or default_difficulty

        count = insert_questions(rows, file.filename)
        return {"ok": True, "questions": count, "source": file.filename}
    finally:
        os.remove(tmp_path)


# ------------------------------ 题库检索接口 ------------------------------

def _has_trgm(conn) -> bool:
    try:
        return _query_one(conn, "SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm';") is not None
    except Exception:
        return False


@api_q.get("/search")
def search_qbank(
    q: Optional[str] = Query(None),
    limit: int = Query(8, ge=1, le=20),
    offset: int = Query(0, ge=0),
) -> Dict[str, Any]:
    conn = get_conn()
    try:
        params: list[Any] = []
        where = ["1=1"]
        use_trgm = _has_trgm(conn)

        listing_mode = (q is None) or (str(q).strip() == "")
        if not listing_mode:
            ilike = f"%{q}%"
            where.append("(stem_md ILIKE %s OR explanation_md ILIKE %s)")
            params.extend([ilike, ilike])
            if use_trgm:
                score_sql = "COALESCE(similarity(stem_md, %s), 0) + COALESCE(similarity(explanation_md, %s), 0) + CASE WHEN stem_md ILIKE %s OR explanation_md ILIKE %s THEN 0.3 ELSE 0 END"
                select_params = [q, q, ilike, ilike]
            else:
                score_sql = "CASE WHEN stem_md ILIKE %s OR explanation_md ILIKE %s THEN 0.5 ELSE 0 END"
                select_params = [ilike, ilike]
        else:
            score_sql = "0.0"
            select_params = []

        order_clause = "ORDER BY score DESC" if not listing_mode else "ORDER BY created_at DESC, qid DESC"

        sql = f"""
        SELECT qid, qtype, stem_md, options_json, answer_text, explanation_md, difficulty, tags, source_file,
               {score_sql} AS score
        FROM public.question
        WHERE {' AND '.join(where)}
        {order_clause}
        LIMIT %s OFFSET %s
        """
        rows = _query(conn, sql, select_params + params + [limit, offset])

        cnt_row = _query_one(conn, f"SELECT COUNT(1) AS total FROM public.question WHERE {' AND '.join(where)}", params)
        total = int(cnt_row["total"]) if cnt_row and "total" in cnt_row else 0

        return {"ok": True, "results": rows, "total": total}
    finally:
        release_conn(conn)


@api_q.get("/detail/{qid}")
def question_detail(qid: int) -> Dict[str, Any]:
    conn = get_conn()
    try:
        row = _query_one(
            conn,
            """
            SELECT qid, qtype, stem_md, options_json, answer_text, explanation_md,
                   difficulty, tags, source_file, created_at
            FROM public.question WHERE qid = %s
            """,
            (qid,),
        )
        if not row:
            raise HTTPException(status_code=404, detail="未找到该题目")
        return row
    finally:
        release_conn(conn)


# 将题库路由在所有定义完成后再包含到应用中
app.include_router(api_q)

# 注册管理系统路由
app.include_router(admin_router)
