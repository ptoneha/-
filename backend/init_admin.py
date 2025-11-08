#!/usr/bin/env python3
"""
ChaoX 管理系统初始化脚本
用于快速初始化管理系统数据库和创建管理员账户
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from admin.db_init import init_admin_schema
from admin.services.user_service import create_user, get_user_by_id
from admin.models.user import UserCreate


def main():
    print("=" * 60)
    print("ChaoX 管理系统初始化")
    print("=" * 60)
    print()
    
    # 初始化数据库
    print("📊 正在初始化数据库结构...")
    try:
        init_admin_schema()
        print("✅ 数据库结构初始化成功")
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return
    
    print()
    print("=" * 60)
    print("管理员账户设置")
    print("=" * 60)
    print()
    
    # 检查是否需要创建新管理员
    choice = input("是否创建新的管理员账户？(默认admin已存在) [y/N]: ").strip().lower()
    
    if choice == 'y':
        print()
        username = input("请输入用户名: ").strip()
        password = input("请输入密码: ").strip()
        full_name = input("请输入全名（可选）: ").strip() or None
        email = input("请输入邮箱（可选）: ").strip() or None
        
        print()
        print("选择角色:")
        print("  1. superadmin (超级管理员)")
        print("  2. admin (管理员)")
        print("  3. editor (编辑)")
        print("  4. viewer (查看者)")
        role_choice = input("请选择 [1-4]: ").strip()
        
        role_map = {
            '1': 'superadmin',
            '2': 'admin',
            '3': 'editor',
            '4': 'viewer'
        }
        role = role_map.get(role_choice, 'admin')
        
        try:
            user_data = UserCreate(
                username=username,
                password=password,
                full_name=full_name,
                email=email,
                role=role
            )
            user = create_user(user_data)
            print()
            print("✅ 管理员账户创建成功！")
            print(f"   用户名: {user['username']}")
            print(f"   角色: {user['role']}")
        except Exception as e:
            print(f"❌ 创建失败: {e}")
            return
    else:
        print()
        print("使用默认管理员账户:")
        print("   用户名: admin")
        print("   密码: admin123")
        print("   ⚠️  请在首次登录后立即修改密码！")
    
    print()
    print("=" * 60)
    print("初始化完成！")
    print("=" * 60)
    print()
    print("接下来的步骤:")
    print("  1. 启动后端服务: uvicorn app:app --reload --port 8787")
    print("  2. 访问API文档: http://localhost:8787/docs")
    print("  3. 登录管理后台: POST /admin/auth/login")
    print()
    print("详细文档:")
    print("  - 使用指南: backend/ADMIN_GUIDE.md")
    print("  - 部署指南: backend/DEPLOYMENT.md")
    print("  - 架构设计: ARCHITECTURE.md")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        sys.exit(1)

