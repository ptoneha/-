"""用户相关数据模型"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str
    password: str


class UserCreate(BaseModel):
    """创建用户请求"""
    username: str
    password: str
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: str = "admin"  # superadmin, admin, editor, viewer


class UserUpdate(BaseModel):
    """更新用户请求"""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserPasswordChange(BaseModel):
    """修改密码请求"""
    old_password: str
    new_password: str


class UserResponse(BaseModel):
    """用户响应"""
    user_id: int
    username: str
    full_name: Optional[str]
    email: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime]

