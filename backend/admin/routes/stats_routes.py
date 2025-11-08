"""统计路由"""
from fastapi import APIRouter, Query, Depends

from admin.auth import require_editor
from admin.services.stats_service import (
    get_system_stats, get_dashboard_data, get_content_distribution,
    get_quality_report, get_usage_stats
)


router = APIRouter(prefix="/stats", tags=["统计"])


@router.get("/system")
async def system_stats(current_user: dict = Depends(require_editor)):
    """获取系统统计"""
    stats = get_system_stats()
    return {"ok": True, "stats": stats}


@router.get("/dashboard")
async def dashboard(current_user: dict = Depends(require_editor)):
    """获取仪表板数据"""
    data = get_dashboard_data()
    return {"ok": True, **data}


@router.get("/content-distribution")
async def content_distribution(current_user: dict = Depends(require_editor)):
    """获取内容分布统计"""
    data = get_content_distribution()
    return {"ok": True, **data}


@router.get("/quality-report")
async def quality_report(current_user: dict = Depends(require_editor)):
    """获取质量报告"""
    data = get_quality_report()
    return {"ok": True, **data}


@router.get("/usage")
async def usage_stats(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(require_editor)
):
    """获取使用统计"""
    data = get_usage_stats(days=days)
    return {"ok": True, **data}

