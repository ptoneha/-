"""分片管理服务"""
from typing import Optional, List, Dict, Any

from db import get_conn, release_conn, _query, _query_one, _execute


def list_chunks(
    doc_id: Optional[int] = None,
    kind: Optional[str] = None,
    search: Optional[str] = None,
    verified_only: Optional[bool] = None,
    limit: int = 20,
    offset: int = 0
) -> tuple[List[Dict[str, Any]], int]:
    """获取分片列表"""
    conn = get_conn()
    try:
        where_clauses = ["c.deleted_at IS NULL"]
        params = []
        
        if doc_id:
            where_clauses.append("c.doc_id = %s")
            params.append(doc_id)
        
        if kind:
            where_clauses.append("c.kind = %s")
            params.append(kind)
        
        if search:
            where_clauses.append("c.content_plain ILIKE %s")
            params.append(f"%{search}%")
        
        if verified_only is not None:
            where_clauses.append("c.is_verified = %s")
            params.append(verified_only)
        
        where_sql = " AND ".join(where_clauses)
        
        chunks = _query(
            conn,
            f"""
            SELECT c.chunk_id, c.doc_id, d.title as doc_title, c.kind,
                   c.heading_h1, c.heading_h2, c.content_md,
                   c.is_verified, c.quality_score, c.tokens,
                   c.created_at, c.updated_at
            FROM public.chunk c
            JOIN public.doc d ON c.doc_id = d.doc_id
            WHERE {where_sql}
            ORDER BY c.created_at DESC
            LIMIT %s OFFSET %s
            """,
            params + [limit, offset]
        )
        
        count_row = _query_one(
            conn,
            f"SELECT COUNT(*) as total FROM public.chunk c WHERE {where_sql}",
            params
        )
        total = count_row["total"] if count_row else 0
        
        return chunks, total
    finally:
        release_conn(conn)


def get_chunk_detail(chunk_id: int) -> Optional[Dict[str, Any]]:
    """获取分片详情"""
    conn = get_conn()
    try:
        chunk = _query_one(
            conn,
            """
            SELECT c.*, d.title as doc_title, d.source
            FROM public.chunk c
            JOIN public.doc d ON c.doc_id = d.doc_id
            WHERE c.chunk_id = %s AND c.deleted_at IS NULL
            """,
            (chunk_id,)
        )
        return chunk
    finally:
        release_conn(conn)


def update_chunk(chunk_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """更新分片"""
    conn = get_conn()
    try:
        update_fields = []
        params = []
        
        allowed_fields = [
            "content_md", "content_plain", "kind", "heading_h1", "heading_h2",
            "is_verified", "quality_score"
        ]
        
        for field in allowed_fields:
            if field in updates:
                update_fields.append(f"{field} = %s")
                params.append(updates[field])
        
        if not update_fields:
            return get_chunk_detail(chunk_id)
        
        params.append(chunk_id)
        
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE public.chunk
                SET {', '.join(update_fields)}
                WHERE chunk_id = %s AND deleted_at IS NULL
                RETURNING *
                """,
                params
            )
            row = cur.fetchone()
            if not row:
                return None
            cols = [d[0] for d in cur.description]
            chunk = dict(zip(cols, row))
        
        conn.commit()
        return chunk
    finally:
        release_conn(conn)


def delete_chunk(chunk_id: int, hard_delete: bool = False) -> bool:
    """删除分片"""
    conn = get_conn()
    try:
        if hard_delete:
            _execute(conn, "DELETE FROM public.chunk WHERE chunk_id = %s", (chunk_id,))
        else:
            _execute(
                conn,
                "UPDATE public.chunk SET deleted_at = now() WHERE chunk_id = %s",
                (chunk_id,)
            )
        
        conn.commit()
        return True
    finally:
        release_conn(conn)


def batch_verify_chunks(chunk_ids: List[int], verified: bool = True) -> int:
    """批量审核分片"""
    if not chunk_ids:
        return 0
    
    conn = get_conn()
    try:
        placeholders = ','.join(['%s'] * len(chunk_ids))
        _execute(
            conn,
            f"UPDATE public.chunk SET is_verified = %s WHERE chunk_id IN ({placeholders})",
            [verified] + chunk_ids
        )
        conn.commit()
        return len(chunk_ids)
    finally:
        release_conn(conn)


def batch_delete_chunks(chunk_ids: List[int], hard_delete: bool = False) -> int:
    """批量删除分片"""
    if not chunk_ids:
        return 0
    
    conn = get_conn()
    try:
        placeholders = ','.join(['%s'] * len(chunk_ids))
        
        if hard_delete:
            _execute(
                conn,
                f"DELETE FROM public.chunk WHERE chunk_id IN ({placeholders})",
                chunk_ids
            )
        else:
            _execute(
                conn,
                f"UPDATE public.chunk SET deleted_at = now() WHERE chunk_id IN ({placeholders})",
                chunk_ids
            )
        
        conn.commit()
        return len(chunk_ids)
    finally:
        release_conn(conn)


def get_chunk_stats() -> Dict[str, Any]:
    """获取分片统计信息"""
    conn = get_conn()
    try:
        stats = _query_one(
            conn,
            """
            SELECT 
                COUNT(*) as total_chunks,
                COUNT(CASE WHEN kind = 'definition' THEN 1 END) as definition_count,
                COUNT(CASE WHEN kind = 'theorem' THEN 1 END) as theorem_count,
                COUNT(CASE WHEN kind = 'formula' THEN 1 END) as formula_count,
                COUNT(CASE WHEN kind = 'example' THEN 1 END) as example_count,
                COUNT(CASE WHEN is_verified = true THEN 1 END) as verified_chunks,
                AVG(quality_score) as avg_quality,
                SUM(tokens) as total_tokens
            FROM public.chunk
            WHERE deleted_at IS NULL
            """
        )
        return stats or {}
    finally:
        release_conn(conn)

