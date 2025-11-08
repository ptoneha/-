"""认证与权限管理"""
from typing import Optional
from fastapi import HTTPException, status, Depends, Header

from utils.jwt_handler import decode_access_token


# 权限级别
ROLE_HIERARCHY = {
    "superadmin": 4,
    "admin": 3,
    "editor": 2,
    "viewer": 1,
}


def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """从请求头获取当前用户"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 解析 Bearer token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌格式",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = parts[1]
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或过期的令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload


def require_role(required_role: str):
    """要求特定角色权限的依赖项"""
    def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role", "viewer")
        
        if ROLE_HIERARCHY.get(user_role, 0) < ROLE_HIERARCHY.get(required_role, 99):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要 {required_role} 或更高权限"
            )
        
        return current_user
    
    return role_checker


# 快捷依赖项
def require_superadmin(current_user: dict = Depends(get_current_user)) -> dict:
    """要求超级管理员权限"""
    return require_role("superadmin")(current_user)


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """要求管理员权限"""
    return require_role("admin")(current_user)


def require_editor(current_user: dict = Depends(get_current_user)) -> dict:
    """要求编辑权限"""
    return require_role("editor")(current_user)

