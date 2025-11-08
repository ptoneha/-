"""
简化的认证模块 - 单用户模式，无需登录
"""
from typing import Optional

# 单用户配置
SINGLE_USER = {
    "user_id": 1,
    "username": "admin",
    "role": "superadmin"
}


def get_current_user() -> dict:
    """返回固定的单用户信息"""
    return SINGLE_USER


# 简化的权限检查函数（总是返回单用户）
def require_editor() -> dict:
    return SINGLE_USER


def require_admin() -> dict:
    return SINGLE_USER


def require_superadmin() -> dict:
    return SINGLE_USER

