"""审计日志数据模型"""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class AuditLogCreate(BaseModel):
    """创建审计日志"""
    user_id: Optional[int]
    username: str
    action: str  # create, update, delete, export, login, logout
    resource_type: Optional[str] = None  # doc, chunk, question, user
    resource_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AuditLogResponse(BaseModel):
    """审计日志响应"""
    log_id: int
    user_id: Optional[int]
    username: str
    action: str
    resource_type: Optional[str]
    resource_id: Optional[int]
    details: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    created_at: datetime

