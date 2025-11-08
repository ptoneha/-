#!/usr/bin/env python3
"""
手动初始化数据库脚本
如果自动初始化失败，使用此脚本
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_database_url():
    url = os.getenv("DATABASE_URL")
    if not url:
        url = "postgresql://appuser:123456@localhost:5432/appdb"
    return url


def main():
    print("=" * 60)
    print("ChaoX 管理系统 - 手动数据库初始化")
    print("=" * 60)
    print()
    
    # 连接数据库
    db_url = get_database_url()
    print(f"连接数据库: {db_url.split('@')[1]}")
    
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        print("✓ 数据库连接成功")
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        return 1
    
    # 读取SQL文件
    sql_file = "admin_schema_fixed.sql"
    if not os.path.exists(sql_file):
        sql_file = "admin_schema.sql"
    
    if not os.path.exists(sql_file):
        print(f"✗ 找不到SQL文件: {sql_file}")
        return 1
    
    print(f"读取SQL文件: {sql_file}")
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    print(f"SQL文件大小: {len(sql_content)} 字节")
    print()
    
    # 执行SQL
    print("开始执行SQL...")
    print("-" * 60)
    
    try:
        cursor = conn.cursor()
        cursor.execute(sql_content)
        cursor.close()
        print("-" * 60)
        print("✓ SQL执行成功")
    except Exception as e:
        print("-" * 60)
        print(f"✗ SQL执行失败:")
        print(f"   {str(e)}")
        return 1
    
    # 验证表是否创建成功
    print()
    print("验证表创建...")
    
    tables_to_check = [
        'admin_user',
        'audit_log',
        'kb_category',
        'tag'
    ]
    
    cursor = conn.cursor()
    for table in tables_to_check:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM public.{table}")
            count = cursor.fetchone()[0]
            print(f"  ✓ {table}: {count} 条记录")
        except Exception as e:
            print(f"  ✗ {table}: 不存在或错误")
    
    cursor.close()
    conn.close()
    
    print()
    print("=" * 60)
    print("✓ 初始化完成！")
    print("=" * 60)
    print()
    print("默认管理员账号:")
    print("  用户名: admin")
    print("  密码: admin123")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

