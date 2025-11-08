"""用户管理路由"""
from fastapi import APIRouter, HTTPException, Query, Depends, Request

from admin.auth_simple import require_admin, require_superadmin
from admin.models.user import UserCreate, UserUpdate
from admin.services.user_service import (
    list_users, get_user_by_id, create_user, update_user, delete_user
)
from admin.services.audit_service import create_audit_log
from admin.models.audit import AuditLogCreate


router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("")
async def list_all_users(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_admin)
):
    """获取用户列表"""
    users, total = list_users(limit=limit, offset=offset)
    return {
        "ok": True,
        "data": users,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/{user_id}")
async def get_user(
    user_id: int,
    current_user: dict = Depends(require_admin)
):
    """获取用户详情"""
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {"ok": True, "data": user}


@router.post("")
async def create_new_user(
    user_data: UserCreate,
    request: Request,
    current_user: dict = Depends(require_superadmin)
):
    """创建新用户（仅超级管理员）"""
    try:
        user = create_user(user_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # 记录审计日志
    try:
        create_audit_log(AuditLogCreate(
            user_id=current_user["user_id"],
            username=current_user["username"],
            action="create",
            resource_type="user",
            resource_id=user["user_id"],
            details={"username": user["username"], "role": user["role"]},
            ip_address=request.client.host if request.client else None
        ))
    except:
        pass
    
    return {"ok": True, "data": user}


@router.put("/{user_id}")
async def update_user_route(
    user_id: int,
    user_data: UserUpdate,
    request: Request,
    current_user: dict = Depends(require_admin)
):
    """更新用户"""
    user = update_user(user_id, user_data)
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 记录审计日志
    try:
        create_audit_log(AuditLogCreate(
            user_id=current_user["user_id"],
            username=current_user["username"],
            action="update",
            resource_type="user",
            resource_id=user_id,
            details={"updates": user_data.dict(exclude_unset=True)},
            ip_address=request.client.host if request.client else None
        ))
    except:
        pass
    
    return {"ok": True, "data": user}


@router.delete("/{user_id}")
async def delete_user_route(
    user_id: int,
    request: Request,
    current_user: dict = Depends(require_superadmin)
):
    """删除用户（仅超级管理员）"""
    if user_id == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="不能删除自己")
    
    success = delete_user(user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 记录审计日志
    try:
        create_audit_log(AuditLogCreate(
            user_id=current_user["user_id"],
            username=current_user["username"],
            action="delete",
            resource_type="user",
            resource_id=user_id,
            ip_address=request.client.host if request.client else None
        ))
    except:
        pass
    
    return {"ok": True, "message": "用户已删除"}

