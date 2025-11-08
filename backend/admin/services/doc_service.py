"""文档管理服务"""
from typing import Optional, List, Dict, Any

from db import get_conn, release_conn, _query, _query_one, _execute


def list_docs(
    source: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> tuple[List[Dict[str, Any]], int]:
    """获取文档列表"""
    conn = get_conn()
    try:
        where_clauses = ["d.deleted_at IS NULL"]
        params = []
        
        if source:
            where_clauses.append("d.source = %s")
            params.append(source)
        
        if search:
            where_clauses.append("d.title ILIKE %s")
            params.append(f"%{search}%")
        
        where_sql = " AND ".join(where_clauses)
        
        docs = _query(
            conn,
            f"""
            SELECT d.doc_id, d.title, d.chapter, d.section_number, d.source,
                   d.source_filename, d.is_published, d.created_at, d.updated_at,
                   COUNT(c.chunk_id) as chunk_count
            FROM public.doc d
            LEFT JOIN public.chunk c ON d.doc_id = c.doc_id AND c.deleted_at IS NULL
            WHERE {where_sql}
            GROUP BY d.doc_id
            ORDER BY d.created_at DESC
            LIMIT %s OFFSET %s
            """,
            params + [limit, offset]
        )
        
        count_row = _query_one(
            conn,
            f"SELECT COUNT(*) as total FROM public.doc d WHERE {where_sql}",
            params
        )
        total = count_row["total"] if count_row else 0
        
        return docs, total
    finally:
        release_conn(conn)


def get_doc_detail(doc_id: int) -> Optional[Dict[str, Any]]:
    """获取文档详情"""
    conn = get_conn()
    try:
        doc = _query_one(
            conn,
            """
            SELECT d.*, 
                   COUNT(c.chunk_id) as chunk_count,
                   SUM(c.tokens) as total_tokens,
                   AVG(c.quality_score) as avg_quality
            FROM public.doc d
            LEFT JOIN public.chunk c ON d.doc_id = c.doc_id AND c.deleted_at IS NULL
            WHERE d.doc_id = %s AND d.deleted_at IS NULL
            GROUP BY d.doc_id
            """,
            (doc_id,)
        )
        return doc
    finally:
        release_conn(conn)


def update_doc(doc_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """更新文档"""
    conn = get_conn()
    try:
        update_fields = []
        params = []
        
        allowed_fields = ["title", "chapter", "section_number", "is_published"]
        for field in allowed_fields:
            if field in updates:
                update_fields.append(f"{field} = %s")
                params.append(updates[field])
        
        if not update_fields:
            return get_doc_detail(doc_id)
        
        params.append(doc_id)
        
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE public.doc
                SET {', '.join(update_fields)}
                WHERE doc_id = %s AND deleted_at IS NULL
                RETURNING *
                """,
                params
            )
            row = cur.fetchone()
            if not row:
                return None
            cols = [d[0] for d in cur.description]
            doc = dict(zip(cols, row))
        
        conn.commit()
        return doc
    finally:
        release_conn(conn)


def delete_doc(doc_id: int, hard_delete: bool = False) -> bool:
    """删除文档（软删除或硬删除）"""
    conn = get_conn()
    try:
        if hard_delete:
            # 硬删除：级联删除chunks
            _execute(conn, "DELETE FROM public.doc WHERE doc_id = %s", (doc_id,))
        else:
            # 软删除
            _execute(
                conn,
                "UPDATE public.doc SET deleted_at = now() WHERE doc_id = %s",
                (doc_id,)
            )
            # 同时软删除关联的chunks
            _execute(
                conn,
                "UPDATE public.chunk SET deleted_at = now() WHERE doc_id = %s AND deleted_at IS NULL",
                (doc_id,)
            )
        
        conn.commit()
        return True
    finally:
        release_conn(conn)


def batch_delete_docs(doc_ids: List[int], hard_delete: bool = False) -> int:
    """批量删除文档"""
    if not doc_ids:
        return 0
    
    conn = get_conn()
    try:
        placeholders = ','.join(['%s'] * len(doc_ids))
        
        if hard_delete:
            _execute(
                conn,
                f"DELETE FROM public.doc WHERE doc_id IN ({placeholders})",
                doc_ids
            )
        else:
            _execute(
                conn,
                f"UPDATE public.doc SET deleted_at = now() WHERE doc_id IN ({placeholders})",
                doc_ids
            )
            _execute(
                conn,
                f"UPDATE public.chunk SET deleted_at = now() WHERE doc_id IN ({placeholders}) AND deleted_at IS NULL",
                doc_ids
            )
        
        conn.commit()
        return len(doc_ids)
    finally:
        release_conn(conn)


def get_doc_stats() -> Dict[str, Any]:
    """获取文档统计信息"""
    conn = get_conn()
    try:
        stats = _query_one(
            conn,
            """
            SELECT 
                COUNT(*) as total_docs,
                COUNT(CASE WHEN source = 'kb' THEN 1 END) as kb_docs,
                COUNT(CASE WHEN source = 'qb' THEN 1 END) as qb_docs,
                COUNT(CASE WHEN is_published = true THEN 1 END) as published_docs,
                COUNT(CASE WHEN is_published = false THEN 1 END) as draft_docs
            FROM public.doc
            WHERE deleted_at IS NULL
            """
        )
        return stats or {}
    finally:
        release_conn(conn)

