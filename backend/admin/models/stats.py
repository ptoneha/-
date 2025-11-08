"""统计数据模型"""
from pydantic import BaseModel
from typing import List, Dict, Any


class SystemStats(BaseModel):
    """系统统计"""
    total_docs: int
    total_chunks: int
    total_questions: int
    active_admins: int
    logs_24h: int


class DocStats(BaseModel):
    """文档统计"""
    doc_id: int
    title: str
    source: str
    chunk_count: int
    avg_quality: float
    total_tokens: int


class DashboardData(BaseModel):
    """仪表板数据"""
    system_stats: SystemStats
    recent_uploads: List[Dict[str, Any]]
    top_searches: List[Dict[str, Any]]
    storage_usage: Dict[str, Any]

