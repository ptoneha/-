"""题库管理服务"""
from typing import Optional, List, Dict, Any

from db import get_conn, release_conn, _query, _query_one, _execute


def list_questions(
    qtype: Optional[str] = None,
    difficulty: Optional[int] = None,
    search: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> tuple[List[Dict[str, Any]], int]:
    """获取题目列表"""
    conn = get_conn()
    try:
        where_clauses = ["deleted_at IS NULL"]
        params = []
        
        if qtype:
            where_clauses.append("qtype = %s")
            params.append(qtype)
        
        if difficulty is not None:
            where_clauses.append("difficulty = %s")
            params.append(difficulty)
        
        if search:
            where_clauses.append("stem_md ILIKE %s")
            params.append(f"%{search}%")
        
        where_sql = " AND ".join(where_clauses)
        
        questions = _query(
            conn,
            f"""
            SELECT qid, qtype, stem_md, answer_text, difficulty, tags,
                   is_published, usage_count, source_file, created_at, updated_at
            FROM public.question
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            params + [limit, offset]
        )
        
        count_row = _query_one(
            conn,
            f"SELECT COUNT(*) as total FROM public.question WHERE {where_sql}",
            params
        )
        total = count_row["total"] if count_row else 0
        
        return questions, total
    finally:
        release_conn(conn)


def get_question_detail(qid: int) -> Optional[Dict[str, Any]]:
    """获取题目详情"""
    conn = get_conn()
    try:
        question = _query_one(
            conn,
            """
            SELECT *
            FROM public.question
            WHERE qid = %s AND deleted_at IS NULL
            """,
            (qid,)
        )
        return question
    finally:
        release_conn(conn)


def update_question(qid: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """更新题目"""
    conn = get_conn()
    try:
        update_fields = []
        params = []
        
        allowed_fields = [
            "qtype", "stem_md", "options_json", "answer_text",
            "explanation_md", "tags", "difficulty", "is_published"
        ]
        
        for field in allowed_fields:
            if field in updates:
                update_fields.append(f"{field} = %s")
                params.append(updates[field])
        
        if not update_fields:
            return get_question_detail(qid)
        
        params.append(qid)
        
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE public.question
                SET {', '.join(update_fields)}
                WHERE qid = %s AND deleted_at IS NULL
                RETURNING *
                """,
                params
            )
            row = cur.fetchone()
            if not row:
                return None
            cols = [d[0] for d in cur.description]
            question = dict(zip(cols, row))
        
        conn.commit()
        return question
    finally:
        release_conn(conn)


def delete_question(qid: int, hard_delete: bool = False) -> bool:
    """删除题目"""
    conn = get_conn()
    try:
        if hard_delete:
            _execute(conn, "DELETE FROM public.question WHERE qid = %s", (qid,))
        else:
            _execute(
                conn,
                "UPDATE public.question SET deleted_at = now() WHERE qid = %s",
                (qid,)
            )
        
        conn.commit()
        return True
    finally:
        release_conn(conn)


def batch_delete_questions(qids: List[int], hard_delete: bool = False) -> int:
    """批量删除题目"""
    if not qids:
        return 0
    
    conn = get_conn()
    try:
        placeholders = ','.join(['%s'] * len(qids))
        
        if hard_delete:
            _execute(
                conn,
                f"DELETE FROM public.question WHERE qid IN ({placeholders})",
                qids
            )
        else:
            _execute(
                conn,
                f"UPDATE public.question SET deleted_at = now() WHERE qid IN ({placeholders})",
                qids
            )
        
        conn.commit()
        return len(qids)
    finally:
        release_conn(conn)


def get_question_stats() -> Dict[str, Any]:
    """获取题库统计信息"""
    conn = get_conn()
    try:
        stats = _query_one(
            conn,
            """
            SELECT 
                COUNT(*) as total_questions,
                COUNT(CASE WHEN qtype = '选择题' THEN 1 END) as choice_count,
                COUNT(CASE WHEN qtype = '填空题' THEN 1 END) as blank_count,
                COUNT(CASE WHEN qtype = '解答题' THEN 1 END) as answer_count,
                COUNT(CASE WHEN difficulty = 1 THEN 1 END) as easy_count,
                COUNT(CASE WHEN difficulty = 2 THEN 1 END) as medium_count,
                COUNT(CASE WHEN difficulty = 3 THEN 1 END) as hard_count,
                COUNT(CASE WHEN is_published = true THEN 1 END) as published_count,
                SUM(usage_count) as total_usage
            FROM public.question
            WHERE deleted_at IS NULL
            """
        )
        return stats or {}
    finally:
        release_conn(conn)

