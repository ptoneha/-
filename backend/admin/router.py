"""管理系统主路由"""
from fastapi import APIRouter

from admin.routes import (
    auth_routes,
    doc_routes,
    chunk_routes,
    question_routes,
    user_routes,
    audit_routes,
    stats_routes
)


# 创建管理系统主路由
admin_router = APIRouter(prefix="/admin", tags=["管理系统"])

# 注册子路由
admin_router.include_router(auth_routes.router)
admin_router.include_router(doc_routes.router)
admin_router.include_router(chunk_routes.router)
admin_router.include_router(question_routes.router)
admin_router.include_router(user_routes.router)
admin_router.include_router(audit_routes.router)
admin_router.include_router(stats_routes.router)


# 健康检查（无需认证）
@admin_router.get("/health")
async def admin_health():
    """管理系统健康检查"""
    return {"ok": True, "service": "admin", "status": "running"}

