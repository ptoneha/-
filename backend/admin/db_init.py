"""管理系统数据库初始化"""
import os
from db import get_conn, release_conn, _execute


def init_admin_schema():
    """初始化管理系统数据库结构"""
    conn = get_conn()
    try:
        conn.autocommit = True
        
        # 读取SQL文件（优先使用fixed版本）
        sql_file_fixed = os.path.join(os.path.dirname(__file__), "../admin_schema_fixed.sql")
        sql_file = os.path.join(os.path.dirname(__file__), "../admin_schema.sql")
        
        # 优先使用fixed版本
        if os.path.exists(sql_file_fixed):
            target_sql = sql_file_fixed
        elif os.path.exists(sql_file):
            target_sql = sql_file
        else:
            print(f"警告: 找不到SQL初始化文件")
            return
        
        with open(target_sql, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 直接执行整个SQL（PostgreSQL支持）
        try:
            _execute(conn, sql_content)
            print(f"✓ 使用 {os.path.basename(target_sql)} 初始化成功")
        except Exception as e:
            print(f"执行SQL时出错: {str(e)}")
        
        print("✓ 管理系统数据库初始化完成")
        
    except Exception as e:
        print(f"✗ 管理系统数据库初始化失败: {e}")
    finally:
        release_conn(conn)


if __name__ == "__main__":
    init_admin_schema()

