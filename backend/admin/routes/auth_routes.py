"""认证路由"""
from fastapi import APIRouter, HTTPException, status, Request
from datetime import timedelta

from admin.models.user import UserLogin, UserResponse, UserPasswordChange
from admin.services.user_service import authenticate_user, get_user_by_id, change_password
from admin.services.audit_service import create_audit_log
from admin.models.audit import AuditLogCreate
from admin.auth import get_current_user
from utils.jwt_handler import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from fastapi import Depends


router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login")
async def login(credentials: UserLogin, request: Request):
    """管理员登录"""
    user = authenticate_user(credentials.username, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # 创建访问令牌
    access_token = create_access_token(
        data={
            "user_id": user["user_id"],
            "username": user["username"],
            "role": user["role"]
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    # 记录登录日志
    try:
        create_audit_log(AuditLogCreate(
            user_id=user["user_id"],
            username=user["username"],
            action="login",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        ))
    except:
        pass  # 日志记录失败不影响登录
    
    return {
        "ok": True,
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "user_id": user["user_id"],
            "username": user["username"],
            "full_name": user.get("full_name"),
            "email": user.get("email"),
            "role": user["role"]
        }
    }


@router.post("/logout")
async def logout(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """管理员登出"""
    try:
        create_audit_log(AuditLogCreate(
            user_id=current_user["user_id"],
            username=current_user["username"],
            action="logout",
            ip_address=request.client.host if request.client else None
        ))
    except:
        pass
    
    return {"ok": True, "message": "登出成功"}


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    user = get_user_by_id(current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {"ok": True, "user": user}


@router.post("/change-password")
async def change_password_route(
    password_data: UserPasswordChange,
    current_user: dict = Depends(get_current_user)
):
    """修改密码"""
    success = change_password(
        current_user["user_id"],
        password_data.old_password,
        password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )
    
    # 记录日志
    try:
        create_audit_log(AuditLogCreate(
            user_id=current_user["user_id"],
            username=current_user["username"],
            action="change_password",
            resource_type="user",
            resource_id=current_user["user_id"]
        ))
    except:
        pass
    
    return {"ok": True, "message": "密码修改成功"}

