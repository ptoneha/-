"""审计日志路由"""
from typing import Optional
from fastapi import APIRouter, Query, Depends

from admin.auth_simple import require_admin
from admin.services.audit_service import list_audit_logs, get_user_activity, get_action_stats


router = APIRouter(prefix="/audit", tags=["审计日志"])


@router.get("/logs")
async def get_audit_logs(
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_admin)
):
    """获取审计日志列表"""
    logs, total = list_audit_logs(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        limit=limit,
        offset=offset
    )
    return {
        "ok": True,
        "data": logs,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/activity/{user_id}")
async def user_activity(
    user_id: int,
    days: int = Query(7, ge=1, le=90),
    current_user: dict = Depends(require_admin)
):
    """获取用户活动统计"""
    activity = get_user_activity(user_id, days=days)
    return {"ok": True, "activity": activity}


@router.get("/action-stats")
async def action_statistics(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(require_admin)
):
    """获取操作统计"""
    stats = get_action_stats(days=days)
    return {"ok": True, "stats": stats}

