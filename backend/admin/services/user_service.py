"""用户管理服务"""
from typing import Optional, List, Dict, Any
from datetime import datetime

from db import get_conn, release_conn, _query, _query_one, _execute
from utils.password import hash_password, verify_password
from admin.models.user import UserCreate, UserUpdate


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """验证用户登录"""
    conn = get_conn()
    try:
        user = _query_one(
            conn,
            """
            SELECT user_id, username, password_hash, full_name, email, role, is_active
            FROM public.admin_user
            WHERE username = %s
            """,
            (username,)
        )
        
        if not user:
            return None
        
        if not user["is_active"]:
            return None
        
        if not verify_password(password, user["password_hash"]):
            return None
        
        # 更新最后登录时间
        _execute(
            conn,
            "UPDATE public.admin_user SET last_login_at = %s WHERE user_id = %s",
            (datetime.utcnow(), user["user_id"])
        )
        conn.commit()
        
        # 不返回密码哈希
        del user["password_hash"]
        return user
        
    finally:
        release_conn(conn)


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """根据ID获取用户"""
    conn = get_conn()
    try:
        user = _query_one(
            conn,
            """
            SELECT user_id, username, full_name, email, role, is_active, 
                   created_at, updated_at, last_login_at
            FROM public.admin_user
            WHERE user_id = %s
            """,
            (user_id,)
        )
        return user
    finally:
        release_conn(conn)


def list_users(limit: int = 50, offset: int = 0) -> tuple[List[Dict[str, Any]], int]:
    """获取用户列表"""
    conn = get_conn()
    try:
        users = _query(
            conn,
            """
            SELECT user_id, username, full_name, email, role, is_active,
                   created_at, last_login_at
            FROM public.admin_user
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            (limit, offset)
        )
        
        count_row = _query_one(conn, "SELECT COUNT(*) as total FROM public.admin_user")
        total = count_row["total"] if count_row else 0
        
        return users, total
    finally:
        release_conn(conn)


def create_user(user_data: UserCreate) -> Dict[str, Any]:
    """创建新用户"""
    conn = get_conn()
    try:
        # 检查用户名是否已存在
        existing = _query_one(
            conn,
            "SELECT user_id FROM public.admin_user WHERE username = %s",
            (user_data.username,)
        )
        if existing:
            raise ValueError("用户名已存在")
        
        # 哈希密码
        password_hash = hash_password(user_data.password)
        
        # 插入用户
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.admin_user (username, password_hash, full_name, email, role)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING user_id, username, full_name, email, role, is_active, created_at
                """,
                (user_data.username, password_hash, user_data.full_name, 
                 user_data.email, user_data.role)
            )
            row = cur.fetchone()
            cols = [d[0] for d in cur.description]
            user = dict(zip(cols, row))
        
        conn.commit()
        return user
    finally:
        release_conn(conn)


def update_user(user_id: int, user_data: UserUpdate) -> Optional[Dict[str, Any]]:
    """更新用户信息"""
    conn = get_conn()
    try:
        # 构建更新字段
        updates = []
        params = []
        
        if user_data.full_name is not None:
            updates.append("full_name = %s")
            params.append(user_data.full_name)
        
        if user_data.email is not None:
            updates.append("email = %s")
            params.append(user_data.email)
        
        if user_data.role is not None:
            updates.append("role = %s")
            params.append(user_data.role)
        
        if user_data.is_active is not None:
            updates.append("is_active = %s")
            params.append(user_data.is_active)
        
        if not updates:
            return get_user_by_id(user_id)
        
        params.append(user_id)
        
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE public.admin_user
                SET {', '.join(updates)}
                WHERE user_id = %s
                RETURNING user_id, username, full_name, email, role, is_active, updated_at
                """,
                params
            )
            row = cur.fetchone()
            if not row:
                return None
            cols = [d[0] for d in cur.description]
            user = dict(zip(cols, row))
        
        conn.commit()
        return user
    finally:
        release_conn(conn)


def change_password(user_id: int, old_password: str, new_password: str) -> bool:
    """修改用户密码"""
    conn = get_conn()
    try:
        # 验证旧密码
        user = _query_one(
            conn,
            "SELECT password_hash FROM public.admin_user WHERE user_id = %s",
            (user_id,)
        )
        
        if not user:
            return False
        
        if not verify_password(old_password, user["password_hash"]):
            return False
        
        # 更新密码
        new_hash = hash_password(new_password)
        _execute(
            conn,
            "UPDATE public.admin_user SET password_hash = %s WHERE user_id = %s",
            (new_hash, user_id)
        )
        conn.commit()
        return True
    finally:
        release_conn(conn)


def delete_user(user_id: int) -> bool:
    """删除用户（软删除，设为不活跃）"""
    conn = get_conn()
    try:
        _execute(
            conn,
            "UPDATE public.admin_user SET is_active = false WHERE user_id = %s",
            (user_id,)
        )
        conn.commit()
        return True
    finally:
        release_conn(conn)

