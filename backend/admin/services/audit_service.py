"""审计日志服务"""
from typing import Optional, List, Dict, Any

from db import get_conn, release_conn, _query, _query_one, _execute
from admin.models.audit import AuditLogCreate


def create_audit_log(log_data: AuditLogCreate) -> int:
    """创建审计日志"""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.audit_log 
                (user_id, username, action, resource_type, resource_id, details, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING log_id
                """,
                (
                    log_data.user_id,
                    log_data.username,
                    log_data.action,
                    log_data.resource_type,
                    log_data.resource_id,
                    log_data.details,
                    log_data.ip_address,
                    log_data.user_agent
                )
            )
            log_id = cur.fetchone()[0]
        
        conn.commit()
        return log_id
    finally:
        release_conn(conn)


def list_audit_logs(
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> tuple[List[Dict[str, Any]], int]:
    """获取审计日志列表"""
    conn = get_conn()
    try:
        where_clauses = ["1=1"]
        params = []
        
        if user_id:
            where_clauses.append("user_id = %s")
            params.append(user_id)
        
        if action:
            where_clauses.append("action = %s")
            params.append(action)
        
        if resource_type:
            where_clauses.append("resource_type = %s")
            params.append(resource_type)
        
        where_sql = " AND ".join(where_clauses)
        
        logs = _query(
            conn,
            f"""
            SELECT log_id, user_id, username, action, resource_type, resource_id,
                   details, ip_address, created_at
            FROM public.audit_log
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            params + [limit, offset]
        )
        
        count_row = _query_one(
            conn,
            f"SELECT COUNT(*) as total FROM public.audit_log WHERE {where_sql}",
            params
        )
        total = count_row["total"] if count_row else 0
        
        return logs, total
    finally:
        release_conn(conn)


def get_user_activity(user_id: int, days: int = 7) -> List[Dict[str, Any]]:
    """获取用户活动统计"""
    conn = get_conn()
    try:
        activity = _query(
            conn,
            """
            SELECT 
                DATE(created_at) as date,
                action,
                COUNT(*) as count
            FROM public.audit_log
            WHERE user_id = %s 
                AND created_at > now() - interval '%s days'
            GROUP BY DATE(created_at), action
            ORDER BY date DESC, action
            """,
            (user_id, days)
        )
        return activity
    finally:
        release_conn(conn)


def get_action_stats(days: int = 30) -> List[Dict[str, Any]]:
    """获取操作统计"""
    conn = get_conn()
    try:
        stats = _query(
            conn,
            """
            SELECT 
                action,
                COUNT(*) as count,
                COUNT(DISTINCT user_id) as unique_users
            FROM public.audit_log
            WHERE created_at > now() - interval '%s days'
            GROUP BY action
            ORDER BY count DESC
            """,
            (days,)
        )
        return stats
    finally:
        release_conn(conn)

