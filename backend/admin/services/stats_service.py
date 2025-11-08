"""统计服务"""
from typing import Dict, Any, List
from datetime import datetime, timedelta

from db import get_conn, release_conn, _query, _query_one


def get_system_stats() -> Dict[str, Any]:
    """获取系统统计数据"""
    conn = get_conn()
    try:
        stats = _query_one(
            conn,
            """
            SELECT * FROM v_admin_stats
            """
        )
        return stats or {}
    finally:
        release_conn(conn)


def get_dashboard_data() -> Dict[str, Any]:
    """获取仪表板数据"""
    conn = get_conn()
    try:
        # 系统统计
        system_stats = get_system_stats()
        
        # 最近上传的文档
        recent_uploads = _query(
            conn,
            """
            SELECT doc_id, title, source, created_at
            FROM public.doc
            WHERE deleted_at IS NULL
            ORDER BY created_at DESC
            LIMIT 10
            """
        )
        
        # 热门搜索（从审计日志分析）
        top_searches = _query(
            conn,
            """
            SELECT 
                details->>'query' as query,
                COUNT(*) as count
            FROM public.audit_log
            WHERE action = 'search' 
                AND created_at > now() - interval '7 days'
                AND details->>'query' IS NOT NULL
            GROUP BY details->>'query'
            ORDER BY count DESC
            LIMIT 10
            """
        )
        
        # 存储使用情况
        storage_usage = _query_one(
            conn,
            """
            SELECT 
                COUNT(DISTINCT d.doc_id) as doc_count,
                COUNT(c.chunk_id) as chunk_count,
                SUM(c.tokens) as total_tokens,
                pg_database_size(current_database()) as db_size
            FROM public.doc d
            LEFT JOIN public.chunk c ON d.doc_id = c.doc_id
            WHERE d.deleted_at IS NULL AND c.deleted_at IS NULL
            """
        )
        
        # 每日上传趋势（最近30天）
        upload_trend = _query(
            conn,
            """
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as count
            FROM public.doc
            WHERE created_at > now() - interval '30 days'
                AND deleted_at IS NULL
            GROUP BY DATE(created_at)
            ORDER BY date DESC
            """
        )
        
        return {
            "system_stats": system_stats,
            "recent_uploads": recent_uploads,
            "top_searches": top_searches,
            "storage_usage": storage_usage,
            "upload_trend": upload_trend
        }
    finally:
        release_conn(conn)


def get_content_distribution() -> Dict[str, Any]:
    """获取内容分布统计"""
    conn = get_conn()
    try:
        # 按类型分布
        kind_dist = _query(
            conn,
            """
            SELECT kind, COUNT(*) as count
            FROM public.chunk
            WHERE deleted_at IS NULL
            GROUP BY kind
            ORDER BY count DESC
            """
        )
        
        # 按章节分布
        section_dist = _query(
            conn,
            """
            SELECT 
                d.section_number,
                COUNT(DISTINCT d.doc_id) as doc_count,
                COUNT(c.chunk_id) as chunk_count
            FROM public.doc d
            LEFT JOIN public.chunk c ON d.doc_id = c.doc_id AND c.deleted_at IS NULL
            WHERE d.deleted_at IS NULL
            GROUP BY d.section_number
            ORDER BY d.section_number
            """
        )
        
        # 按来源分布
        source_dist = _query(
            conn,
            """
            SELECT 
                source,
                COUNT(*) as doc_count
            FROM public.doc
            WHERE deleted_at IS NULL
            GROUP BY source
            """
        )
        
        return {
            "by_kind": kind_dist,
            "by_section": section_dist,
            "by_source": source_dist
        }
    finally:
        release_conn(conn)


def get_quality_report() -> Dict[str, Any]:
    """获取质量报告"""
    conn = get_conn()
    try:
        # 分片质量分布
        quality_dist = _query(
            conn,
            """
            SELECT 
                CASE 
                    WHEN quality_score >= 80 THEN 'excellent'
                    WHEN quality_score >= 60 THEN 'good'
                    WHEN quality_score >= 40 THEN 'fair'
                    ELSE 'poor'
                END as quality_level,
                COUNT(*) as count
            FROM public.chunk
            WHERE deleted_at IS NULL AND quality_score > 0
            GROUP BY quality_level
            """
        )
        
        # 待审核分片
        unverified = _query_one(
            conn,
            """
            SELECT COUNT(*) as count
            FROM public.chunk
            WHERE deleted_at IS NULL AND is_verified = false
            """
        )
        
        # 低质量文档（平均质量<50分）
        low_quality_docs = _query(
            conn,
            """
            SELECT 
                d.doc_id,
                d.title,
                AVG(c.quality_score) as avg_quality,
                COUNT(c.chunk_id) as chunk_count
            FROM public.doc d
            JOIN public.chunk c ON d.doc_id = c.doc_id
            WHERE d.deleted_at IS NULL AND c.deleted_at IS NULL
            GROUP BY d.doc_id, d.title
            HAVING AVG(c.quality_score) < 50
            ORDER BY avg_quality ASC
            LIMIT 10
            """
        )
        
        return {
            "quality_distribution": quality_dist,
            "unverified_count": unverified.get("count", 0) if unverified else 0,
            "low_quality_docs": low_quality_docs
        }
    finally:
        release_conn(conn)


def get_usage_stats(days: int = 30) -> Dict[str, Any]:
    """获取使用统计"""
    conn = get_conn()
    try:
        # 搜索量趋势
        search_trend = _query(
            conn,
            """
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as count
            FROM public.audit_log
            WHERE action = 'search'
                AND created_at > now() - interval '%s days'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
            """,
            (days,)
        )
        
        # 活跃用户
        active_users = _query(
            conn,
            """
            SELECT 
                user_id,
                username,
                COUNT(*) as action_count,
                MAX(created_at) as last_active
            FROM public.audit_log
            WHERE created_at > now() - interval '%s days'
            GROUP BY user_id, username
            ORDER BY action_count DESC
            LIMIT 10
            """,
            (days,)
        )
        
        return {
            "search_trend": search_trend,
            "active_users": active_users
        }
    finally:
        release_conn(conn)

