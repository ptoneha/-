from typing import Any, Dict, List, Optional, Tuple

from db import get_conn, release_conn, _query, _query_one


ALLOWED_KINDS = {"definition", "theorem", "formula", "example", "property", "remark"}


def _neighbors(conn, doc_id: int, chunk_id: int) -> Dict[str, Any]:
    prev_row = _query_one(
        conn,
        """
        SELECT c.chunk_id, d.section_number as section, c.kind, c.heading_h1 as h1,
               c.heading_h2 as h2, c.anchor, c.content_md
        FROM public.chunk c
        JOIN public.doc d ON d.doc_id = c.doc_id
        WHERE c.doc_id = %s AND c.chunk_id < %s
        ORDER BY c.chunk_id DESC
        LIMIT 1
        """,
        (doc_id, chunk_id),
    )
    next_row = _query_one(
        conn,
        """
        SELECT c.chunk_id, d.section_number as section, c.kind, c.heading_h1 as h1,
               c.heading_h2 as h2, c.anchor, c.content_md
        FROM public.chunk c
        JOIN public.doc d ON d.doc_id = c.doc_id
        WHERE c.doc_id = %s AND c.chunk_id > %s
        ORDER BY c.chunk_id ASC
        LIMIT 1
        """,
        (doc_id, chunk_id),
    )
    return {"prev": prev_row, "next": next_row}


def _has_trgm(conn) -> bool:
    try:
        return _query_one(conn, "SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm';") is not None
    except Exception:
        return False


def perform_search(q: Optional[str], kind: Optional[str], section: Optional[int], limit: int, offset: int, neighbor: int, source: Optional[str] = None) -> Tuple[List[Dict[str, Any]], int]:
    conn = get_conn()
    try:
        params: List[Any] = []
        where = ["1=1"]
        use_trgm = _has_trgm(conn)

        listing_mode = (q is None) or (str(q).strip() == "")
        if not listing_mode:
            ilike_param = f"%{q}%"
            where.append("c.content_plain ILIKE %s")
            params.append(ilike_param)

            if use_trgm:
                score_sql = "COALESCE(similarity(c.content_plain, %s), 0) + CASE WHEN c.content_plain ILIKE %s THEN 0.3 ELSE 0 END"
                params_for_select = [q, ilike_param]
            else:
                score_sql = "CASE WHEN c.content_plain ILIKE %s THEN 0.5 ELSE 0 END"
                params_for_select = [ilike_param]
        else:
            # 列表模式：不基于 q 召回，直接按时间倒序展示
            score_sql = "0.0"
            params_for_select = []

        if kind:
            if kind not in ALLOWED_KINDS:
                # 忽略非法 kind
                pass
            else:
                where.append("c.kind = %s")
                params.append(kind)

        if section is not None:
            where.append("d.section_number = %s")
            params.append(section)

        if source:
            where.append("d.source = %s")
            params.append(source)

        order_clause = "ORDER BY score DESC" if not listing_mode else "ORDER BY c.created_at DESC, c.chunk_id DESC"

        sql = f"""
        SELECT c.chunk_id, d.section_number as section, c.kind,
               c.heading_h1 as h1, c.heading_h2 as h2, c.anchor,
               c.content_md, {score_sql} as score, c.doc_id
        FROM public.chunk c
        JOIN public.doc d ON d.doc_id = c.doc_id
        WHERE {' AND '.join(where)}
        {order_clause}
        LIMIT %s OFFSET %s
        """
        rows = _query(conn, sql, params_for_select + params + [limit, offset])

        # 统计总数（不含打分参数，只用 where 的条件）
        count_sql = f"""
        SELECT COUNT(1) AS total
        FROM public.chunk c
        JOIN public.doc d ON d.doc_id = c.doc_id
        WHERE {' AND '.join(where)}
        """
        total_row = _query_one(conn, count_sql, params)
        total = int(total_row["total"]) if total_row and "total" in total_row else 0

        results: List[Dict[str, Any]] = []
        for r in rows:
            item = {
                "chunk_id": r["chunk_id"],
                "section": r["section"],
                "kind": r["kind"],
                "h1": r["h1"],
                "h2": r["h2"],
                "anchor": r["anchor"],
                "content_md": r["content_md"],
                "score": round(float(r["score"] or 0.0), 4),
            }
            if neighbor == 1:
                nbs = _neighbors(conn, doc_id=r["doc_id"], chunk_id=r["chunk_id"]) if r.get("doc_id") else {"prev": None, "next": None}
                item["neighbors"] = nbs
            results.append(item)

        return results, total
    finally:
        release_conn(conn)


def fetch_chunk_detail(chunk_id: int) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    try:
        row = _query_one(
            conn,
            """
            SELECT c.chunk_id, c.doc_id, d.section_number as section, c.kind,
                   c.heading_h1 as h1, c.heading_h2 as h2, c.anchor,
                   c.content_md, c.content_plain, c.canonical, c.tokens, c.created_at
            FROM public.chunk c
            JOIN public.doc d ON d.doc_id = c.doc_id
            WHERE c.chunk_id = %s
            """,
            (chunk_id,),
        )
        return row
    finally:
        release_conn(conn)


def fetch_sections_with_counts(source: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_conn()
    try:
        if source:
            rows = _query(
                conn,
                """
                SELECT COALESCE(d.section_number, 0) AS section, COUNT(1) AS count
                FROM public.chunk c
                JOIN public.doc d ON d.doc_id = c.doc_id
                WHERE d.source = %s
                GROUP BY COALESCE(d.section_number, 0)
                ORDER BY section
                """,
                (source,),
            )
        else:
            rows = _query(
                conn,
                """
                SELECT COALESCE(d.section_number, 0) AS section, COUNT(1) AS count
                FROM public.chunk c
                JOIN public.doc d ON d.doc_id = c.doc_id
                GROUP BY COALESCE(d.section_number, 0)
                ORDER BY section
                """,
            )
        return rows
    finally:
        release_conn(conn)


# 旧版本的 doc 级统计已废弃，统一使用上面的基于 chunk 的统计（支持 source 过滤）


